"""数据库基础设施层（Model 层之上）。

归属：app/core/database.py —— 数据库引擎与 Session 管理。

思路：
- 使用原生 SQLAlchemy 2.0（DeclarativeBase），不依赖 Flask-SQLAlchemy；
- 每个 HTTP 请求按需创建 Session 并挂到 g.db，请求结束由 teardown 钩子关闭；
- SQLite 场景下开启 check_same_thread=False 以适配 Flask 请求线程。
"""

from __future__ import annotations

import os
from typing import Optional

from flask import g
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import BASE_DIR, settings


def _normalize_sqlite_url(database_url: str) -> str:
    """SQLite 相对路径转绝对路径，避免依赖 CWD。"""
    if not database_url.startswith("sqlite"):
        return database_url
    prefix, sep, rest = database_url.partition(":///")
    if not sep:
        return database_url
    if rest.strip() == ":memory:":
        return database_url
    is_win_abs = len(rest) >= 2 and rest[1] == ":"
    if is_win_abs or rest.startswith("/"):
        return database_url
    abs_path = (BASE_DIR / rest).resolve()
    os.makedirs(abs_path.parent, exist_ok=True)
    return f"{prefix}:///{abs_path.as_posix()}"


def _make_engine(database_url: str) -> Engine:
    """按数据库 URL 生成 engine，SQLite 配置 check_same_thread=False。"""
    database_url = _normalize_sqlite_url(database_url)
    connect_args: dict = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(
        database_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


# 模块级全局：engine 与 SessionLocal 工厂
engine: Engine = _make_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """全项目共享的 ORM 基类。所有模型继承此类。"""


def get_db() -> Session:
    """获取当前请求的 Session。首次调用时挂到 g.db。"""
    try:
        db: Optional[Session] = g.get("db")
    except RuntimeError:
        return SessionLocal()

    if db is None:
        db = SessionLocal()
        g.db = db
    return db


def close_db(exception: Optional[BaseException] = None) -> None:
    """teardown_appcontext 钩子：请求结束时关闭 Session。"""
    try:
        db: Optional[Session] = g.pop("db", None)
    except RuntimeError:
        return
    if db is not None:
        db.close()