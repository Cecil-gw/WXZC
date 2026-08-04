"""大模型业务层（docs/02_AI技术方案.md §3）。

职责：把客户画像转成自然语言、填入 Prompt 模板、调用 OpenAI 兼容接口、
清理并解析返回的 JSON。

三条设计约束来自 docs/02：
1. §3.4 降级优先 —— 未配置 `LLM_API_KEY` 时 `client=None`，本模块所有失败
   路径都返回 `{"success": False, "error": ...}` 而非抛异常。LLM 是外部依赖，
   它挂掉不该拖垮整个邮件生成流程；
2. §4.1 反编码 —— ML 用 0/1 编码训练，LLM 要看自然语言。两个 AI 子系统之间
   必须做语义还原，不能直接传编码值；
3. §3.3 花括号转义 —— 模板从 DB 读，用 `str.format` 而非 f-string；模板里
   的 JSON 输出示例须写成 `{{ }}`，否则 format 会把它当占位符。
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from app.core.config import settings

# 兜底模板：DB 中无 is_active 模板时使用（与 app/__init__.py 的 seed 内容一致）
DEFAULT_PROMPT_TEMPLATE = (
    "你是保险营销文案专家。请根据以下客户画像生成一封个性化车险营销邮件。\n"
    "客户画像：性别{gender}，年龄{age}岁，{driving_license}驾照，"
    "车龄{vehicle_age}，车辆{vehicle_damage}，年保费{annual_premium}元。\n"
    "要求：语气专业有温度，突出该客户画像的痛点与利益，包含行动号召(CTA)。\n"
    "仅返回严格 JSON，格式："
    '{{"subject":"邮件主题","content":"HTML格式正文"}}'
)

# Prompt 模板必须至少含其中一个占位符，否则说明模板写错了（P1-12 校验用）
REQUIRED_PLACEHOLDERS = ("{gender}", "{age}")

# 反编码映射（docs/02 §4.1）
_GENDER_MAP = {"Male": "男", "Female": "女"}
_DAMAGE_MAP = {"Yes": "曾受损", "No": "无损记录"}
_VEHICLE_AGE_MAP = {
    "< 1 Year": "不足 1 年",
    "1-2 Year": "1 至 2 年",
    "> 2 Years": "2 年以上",
}


def naturalize(customer: Dict[str, Any]) -> Dict[str, Any]:
    """客户画像反编码为自然语言（docs/02 §4.1）。

    ML 侧的 `driving_license=1` / `vehicle_damage="Yes"` 对 LLM 毫无意义，
    必须还原成「有」「曾受损」这类人类语言。未知取值原样透传，避免因为
    数据里出现意外值就整条生成失败。
    """
    return {
        "gender": _GENDER_MAP.get(customer.get("gender"), customer.get("gender") or "未知"),
        "age": customer.get("age") if customer.get("age") is not None else "未知",
        "driving_license": "有" if customer.get("driving_license") == 1 else "无",
        "vehicle_age": _VEHICLE_AGE_MAP.get(
            customer.get("vehicle_age"), customer.get("vehicle_age") or "未知"
        ),
        "vehicle_damage": _DAMAGE_MAP.get(
            customer.get("vehicle_damage"), customer.get("vehicle_damage") or "未知"
        ),
        "annual_premium": customer.get("annual_premium")
        if customer.get("annual_premium") is not None
        else "未知",
        "previously_insured": "已投保" if customer.get("previously_insured") == 1 else "未投保",
        "predicted_prob": customer.get("predicted_prob"),
    }


def _strip_markdown_fence(text: str) -> str:
    """清理 LLM 返回的 markdown 代码块包裹（docs/02 §3.4）。

    即便 Prompt 写了「仅返回严格 JSON」，模型仍常常裹上 ```json ... ```。
    """
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


class LLMService:
    """OpenAI 兼容协议的大模型调用封装。

    实例化不会因缺少 API Key 而失败 —— 这是 docs/02 §3.4 的核心要求：
    没配 Key 时系统照常启动运行，只是邮件生成功能返回 failed。
    """

    def __init__(self) -> None:
        self.client = None
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        if not settings.LLM_API_KEY:
            return
        try:
            from openai import OpenAI

            self.client = OpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_API_BASE or None,
            )
        except Exception:  # noqa: BLE001 - SDK 缺失或初始化失败一律降级
            self.client = None

    @property
    def available(self) -> bool:
        """LLM 是否可用。供上层决定是否值得逐个客户重试。"""
        return self.client is not None

    def render_prompt(self, customer: Dict[str, Any], template: Optional[str] = None) -> str:
        """把客户画像填入模板。

        用 `str.format(**profile)` 而非 f-string —— 模板来自 DB，是运行期
        数据不是代码期字面量。缺失占位符（模板里写了 DB 没有的字段）会抛
        KeyError，这里转成可读的 ValueError 由调用方降级。
        """
        tpl = template or DEFAULT_PROMPT_TEMPLATE
        profile = naturalize(customer)
        try:
            return tpl.format(**profile)
        except (KeyError, IndexError, ValueError) as exc:
            raise ValueError(f"Prompt 模板占位符无法填充: {exc}") from exc

    def generate_email(
        self, customer: Dict[str, Any], prompt_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """为单个客户生成邮件。

        永不抛异常（docs/02 §3.4 降级策略）：任何失败都返回
        `{"success": False, "error": ...}`，让上层照常建 status=failed 记录。

        Returns
        -------
        dict
            成功 `{"success": True, "subject": str, "content": str}`；
            失败 `{"success": False, "error": str}`。
        """
        if not self.client:
            return {"success": False, "error": "LLM_API_KEY 未配置"}
        try:
            prompt = self.render_prompt(customer, prompt_template)
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            raw = (resp.choices[0].message.content or "").strip()
            if not raw:
                return {"success": False, "error": "LLM 返回空内容"}
            payload = json.loads(_strip_markdown_fence(raw))
            if not isinstance(payload, dict):
                return {"success": False, "error": "LLM 返回的 JSON 不是对象"}
            subject = payload.get("subject")
            content = payload.get("content")
            if not subject or not content:
                return {"success": False, "error": "LLM 返回缺少 subject 或 content"}
            return {"success": True, "subject": str(subject), "content": str(content)}
        except json.JSONDecodeError as exc:
            return {"success": False, "error": f"LLM 返回非合法 JSON: {exc}"}
        except Exception as exc:  # noqa: BLE001 - 网络/限流/SDK 异常一律降级
            return {"success": False, "error": f"{type(exc).__name__}: {exc}"}