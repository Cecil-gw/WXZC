"""校验层统一入口

【作用】请求体 Pydantic 模型在此集中暴露，Controller 层可直接
from app.schemas.auth import LoginRequest, RegisterRequest
"""
from app.schemas.auth import LoginRequest, RegisterRequest

__all__ = ["LoginRequest", "RegisterRequest"]
