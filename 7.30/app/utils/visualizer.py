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
from typing import Any, Dict, List  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
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

# ====================================================================
# P1-08：模型评估可视化（docs/03 §3.6）
#
# 数据源是 `experiments.params`（P1-04 训练时已落库的 ROC/CM/特征重要性），
# 因此绘图无需重新训练，也不接触模型文件。
# 本组函数输入为已反序列化的 dict，与上面 EDA 组（输入 DataFrame）区分。
# ====================================================================


def roc_curve_png(series: List[Dict[str, Any]]) -> str:
    """多模型 ROC 曲线叠加对比。

    `series` 元素：`{"model_name": str, "fpr": list, "tpr": list, "roc_auc": float}`。
    对角虚线是随机猜测基线（AUC=0.5），曲线离它越远说明排序能力越强。
    """
    fig, ax = plt.subplots(figsize=(7, 5.5))
    palette = ["#0d6efd", "#198754", "#dc3545", "#6f42c1", "#fd7e14"]
    for i, s in enumerate(series):
        ax.plot(
            s["fpr"],
            s["tpr"],
            color=palette[i % len(palette)],
            linewidth=1.8,
            label=f"{s['model_name']} (AUC={s['roc_auc']:.4f})",
        )
    ax.plot([0, 1], [0, 1], color="#adb5bd", linestyle="--", linewidth=1, label="Random (AUC=0.5)")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.02)
    ax.set_title("ROC Curve Comparison")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.25)
    return _to_base64(fig)


def metrics_comparison_png(rows: List[Dict[str, Any]]) -> str:
    """多模型五指标分组柱状图。

    `rows` 元素：`{"model_name": str, "accuracy": float, ...,"roc_auc": float}`。
    ROC-AUC 单独用深色强调，因为它才是本项目的选优依据（docs/02 §2.5）。
    """
    metrics = ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
    labels = ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]
    colors = ["#adb5bd", "#8ab4f8", "#6c9bd1", "#4a7fb5", "#0d6efd"]

    n_models = len(rows)
    x = np.arange(n_models)
    width = 0.15
    fig, ax = plt.subplots(figsize=(max(7, n_models * 2.6), 5))
    for i, (key, label) in enumerate(zip(metrics, labels)):
        offset = (i - (len(metrics) - 1) / 2) * width
        values = [float(r.get(key) or 0.0) for r in rows]
        bars = ax.bar(x + offset, values, width, label=label, color=colors[i])
        for b, v in zip(bars, values):
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.3f}",
                    ha="center", va="bottom", fontsize=7, rotation=90)
    ax.set_xticks(x)
    ax.set_xticklabels([r["model_name"] for r in rows], fontsize=9)
    ax.set_ylim(0.0, 1.15)
    ax.set_title("Model Metrics Comparison")
    ax.set_ylabel("Score")
    ax.legend(ncol=5, fontsize=8, loc="upper center")
    ax.grid(axis="y", alpha=0.25)
    return _to_base64(fig)


def confusion_matrix_png(matrix: List[List[int]], model_name: str) -> str:
    """单模型混淆矩阵热力图（2x2）。

    行是真实标签、列是预测标签；格内标注计数与占该行的比例，
    便于直接看出正类召回情况（不平衡数据下只看总量会有误导）。
    """
    cm = np.asarray(matrix, dtype=float)
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    im = ax.imshow(cm, cmap="Blues")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ticks = ["No (0)", "Yes (1)"]
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(ticks)
    ax.set_yticklabels(ticks)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"Confusion Matrix - {model_name}")

    vmax = cm.max() if cm.size else 1.0
    for r in range(cm.shape[0]):
        row_total = cm[r].sum()
        for c in range(cm.shape[1]):
            pct = (cm[r, c] / row_total * 100) if row_total else 0.0
            ax.text(
                c, r, f"{int(cm[r, c])}\n{pct:.1f}%",
                ha="center", va="center", fontsize=10,
                color="white" if cm[r, c] > vmax / 2 else "#212529",
            )
    return _to_base64(fig)


def feature_importance_png(
    importances: List[float], feature_names: List[str], model_name: str
) -> str:
    """单模型特征重要性横向条形图（按重要性升序排列，最重要的在最上方）。"""
    pairs = sorted(zip(feature_names, importances), key=lambda kv: float(kv[1]))
    names = [k for k, _ in pairs]
    values = [float(v) for _, v in pairs]

    fig, ax = plt.subplots(figsize=(7.5, max(4, len(names) * 0.42)))
    ax.barh(names, values, color="#0d6efd")
    ax.set_title(f"Feature Importance - {model_name}")
    ax.set_xlabel("Importance")
    span = max(values) if values else 1.0
    for i, v in enumerate(values):
        ax.text(v + span * 0.01, i, f"{v:.4f}", va="center", fontsize=8)
    ax.set_xlim(0, span * 1.18 if span else 1.0)
    ax.grid(axis="x", alpha=0.25)
    return _to_base64(fig)


# 需要 model 查询参数的图表（docs/03 §3.6：confusion_matrix / feature_importance 必填）
MODEL_REQUIRED_CHARTS = frozenset({"confusion_matrix", "feature_importance"})

# 模型评估图表白名单（与数据模块的 CHART_FUNCS 分开，避免两套图表混淆）
MODEL_CHART_TYPES = (
    "roc_curve",
    "metrics_comparison",
    "confusion_matrix",
    "feature_importance",
)
