"""api/v1 包：蓝图聚合注册。"""
from flask import Flask


def register_blueprints(app: Flask):
    """注册所有业务蓝图到 app。"""
    from app.api.v1.auth import bp as auth_bp
    from app.api.v1.data import bp as data_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(data_bp, url_prefix="/api/v1/data")
