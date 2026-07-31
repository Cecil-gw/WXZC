"""数据库基础设施：engine / SessionLocal / Base / 请求级 Session。

设计对齐 `docs/04_技术框架方案.md §6.2`：
- 使用原生 SQLAlchemy 2.0（`DeclarativeBase`），不用 Flask-SQLAlchemy 扩展；
- 每个 HTTP 请求按需创建 Session 并挂到 `g.db`，请求结束由
  `teardown_appcontext(close_db)` 自动关闭，避免连接泄漏；
- SQLite 场景下开启 `check_same_thread=False` 以适配 Flask 请求线程。

本模块不引入任何业务模型；ORM 表定义放在 `app/models/*`，import 模型时以
`from app.core.database import Base` 为准，保证 `Base.metadata` 单一来源。
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
    """SQLite 相对路径转项目根下的绝对路径，避免依赖 CWD。

    - `sqlite:///:memory:` 保持不变；
    - `sqlite:///relative/path.db` -> `sqlite:///<BASE_DIR>/relative/path.db`；
    - 已经是绝对路径（`sqlite:////abs/path` on POSIX，`sqlite:///C:/...` on Windows）保持不变。
    """
    if not database_url.startswith("sqlite"):
        return database_url
    prefix, sep, rest = database_url.partition(":///")
    if not sep:
        return database_url
    if rest.strip() == ":memory:":
        return database_url
    # Windows 绝对路径形如 `C:/...` 或 `C:\...`
    is_win_abs = len(rest) >= 2 and rest[1] == ":"
    if is_win_abs or rest.startswith("/"):
        return database_url
    abs_path = (BASE_DIR / rest).resolve()
    # 确保目录存在（instance/ 等）
    os.makedirs(abs_path.parent, exist_ok=True)
    return f"{prefix}:///{abs_path.as_posix()}"


def _make_engine(database_url: str) -> Engine:
    """按数据库 URL 生成 engine，SQLite 与其它数据库分别配置。"""
    database_url = _normalize_sqlite_url(database_url)
    connect_args: dict = {}
    if database_url.startswith("sqlite"):
        # Flask 多线程访问 SQLite 需要放开线程检查
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
    """全项目共享的 ORM 基类。所有模型继承此类以复用 `metadata`。"""


def get_db() -> Session:
    """获取当前请求的 Session。首次调用时挂到 `g.db`。

    非请求上下文（如 CLI / 后台任务）调用时同样可用：直接返回一个新的 Session，
    调用方负责关闭。
    """
    try:
        db: Optional[Session] = g.get("db")  # type: ignore[assignment]
    except RuntimeError:
        # 没有 Flask 请求上下文时，`g` 不可用；直接返回新 Session
        return SessionLocal()

    if db is None:
        db = SessionLocal()
        g.db = db
    return db


def close_db(exception: Optional[BaseException] = None) -> None:
    """`teardown_appcontext` 钩子：请求结束时关闭 Session。

    该函数签名符合 Flask `teardown_appcontext` 的要求（接收一个可选异常参数）。
    """
    try:
        db: Optional[Session] = g.pop("db", None)  # type: ignore[assignment]
    except RuntimeError:
        return
    if db is not None:
        db.close()
