"""邮件模块 /email Blueprint。

设计对齐 `docs/03_API接口文档.md §4`：
- P1-10 实现 GET /email/targets（高潜客户筛选）
- P1-11~P1-13 将实现 POST /email/generate、Prompt 模板与邮件记录 CRUD

路由层只做参数提取与响应包装，业务全部走 `app.services.email_service.EmailService`。
本模块所有接口需登录（docs §4 开头统一声明），未标注「仅 admin」故不加角色限制。
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.core.database import get_db
from app.core.dependencies import login_required
from app.core.response import CODE_PARAM_ERROR, BizException, success
from app.services.email_service import _UNSET as UNSET
from app.services.email_service import EmailService

bp = Blueprint("email", __name__)


@bp.route("/targets", methods=["GET"])
@login_required
def targets():
    """GET /email/targets：按分位数筛选高潜客户（docs/03 §4.1）。

    Query: percentile（默认 0.9）/ page（默认 1）/ per_page（默认 20）
    响应 data: {threshold, total, customers}。无预测数据 → 3002。
    """
    percentile = _float_arg("percentile", default=None)
    page = _int_arg("page", default=1, min_val=1)
    per_page = _int_arg("per_page", default=20, min_val=1)
    kwargs = {"page": page, "per_page": per_page}
    # percentile 未传时交给 Service 用 ml_service 的默认分位数，不在此处复制默认值
    if percentile is not None:
        kwargs["percentile"] = percentile
    return success(EmailService.targets(get_db(), **kwargs))


# -------------------- 参数解析辅助 --------------------


def _int_arg(name: str, default=None, min_val=None, max_val=None):
    """从 request.args 读整数。空字符串视作未传。非整数/越界抛 BizException(1001)。"""
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        v = int(raw)
    except (TypeError, ValueError):
        raise BizException(CODE_PARAM_ERROR, f"参数 {name} 必须是整数", 400)
    if min_val is not None and v < min_val:
        raise BizException(CODE_PARAM_ERROR, f"参数 {name} 不能小于 {min_val}", 400)
    if max_val is not None and v > max_val:
        raise BizException(CODE_PARAM_ERROR, f"参数 {name} 不能大于 {max_val}", 400)
    return v


def _float_arg(name: str, default=None):
    """从 request.args 读浮点数。空字符串视作未传。

    显式拦掉 nan / inf：float("nan") 不会抛异常，但会让后续的区间比较
    静默失效（任何与 nan 的比较都是 False），必须在入口处挡下。
    """
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        v = float(raw)
    except (TypeError, ValueError):
        raise BizException(CODE_PARAM_ERROR, f"参数 {name} 必须是数字", 400)
    if v != v or v in (float("inf"), float("-inf")):
        raise BizException(CODE_PARAM_ERROR, f"参数 {name} 必须是有限数字", 400)
    return v

@bp.route("/generate", methods=["POST"])
@login_required
def generate():
    """POST /email/generate：为高潜客户生成营销邮件（docs/03 §4.2）。

    请求体（二选一）：`customer_ids`（array<int>）或 `limit`（int，默认 5）。
    响应 data: {generated_count, failed_count, records}。
    未配置 LLM_API_KEY 时不报错，逐条记 status=failed（docs/02 §3.4 降级）。
    """
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        raise BizException(CODE_PARAM_ERROR, "请求体必须是 JSON 对象", 400)
    customer_ids = body.get("customer_ids")
    limit = body.get("limit", 5)
    result = EmailService.generate(
        get_db(),
        g.current_user["id"],
        customer_ids=customer_ids,
        limit=limit,
    )
    return success(result)


@bp.route("/prompt", methods=["GET"])
@login_required
def get_prompt():
    """GET /email/prompt：取当前生效的 Prompt 模板（docs/03 §4.3）。

    响应 data: {name, content}。无 is_active 行时返回内置默认模板。
    """
    return success(EmailService.get_prompt(get_db()))


@bp.route("/prompt", methods=["PUT"])
@login_required
def update_prompt():
    """PUT /email/prompt：更新 Prompt 模板（docs/03 §4.4）。

    请求体：{content: string}（须含 {gender}/{age} 占位符），可选 name。
    响应 data: {name, content}。校验失败 → 1001。
    """
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        raise BizException(CODE_PARAM_ERROR, "请求体必须是 JSON 对象", 400)
    return success(
        EmailService.update_prompt(get_db(), body.get("content"), body.get("name"))
    )


@bp.route("/records", methods=["GET"])
@login_required
def list_records():
    """GET /email/records：分页 + status 过滤（docs/03 §4.5）。

    普通用户只看自己生成的；admin 看全部并附 created_by_username。
    """
    return success(
        EmailService.list_records(
            get_db(),
            g.current_user,
            page=_int_arg("page", default=1, min_val=1),
            per_page=_int_arg("per_page", default=50, min_val=1),
            status=request.args.get("status") or None,
        )
    )


@bp.route("/records/<int:record_id>", methods=["GET"])
@login_required
def get_record(record_id: int):
    """GET /email/records/{id}：详情，含完整正文（docs/03 §4.6）。不存在 → 2001。"""
    return success(EmailService.get_record(get_db(), g.current_user, record_id))


@bp.route("/records/<int:record_id>", methods=["PUT"])
@login_required
def update_record(record_id: int):
    """PUT /email/records/{id}：更新主题/正文（docs/03 §4.7）。

    请求体：{email_subject?, email_content?}，两者至少一个。
    """
    body = _json_body()
    return success(
        EmailService.update_record(
            get_db(),
            g.current_user,
            record_id,
            subject=body["email_subject"] if "email_subject" in body else UNSET,
            content=body["email_content"] if "email_content" in body else UNSET,
        )
    )


@bp.route("/records/<int:record_id>", methods=["PATCH"])
@login_required
def mark_record(record_id: int):
    """PATCH /email/records/{id}：标记状态（docs/03 §4.8）。请求体 {status}。"""
    return success(
        EmailService.mark_record(
            get_db(), g.current_user, record_id, _json_body().get("status")
        )
    )


@bp.route("/records/<int:record_id>", methods=["DELETE"])
@login_required
def delete_record(record_id: int):
    """DELETE /email/records/{id}：删除单条（docs/03 §4.9）。响应 {success: true}。"""
    return success(EmailService.delete_record(get_db(), g.current_user, record_id))


@bp.route("/records", methods=["DELETE"])
@login_required
def delete_records():
    """DELETE /email/records：批量删除（docs/03 §4.10）。

    请求体 {record_ids: array<int>}，响应 {deleted_count}。
    """
    return success(
        EmailService.delete_records(get_db(), g.current_user, _json_body().get("record_ids"))
    )


def _json_body() -> dict:
    """取 JSON 请求体，非对象一律 1001。"""
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        raise BizException(CODE_PARAM_ERROR, "请求体必须是 JSON 对象", 400)
    return body
