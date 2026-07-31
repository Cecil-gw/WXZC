"""鉴权装饰器：`login_required` 与 `role_required`。

设计对齐 `docs/04_技术框架方案.md §6.4`：

- 从请求头 `Authorization: Bearer <token>` 解析 JWT；
- 校验通过则把当前用户信息挂到 `g.current_user`（含 `id`/`username`/`role`）；
- 失败按 API 文档业务码返回：未认证 `1002/401`，权限不足 `1003/403`。

装饰器不直接查库，只解析 JWT 中的 claim；如需最新用户信息由业务层再查。
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
    """从 `Authorization` 头解析 Bearer token。"""
    auth = request.headers.get("Authorization", "")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def _resolve_current_user() -> Dict[str, Any]:
    """解析 JWT 并返回当前用户 claim。失败抛 `BizException(1002)`。"""
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
    """要求请求携带有效 JWT，通过后把当前用户挂到 `g.current_user`。"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        g.current_user = _resolve_current_user()
        return func(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """要求当前用户角色属于 `allowed_roles`。可与 `login_required` 组合，也可独立使用。

    用法：
        @role_required("admin")
        def train(): ...
    """

    if not allowed_roles:
        raise ValueError("role_required needs at least one role")

    allowed: Iterable[str] = tuple(allowed_roles)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 若上游没先跑 login_required，这里补一次；等价于自动登录校验
            if not getattr(g, "current_user", None):
                g.current_user = _resolve_current_user()
            role = g.current_user.get("role")
            if role not in allowed:
                raise BizException(CODE_FORBIDDEN, "权限不足", 403)
            return func(*args, **kwargs)

        return wrapper

    return decorator
