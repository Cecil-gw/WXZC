"""应用工厂：延迟创建 Flask 实例，注册所有组件。

设计对齐 `docs/04_技术框架方案.md §6.1`：

- `create_app()` 工厂函数延迟创建 Flask 实例，便于测试与多环境部署；
- 按顺序：配置路由 → 蓝图 → 静态文件 → teardown 钩子 → 异常处理器；
- 首次启动自动建表 + seed 默认管理员 + default Prompt 模板。
"""

from __future__ import annotations

from flask import Flask, jsonify
from flask.wrappers import Response
from werkzeug.exceptions import HTTPException

from app.core.config import settings
from app.core.database import Base, engine, close_db
from app.core.response import CODE_INTERNAL_ERROR, BizException, fail
from app.core.security import hash_password

# 确保所有模型在 create_all 前注册到 Base.metadata
import app.models  # noqa: F401, E402


def _seed_admin() -> None:
    """首次启动时创建默认管理员（若不存在）。"""
    from app.core.database import SessionLocal
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


def _seed_prompt_template() -> None:
    """首次启动时插入默认 Prompt 模板（若不存在）。"""
    from app.core.database import SessionLocal
    from app.models.prompt_template import PromptTemplate

    DEFAULT_TEMPLATE = (
        "你是保险营销文案专家。请根据以下客户画像生成一封个性化车险营销邮件。\n"
        "客户画像：性别{gender}，年龄{age}岁，{driving_license}驾照，"
        "车龄{vehicle_age}，车辆{vehicle_damage}，年保费{annual_premium}元。\n"
        "要求：语气专业有温度，突出该客户画像的痛点与利益，包含行动号召(CTA)。\n"
        "仅返回严格 JSON，格式："
        '{{"subject":"邮件主题","content":"HTML格式正文"}}'
    )
    db = SessionLocal()
    try:
        existing = db.query(PromptTemplate).filter_by(is_active=True).first()
        if existing is None:
            tpl = PromptTemplate(name="default", content=DEFAULT_TEMPLATE, is_active=True)
            db.add(tpl)
            db.commit()
    finally:
        db.close()


def create_app() -> Flask:
    """应用工厂：创建并配置 Flask 实例。"""
    app = Flask(__name__, static_folder="static", static_url_path="/static")

    # -------- 1. 运行期目录 --------
    settings.ensure_runtime_dirs()

    # -------- 2. 蓝图注册 --------
    from app.api.v1 import register_blueprints

    register_blueprints(app)

    # -------- 3. 前端 SPA 入口 --------
    @app.route("/")
    def index() -> Response:
        return app.send_static_file("index.html")

    # -------- 4. teardown 钩子 --------
    app.teardown_appcontext(close_db)

    # -------- 5. 三级异常处理器 --------
    @app.errorhandler(BizException)
    def handle_biz_exception(e: BizException):
        return e.to_response()

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        return fail(CODE_INTERNAL_ERROR, e.description, e.code)

    @app.errorhandler(Exception)
    def handle_unexpected(e: Exception):
        return fail(CODE_INTERNAL_ERROR, "服务器内部错误", 500)

    # -------- 6. 首次启动 seed --------
    with app.app_context():
        Base.metadata.create_all(bind=engine)
        _seed_admin()
        _seed_prompt_template()

    return app
