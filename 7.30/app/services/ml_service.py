"""机器学习业务层：特征标准化 + 三模型训练 + 选优 + 落库落盘。

设计对齐 `docs/02_AI技术方案.md §2.3~§2.8` 与 `docs/03_API接口文档.md §3.1`：

- 编码在 `app.utils.data_processor.prepare_features`，本模块只负责标准化与建模；
- `train_test_split(stratify=y)` 保证测试集正负比与全量一致；
- `StandardScaler` 只 fit 训练集，测试集仅 transform（防数据泄漏）；
- 不平衡处理：LR/RF 用 `class_weight="balanced"`，XGBoost 用 `scale_pos_weight=n_neg/n_pos`；
- 选优指标固定为 **ROC-AUC**（Accuracy 在 87:13 下不可靠）；
- 持久化 `{"model": ..., "scaler": ...}` 一起 dump，保证预测期特征分布一致；
- ROC / 混淆矩阵 / 特征重要性序列化进 `experiments.params`，供可视化接口复原。

本模块只做训练；`predicted_prob` 回写属于 P1-06 的预测链路。
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session
from xgboost import XGBClassifier

from app.core.config import settings
from app.core.response import (
    CODE_NOT_FOUND,
    CODE_PARAM_ERROR,
    CODE_TRAIN_FAILED,
    BizException,
)
from app.models.customer import Customer
from app.models.experiment import Experiment
from app.utils.data_processor import prepare_features

# 支持的算法名（与 docs/02 §2.4 一致）
SUPPORTED_MODELS: List[str] = [
    "logistic_regression",
    "random_forest",
    "xgboost",
]

# 默认超参（38 万行单机 60s 内可完成）
_DEFAULT_PARAMS: Dict[str, Dict[str, Any]] = {
    "logistic_regression": {"max_iter": 1000, "n_jobs": None},
    "random_forest": {"n_estimators": 100, "max_depth": 12, "n_jobs": -1},
    "xgboost": {
        "n_estimators": 200,
        "max_depth": 6,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "eval_metric": "auc",
        "n_jobs": -1,
    },
}

_MIN_ROWS: int = 20


def _get_model(name: str, scale_pos_weight: float, random_state: int, params: Optional[Dict[str, Any]] = None):
    """按算法名构造分类器，内置不平衡处理（docs/02 §2.4）。"""
    overrides = dict(params or {})
    if name == "logistic_regression":
        kwargs = {**_DEFAULT_PARAMS[name], **overrides}
        return LogisticRegression(
            class_weight="balanced", random_state=random_state, **kwargs
        )
    if name == "random_forest":
        kwargs = {**_DEFAULT_PARAMS[name], **overrides}
        return RandomForestClassifier(
            class_weight="balanced", random_state=random_state, **kwargs
        )
    if name == "xgboost":
        kwargs = {**_DEFAULT_PARAMS[name], **overrides}
        return XGBClassifier(
            scale_pos_weight=scale_pos_weight,
            random_state=random_state,
            **kwargs,
        )
    raise BizException(
        CODE_PARAM_ERROR,
        f"不支持的模型: {name}，可选 {SUPPORTED_MODELS}",
        400,
    )


def _feature_importances(model, feature_names: List[str]) -> List[float]:
    """统一取特征重要性：树模型用 feature_importances_，LR 用系数绝对值。"""
    if hasattr(model, "feature_importances_"):
        return [float(v) for v in np.asarray(model.feature_importances_).ravel()]
    if hasattr(model, "coef_"):
        return [float(abs(v)) for v in np.asarray(model.coef_).ravel()[: len(feature_names)]]
    return [0.0] * len(feature_names)


def _load_dataframe(db: Session) -> pd.DataFrame:
    """从 customers 表读全量训练数据。无数据抛 2001。"""
    rows = [c.to_dict() for c in db.query(Customer).all()]
    if len(rows) < _MIN_ROWS:
        raise BizException(
            CODE_NOT_FOUND,
            f"训练数据不足（当前 {len(rows)} 行，至少需要 {_MIN_ROWS} 行），请先上传数据",
            400,
        )
    return pd.DataFrame(rows)


class MLService:
    """模型训练业务层。"""

    @staticmethod
    def train(
        db: Session,
        models: Optional[List[str]] = None,
        test_size: float = 0.2,
        random_state: int = 42,
        params: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """训练指定算法并写入 experiments，返回 `{best_model, results}`。"""
        names = list(models) if models else list(SUPPORTED_MODELS)
        unknown = [n for n in names if n not in SUPPORTED_MODELS]
        if unknown:
            raise BizException(
                CODE_PARAM_ERROR,
                f"不支持的模型: {', '.join(unknown)}，可选 {SUPPORTED_MODELS}",
                400,
            )
        if not 0.05 <= float(test_size) <= 0.5:
            raise BizException(CODE_PARAM_ERROR, "test_size 需在 [0.05, 0.5] 之间", 400)

        df = _load_dataframe(db)
        X, y, feature_names = prepare_features(df, with_target=True)
        if int(y.nunique()) < 2:
            raise BizException(CODE_NOT_FOUND, "标签只有单一类别，无法训练", 400)

        # 分层拆分：保证训练/测试集正负比一致
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=float(test_size),
            random_state=int(random_state),
            stratify=y,
        )
        # 标准化：只 fit 训练集
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        n_neg = int((y_train == 0).sum())
        n_pos = int((y_train == 1).sum())
        spw = (n_neg / n_pos) if n_pos > 0 else 1.0

        model_dir = settings.model_dir_abs
        os.makedirs(model_dir, exist_ok=True)

        results: Dict[str, Dict[str, float]] = {}
        records: List[Experiment] = []
        for name in names:
            try:
                estimator = _get_model(
                    name, spw, int(random_state), (params or {}).get(name)
                )
                estimator.fit(X_train_s, y_train)
                proba = estimator.predict_proba(X_test_s)[:, 1]
                pred = (proba >= 0.5).astype(int)

                metrics = {
                    "accuracy": float(accuracy_score(y_test, pred)),
                    "precision": float(precision_score(y_test, pred, zero_division=0)),
                    "recall": float(recall_score(y_test, pred, zero_division=0)),
                    "f1_score": float(f1_score(y_test, pred, zero_division=0)),
                    "roc_auc": float(roc_auc_score(y_test, proba)),
                }
                results[name] = {k: round(v, 4) for k, v in metrics.items()}

                # model + scaler 一起存盘（docs/02 §2.6 关键约束）
                model_path = os.path.join(model_dir, f"{name}.joblib")
                joblib.dump({"model": estimator, "scaler": scaler}, model_path)

                fpr, tpr, _ = roc_curve(y_test, proba)
                cm = confusion_matrix(y_test, pred)
                params_json = json.dumps(
                    {
                        "roc": {
                            "fpr": [float(v) for v in fpr],
                            "tpr": [float(v) for v in tpr],
                        },
                        "confusion_matrix": cm.tolist(),
                        "feature_importances": _feature_importances(estimator, feature_names),
                        "feature_names": feature_names,
                        "train_config": {
                            "test_size": float(test_size),
                            "random_state": int(random_state),
                            "scale_pos_weight": round(float(spw), 4),
                            "n_train": int(len(y_train)),
                            "n_test": int(len(y_test)),
                        },
                    },
                    ensure_ascii=False,
                )
                records.append(
                    Experiment(
                        model_name=name,
                        accuracy=metrics["accuracy"],
                        precision=metrics["precision"],
                        recall=metrics["recall"],
                        f1_score=metrics["f1_score"],
                        roc_auc=metrics["roc_auc"],
                        params=params_json,
                        model_path=model_path,
                        is_best=False,
                    )
                )
            except BizException:
                raise
            except Exception as exc:  # noqa: BLE001
                raise BizException(
                    CODE_TRAIN_FAILED, f"模型 {name} 训练失败: {exc}", 500
                ) from exc

        if not records:
            raise BizException(CODE_TRAIN_FAILED, "没有任何模型训练成功", 500)

        # 选优：ROC-AUC 最高；先全量失活历史 is_best，保证唯一
        best = max(records, key=lambda r: r.roc_auc)
        db.query(Experiment).filter(Experiment.is_best.is_(True)).update(
            {Experiment.is_best: False}, synchronize_session=False
        )
        best.is_best = True
        db.add_all(records)
        db.commit()

        return {"best_model": best.model_name, "results": results}