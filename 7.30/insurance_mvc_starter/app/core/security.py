"""安全模块（Model 层之上的基础设施层）。

归属：app/core/security.py —— 密码哈希与 JWT 签发/校验。

思路：
- 密码使用 bcrypt 带随机盐哈希；
- Token 使用 HS256 算法，sub 存 user_id，role 存角色；
- Token 无效/过期/签名错误统一抛 TokenInvalidError。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """返回 bcrypt 哈希（含盐）。"""
    if not isinstance(password, str) or password == "":
        raise ValueError("password must be a non-empty str")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """校验明文密码与已存哈希是否匹配。"""
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


class TokenInvalidError(Exception):
    """Token 无效/过期/签名错误。"""


def create_access_token(
    user_id: int,
    role: str,
    username: Optional[str] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    """签发 JWT。返回 encoded token 字符串。"""
    if expires_minutes is None:
        expires_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(tz=timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    if username is not None:
        payload["username"] = username
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def decode_token(token: str) -> Dict[str, Any]:
    """校验并解析 JWT。失败抛 TokenInvalidError。"""
    if not token:
        raise TokenInvalidError("empty token")
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise TokenInvalidError(str(exc)) from exc

    if "sub" not in payload:
        raise TokenInvalidError("missing sub claim")
    return payload