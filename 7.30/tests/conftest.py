"""Pytest 测试配置与共享 fixture。

设计要点：
- 测试环境使用临时文件 SQLite（不污染开发数据库）；
- LLM_API_KEY 置空，所有 LLM 调用走降级路径，不依赖外部服务；
- 每个测试前重置数据库并 seed 基础用户；
- admin_token / user_token 通过登录接口获取，模拟真实鉴权流程。
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from flask import Flask
from flask.wrappers import Response
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from app.core.config import settings
from app.core.database import Base, _make_engine
from app.core.security import create_access_token, hash_password
from app.models import Customer, User, Experiment, EmailRecord, PromptTemplate, OperationLog
from app.api.v1 import register_blueprints
from app.core.response import (
    CODE_INTERNAL_ERROR,
    CODE_PARAM_ERROR,
    BizException,
    fail,
)


@pytest.fixture(scope="session")
def _engine_setup():
    """Session 级 engine 初始化：临时目录 SQLite，整个测试会话共享。"""
    tmp = tempfile.TemporaryDirectory()
    db_path = Path(tmp.name) / "test.db"
    db_url = f"sqlite:///{db_path}"

    settings.DATABASE_URL = db_url
    _model_dir = os.path.join(tmp.name, "test_models")
    settings.MODEL_DIR = _model_dir
    os.makedirs(_model_dir, exist_ok=True)
    settings.LLM_API_KEY = ""

    test_engine = _make_engine(db_url)
    Base.metadata.create_all(bind=test_engine)

    import app.core.database as db_module

    db_module.engine = test_engine
    from sqlalchemy.orm import sessionmaker

    db_module.SessionLocal = sessionmaker(
        bind=test_engine, autoflush=False, autocommit=False, future=True
    )

    _seed_initial_data()

    yield

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    tmp.cleanup()


def _get_session():
    from app.core.database import SessionLocal

    return SessionLocal()


def _seed_initial_data():
    """Seed 默认 admin 用户和 Prompt 模板。"""
    db = _get_session()
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

        existing = db.query(PromptTemplate).filter_by(is_active=True).first()
        if existing is None:
            DEFAULT_TEMPLATE = (
                "你是保险营销文案专家。请根据以下客户画像生成一封个性化车险营销邮件。\n"
                "客户画像：性别{gender}，年龄{age}岁，{driving_license}驾照，"
                "车龄{vehicle_age}，车辆{vehicle_damage}，年保费{annual_premium}元。\n"
                "要求：语气专业有温度，突出该客户画像的痛点与利益，包含行动号召(CTA)。\n"
                "仅返回严格 JSON，格式："
                '{{"subject":"邮件主题","content":"HTML格式正文"}}'
            )
            tpl = PromptTemplate(name="default", content=DEFAULT_TEMPLATE, is_active=True)
            db.add(tpl)
            db.commit()
    finally:
        db.close()


def _clean_all_tables():
    """清空所有业务表（不含 users 和 prompt_templates）。"""
    db = _get_session()
    try:
        db.query(EmailRecord).delete()
        db.query(OperationLog).delete()
        db.query(Experiment).delete()
        db.query(Customer).delete()
        db.commit()
    finally:
        db.close()


def _clean_model_files():
    """清理测试期间生成的 .joblib 文件。"""
    model_dir = settings.model_dir_abs
    if os.path.isdir(model_dir):
        for f in os.listdir(model_dir):
            if f.endswith(".joblib"):
                os.remove(os.path.join(model_dir, f))


def _register_error_handlers(flask_app: Flask):
    """注册全局错误处理器，与 create_app() 保持一致。"""

    @flask_app.errorhandler(BizException)
    def handle_biz_exception(e: BizException):
        return e.to_response()

    @flask_app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(e: RequestEntityTooLarge):
        return fail(CODE_PARAM_ERROR, "上传文件超过50MB限制", 413)

    @flask_app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        return fail(CODE_INTERNAL_ERROR, e.description, e.code)

    @flask_app.errorhandler(Exception)
    def handle_unexpected(e: Exception):
        return fail(CODE_INTERNAL_ERROR, "服务器内部错误", 500)


@pytest.fixture
def app(_engine_setup):
    """Function 级 Flask 应用。每个测试前清空业务数据并 seed 默认用户。"""
    _clean_all_tables()
    _clean_model_files()

    flask_app = Flask(__name__, static_folder="static", static_url_path="/static")
    flask_app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

    register_blueprints(flask_app)
    _register_error_handlers(flask_app)

    from app.core.database import close_db

    flask_app.teardown_appcontext(close_db)

    yield flask_app


@pytest.fixture
def client(app):
    """Function 级测试客户端。"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Function 级数据库会话。"""
    session = _get_session()
    yield session
    session.close()


@pytest.fixture
def auth_headers(app):
    """admin 用户的 Authorization headers。"""
    db = _get_session()
    try:
        user = db.query(User).filter_by(username="test_admin").first()
        if user is None:
            user = User(
                username="test_admin",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        token = create_access_token(user.id, "admin", user.username)
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


@pytest.fixture
def admin_user(app):
    """admin 用户数据字典。"""
    db = _get_session()
    try:
        user = db.query(User).filter_by(username="test_admin").first()
        if user is None:
            user = User(
                username="test_admin",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return {"id": user.id, "username": user.username, "role": user.role}
    finally:
        db.close()


@pytest.fixture
def regular_user(app):
    """普通用户数据字典。"""
    db = _get_session()
    try:
        user = db.query(User).filter_by(username="test_user").first()
        if user is None:
            user = User(
                username="test_user",
                password_hash=hash_password("user123"),
                role="user",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return {"id": user.id, "username": user.username, "role": user.role}
    finally:
        db.close()


@pytest.fixture
def user_headers(app, regular_user):
    """普通用户的 Authorization headers。"""
    token = create_access_token(regular_user["id"], "user", regular_user["username"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_token(client):
    """admin JWT token 字符串（通过登录接口获取）。"""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": settings.DEFAULT_ADMIN_USERNAME, "password": settings.DEFAULT_ADMIN_PASSWORD},
    )
    data = resp.get_json()
    assert data["code"] == 0
    return data["data"]["access_token"]


@pytest.fixture
def user_token(client, regular_user):
    """user JWT token 字符串（通过登录接口获取）。"""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": regular_user["username"], "password": "user123"},
    )
    data = resp.get_json()
    assert data["code"] == 0
    return data["data"]["access_token"]
