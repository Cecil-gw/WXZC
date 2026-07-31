"""数据库：SQLAlchemy 2.0 引擎 / 会话 / Base / Flask 请求级会话管理

【MVC 归属】基础设施层（被 Model 层依赖）
【思路】
1. 建 engine(连接池)
2. 用 sessionmaker 包装成会话工厂
3. 写 get_db() 从 g 取/建会话
4. 导出 Base 给 Model 层用

为什么不用 Flask-SQLAlchemy？
  用原生 SQLAlchemy 2.0，Model 层独立于 Web 框架，可被 CLI/测试复用。
"""
import os
from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

# SQLite：确保数据库文件所在目录存在(导入时即创建)
if settings.DATABASE_URL.startswith("sqlite"):
    _db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    _db_dir = os.path.dirname(_db_path)
    if _db_dir:
        os.makedirs(_db_dir, exist_ok=True)

# check_same_thread=False：SQLite 在多线程(Flask 多 worker)下共享连接需要，否则会报错：
#   sqlite3.ProgrammingError: SQLite Error: database is locked: database is locked
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})    

# 会话工厂：每次调用 SessionLocal() 产生一个独立的数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    if "db" not in g:
        g.db = SessionLocal()
    return g.db

def close_db(e=None):
    """请求结束时关闭 DB 会话（注册为 teardown_appcontext 钩子）"""
    db = g.pop("db", None)
    if db is not None:
        db.close()