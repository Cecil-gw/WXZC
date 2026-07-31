from flask import Blueprint, request
from pydantic import ValidationError
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, hash_password
from app.core.response import json, BizException
from app.core.dependencies import login_required, role_required, get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UpdatePasswordRequest
)
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
    if User.find_by_username(db, req.username):
        raise BizException(1004, "用户名已存在", 400)
    try:
        user = User.create(db, req.username, hash_password(req.password), role="user")
        db.commit()
    except Exception:
        db.rollback()
        raise BizException(500, "注册失败", 500)
    return _token_response(user)


@bp.route("/login", methods=["POST"])
def login():
    """登录：校验-签JWT(返回token)"""
    req = _parse_body(LoginRequest)
    db = get_db()
    user = User.find_by_username(db, req.username)
    if not user or not verify_password(req.password, user.password_hash):
        raise BizException(1002, "用户名或密码错误", 401)
    return _token_response(user)


@bp.route("/me")
@login_required
def me():
    """获取当前用户信息"""
    user = get_current_user()
    return json({
        "id": user.id,
        "username": user.username,
        "role": user.role,
    })


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """退出登录：JWT 无状态，前端丢弃 Token 即可，后端返回成功提示"""
    return json(message="已登出")


@bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    """修改个人资料：普通用户只能改用户名、密码，不能修改角色"""
    req = _parse_body(UpdateProfileRequest)
    db = get_db()
    user = get_current_user()

    update_args = {}

    # 修改用户名逻辑
    if req.username is not None:
        new_username = req.username.strip()
        # 判断是否别的用户占用该用户名
        exist = User.find_by_username(db, new_username)
        if exist and exist.id != user.id:
            raise BizException(1004, "用户名已存在", 400)
        update_args["username"] = new_username

    # 修改密码逻辑：只有前端传password才更新密码
    if req.password is not None:
        update_args["password_hash"] = hash_password(req.password)

    if not update_args:
        raise BizException(1006, "没有提供任何需要修改的字段", 400)

    try:
        user = User.update_profile(db, user.id, **update_args)
        db.commit()
    except Exception:
        db.rollback()
        raise BizException(500, "个人资料修改失败", 500)

    # 如果修改了用户名，旧JWT失效，返回新token；否则只返回用户信息
    if req.username is not None:
        return _token_response(user)
    return json(message="个人信息修改成功", data={
        "id": user.id,
        "username": user.username,
        "role": user.role
    })

@bp.route("/password", methods=["PUT"])
@login_required
def update_password():
    req = _parse_body(UpdatePasswordRequest)

    db = get_db()
    user = get_current_user()

    # 验证旧密码
    if not verify_password(req.old_password, user.password_hash):
        raise BizException(1002, "旧密码错误", 400)

    try:
        User.update_password(
            db,
            user.id,
            hash_password(req.new_password)
        )
        db.commit()
    except Exception:
        db.rollback()
        raise BizException(500, "修改密码失败", 500)

    return json(message="密码修改成功")


@bp.route("/users", methods=["GET"])
@login_required
@role_required("admin")
def users():
    """获取所有用户列表"""
    db = get_db()
    user_list = User.all_users(db)
    return json([
        {"id": u.id, "username": u.username, "role": u.role,
         "created_at": u.created_at.isoformat() if u.created_at else None}
        for u in user_list
    ])