"""API v1 蓝图聚合注册。

`register_blueprints(app)` 一次性挂载 5 个业务蓝图到 Flask 实例。
路由逻辑按模块拆分到同目录 `auth.py` / `data.py` / `model.py` / `email.py` / `log.py`。
"""

from flask import Flask

from app.api.v1.auth import bp as auth_bp
from app.api.v1.data import bp as data_bp
from app.api.v1.model import bp as model_bp
from app.api.v1.email import bp as email_bp
from app.api.v1.log import bp as log_bp


def register_blueprints(app: Flask) -> None:
    """向 Flask 实例注册全部 API v1 蓝图。"""
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(data_bp, url_prefix="/api/v1/data")
    app.register_blueprint(model_bp, url_prefix="/api/v1/model")
    app.register_blueprint(email_bp, url_prefix="/api/v1/email")
    app.register_blueprint(log_bp, url_prefix="/api/v1/logs")
