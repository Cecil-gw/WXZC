"""应用工厂：延迟创建 Flask 实例，注册所有组件。

设计对齐 `docs/04_技术框架方案.md §6.1`：

- `create_app()` 工厂函数延迟创建 Flask 实例，便于测试与多环境部署；
- 按顺序：配置路由 → 蓝图 → 静态文件 → teardown 钩子 → 异常处理器；
- 首次启动自动建表 + seed 默认管理员 + default Prompt 模板。
"""

from __future__ import annotations

from flask import Flask, jsonify
from flask.wrappers import Response
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from app.core.config import settings
from app.core.database import Base, engine, close_db
from app.core.response import (
    CODE_INTERNAL_ERROR,
    CODE_PARAM_ERROR,
    BizException,
    fail,
)

# 上传文件大小上限（DECISION-004 方案 C）：
# 10MB 与 PRD §170「38 万行 Excel 上传入库 < 60 秒」冲突——38 万行 x 12 列的 xlsx
# 实测约 12~20MB，10MB 会把真实数据集直接拒掉。50MB 既留足余量又拦住恶意超大文件。
MAX_UPLOAD_BYTES: int = 50 * 1024 * 1024
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
    import os
    from pathlib import Path
    base_dir = Path(__file__).parent.parent.absolute()
    app = Flask(
        __name__,
        static_folder=os.path.normpath(str(base_dir / "app" / "static")),
        static_url_path="/static",
    )

    # 请求体上限，超出由 werkzeug 抛 RequestEntityTooLarge(413)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

    # -------- 1. 运行期目录 --------
    settings.ensure_runtime_dirs()

    # -------- 2. 蓝图注册 --------
    from app.api.v1 import register_blueprints

    register_blueprints(app)

    # -------- 3. 前端 SPA 入口 --------
    @app.route("/")
    def index() -> Response:
        return app.send_static_file("index.html")

    @app.route("/favicon.ico")
    def favicon():
        """空响应favicon，避免404"""
        return ("", 204)

    # -------- 4. teardown 钩子 --------
    app.teardown_appcontext(close_db)

    # -------- 5. 三级异常处理器 --------
    @app.errorhandler(BizException)
    def handle_biz_exception(e: BizException):
        return e.to_response()

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(e: RequestEntityTooLarge):
        """413：上传超限。比通用 HTTPException 处理器更特异，Flask 优先命中此处。

        不落到 5000 通用分支，而是按 docs/03 §0.5 归为参数错误 1001。
        """
        return fail(CODE_PARAM_ERROR, "上传文件超过50MB限制", 413)

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        from app.core.response import CODE_NOT_FOUND
        biz_code = CODE_NOT_FOUND if e.code == 404 else CODE_INTERNAL_ERROR
        return fail(biz_code, e.description, e.code)

    @app.errorhandler(Exception)
    def handle_unexpected(e: Exception):
        import traceback, logging
        logging.error("未捕获的异常:\n%s", traceback.format_exc())
        return fail(CODE_INTERNAL_ERROR, "服务器内部错误: " + str(e), 500)

    # -------- 6. 首次启动 seed --------
    with app.app_context():
        Base.metadata.create_all(bind=engine)
        _seed_admin()
        _seed_prompt_template()

    return app
