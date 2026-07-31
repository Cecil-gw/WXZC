from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    """登录请求体：POST /auth/login 时发送

    1. username: str 必填
    2. password: str 必填，服务端 hash 比对
    """
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class RegisterRequest(BaseModel):
    """注册请求体：POST /auth/register 时发送

    1. username/password 必填
    2. password 至少 6 位
    3. 不含 role：防止越权注册 admin（role 由服务端硬编码）
    """
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)




class UpdateProfileRequest(BaseModel):
    username: str | None = None
    password: str | None = None


class UpdatePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=100)
