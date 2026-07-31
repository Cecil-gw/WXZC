"""统一响应封装 + 业务异常

【MVC 归属】View 层（视图层）——所有响应都经过这里封装成统一格式
【思路】
1. unified_response 统一所有成功响应的外壳 {code, message, data}
2. paginate 包装分页
3. BizException 让业务能"抛"业务码
4. json() 辅助函数让 Flask 路由少写一层 jsonify

为什么用统一信封？
  - 前端只处理一种结构 {code, message, data}
  - 业务异常与 HTTP 解耦：业务错误 raise BizException，全局处理器转成统一信封
"""

from typing import Any
from flask import jsonify

def unified_response(data: Any = None, code: int = 0, message: str = "success") -> dict:
    """统一响应信封：{code, message, data}

    code=0 成功，非 0 失败，data 是真正的业务数据。
    """
    return {"code": code, "message": message, "data": data}

# def paginate(items: list, total: int, page: int, per_page: int) -> dict:
#     """分页响应封装：向上取整算总页数"""
#     return {
#         "items": items,
#         "total": total,
#         "page": page,
#         "per_page": per_page,
#         # 向上取整公式：math.ceil(total/per_page) 的整数版
#         "pages": (total + per_page - 1) // per_page if per_page else 0,
#     }

def json(data: Any = None, code: int = 0, message: str = "success", status: int = 200):
    """Flask 路由专用：unified_response + jsonify 二合一，返回 Response 对象

    逐字思路：
    1. 用 unified_response 拼出 {code, message, data} 字典
    2. 用 jsonify 转成 Flask Response 对象
    3. status 控制 HTTP 状态码（默认 200，业务错误时传 400/401/403 等）
    """
    response = jsonify(unified_response(data, code, message))
    response.status_code = status
    return response
'''
@bp.route("/me")
def me():
    return json({"name": "张三"})
'''


class BizException(Exception):
    """业务异常基类，用于抛出业务错误"""
    # code：业务码
    # message：业务错误信息
    # status_code：HTTP 状态码
    #内置异常：`ValueError`（值错误）、`TypeError`（类型错误）、`Exception`（所有异常的爸爸）。
    # 业务异常：`BizException`（业务异常基类）。
    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    

