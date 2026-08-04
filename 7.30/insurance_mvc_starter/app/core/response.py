"""统一响应封装（路由层与前端交互的统一数据格式）。

归属：app/core/response.py —— 响应信封与业务异常。

思路：
- 所有 JSON 接口统一返回 {code, message, data}；
- 业务错误抛 BizException(code, message, http_status)，由全局 errorhandler 统一转成信封响应；
- code=0 表示成功，非零业务码表示各类错误。
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

from flask import jsonify
from flask.wrappers import Response


# ---------------- 业务码常量 ----------------
CODE_SUCCESS: int = 0
CODE_PARAM_ERROR: int = 1001
CODE_UNAUTHORIZED: int = 1002
CODE_FORBIDDEN: int = 1003
CODE_USERNAME_EXISTS: int = 1004
CODE_NOT_FOUND: int = 2001
CODE_EXCEL_PARSE_ERROR: int = 2002
CODE_INTERNAL_ERROR: int = 5000


def success(data: Any = None, message: str = "success", http_status: int = 200) -> Tuple[Response, int]:
    """构造成功响应。"""
    payload = {"code": CODE_SUCCESS, "message": message, "data": data}
    return jsonify(payload), http_status


def fail(code: int, message: str, http_status: int = 400, data: Any = None) -> Tuple[Response, int]:
    """构造失败响应。"""
    payload = {"code": code, "message": message, "data": data}
    return jsonify(payload), http_status


class BizException(Exception):
    """业务异常。由全局 errorhandler 捕获并转成统一响应。"""

    def __init__(
        self,
        code: int,
        message: str,
        http_status: Optional[int] = None,
        data: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status if http_status is not None else _default_http_for(code)
        self.data = data

    def to_response(self) -> Tuple[Response, int]:
        return fail(self.code, self.message, self.http_status, self.data)


def _default_http_for(code: int) -> int:
    """按业务码给出默认 HTTP 状态码。"""
    return {
        CODE_SUCCESS: 200,
        CODE_PARAM_ERROR: 400,
        CODE_UNAUTHORIZED: 401,
        CODE_FORBIDDEN: 403,
        CODE_USERNAME_EXISTS: 400,
        CODE_NOT_FOUND: 404,
        CODE_EXCEL_PARSE_ERROR: 400,
        CODE_INTERNAL_ERROR: 500,
    }.get(code, 400)