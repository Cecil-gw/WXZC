"""应用配置（Settings）。

职责：从项目根目录的 `.env` 加载环境变量并做类型校验，模块级实例化 `settings`
全局复用。变量清单严格对齐 `docs/04_技术框架方案.md §6.5` 与
`docs/02_AI技术方案.md §3.2`。

设计要点：
- 使用 `pydantic-settings` 而非直接读取 `os.environ`，天然带类型校验与默认值。
- `.env` 缺省或字段缺失时按类属性默认值兜底，避免开发环境炸掉。
- `MODEL_DIR` 统一解析为绝对路径，规避 Windows 下 `send_file` 相对路径 bug。
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# 项目根目录（`app/core/config.py` -> 上溯三层）
BASE_DIR: Path = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """应用运行期配置。"""

    # -------- 应用 --------
    APP_ENV: str = "dev"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 5000

    # -------- 数据库 --------
    DATABASE_URL: str = "sqlite:///instance/insurance.db"

    # -------- JWT / 安全 --------
    JWT_SECRET_KEY: str = "change-me-please-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_SECONDS: int = 86400

    # -------- 默认管理员（首次启动 seed） --------
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    # -------- 大模型（OpenAI 兼容协议） --------
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen-flash"
    LLM_TEMPERATURE: float = 0.7

    # -------- 目录 --------
    # 训练产出的 joblib 存放目录，运行时会自动创建
    MODEL_DIR: str = Field(default="data/models")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ---------- 派生便利属性 ----------
    @property
    def model_dir_abs(self) -> str:
        """`MODEL_DIR` 的绝对路径。相对路径以项目根为基准。"""
        p = Path(self.MODEL_DIR)
        if not p.is_absolute():
            p = BASE_DIR / p
        return str(p.resolve())

    def ensure_runtime_dirs(self) -> None:
        """启动时创建运行期必需目录（instance / MODEL_DIR）。"""
        os.makedirs(self.model_dir_abs, exist_ok=True)
        os.makedirs(str(BASE_DIR / "instance"), exist_ok=True)


# 模块级单例，导入即可用
settings = Settings()
