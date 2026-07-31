from flask import Blueprint, request
from pydantic import ValidationError
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, hash_password
from app.core.response import json, BizException
from app.core.dependencies import login_required, role_required, get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest

bp = Blueprint("auth", __name__)

def _parse_body(model_cls):
    """公共辅助：取 JSON body → Pydantic 校验 → 返回模型实例

    逐字思路：
    1. request.get_json(silent=True) 取 body，取不到返回 None
    2. body 为 None 用空字典兜底
    3. 校验不过抛 BizException(1001)
    """
    body = request.get_json(silent=True) or {}
    try:
        return model_cls(**body)
    except ValidationError:
        raise BizException(1001, "参数校验错误，请检查请求体字段", 400)

def _token_response(user: User) -> dict:
    """拼统一的 token 响应体（登录/注册复用）"""
    return json({
        "access_token": create_access_token(user.username),
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {"id": user.id, "username": user.username, "role": user.role},
    })

@bp.route("/register", methods=["POST"])
def register():
    """注册：查重-哈希-入库-签JWT(返回token)"""
    req = _parse_body(RegisterRequest)
    db = get_db()
    user = User.find_by_username(db, req.username)
    if user:
        raise BizException(1004, "用户名已存在", 400)
    user = User.create(db, req.username, hash_password(req.password), role = "user")
    return _token_response(user)
    
@bp.route("/login", methods=["POST"])
def login():
    """登录：校验-签JWT(返回token)"""
    req = _parse_body(LoginRequest)
    db = get_db()
    user = User.find_by_username(db, req.username)
    if not user or not verify_password(req.password, user.password):
        raise BizException(1002, "用户名或密码错误", 401)
    return _token_response(user)