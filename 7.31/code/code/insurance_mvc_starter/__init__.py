"""Flask 应用入口：create_app 工厂 + 建表/建admin + 全局异常处理

【MVC 归属】基础设施层（应用工厂，串起 M/V/C 三层）
【思路】
1. _init_admin：建默认管理员 admin/admin123
2. create_app：创建 app → 注册蓝图 → 注册异常处理器 → 建表+建 admin

【和主项目的关系】本文件和主项目 app/__init__.py 同名同职责，
学生 Day 3 切到主项目时，会看到主项目多了 _init_prompt_template 和静态文件挂载，
但 create_app 工厂的核心结构完全一致，零迁移成本。
"""
from flask import Flask
from werkzeug.exceptions import HTTPException

from app.core.database import Base, engine, SessionLocal, close_db
from app.core.response import BizException, json
from app.core.security import hash_password


def _init_admin():
    """首次启动创建默认管理员 admin/admin123

    1. 开独立 session（不在请求上下文里，手动管）
    2. 查 admin 是否已存在；不存在才插入
    3. finally 关闭 session
    """
    # 函数内 import：避免模块加载时触发 app/models/__init__.py 整包加载
    from app.models.user import User
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(username="admin", password_hash=hash_password("admin123"), role="admin"))
            db.commit()
    finally:
        db.close()


def create_app() -> Flask:
    """Flask 应用工厂：创建并配置 Flask app

    逐字思路：
    1. 创建 Flask app
    2. strict_slashes=False：/users 和 /users/ 都能匹配
    3. 注册业务蓝图（auth）
    4. 注册 teardown 钩子（请求结束自动关 DB 会话）
    5. 注册三级异常处理器（BizException → HTTPException → Exception 兜底）
    6. 在 app_context 里建表 + 建 admin
    """
    app = Flask(__name__)
    # strict_slashes=False：/api/v1/auth/users 和 /api/v1/auth/users/ 都能匹配
    app.url_map.strict_slashes = False

    # ===== 注册蓝图（Controller 层）=====
    from app.api.v1 import register_blueprints
    register_blueprints(app)

    # ===== 注册 teardown 钩子：请求结束自动关 DB 会话 =====
    app.teardown_appcontext(close_db)

    # ===== 三级全局异常处理（从具体到宽泛）=====
    # 优先级：BizException(业务) → HTTPException(框架HTTP) → Exception(兜底)

    @app.errorhandler(BizException)
    def handle_biz_exception(e: BizException):
        """业务异常 → 统一响应(携带具体业务码)"""
        return json(None, e.code, e.message, status=e.status_code)

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        """框架级 HTTP 异常 → 业务码映射(401→1002, 403→1003, 404→2001)"""
        code_map = {401: 1002, 403: 1003, 404: 2001, 405: 1001}
        code = code_map.get(e.code, 5000)
        return json(None, code, str(e.description), status=e.code)

    @app.errorhandler(Exception)
    def handle_global_exception(e: Exception):
        """兜底异常 → 5000"""
        import traceback
        traceback.print_exc()  # 打印堆栈方便排查
        return json(None, 5000, f"服务器内部错误: {e}", status=500)

    # ===== 启动初始化：建表 + 建 admin =====
    with app.app_context():
        # 关键：必须 import 所有模型，Base.metadata 才能发现它们 → create_all 才能建表
        # 【坑】不能用 `import app.models`！会与局部变量 app(Flask实例) 冲突，
        #        把 app 重新绑定为模块，导致 return app 返回模块而非 Flask 实例
        import app.models as _models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        _init_admin()

    return app