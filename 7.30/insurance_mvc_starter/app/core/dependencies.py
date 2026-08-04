"""依赖注入层（路由层与业务层之间的桥接层）。

归属：app/core/dependencies.py —— 鉴权装饰器。

思路：
- login_required：要求请求携带有效 JWT，通过后把当前用户挂到 g.current_user；
- role_required：要求当前用户角色属于指定角色集合；
- get_current_user：从 g 中获取当前用户信息。
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, Iterable, Optional

from flask import g, request

from app.core.response import (
    CODE_FORBIDDEN,
    CODE_UNAUTHORIZED,
    BizException,
)
from app.core.security import TokenInvalidError, decode_token


def _extract_token() -> Optional[str]:
    """从 Authorization 头解析 Bearer token。"""
    auth = request.headers.get("Authorization", "")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def _resolve_current_user() -> Dict[str, Any]:
    """解析 JWT 并返回当前用户 claim。失败抛 BizException(1002)。"""
    token = _extract_token()
    if not token:
        raise BizException(CODE_UNAUTHORIZED, "未提供认证令牌", 401)
    try:
        payload = decode_token(token)
    except TokenInvalidError as exc:
        raise BizException(CODE_UNAUTHORIZED, "认证令牌无效或已过期", 401) from exc

    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError, TypeError) as exc:
        raise BizException(CODE_UNAUTHORIZED, "认证令牌无效", 401) from exc

    return {
        "id": user_id,
        "username": payload.get("username"),
        "role": payload.get("role", "user"),
    }


def login_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """要求请求携带有效 JWT。通过后 g.current_user 可用。"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        g.current_user = _resolve_current_user()
        return func(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """要求当前用户角色属于 allowed_roles。"""

    if not allowed_roles:
        raise ValueError("role_required needs at least one role")

    allowed: Iterable[str] = tuple(allowed_roles)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not getattr(g, "current_user", None):
                g.current_user = _resolve_current_user()
            role = g.current_user.get("role")
            if role not in allowed:
                raise BizException(CODE_FORBIDDEN, "权限不足", 403)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_current_user() -> Optional[Dict[str, Any]]:
    """获取当前用户信息（从 g.current_user），未登录返回 None。"""
    return getattr(g, "current_user", None)