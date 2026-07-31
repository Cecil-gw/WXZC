"""密码哈希（bcrypt）与 JWT 签发/校验（python-jose，HS256）。

设计对齐 `docs/01_PRD_产品需求文档.md §3.1` 与 `docs/04_技术框架方案.md §8`：

- 密码使用 bcrypt 带随机盐哈希；不经过 passlib，避免 4.x 兼容坑。
- Token 使用 HS256；`sub` 存 `user_id`，`role` 存角色，`exp` 存过期时间。
- Token 无效 / 过期 / 签名错误统一抛 `TokenInvalidError`，供上层转成 `BizException`。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# ---------------- 密码哈希 ----------------
def hash_password(password: str) -> str:
    """返回 bcrypt 哈希（含盐）。存库使用字符串形式，便于跨库/跨语言。"""
    if not isinstance(password, str) or password == "":
        raise ValueError("password must be a non-empty str")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """校验明文密码与已存哈希是否匹配。任何异常都视为失败，返回 False。"""
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------------- JWT ----------------
class TokenInvalidError(Exception):
    """Token 无效 / 过期 / 签名错误。由上层转 `BizException(1002, ...)`。"""


def create_access_token(
    user_id: int,
    role: str,
    username: Optional[str] = None,
    expires_seconds: Optional[int] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """签发 JWT。返回 encoded token 字符串。"""
    if expires_seconds is None:
        expires_seconds = settings.JWT_EXPIRE_SECONDS
    now = datetime.now(tz=timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_seconds)).timestamp()),
    }
    if username is not None:
        payload["username"] = username
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    # python-jose 在部分版本下会返回 bytes，这里做一次归一化
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def decode_token(token: str) -> Dict[str, Any]:
    """校验并解析 JWT。签名错误 / 过期 / 结构错误都抛 `TokenInvalidError`。"""
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
