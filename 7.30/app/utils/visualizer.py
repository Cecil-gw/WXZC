"""可视化工具：matplotlib Agg 后端生成 base64 PNG。

设计要点：
- 第 1 行 `matplotlib.use("Agg")`（对齐 P0 Gate Review WARNING 7-A，避免 Windows headless Tk 崩溃）；
- 4 个图表类型对齐 `docs/03 §2.5`；
- 每个函数返回 base64 字符串，前端可直接用 `<img src="data:image/png;base64,...">` 显示；
- 不依赖 Flask / DB（输入是 DataFrame，由 Service 层传入）。

P1-03 范围：响应分布 / 性别 x 响应 / 年龄分布 / 年保费分布。
"""

import matplotlib

matplotlib.use("Agg")  # 必须在 import pyplot 之前

import base64  # noqa: E402
import io  # noqa: E402
from typing import Dict  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


def _to_base64(fig) -> str:
    """把 matplotlib Figure 序列化为 base64 字符串。"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def response_distribution_png(df: pd.DataFrame) -> str:
    """response 分布（柱状图）。"""
    counts = df["response"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ["#6c757d", "#0d6efd"]
    ax.bar(counts.index.astype(str), counts.values, color=colors[: len(counts)])
    ax.set_title("Response Distribution")
    ax.set_xlabel("Response (0=No, 1=Yes)")
    ax.set_ylabel("Count")
    for i, v in enumerate(counts.values):
        ax.text(i, v, str(int(v)), ha="center", va="bottom")
    return _to_base64(fig)


def gender_response_png(df: pd.DataFrame) -> str:
    """gender x response 交叉表（分组柱状图）。"""
    ct = pd.crosstab(df["gender"], df["response"])
    fig, ax = plt.subplots(figsize=(6, 4))
    ct.plot(kind="bar", ax=ax, color=["#6c757d", "#0d6efd"])
    ax.set_title("Gender x Response")
    ax.set_xlabel("Gender")
    ax.set_ylabel("Count")
    ax.legend(title="Response")
    return _to_base64(fig)


def age_distribution_png(df: pd.DataFrame) -> str:
    """age 直方图。"""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(df["age"].dropna(), bins=20, color="#0d6efd", edgecolor="white")
    ax.set_title("Age Distribution")
    ax.set_xlabel("Age")
    ax.set_ylabel("Count")
    return _to_base64(fig)


def premium_distribution_png(df: pd.DataFrame) -> str:
    """annual_premium 直方图。"""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(df["annual_premium"].dropna(), bins=30, color="#198754", edgecolor="white")
    ax.set_title("Annual Premium Distribution")
    ax.set_xlabel("Annual Premium")
    ax.set_ylabel("Count")
    return _to_base64(fig)


# 路由层 -> 函数 映射
CHART_FUNCS: Dict[str, callable] = {
    "response_distribution": response_distribution_png,
    "gender_response": gender_response_png,
    "age_distribution": age_distribution_png,
    "premium_distribution": premium_distribution_png,
}