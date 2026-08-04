"""模型模块 /model Blueprint。

设计对齐 `docs/03_API接口文档.md §3`：
- P1-04 实现 POST /model/train（仅 admin）
- P1-05 实现 GET /model/experiments（分页 + model_name 过滤）与 GET /model/best
- P1-06 实现 POST /model/predict（全量预测 + 回写 predicted_prob）
- P1-07 实现 POST /model/predict_upload（上传 Excel 预测，不入库）
- P1-08 实现 GET /model/visualization/{chart_type}（数据源为 experiments.params）
- P1-09 实现 GET /model/export/{model_name} 与 POST /model/import（均仅 admin）

路由层只做参数提取与响应包装，业务全部走 `app.services.ml_service.MLService`。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from flask import Blueprint, g, request, send_file

from app.core.database import get_db
from app.core.dependencies import login_required, role_required
from app.core.response import CODE_PARAM_ERROR, BizException, success
from app.services import operation_log_service
from app.services.ml_service import MLService

bp = Blueprint("model", __name__)

# 与 api/v1/data.py 保持一致的 Excel 扩展名白名单
_ALLOWED_EXTENSIONS = {".xlsx", ".xls"}


@bp.route("/train", methods=["POST"])
@login_required
@role_required("admin")
def train():
    """POST /model/train：训练三算法，按 ROC-AUC 选最佳（docs/03 §3.1）。

    请求体（均可选）：models / test_size / random_state / params。
    响应 data: {best_model, results:{model:{accuracy,precision,recall,f1_score,roc_auc}}}。
    """
    body = request.get_json(silent=True) or {}
    models = _models_arg(body.get("models"))
    test_size = _float_arg(body.get("test_size"), "test_size", 0.2)
    random_state = _int_arg(body.get("random_state"), "random_state", 42)
    params = _params_arg(body.get("params"))

    db = get_db()
    result = MLService.train(
        db,
        models=models,
        test_size=test_size,
        random_state=random_state,
        params=params,
    )
    operation_log_service.log(
        db,
        g.current_user["id"],
        "model_training",
        {
            "best_model": result["best_model"],
            "models": list(result["results"].keys()),
            "test_size": test_size,
            "random_state": random_state,
        },
    )
    return success(result)


@bp.route("/experiments", methods=["GET"])
@login_required
def experiments():
    """GET /model/experiments：实验记录分页（docs/03 §3.2）。

    Query: page / per_page（默认 50，上限 200）/ model_name（可选过滤）。
    items 元素含 id/model_name/4 项指标/roc_auc/params/model_path/is_best/created_at。
    """
    page = _query_int("page", default=1, min_val=1)
    per_page = _query_int("per_page", default=50, min_val=1)
    model_name = request.args.get("model_name") or None
    return success(
        MLService.list_experiments(
            get_db(), page=page, per_page=per_page, model_name=model_name
        )
    )


@bp.route("/best", methods=["GET"])
@login_required
def best():
    """GET /model/best：当前最佳模型（docs/03 §3.3）。

    响应 data: {model_name, roc_auc, experiment_id}；无最佳模型 → code=3002。
    """
    return success(MLService.get_best(get_db()))


@bp.route("/predict", methods=["POST"])
@login_required
def predict():
    """POST /model/predict：全量预测并回写 predicted_prob（docs/03 §3.4）。

    请求体（可选）：model_name（缺省用最佳模型）。
    响应 data: {model_name, predicted_count}。
    无最佳模型 / 模型文件丢失 / 预测异常 → code=3002。
    """
    body = request.get_json(silent=True) or {}
    raw = body.get("model_name")
    if raw is not None and (not isinstance(raw, str) or not raw.strip()):
        raise BizException(CODE_PARAM_ERROR, "model_name 必须是非空字符串", 400)
    model_name = raw.strip() if isinstance(raw, str) else None

    db = get_db()
    result = MLService.predict(db, model_name=model_name)
    operation_log_service.log(
        db,
        g.current_user["id"],
        "prediction",
        {
            "model_name": result["model_name"],
            "predicted_count": result["predicted_count"],
            "requested_model": model_name,
        },
    )
    return success(result)


@bp.route("/predict_upload", methods=["POST"])
@login_required
def predict_upload():
    """POST /model/predict_upload：对上传的新一批客户预测，不入库（docs/03 §3.5）。

    请求：multipart/form-data，`file` 为 .xlsx/.xls；可选表单字段 `model`。
    响应 data: {model_name, total_count, statistics, predictions}。
    文件格式错 → 1001；解析失败 → 2002；模型不可用 → 3002。
    """
    file = request.files.get("file")
    if file is None or not file.filename:
        raise BizException(CODE_PARAM_ERROR, "未上传文件", 400)
    if "." not in file.filename:
        raise BizException(CODE_PARAM_ERROR, "文件缺少扩展名", 400)
    ext = "." + file.filename.rsplit(".", 1)[-1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise BizException(CODE_PARAM_ERROR, "仅支持 .xlsx / .xls 格式", 400)

    raw = request.form.get("model")
    if raw is not None and not raw.strip():
        raise BizException(CODE_PARAM_ERROR, "model 不能为空字符串", 400)
    model_name = raw.strip() if raw else None

    db = get_db()
    result = MLService.predict_upload(db, file, model_name=model_name)
    operation_log_service.log(
        db,
        g.current_user["id"],
        "prediction",
        {
            "scope": "upload",
            "model_name": result["model_name"],
            "total_count": result["total_count"],
            "filename": file.filename,
        },
    )
    return success(result)


@bp.route("/visualization/<chart_type>", methods=["GET"])
@login_required
def visualization(chart_type: str):
    """GET /model/visualization/{chart_type}：评估可视化（docs/03 §3.6）。

    chart_type ∈ roc_curve / metrics_comparison / confusion_matrix / feature_importance。
    Query: model（confusion_matrix / feature_importance 必填）。
    响应 data: {chart_type, image_base64, format: "png"}。
    """
    model_name = request.args.get("model") or None
    return success(
        MLService.visualization(get_db(), chart_type, model_name=model_name)
    )


@bp.route("/export/<model_name>", methods=["GET"])
@login_required
@role_required("admin")
def export_model(model_name: str):
    """GET /model/export/{model_name}：下载 .joblib（docs/03 §3.7，仅 admin）。

    响应二进制流，带 `Content-Disposition: attachment`。
    模型名非法 → 1001；文件不存在 → 3002；普通用户 → 403 / 1003。
    """
    info = MLService.export_model(model_name)
    return send_file(
        info["path"],
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=info["filename"],
    )


@bp.route("/import", methods=["POST"])
@login_required
@role_required("admin")
def import_model():
    """POST /model/import：上传 .joblib 复用模型（docs/03 §3.8，仅 admin）。

    请求：multipart/form-data，`file` 为 .joblib。
    响应 data: {model_name, path}。非 .joblib 或结构不符 → 1001。
    """
    file = request.files.get("file")
    if file is None or not file.filename:
        raise BizException(CODE_PARAM_ERROR, "未上传文件", 400)

    db = get_db()
    result = MLService.import_model(file)
    operation_log_service.log(
        db,
        g.current_user["id"],
        "model_import",
        {
            "model_name": result["model_name"],
            "source_filename": file.filename,
        },
    )
    return success(result)


# -------------------- 参数解析辅助 --------------------


def _query_int(name: str, default: int, min_val: int) -> int:
    """从 query string 读整数。空字符串视作未传；非整数/越界抛 1001。

    与 `app/api/v1/data.py::_int_arg` 同语义，此处独立实现以避免蓝图间横向依赖。
    """
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise BizException(CODE_PARAM_ERROR, f"参数 {name} 必须是整数", 400) from None
    if value < min_val:
        raise BizException(CODE_PARAM_ERROR, f"参数 {name} 不能小于 {min_val}", 400)
    return value

def _models_arg(raw: Any) -> Optional[List[str]]:
    """models：null 表示训练全部；否则必须是非空字符串数组。"""
    if raw is None:
        return None
    if not isinstance(raw, list) or not raw:
        raise BizException(CODE_PARAM_ERROR, "models 必须是非空字符串数组", 400)
    if not all(isinstance(v, str) and v for v in raw):
        raise BizException(CODE_PARAM_ERROR, "models 元素必须是非空字符串", 400)
    return raw


def _float_arg(raw: Any, name: str, default: float) -> float:
    if raw is None:
        return default
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise BizException(CODE_PARAM_ERROR, f"参数 {name} 必须是数字", 400)
    return float(raw)


def _int_arg(raw: Any, name: str, default: int) -> int:
    if raw is None:
        return default
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise BizException(CODE_PARAM_ERROR, f"参数 {name} 必须是整数", 400)
    return raw


def _params_arg(raw: Any) -> Optional[Dict[str, Dict[str, Any]]]:
    """params：{模型名: {超参: 值}}。"""
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise BizException(CODE_PARAM_ERROR, "params 必须是对象", 400)
    for key, value in raw.items():
        if not isinstance(value, dict):
            raise BizException(
                CODE_PARAM_ERROR, f"params.{key} 必须是对象", 400
            )
    return raw