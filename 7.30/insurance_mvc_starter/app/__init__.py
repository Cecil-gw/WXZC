"""Flask 应用工厂（MVC 入口）。"""

from __future__ import annotations

import os

from flask import Flask, render_template, redirect, url_for, request
from werkzeug.exceptions import HTTPException

from app.core.config import settings
from app.core.database import Base, engine, close_db, SessionLocal
from app.core.response import (
    CODE_INTERNAL_ERROR,
    BizException,
    fail,
    success,
)
from app.core.security import hash_password


def _init_admin() -> None:
    """首次启动时创建默认管理员（若不存在）。"""
    from app.models.user import User
    db = SessionLocal()
    try:
        existing = db.query(User).filter_by(username=settings.DEFAULT_ADMIN_USERNAME).first()
        if existing is None:
            admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                role="admin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


def create_app() -> Flask:
    """应用工厂：创建并配置 Flask 实例。"""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, "templates")
    static_dir = os.path.join(os.path.dirname(base_dir), "static")

    flask_app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path="/static",
    )
    flask_app.secret_key = settings.JWT_SECRET_KEY

    settings.ensure_runtime_dirs()

    # -------- API 蓝图注册 --------
    from app.api.v1 import register_blueprints
    register_blueprints(flask_app)

    # -------- 页面路由 --------
    @flask_app.route("/")
    def index():
        return redirect(url_for("login_page"))

    @flask_app.route("/login")
    def login_page():
        return render_template("login.html")

    @flask_app.route("/register")
    def register_page():
        return render_template("register.html")

    @flask_app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @flask_app.route("/upload")
    def upload_page():
        return render_template("upload.html")

    @flask_app.route("/customers")
    def customers_page():
        return render_template("customers.html")

    # -------- 统计 API --------
    @flask_app.route("/api/v1/stats/overview")
    def stats_overview():
        from app.models.customer import Customer
        db = SessionLocal()
        try:
            total = db.query(Customer).count()
            responded = db.query(Customer).filter(Customer.response == 1).count()
            response_rate = round(responded / total * 100, 2) if total > 0 else 0
            data = {
                "total_customers": total,
                "responded": responded,
                "response_rate": response_rate,
                "male_count": db.query(Customer).filter(Customer.gender == "Male").count(),
                "female_count": db.query(Customer).filter(Customer.gender == "Female").count(),
                "damaged_count": db.query(Customer).filter(Customer.vehicle_damage == "Yes").count(),
            }
            return success(data)
        finally:
            db.close()

    # -------- teardown --------
    flask_app.teardown_appcontext(close_db)

    # -------- 全局异常处理 --------
    @flask_app.errorhandler(BizException)
    def handle_biz_exception(e: BizException):
        return e.to_response()

    @flask_app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        return fail(CODE_INTERNAL_ERROR, e.description, e.code)

    @flask_app.errorhandler(Exception)
    def handle_unexpected(e: Exception):
        import traceback
        traceback.print_exc()
        return fail(CODE_INTERNAL_ERROR, "服务器内部错误", 500)

    # -------- 建表 + seed --------
    with flask_app.app_context():
        import app.models as _models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        _init_admin()

    return flask_app
