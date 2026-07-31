"""认证模块 Pydantic 请求体模型。

设计对齐 `docs/03_API接口文档.md §1.1-1.2`。

- `LoginRequest`：username + password，登录校验用。
- `RegisterRequest`：username + password，不包含 role 字段（服务端硬编码 user）。
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)
    # 注意：不包含 role——服务端硬编码为 "user"，防越权
