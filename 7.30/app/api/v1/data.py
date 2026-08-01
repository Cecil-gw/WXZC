"""数据模块 /data Blueprint。

设计对齐 `docs/03_API接口文档.md §2`：
- P1-01 实现 POST /data/upload（Excel 上传，解析+清空+批量入库）—— P1-01-5
- P1-02 将实现 GET /data/customers（分页 + 过滤）
- P1-03 将实现 GET /data/statistics / /data/quality / /data/visualization/{chart_type}

路由层只做参数提取与响应包装，业务全部走 `app.services.data_service.DataService`。
"""

from __future__ import annotations

from flask import Blueprint, request

from app.core.database import get_db
from app.core.dependencies import login_required
from app.core.response import CODE_PARAM_ERROR, BizException, success
from app.services.data_service import DataService

bp = Blueprint("data", __name__, url_prefix="/api/v1/data")

_ALLOWED_EXTENSIONS = {".xlsx", ".xls"}


@bp.route("/statistics", methods=["GET"])
@login_required
def statistics():
    """GET /data/statistics：数据概览（docs/03 §2.3）。

    响应 data: {total, gender_distribution, response_distribution, age_stats}。
    """
    return success(DataService.statistics(get_db()))


@bp.route("/quality", methods=["GET"])
@login_required
def quality():
    """GET /data/quality：数据质量报告（docs/03 §2.4）。

    响应 data: {total_rows, total_cols, missing_values, duplicates, dtypes}。
    """
    return success(DataService.quality(get_db()))


@bp.route("/visualization/<chart_type>", methods=["GET"])
@login_required
def visualization(chart_type: str):
    """GET /data/visualization/{chart_type}：EDA 可视化（docs/03 §2.5）。

    chart_type ∈ response_distribution / gender_response / age_distribution / premium_distribution。
    响应 data: {chart_type, image_base64, format: "png"}。
    """
    return success(DataService.visualization(get_db(), chart_type))


@bp.route("/customers", methods=["GET"])
@login_required
def list_customers():
    """GET /data/customers：分页 + 过滤（docs/03 §2.2）。

    Query: page / per_page / gender / age_min / age_max / previously_insured / keyword
    """
    page = _int_arg("page", default=1, min_val=1)
    per_page = _int_arg("per_page", default=50, min_val=1)
    gender = request.args.get("gender") or None
    age_min = _int_arg("age_min", default=None, min_val=0)
    age_max = _int_arg("age_max", default=None, min_val=0)
    previously_insured = _int_arg("previously_insured", default=None, min_val=0, max_val=1)
    keyword = request.args.get("keyword") or None
    result = DataService.list_customers(
        get_db(),
        page=page,
        per_page=per_page,
        gender=gender,
        age_min=age_min,
        age_max=age_max,
        previously_insured=previously_insured,
        keyword=keyword,
    )
    return success(result)


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


@bp.route("/upload", methods=["POST"])
@login_required
def upload():
    """POST /data/upload：上传 Excel，清空旧 customers 后批量入库。

    请求：multipart/form-data，file 字段为 .xlsx/.xls 文件。
    响应：{imported_count, quality_report}。
    """
    file = request.files.get("file")
    if file is None or not file.filename:
        raise BizException(CODE_PARAM_ERROR, "未上传文件", 400)
    # 扩展名白名单（防御非 Excel 文件）
    if "." not in file.filename:
        raise BizException(CODE_PARAM_ERROR, "文件缺少扩展名", 400)
    ext = "." + file.filename.rsplit(".", 1)[-1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise BizException(CODE_PARAM_ERROR, "仅支持 .xlsx / .xls 格式", 400)
    result = DataService.upload(get_db(), file)
    return success(result)