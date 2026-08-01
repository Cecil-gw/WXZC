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

from app.models.operation_log import OperationLog


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