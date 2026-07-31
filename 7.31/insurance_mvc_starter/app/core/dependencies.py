"""鉴权装饰器：login_required / role_required + get_current_user

【MVC 归属】基础设施层（被 Controller 层依赖，实现 RBAC）
【思路】
1. 写 _authenticate 公共鉴权逻辑（取 token → 解析 → 查用户 → 存 g）
2. 包成 login_required 装饰器
3. 写 role_required 工厂做角色校验
4. 导出 get_current_user 给路由用

RBAC 核心思想：不直接给用户授权，而是给角色授权，用户通过角色获得权限。
本项目两类角色：
  - admin：全部接口（如查所有用户）
  - user：基础接口（登录后即可用）
"""
from functools import wraps
from flask import request, g
from app.core.database import get_db
from app.core.security import decode_token
from app.core.response import BizException
from app.models.user import User


def _authenticate() -> User:
    """公共鉴权逻辑：取 token → 解析 → 查用户 → 存 g.current_user → 返回 user

    抽成独立函数让 login_required 和 role_required 复用，避免重复代码。

    逐字思路：
    1. 从 Authorization 头取 Bearer token（格式 "Bearer xxx.yyy.zzz"）
    2. decode_token 解 JWT 拿用户名；解析失败(token 坏/过期) → 401
    3. 用 username 查数据库；查不到(用户被删) → 401
    4. 把 user 挂到 g.current_user 上供路由内取用
    """
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    if not token:
        raise BizException(1002, "未提供Token，请先登录", 401)
    username = decode_token(token)
    if not username:
        raise BizException(1002, "Token无效或已过期", 401)
    db = get_db()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise BizException(1002, "用户不存在", 401)
    g.current_user = user
    return user


def login_required(f):
    """登录校验装饰器：校验 Token + 查用户，通过则放行

    用法：@bp.route('/me') \n @login_required \n def me(): ...
    校验失败抛 BizException(401) 被全局处理器拦截
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        _authenticate()
        return f(*args, **kwargs)
    return wrapper


def role_required(role: str):
    """角色守卫工厂：role_required('admin') 只放行 admin

    【为什么是工厂】因为装饰器需要一个可调用对象，而我们还要传入 role 参数。
    所以写成"外层函数接收 role，返回一个装饰器"——闭包把 role 圈住。

    用法：@bp.route('/users') \n @role_required('admin') \n def users(): ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = _authenticate()
            if user.role != role:
                raise BizException(1003, "权限不足，需要管理员权限", 403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user() -> User:
    """路由函数内调用，返回当前登录用户对象（须在 @login_required 之后调用）"""
    return g.current_user
