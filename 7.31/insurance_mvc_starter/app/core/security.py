"""安全：bcrypt 密码哈希 + JWT 签发/校验

【MVC 归属】基础设施层（Controller层）
【思路】
1. hash_password/verify_password 处理密码
2. create_access_token 签发 JWT
3. decode_token 解析 JWT 取出用户名

密码哈希和 JWT 是独立于 Web 框架的纯算法层。
- 密码哈希：直接用 bcrypt 库（不用 passlib，避免与 bcrypt 4.x 兼容性坑）
- 登录态：用 JWT 无状态令牌（校验只看签名+过期时间）
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from jose import jwt, JWTError
from bcrypt import hashpw, gensalt, checkpw
from .config import settings

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    return hashpw(pwd_bytes, gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": subject, "exp": expire}, # 有效载荷：用户名+过期时间
        settings.JWT_SECRET_KEY, # 密钥 用于签名
        algorithm=settings.JWT_ALGORITHM, # 算法：HS256
    )    # 返回三段式的token

def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
    