"""日志模块 /logs Blueprint（占位，路由在 P1-14 实现）。"""
from flask import Blueprint

bp = Blueprint("log", __name__, url_prefix="/api/v1/logs")
