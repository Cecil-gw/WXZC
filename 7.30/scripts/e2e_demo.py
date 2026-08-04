"""端到端演示脚本：一条命令跑通 登录 → 上传 → 训练 → 预测 → 生成邮件。

使用方式（在项目根目录执行）：

    python scripts/e2e_demo.py
    python scripts/e2e_demo.py --file data/sample_insurance.xlsx
    python scripts/e2e_demo.py --host 127.0.0.1 --port 5000

依赖：`pip install requests`（已包含在 requirements.txt 中）。
前置：主项目已启动（`python run_flask.py`），且默认管理员账号可用。

脚本按顺序调用 10 个核心接口，每步打印进度与结果摘要，
最终以表格形式输出执行总结，方便快速验证系统健康度。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests


STEP_WIDTH = 60


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def _print_header(title: str) -> None:
    print()
    print("=" * STEP_WIDTH)
    print(f"  {title}")
    print("=" * STEP_WIDTH)


def _print_step(step_no: int, title: str) -> None:
    print(f"\n[{step_no:>2}] {title}")
    print("-" * STEP_WIDTH)


def _pretty(data: Any, indent: int = 2) -> str:
    """将任意数据格式化为易读字符串。"""
    if isinstance(data, (dict, list)):
        try:
            return json.dumps(data, ensure_ascii=False, indent=indent)
        except (TypeError, ValueError):
            return str(data)
    return str(data)


def _request(
    method: str,
    url: str,
    *,
    step_no: int,
    title: str,
    expected_code: int = 200,
    **kwargs: Any,
) -> Dict[str, Any]:
    """统一封装的 HTTP 请求：打印 → 发送 → 校验业务 code → 返回 data。"""
    _print_step(step_no, title)
    t0 = time.time()
    resp = requests.request(method, url, timeout=60, **kwargs)
    elapsed = time.time() - t0

    print(f"  HTTP {resp.status_code} ({elapsed:.2f}s)")

    try:
        payload = resp.json()
    except ValueError:
        print(f"  [WARN] 响应非 JSON：{resp.text[:200]}")
        resp.raise_for_status()
        return {}

    # 校验业务 code（项目统一使用 code==0 表示成功）
    code = payload.get("code", -1)
    msg = payload.get("message", "")
    data = payload.get("data")

    if resp.status_code != expected_code:
        print(f"  [FAIL] HTTP 状态码异常：期望 {expected_code}，实际 {resp.status_code}")
        print(f"  响应体：{_pretty(payload)[:500]}")
        raise SystemExit(1)

    if code != 0:
        print(f"  [FAIL] 业务错误 code={code}，message={msg}")
        print(f"  响应体：{_pretty(payload)[:500]}")
        raise SystemExit(1)

    # 摘要打印
    if isinstance(data, dict):
        keys = list(data.keys())
        preview = {k: (f"... ({len(v)} items)" if isinstance(v, (list, dict)) and len(str(v)) > 80 else v) for k, v in data.items()}
        print(f"  OK → 字段：{keys}")
        print(f"  摘要：{_pretty(preview)[:400]}")
    else:
        print(f"  OK → data={_pretty(data)[:200]}")

    return {
        "http_status": resp.status_code,
        "elapsed": elapsed,
        "code": code,
        "message": msg,
        "data": data,
    }


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def run_demo(args: argparse.Namespace) -> int:
    base = f"http://{args.host}:{args.port}"
    print(f"目标地址：{base}")
    print(f"账号：{args.username}")

    summary_rows = []  # (步骤, 标题, 状态, 耗时)

    def record(step: int, title: str, ok: bool, elapsed: float) -> None:
        summary_rows.append((step, title, "✓" if ok else "✗", f"{elapsed:.2f}s"))

    # ---- 1. 登录获取 token ----
    step_no = 1
    t0 = time.time()
    login_resp = _request(
        "POST",
        f"{base}/api/v1/auth/login",
        step_no=step_no,
        title="登录获取 Token",
        json={"username": args.username, "password": args.password},
    )
    token = (login_resp.get("data") or {}).get("token")
    if not token:
        print("[FAIL] 登录响应中未找到 token 字段")
        return 1
    record(step_no, "登录", True, time.time() - t0)

    headers = {"Authorization": f"Bearer {token}"}

    # ---- 2. 上传 Excel ----
    step_no += 1
    file_path = Path(args.file)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path
    if not file_path.exists():
        print(f"[WARN] 数据文件不存在：{file_path}，跳过上传步骤")
        record(step_no, f"上传 {file_path.name}", False, 0.0)
        data_uploaded = False
    else:
        t0 = time.time()
        with file_path.open("rb") as f:
            upload_resp = _request(
                "POST",
                f"{base}/api/v1/data/upload",
                step_no=step_no,
                title=f"上传 Excel：{file_path.name}",
                headers=headers,
                files={"file": (file_path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
        imported = (upload_resp.get("data") or {}).get("imported_count", "?")
        print(f"  导入行数：{imported}")
        record(step_no, "上传 Excel", True, time.time() - t0)
        data_uploaded = True

    # ---- 3. 查询数据统计 ----
    step_no += 1
    t0 = time.time()
    stats_resp = _request(
        "GET",
        f"{base}/api/v1/data/statistics",
        step_no=step_no,
        title="查询数据统计",
        headers=headers,
    )
    total = (stats_resp.get("data") or {}).get("total", "?")
    print(f"  客户总数：{total}")
    record(step_no, "数据统计", True, time.time() - t0)

    if not data_uploaded:
        print("\n[SKIP] 未上传数据，后续步骤依赖数据与模型，将跳过部分接口。")

    # ---- 4. 训练模型（XGBoost） ----
    step_no += 1
    t0 = time.time()
    try:
        train_resp = _request(
            "POST",
            f"{base}/api/v1/model/train",
            step_no=step_no,
            title="训练模型（XGBoost）",
            headers=headers,
            json={"models": ["XGBoost"]},
        )
        best_model = (train_resp.get("data") or {}).get("best_model", "?")
        results = (train_resp.get("data") or {}).get("results", {})
        best_auc = "?"
        if isinstance(results, dict):
            for name, metrics in results.items():
                if isinstance(metrics, dict) and "roc_auc" in metrics:
                    auc = metrics["roc_auc"]
                    if best_auc == "?" or (isinstance(auc, (int, float)) and isinstance(best_auc, (int, float)) and auc > best_auc):
                        best_auc = auc
            # 若只训练一个模型，直接取该模型的 AUC
            if best_auc == "?" and best_model in results:
                m = results[best_model]
                if isinstance(m, dict):
                    best_auc = m.get("roc_auc", "?")
        print(f"  最佳模型：{best_model}  AUC={best_auc}")
        record(step_no, "训练模型", True, time.time() - t0)
    except SystemExit:
        record(step_no, "训练模型", False, time.time() - t0)
        best_model = None

    # ---- 5. 获取最佳模型 ----
    step_no += 1
    t0 = time.time()
    try:
        best_resp = _request(
            "GET",
            f"{base}/api/v1/model/best",
            step_no=step_no,
            title="获取当前最佳模型",
            headers=headers,
        )
        best_info = best_resp.get("data") or {}
        print(f"  模型：{best_info.get('model_name')}  AUC={best_info.get('roc_auc')}")
        record(step_no, "获取最佳模型", True, time.time() - t0)
    except SystemExit:
        record(step_no, "获取最佳模型", False, time.time() - t0)

    # ---- 6. 全量预测 ----
    step_no += 1
    t0 = time.time()
    try:
        predict_resp = _request(
            "POST",
            f"{base}/api/v1/model/predict",
            step_no=step_no,
            title="全量预测",
            headers=headers,
            json={},
        )
        predicted_count = (predict_resp.get("data") or {}).get("predicted_count", "?")
        model_name = (predict_resp.get("data") or {}).get("model_name", "?")
        print(f"  使用模型：{model_name}，预测客户数：{predicted_count}")
        record(step_no, "全量预测", True, time.time() - t0)
    except SystemExit:
        record(step_no, "全量预测", False, time.time() - t0)

    # ---- 7. 查询高潜客户 ----
    step_no += 1
    t0 = time.time()
    try:
        targets_resp = _request(
            "GET",
            f"{base}/api/v1/email/targets",
            step_no=step_no,
            title="查询高潜客户（默认 percentile=0.9）",
            headers=headers,
            params={"percentile": 0.9, "page": 1, "per_page": 10},
        )
        targets_data = targets_resp.get("data") or {}
        high_total = targets_data.get("total", "?")
        threshold = targets_data.get("threshold", "?")
        customers = targets_data.get("customers") or []
        print(f"  高潜总数：{high_total}，阈值：{threshold}")
        if customers:
            sample = customers[0]
            print(f"  Top1 样本：id={sample.get('id')} prob={sample.get('predicted_prob')}")
        record(step_no, "高潜客户", True, time.time() - t0)
    except SystemExit:
        record(step_no, "高潜客户", False, time.time() - t0)
        customers = []

    # ---- 8. 批量生成邮件 ----
    step_no += 1
    t0 = time.time()
    try:
        # 优先使用高潜客户 ID，否则用 limit=3 触发降级演示
        customer_ids = [c.get("id") for c in customers[:3] if c.get("id") is not None]
        payload: Dict[str, Any]
        if customer_ids:
            payload = {"customer_ids": customer_ids}
        else:
            payload = {"limit": 3}
        email_resp = _request(
            "POST",
            f"{base}/api/v1/email/generate",
            step_no=step_no,
            title="批量生成邮件（无 LLM Key 时将降级）",
            headers=headers,
            json=payload,
        )
        email_data = email_resp.get("data") or {}
        generated = email_data.get("generated_count", 0)
        failed = email_data.get("failed_count", 0)
        print(f"  生成：{generated}  失败（降级）：{failed}")
        record(step_no, "生成邮件", True, time.time() - t0)
    except SystemExit:
        record(step_no, "生成邮件", False, time.time() - t0)

    # ---- 9. 查询邮件记录 ----
    step_no += 1
    t0 = time.time()
    try:
        records_resp = _request(
            "GET",
            f"{base}/api/v1/email/records",
            step_no=step_no,
            title="查询邮件记录",
            headers=headers,
            params={"page": 1, "per_page": 5},
        )
        records_data = records_resp.get("data") or {}
        items = records_data.get("items") or []
        total_records = records_data.get("total", len(items))
        print(f"  邮件记录总数：{total_records}")
        if items:
            top = items[0]
            print(f"  最新主题：{top.get('email_subject', '')[:60]}")
        record(step_no, "邮件记录", True, time.time() - t0)
    except SystemExit:
        record(step_no, "邮件记录", False, time.time() - t0)

    # ---- 10. 查询操作日志 ----
    step_no += 1
    t0 = time.time()
    try:
        logs_resp = _request(
            "GET",
            f"{base}/api/v1/logs",
            step_no=step_no,
            title="查询操作日志（仅 admin）",
            headers=headers,
            params={"page": 1, "per_page": 10},
        )
        logs_data = logs_resp.get("data") or {}
        log_items = logs_data.get("items") or []
        total_logs = logs_data.get("total", len(log_items))
        print(f"  日志总数：{total_logs}")
        if log_items:
            top = log_items[0]
            print(f"  最新动作：{top.get('action')}  by user_id={top.get('user_id')}")
        record(step_no, "操作日志", True, time.time() - t0)
    except SystemExit:
        record(step_no, "操作日志", False, time.time() - t0)

    # ---- 执行摘要 ----
    _print_header("执行摘要")
    print(f"{'步骤':>4}  {'功能':<20}  {'状态':<4}  {'耗时':<10}")
    print("-" * 50)
    for step, title, status, elapsed in summary_rows:
        print(f"{step:>4}  {title:<20}  {status:<4}  {elapsed:<10}")
    print("-" * 50)

    ok_count = sum(1 for row in summary_rows if row[2] == "✓")
    total_count = len(summary_rows)
    print(f"合计：{ok_count}/{total_count} 步成功")
    print("演示完成 ✓" if ok_count == total_count else "演示部分失败，请查看上方日志 ✗")

    return 0 if ok_count == total_count else 2


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="保险 AI 系统端到端演示脚本：登录 → 上传 → 训练 → 预测 → 邮件",
    )
    parser.add_argument("--host", default="127.0.0.1", help="后端主机，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=5000, help="后端端口，默认 5000")
    parser.add_argument("--username", default="admin", help="登录用户名，默认 admin")
    parser.add_argument("--password", default="admin123", help="登录密码，默认 admin123")
    parser.add_argument(
        "--file",
        default="data/sample_insurance.xlsx",
        help="上传的 Excel 文件路径（相对或绝对），默认 data/sample_insurance.xlsx",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    return run_demo(args)


if __name__ == "__main__":
    sys.exit(main())
