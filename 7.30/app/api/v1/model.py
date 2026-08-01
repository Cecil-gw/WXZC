"""模型模块 /model Blueprint。

设计对齐 `docs/03_API接口文档.md §3`：
- P1-04 实现 POST /model/train（仅 admin）
- P1-05~P1-09 将实现 /experiments、/best、/predict 等

路由层只做参数提取与响应包装，业务全部走 `app.services.ml_service.MLService`。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from flask import Blueprint, g, request

from app.core.database import get_db
from app.core.dependencies import login_required, role_required
from app.core.response import CODE_PARAM_ERROR, BizException, success
from app.services import operation_log_service
from app.services.ml_service import MLService

bp = Blueprint("model", __name__, url_prefix="/api/v1/model")


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


# -------------------- 参数解析辅助 --------------------

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