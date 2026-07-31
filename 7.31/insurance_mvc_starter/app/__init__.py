"""应用工厂：create_app()

【MVC 归属】整个 Flask 应用的入口，把所有层（Controller/Model/Infra）组装起来

应用工厂模式（App Factory）的好处：
1. 可创建多个实例：测试时传不同配置、生产部署多 worker
2. 延迟初始化：import app 包不会立即建 DB / 建表，只有 create_app() 才真正做
3. 顺序可控：先注册蓝图/异常处理器，再 with app_context() 建表/seed admin

执行顺序（create_app 内部）：
  ① Flask(__name__)           实例化 app
  ② register_blueprints(app)  挂载 /api/v1/* 路由
  ③ 注册 teardown_appcontext  每个请求结束自动关 DB 会话
  ④ 注册 3 个 errorhandler     BizException / HTTPException / Exception 兜底
  ⑤ with app.app_context():
       a. Base.metadata.create_all()  建所有表（经过 app.models 的 import）
       b. _init_admin()               首次启动建 admin/admin123 默认账号
"""
from flask import Flask
from werkzeug.exceptions import HTTPException

from .core.database import Base, engine, close_db, SessionLocal
from .core.security import hash_password
from .core.response import json, BizException
from .api.v1 import register_blueprints
# 必须显式 import models：SQLAlchemy 只有在 import 模型后，Base.metadata 里才会登记这些表
from . import models  # noqa: F401


def _init_admin():
    """首次启动时自动创建默认管理员 admin / admin123

    幂等：已存在就直接跳过，保证多次 create_app（如热重载）不重复建。
    为什么不放在路由启动时做？因为要保证有一个能登录的管理员，否则第一次进系统谁都登不上。
    """
    db = SessionLocal()
    try:
        from .models.user import User
        exists = User.find_by_username(db, "admin")
        if not exists:
            User.create(
                db,
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            print("[INIT] 默认管理员已创建：admin / admin123")
        else:
            print("[INIT] 管理员已存在，跳过创建")
    finally:
        db.close()


def create_app() -> Flask:
    """应用工厂：返回一个装配好的 Flask 实例"""
    # ① 创建 Flask 实例
    app = Flask(__name__)

    # ② 注册蓝图（挂载路由）
    register_blueprints(app)

    # ③ 请求结束钩子：自动关 DB 会话（防连接泄漏）
    app.teardown_appcontext(close_db)

    # ④ 三级异常处理器：从具体到宽泛，保证任何异常都返回统一信封
    @app.errorhandler(BizException)
    def _handle_biz(e: BizException):
        """业务异常：直接按业务码 + message + HTTP status 包成统一信封"""
        return json(data=None, code=e.code, message=e.message, status=e.status_code)

    @app.errorhandler(HTTPException)
    def _handle_http(e: HTTPException):
        """Flask 内置 HTTP 异常（404/405 等）：转成统一信封"""
        biz_code = 2001 if e.code == 404 else 5000
        return json(data=None, code=biz_code, message=e.description, status=e.code or 500)

    @app.errorhandler(Exception)
    def _handle_exc(e: Exception):
        """兜底 500：任何未被捕获的异常，返回统一信封不暴露堆栈（生产安全）"""
        import traceback
        traceback.print_exc()
        return json(data=None, code=5000, message="服务器内部错误", status=500)

    # ⑤ 在 app 上下文里建表 + seed（需要 g/Session 等能正常工作的环境）
    with app.app_context():
        Base.metadata.create_all(bind=engine)
        _init_admin()

    # 健康检查：GET /health，部署时探针用
    @app.route("/health")
    def _health():
        return json({"status": "ok", "app": "insurance_mvc_starter"})

    return app
