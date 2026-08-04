"""邮件模块业务层。

对齐 `docs/03_API接口文档.md §4`：
- P1-10 实现 targets（高潜客户筛选）
- P1-11~P1-13 将实现邮件生成与记录 CRUD

筛选策略遵循 `docs/02_AI技术方案.md §2.7`：按预测概率的分位数取 top N%，
而非固定阈值 0.5。不同模型的概率分布差异很大（LR 集中在 0.5 附近，
XGBoost 偏两端），固定阈值会让筛选结果随模型漂移；分位数则保证永远
取到 top 10%，业务策略与模型解耦。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.core.response import (
    CODE_MODEL_UNAVAILABLE,
    CODE_NOT_FOUND,
    CODE_PARAM_ERROR,
    BizException,
)
from app.models.customer import Customer
from app.models.email_record import EmailRecord
from app.models.prompt_template import PromptTemplate
from app.models.user import User
from app.services import operation_log_service
from app.services.llm_service import (
    DEFAULT_PROMPT_TEMPLATE,
    REQUIRED_PLACEHOLDERS,
    LLMService,
)
from app.services.ml_service import _HIGH_POTENTIAL_QUANTILE

# 与 data_service 保持一致的分页上限
_MAX_PER_PAGE = 200
# docs/03 §4.2：limit 默认 5
_DEFAULT_GENERATE_LIMIT = 5
# 单次生成上限。LLM 调用在请求线程内串行（docs/02 §3.6），批量过大会请求超时
_MAX_GENERATE_BATCH = 50
# Prompt 模板长度上限，防止误粘贴超长文本
_MAX_PROMPT_LENGTH = 4000
# 校验模板可被 str.format 填充用的探针画像（字段与 naturalize 输出一致）
# docs/03 §4.5/4.8 的 status 取值域（EmailRecord 注释同源）
_ALLOWED_STATUSES = {"generated", "sent", "failed"}
_MAX_SUBJECT_LENGTH = 256
_MAX_DELETE_BATCH = 200


class _Unset:
    """「未传该字段」的哨兵。

    PUT 的两个字段都可选，用 None 作默认值就无法区分「未传」与「显式传
    null 表示清空」。单独一个哨兵类型让语义明确。
    """

    def __repr__(self) -> str:  # pragma: no cover - 仅调试用
        return "<UNSET>"


_UNSET = _Unset()


def _usernames(db: Session, user_ids) -> Dict[int, str]:
    """批量取 user_id -> username 映射。

    一次 IN 查询换掉逐条 record 访问 `record.creator.username` 的 N+1。
    """
    ids = {uid for uid in user_ids if uid is not None}
    if not ids:
        return {}
    rows = db.query(User.id, User.username).filter(User.id.in_(ids)).all()
    return {row[0]: row[1] for row in rows}


def _fetch_record(db: Session, user: Dict[str, Any], record_id: Any) -> EmailRecord:
    """取单条记录并做归属校验。

    越权访问返回 2001（不存在）而非 1003（无权限）—— 后者会泄露「这条记录
    确实存在，只是不属于你」，让攻击者能靠错误码枚举出他人记录的 id。
    """
    if isinstance(record_id, bool) or not isinstance(record_id, int) or record_id < 1:
        raise BizException(CODE_PARAM_ERROR, "record_id 必须是正整数", 400)
    record = db.query(EmailRecord).filter(EmailRecord.id == record_id).first()
    if record is None:
        raise BizException(CODE_NOT_FOUND, "邮件记录不存在", 400)
    if user.get("role") != "admin" and record.created_by != user["id"]:
        raise BizException(CODE_NOT_FOUND, "邮件记录不存在", 400)
    return record


_PROMPT_PROBE = {
    "gender": "Male",
    "age": 30,
    "driving_license": 1,
    "vehicle_age": "1-2 Year",
    "vehicle_damage": "No",
    "annual_premium": 10000.0,
    "previously_insured": 0,
}


class EmailService:
    """邮件模块业务编排。"""

    # ----- P1-10：高潜客户筛选 -----

    @staticmethod
    def targets(
        db: Session,
        percentile: float = _HIGH_POTENTIAL_QUANTILE,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """GET /email/targets（docs/03 §4.1）。

        Parameters
        ----------
        percentile:
            分位阈值，开区间 (0, 1)。0.9 表示取 top 10%。
        page / per_page:
            分页参数，per_page 上限 200。

        Returns
        -------
        dict
            `{threshold, total, customers}`，customers 为精简字段。

        Raises
        ------
        BizException
            percentile 越界 → 1001；无任何预测数据 → 3002。
        """
        if not 0 < percentile < 1:
            raise BizException(
                CODE_PARAM_ERROR, "参数 percentile 必须在 0 与 1 之间（不含端点）", 400
            )
        if per_page > _MAX_PER_PAGE:
            per_page = _MAX_PER_PAGE
        if per_page < 1:
            per_page = 1
        if page < 1:
            page = 1

        probs = Customer.predicted_probs(db)
        if not probs:
            raise BizException(
                CODE_MODEL_UNAVAILABLE,
                "暂无预测数据，请先调用 POST /model/predict 生成预测概率",
                400,
            )

        threshold = float(np.quantile(np.asarray(probs, dtype=float), percentile))
        items, total = Customer.paginate_by_prob(
            db, threshold=threshold, page=page, per_page=per_page
        )
        return {
            "threshold": threshold,
            "total": total,
            "customers": [c.to_target_dict() for c in items],
        }
    # ----- P1-11：LLM 邮件生成 -----

    @staticmethod
    def active_prompt(db: Session) -> "PromptTemplate":
        """取当前生效的 Prompt 模板（docs/02 §3.5）。

        无 is_active 记录时返回 None，由调用方回落到
        `llm_service.DEFAULT_PROMPT_TEMPLATE`。这样即使 seed 失败或模板被
        误删，邮件生成仍能工作。
        """
        return (
            db.query(PromptTemplate)
            .filter(PromptTemplate.is_active.is_(True))
            .order_by(PromptTemplate.id.desc())
            .first()
        )

    @staticmethod
    def generate(
        db: Session,
        user_id: int,
        customer_ids: Optional[List[int]] = None,
        limit: int = _DEFAULT_GENERATE_LIMIT,
    ) -> Dict[str, Any]:
        """POST /email/generate（docs/03 §4.2）。

        两种候选池来源（二选一，docs 明确 customer_ids 优先）：
        - 传了 `customer_ids`：精确取这些客户，不做分位数筛选；
        - 未传：按 `_HIGH_POTENTIAL_QUANTILE` 取 top，最多 `limit` 个。

        无论 LLM 成功或失败都会建 `email_records` 行（失败记 status=failed），
        这是 docs/02 §3.4 的降级要求：不让 LLM 故障拖垮流程，已生成的记录保留。

        Returns
        -------
        dict
            `{generated_count, failed_count, records}`，records 每项为
            `{customer_id, status, subject}`。

        Raises
        ------
        BizException
            limit 非法 / customer_ids 非法 → 1001；候选客户为空 → 2001；
            未做过预测且未指定 customer_ids → 3002。
        """
        if customer_ids is not None:
            if not isinstance(customer_ids, list) or not customer_ids:
                raise BizException(CODE_PARAM_ERROR, "customer_ids 必须是非空数组", 400)
            if len(customer_ids) > _MAX_GENERATE_BATCH:
                raise BizException(
                    CODE_PARAM_ERROR,
                    f"单次最多生成 {_MAX_GENERATE_BATCH} 封邮件",
                    400,
                )
            ids: List[int] = []
            for raw in customer_ids:
                # bool 是 int 的子类，True 会被当成 id=1，必须显式排除
                if isinstance(raw, bool) or not isinstance(raw, int):
                    raise BizException(CODE_PARAM_ERROR, "customer_ids 只能包含整数", 400)
                ids.append(raw)
            customers = Customer.by_ids(db, ids)
            if not customers:
                raise BizException(CODE_NOT_FOUND, "指定的客户不存在", 400)
        else:
            if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
                raise BizException(CODE_PARAM_ERROR, "参数 limit 必须是正整数", 400)
            if limit > _MAX_GENERATE_BATCH:
                raise BizException(
                    CODE_PARAM_ERROR,
                    f"单次最多生成 {_MAX_GENERATE_BATCH} 封邮件",
                    400,
                )
            probs = Customer.predicted_probs(db)
            if not probs:
                raise BizException(
                    CODE_MODEL_UNAVAILABLE,
                    "暂无预测数据，请先调用 POST /model/predict 生成预测概率",
                    400,
                )
            threshold = float(np.quantile(np.asarray(probs, dtype=float), _HIGH_POTENTIAL_QUANTILE))
            customers, _ = Customer.paginate_by_prob(
                db, threshold=threshold, page=1, per_page=limit
            )
            if not customers:
                raise BizException(CODE_NOT_FOUND, "无符合条件的高潜客户", 400)

        tpl = EmailService.active_prompt(db)
        template = tpl.content if tpl else DEFAULT_PROMPT_TEMPLATE
        service = LLMService()

        records: List[Dict[str, Any]] = []
        generated = 0
        failed = 0
        for cust in customers:
            result = service.generate_email(cust.to_dict(), template)
            if result.get("success"):
                subject = result["subject"]
                content = result["content"]
                status = "generated"
                generated += 1
            else:
                # 降级：主题里带上失败原因，便于前端与运维定位，正文留错误详情
                subject = None
                content = f"生成失败: {result.get('error', '未知错误')}"
                status = "failed"
                failed += 1
            db.add(
                EmailRecord(
                    customer_id=cust.id,
                    subject=subject,
                    content=content,
                    status=status,
                    created_by=user_id,
                )
            )
            records.append({"customer_id": cust.id, "status": status, "subject": subject})
        db.commit()

        operation_log_service.log(
            db,
            user_id,
            "email_generation",
            {
                "generated_count": generated,
                "failed_count": failed,
                "llm_available": service.available,
                "prompt_template": tpl.name if tpl else "default",
            },
        )
        return {
            "generated_count": generated,
            "failed_count": failed,
            "records": records,
        }

    # ----- P1-12：Prompt 模板管理 -----

    @staticmethod
    def get_prompt(db: Session) -> Dict[str, str]:
        """GET /email/prompt（docs/03 §4.3）。

        无 is_active 记录时返回内置默认模板而非报错，与 `generate()` 的
        回落行为保持一致 —— 前端拿到的永远是「下次生成实际会用的模板」。
        """
        tpl = EmailService.active_prompt(db)
        if tpl is None:
            return {"name": "default", "content": DEFAULT_PROMPT_TEMPLATE}
        return {"name": tpl.name, "content": tpl.content}

    @staticmethod
    def update_prompt(db: Session, content: Any, name: Optional[str] = None) -> Dict[str, str]:
        """PUT /email/prompt（docs/03 §4.4）。

        校验 content 至少含一个必需占位符 —— 模板不含占位符意味着所有客户
        收到完全相同的邮件，等于把个性化营销退化成群发。

        `is_active` 无数据库唯一约束（P0 Gate WARNING 5-C），因此激活走
        「同一事务内先全量失活再激活」，写法与 `ml_service.train()` 处理
        `is_best` 一致。整个过程单次 commit，中途失败回滚，不会出现
        「全部失活但新模板没激活」的空窗。

        Raises
        ------
        BizException
            content 非字符串 / 为空 / 缺占位符 / 过长 → 1001。
        """
        if not isinstance(content, str) or not content.strip():
            raise BizException(CODE_PARAM_ERROR, "content 不能为空", 400)
        content = content.strip()
        if len(content) > _MAX_PROMPT_LENGTH:
            raise BizException(
                CODE_PARAM_ERROR, f"content 长度不能超过 {_MAX_PROMPT_LENGTH} 字符", 400
            )
        missing = [ph for ph in REQUIRED_PLACEHOLDERS if ph not in content]
        if missing:
            raise BizException(
                CODE_PARAM_ERROR,
                f"content 必须包含占位符 {'、'.join(REQUIRED_PLACEHOLDERS)}，缺少 {'、'.join(missing)}",
                400,
            )
        # 提前验证模板可被 str.format 填充，避免坏模板存进去后每次生成都失败
        try:
            LLMService().render_prompt(_PROMPT_PROBE, content)
        except ValueError as exc:
            raise BizException(CODE_PARAM_ERROR, str(exc), 400) from exc

        target_name = (name or "").strip() if isinstance(name, str) else ""
        tpl = EmailService.active_prompt(db)
        try:
            # 事务内先全量失活，再激活目标行（WARNING 5-C：is_active 无唯一约束）。
            # synchronize_session="fetch" 是必需的：用 False 时 session 里的 tpl
            # 仍认为 is_active 是 True，随后 `tpl.is_active = True` 被判定为无变化
            # 而不发 UPDATE，数据库就停在 False，导致活跃行归零（BUG-017）。
            db.query(PromptTemplate).filter(PromptTemplate.is_active.is_(True)).update(
                {PromptTemplate.is_active: False}, synchronize_session="fetch"
            )
            if tpl is None:
                tpl = PromptTemplate(
                    name=target_name or "default", content=content, is_active=True
                )
                db.add(tpl)
            else:
                tpl.content = content
                if target_name:
                    tpl.name = target_name
                tpl.is_active = True
            db.commit()
        except BizException:
            db.rollback()
            raise
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            raise BizException(CODE_PARAM_ERROR, f"模板更新失败: {exc}", 400) from exc
        db.refresh(tpl)
        return {"name": tpl.name, "content": tpl.content}

    # ----- P1-13：邮件记录 CRUD -----

    @staticmethod
    def list_records(
        db: Session,
        user: Dict[str, Any],
        page: int = 1,
        per_page: int = 50,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """GET /email/records（docs/03 §4.5）。

        权限分流：admin 看全部并附 `created_by_username`，普通用户只看自己。
        隔离在 SQL 层（`created_by` 过滤）而非取出后再筛，避免把别人的数据
        先读进内存。

        Raises
        ------
        BizException
            status 不在允许集合 → 1001。
        """
        if status is not None:
            if not isinstance(status, str) or status not in _ALLOWED_STATUSES:
                raise BizException(
                    CODE_PARAM_ERROR,
                    f"status 只能是 {'/'.join(sorted(_ALLOWED_STATUSES))}",
                    400,
                )
        if per_page > _MAX_PER_PAGE:
            per_page = _MAX_PER_PAGE
        if per_page < 1:
            per_page = 1
        if page < 1:
            page = 1

        is_admin = user.get("role") == "admin"
        items, total = EmailRecord.paginate(
            db,
            page=page,
            per_page=per_page,
            status=status,
            created_by=None if is_admin else user["id"],
        )
        if is_admin:
            # 一次批量查用户名，避免逐条 record 触发 N+1 查询
            names = _usernames(db, [r.created_by for r in items])
            result = [r.to_dict(username=names.get(r.created_by)) for r in items]
        else:
            result = [r.to_dict() for r in items]
        pages = (total + per_page - 1) // per_page if total > 0 else 0
        return {
            "items": result,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    @staticmethod
    def get_record(db: Session, user: Dict[str, Any], record_id: int) -> Dict[str, Any]:
        """GET /email/records/{id}（docs/03 §4.6），含完整正文。"""
        record = _fetch_record(db, user, record_id)
        names = _usernames(db, [record.created_by])
        return record.to_dict(with_content=True, username=names.get(record.created_by))

    @staticmethod
    def update_record(
        db: Session,
        user: Dict[str, Any],
        record_id: int,
        subject: Any = _UNSET,
        content: Any = _UNSET,
    ) -> Dict[str, Any]:
        """PUT /email/records/{id}（docs/03 §4.7）。

        两个字段都可选，用 `_UNSET` 哨兵区分「未传」与「显式传 null」：
        未传保持原值，传 null 才清空。若用 None 作默认值，就无法表达
        「只改主题不动正文」这个最常见的操作。

        Raises
        ------
        BizException
            两字段都未传 → 1001；类型错误或过长 → 1001。
        """
        record = _fetch_record(db, user, record_id)
        if subject is _UNSET and content is _UNSET:
            raise BizException(
                CODE_PARAM_ERROR, "email_subject 与 email_content 至少提供一个", 400
            )
        if subject is not _UNSET:
            if subject is not None:
                if not isinstance(subject, str):
                    raise BizException(CODE_PARAM_ERROR, "email_subject 必须是字符串", 400)
                if len(subject) > _MAX_SUBJECT_LENGTH:
                    raise BizException(
                        CODE_PARAM_ERROR,
                        f"email_subject 长度不能超过 {_MAX_SUBJECT_LENGTH} 字符",
                        400,
                    )
            record.subject = subject
        if content is not _UNSET:
            if content is not None and not isinstance(content, str):
                raise BizException(CODE_PARAM_ERROR, "email_content 必须是字符串", 400)
            record.content = content
        db.commit()
        db.refresh(record)
        operation_log_service.log(
            db, user["id"], "email_update", {"record_id": record_id}
        )
        return record.to_dict(with_content=True)

    @staticmethod
    def mark_record(
        db: Session, user: Dict[str, Any], record_id: int, status: Any
    ) -> Dict[str, Any]:
        """PATCH /email/records/{id}（docs/03 §4.8）：标记状态。"""
        if not isinstance(status, str) or status not in _ALLOWED_STATUSES:
            raise BizException(
                CODE_PARAM_ERROR,
                f"status 只能是 {'/'.join(sorted(_ALLOWED_STATUSES))}",
                400,
            )
        record = _fetch_record(db, user, record_id)
        record.status = status
        db.commit()
        db.refresh(record)
        operation_log_service.log(
            db, user["id"], "email_mark", {"record_id": record_id, "status": status}
        )
        return record.to_dict()

    @staticmethod
    def delete_record(db: Session, user: Dict[str, Any], record_id: int) -> Dict[str, bool]:
        """DELETE /email/records/{id}（docs/03 §4.9）。"""
        record = _fetch_record(db, user, record_id)
        db.delete(record)
        db.commit()
        operation_log_service.log(
            db, user["id"], "email_delete", {"record_id": record_id, "count": 1}
        )
        return {"success": True}

    @staticmethod
    def delete_records(
        db: Session, user: Dict[str, Any], record_ids: Any
    ) -> Dict[str, int]:
        """DELETE /email/records（docs/03 §4.10）：批量删除。

        普通用户的越权 id 被静默跳过而非整批失败 —— 批量操作里夹一个别人的
        id 就全批拒绝，对前端多选场景不友好。`deleted_count` 会如实反映
        实际删除数量，调用方能自行发现差异。
        """
        if not isinstance(record_ids, list) or not record_ids:
            raise BizException(CODE_PARAM_ERROR, "record_ids 必须是非空数组", 400)
        if len(record_ids) > _MAX_DELETE_BATCH:
            raise BizException(
                CODE_PARAM_ERROR, f"单次最多删除 {_MAX_DELETE_BATCH} 条", 400
            )
        ids = []
        for raw in record_ids:
            if isinstance(raw, bool) or not isinstance(raw, int):
                raise BizException(CODE_PARAM_ERROR, "record_ids 只能包含整数", 400)
            ids.append(raw)

        q = db.query(EmailRecord).filter(EmailRecord.id.in_(list(set(ids))))
        if user.get("role") != "admin":
            q = q.filter(EmailRecord.created_by == user["id"])
        deleted = q.delete(synchronize_session="fetch")
        db.commit()
        operation_log_service.log(
            db, user["id"], "email_delete", {"count": deleted, "requested": len(set(ids))}
        )
        return {"deleted_count": int(deleted)}
