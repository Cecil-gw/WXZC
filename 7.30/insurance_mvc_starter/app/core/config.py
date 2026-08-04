"""配置模块（Model 层之上的基础设施层）。

归属：app/core/config.py —— 配置中心。

思路：使用 pydantic-settings 从 .env 加载环境变量并做类型校验，
模块级实例化 settings 单例，全局复用。
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# 项目根目录：当前文件 app/core/config.py -> 上溯两层
BASE_DIR: Path = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """应用运行期配置。字段对应教学骨架的最小集合。"""

    # -------- 应用 --------
    APP_NAME: str = "InsuranceMVC"
    DEBUG: bool = True

    # -------- 数据库 --------
    DATABASE_URL: str = "sqlite:///insurance.db"

    # -------- JWT / 安全 --------
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # -------- 默认管理员 --------
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def ensure_runtime_dirs(self) -> None:
        """启动时创建运行期必需目录。"""
        os.makedirs(str(BASE_DIR / "instance"), exist_ok=True)


settings = Settings()