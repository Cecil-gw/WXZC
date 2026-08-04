"""操作日志业务层（补 P0 Gate Review WARNING 7-C）。

统一收口 `operation_logs` 写入，避免 P1-04/06/09/11/13 五处重复
`db.add(OperationLog(...)); db.commit()`。

设计要点：
- `details` 接受 dict，内部统一 `json.dumps(ensure_ascii=False)` 落库；
- 日志写入失败不应影响主业务，因此内部 `rollback` 后静默返回 None；
- 纯业务层（不依赖 Flask），`user_id` 由调用方从 `g.current_user` 取。
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.response import CODE_PARAM_ERROR, BizException
from app.models.operation_log import OperationLog
from app.models.user import User

# 与其它模块保持一致的分页上限
_MAX_PER_PAGE = 200


def log(
    db: Session,
    user_id: int,
    action: str,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[OperationLog]:
    """写一条操作日志。失败不抛异常，返回 None。"""
    try:
        record = OperationLog(
            user_id=user_id,
            action=action,
            details=json.dumps(details, ensure_ascii=False) if details else None,
        )
        db.add(record)
        db.commit()
        return record
    except Exception:  # noqa: BLE001 - 日志失败不影响主流程
        db.rollback()
        return None

def list_logs(
    db: Session,
    page: int = 1,
    per_page: int = 50,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
) -> Dict[str, Any]:
    """GET /logs 的业务编排（docs/03 §5.1）。

    `action` 走白名单校验：拼错的取值（比如 "email_send"）静默返回空列表会让
    使用者以为「确实没有这类操作」，明确报 1001 更容易发现问题。

    Raises
    ------
    BizException
        action 不在允许集合 → 1001。
    """
    if action is not None:
        if not isinstance(action, str) or action not in OperationLog.ALLOWED_ACTIONS:
            raise BizException(
                CODE_PARAM_ERROR,
                f"action 只能是 {'/'.join(OperationLog.ALLOWED_ACTIONS)}",
                400,
            )
    if per_page > _MAX_PER_PAGE:
        per_page = _MAX_PER_PAGE
    if per_page < 1:
        per_page = 1
    if page < 1:
        page = 1

    items, total = OperationLog.paginate(
        db, page=page, per_page=per_page, user_id=user_id, action=action
    )
    # 批量取用户名，避免逐条访问 log.user.username 触发 N+1
    ids = {r.user_id for r in items if r.user_id is not None}
    names: Dict[int, str] = {}
    if ids:
        names = {
            row[0]: row[1]
            for row in db.query(User.id, User.username).filter(User.id.in_(ids)).all()
        }
    pages = (total + per_page - 1) // per_page if total > 0 else 0
    return {
        "items": [r.to_dict(username=names.get(r.user_id)) for r in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }
