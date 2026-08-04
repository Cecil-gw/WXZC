"""数据 API（路由层）。

归属：app/api/v1/data.py —— /api/v1/data 下的数据路由。

思路：
- 路由层只做参数提取与响应包装；
- 业务全部走 app.services.data_service.DataService；
- POST /upload → 上传 Excel 并解析入库；
- GET /customers → 分页查询客户列表。
"""

from __future__ import annotations

from flask import Blueprint, request

from app.core.database import get_db
from app.core.dependencies import login_required
from app.core.response import CODE_PARAM_ERROR, BizException, success
from app.services.data_service import DataService

bp = Blueprint("data", __name__, url_prefix="/api/v1/data")

_ALLOWED_EXTENSIONS = {".xlsx", ".xls"}


@bp.route("/upload", methods=["POST"])
@login_required
def upload():
    """POST /data/upload：上传 Excel，解析后批量入库。"""
    file = request.files.get("file")
    if file is None or not file.filename:
        raise BizException(CODE_PARAM_ERROR, "未上传文件", 400)
    if "." not in file.filename:
        raise BizException(CODE_PARAM_ERROR, "文件缺少扩展名", 400)
    ext = "." + file.filename.rsplit(".", 1)[-1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise BizException(CODE_PARAM_ERROR, "仅支持 .xlsx / .xls 格式", 400)
    result = DataService.upload(get_db(), file)
    return success(result)


@bp.route("/customers", methods=["GET"])
@login_required
def list_customers():
    """GET /data/customers：分页查询客户列表。"""
    page = _int_arg("page", default=1, min_val=1)
    per_page = _int_arg("per_page", default=50, min_val=1, max_val=200)
    gender = request.args.get("gender") or None
    result = DataService.list_customers(
        get_db(), page=page, per_page=per_page, gender=gender,
    )
    return success(result)


def _int_arg(name: str, default=None, min_val=None, max_val=None):
    """从 request.args 读整数。空字符串视作未传。"""
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