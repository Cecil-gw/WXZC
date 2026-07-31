"""api/v1 包：蓝图聚合注册

【思路】把各业务蓝图统一挂到 /api/v1 前缀下。
后续新增蓝图（如 data/model/email）时，在这里加 register_blueprint。
"""
from flask import Flask


def register_blueprints(app: Flask):
    """注册所有业务蓝图到 app

    逐字思路：
    1. 从各业务模块 import bp（Blueprint 实例）
    2. app.register_blueprint 挂载，url_prefix 统一加 /api/v1/xxx 前缀
    3. 前端 fetch("/api/v1/auth/login") 就能路由到 auth.bp 的 /login
    """
    from app.api.v1.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    