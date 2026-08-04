"""日志模块 /logs Blueprint。

设计对齐 `docs/03_API接口文档.md §5.1`：仅 admin 可查操作日志。
路由层只做参数提取，业务在 `app.services.operation_log_service.list_logs`。
"""

from __future__ import annotations

from flask import Blueprint, request

from app.core.database import get_db
from app.core.dependencies import login_required, role_required
from app.core.response import CODE_PARAM_ERROR, BizException, success
from app.services import operation_log_service

bp = Blueprint("log", __name__)


@bp.route("", methods=["GET"])
@login_required
@role_required("admin")
def list_logs():
    """GET /logs：操作日志分页查询（docs/03 §5.1，仅 admin）。

    Query: page / per_page（默认 50）/ user_id / action
    响应 data: 分页结构，items 含 id/user_id/username/action/details/created_at。
    """
    return success(
        operation_log_service.list_logs(
            get_db(),
            page=_int_arg("page", default=1, min_val=1),
            per_page=_int_arg("per_page", default=50, min_val=1),
            user_id=_int_arg("user_id", default=None, min_val=1),
            action=request.args.get("action") or None,
        )
    )


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