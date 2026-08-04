"""认证模块 /auth Blueprint。

设计对齐 `docs/03_API接口文档.md §1.1-1.4`。
"""

from __future__ import annotations

from flask import Blueprint, g, request
from pydantic import ValidationError

from app.core.database import get_db
from app.core.dependencies import login_required
from app.core.response import CODE_PARAM_ERROR, CODE_UNAUTHORIZED, BizException, success
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService

bp = Blueprint("auth", __name__)


def _validate(schema_cls, data):
    """Pydantic 校验并统一转 BizException(1001)。"""
    try:
        return schema_cls(**data)
    except ValidationError as e:
        raise BizException(CODE_PARAM_ERROR, f"参数校验错误: {e}", 400) from e


@bp.route("/login", methods=["POST"])
def login():
    """POST /auth/login：校验用户名密码，签发 JWT。"""
    body = _validate(LoginRequest, request.get_json(silent=True) or {})
    result = AuthService.login(get_db(), body.username, body.password)
    return success(result)


@bp.route("/register", methods=["POST"])
def register():
    """POST /auth/register：注册新用户，角色强制 user。"""
    body = _validate(RegisterRequest, request.get_json(silent=True) or {})
    result = AuthService.register(get_db(), body.username, body.password)
    return success(result)


@bp.route("/me", methods=["GET"])
@login_required
def me():
    """GET /auth/me：凭 Token 返回当前用户信息。"""
    return success(g.current_user)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """POST /auth/logout：JWT 无状态，前端丢弃 Token 即可。"""
    return success(None, "已登出")
