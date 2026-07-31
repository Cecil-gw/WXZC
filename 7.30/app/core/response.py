"""统一响应封装与业务异常。

设计对齐 `docs/03_API接口文档.md §0.1 / §0.5` 与 `docs/04_技术框架方案.md §6.3`：

- 所有 JSON 接口统一返回 `{code, message, data}`；
- 业务错误抛 `BizException(code, message, http_status)`，由全局 errorhandler
  统一转成信封响应，避免路由层四处拼字典；
- `code=0` 表示成功；非零业务码含义见 API 文档 §0.5。
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

from flask import jsonify
from flask.wrappers import Response


# ---------------- 业务码常量（与 API 文档 §0.5 对齐） ----------------
CODE_SUCCESS: int = 0
CODE_PARAM_ERROR: int = 1001
CODE_UNAUTHORIZED: int = 1002
CODE_FORBIDDEN: int = 1003
CODE_USERNAME_EXISTS: int = 1004
CODE_NOT_FOUND: int = 2001
CODE_EXCEL_PARSE_ERROR: int = 2002
CODE_TRAIN_FAILED: int = 3001
CODE_MODEL_UNAVAILABLE: int = 3002
CODE_EMAIL_FAILED: int = 4001
CODE_INTERNAL_ERROR: int = 5000


def success(data: Any = None, message: str = "success", http_status: int = 200) -> Tuple[Response, int]:
    """构造成功响应。默认 `code=0`、`message="success"`、HTTP 200。"""
    payload = {"code": CODE_SUCCESS, "message": message, "data": data}
    return jsonify(payload), http_status


def fail(code: int, message: str, http_status: int = 400, data: Any = None) -> Tuple[Response, int]:
    """构造失败响应。通常由 errorhandler 调用，路由层优先抛 `BizException`。"""
    payload = {"code": code, "message": message, "data": data}
    return jsonify(payload), http_status


class BizException(Exception):
    """业务异常。

    Attributes
    ----------
    code : int
        业务码，见本模块常量或 `docs/03_API接口文档.md §0.5`。
    message : str
        用户可读的错误信息。
    http_status : int
        HTTP 状态码，默认按业务码常见映射。
    data : Any
        可选的附加数据（一般为 None）。
    """

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
    """按业务码给出默认 HTTP 状态码。未列出的走 400。"""
    return {
        CODE_SUCCESS: 200,
        CODE_PARAM_ERROR: 400,
        CODE_UNAUTHORIZED: 401,
        CODE_FORBIDDEN: 403,
        CODE_USERNAME_EXISTS: 400,
        CODE_NOT_FOUND: 404,
        CODE_EXCEL_PARSE_ERROR: 400,
        CODE_TRAIN_FAILED: 500,
        CODE_MODEL_UNAVAILABLE: 400,
        CODE_EMAIL_FAILED: 500,
        CODE_INTERNAL_ERROR: 500,
    }.get(code, 400)
