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
import uuid
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
    CODE_EXCEL_PARSE_ERROR,
    CODE_MODEL_UNAVAILABLE,
    CODE_NOT_FOUND,
    CODE_PARAM_ERROR,
    CODE_TRAIN_FAILED,
    BizException,
)
from app.models.customer import Customer
from app.models.experiment import Experiment
from app.utils.data_processor import prepare_features, read_excel_to_df
from app.utils.visualizer import (
    MODEL_CHART_TYPES,
    MODEL_REQUIRED_CHARTS,
    confusion_matrix_png,
    feature_importance_png,
    metrics_comparison_png,
    roc_curve_png,
)

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
# 回写 predicted_prob 的分批规模，与 data_service.bulk_insert 保持一致
_BATCH_SIZE: int = 5000
_MAX_PER_PAGE: int = 200


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


def _load_bundle(model_path: str) -> Dict[str, Any]:
    """加载 joblib bundle 并校验含 model 与 scaler。损坏/结构不符抛 3002。"""
    try:
        bundle = joblib.load(model_path)
    except Exception as exc:  # noqa: BLE001
        raise BizException(
            CODE_MODEL_UNAVAILABLE, f"模型文件加载失败: {exc}", 400
        ) from exc
    if not isinstance(bundle, dict) or "model" not in bundle or "scaler" not in bundle:
        raise BizException(
            CODE_MODEL_UNAVAILABLE,
            "模型文件结构异常（缺少 model 或 scaler），请重新训练",
            400,
        )
    return bundle


# 高潜客户分位数（docs/02 §2.7：默认取 top 10%）
_HIGH_POTENTIAL_QUANTILE: float = 0.9


def _prob_statistics(proba: "np.ndarray") -> Dict[str, Any]:
    """汇总预测概率分布。

    `high_potential_threshold` 用 0.9 分位数而非固定 0.5：不同算法的概率分布
    差异很大（LR 偏中间、XGBoost 偏两端），固定阈值没有可比性；分位数保证
    永远取 top 10%，业务策略稳定（docs/02 §2.7）。
    """
    threshold = float(np.quantile(proba, _HIGH_POTENTIAL_QUANTILE))
    return {
        "count": int(len(proba)),
        "mean_prob": round(float(np.mean(proba)), 6),
        "min_prob": round(float(np.min(proba)), 6),
        "max_prob": round(float(np.max(proba)), 6),
        "high_potential_threshold": round(threshold, 6),
        "high_potential_count": int((proba >= threshold).sum()),
    }


# sklearn/xgboost 类名 -> 本项目算法名
_ESTIMATOR_CLASS_MAP: Dict[str, str] = {
    "LogisticRegression": "logistic_regression",
    "RandomForestClassifier": "random_forest",
    "XGBClassifier": "xgboost",
}


def _infer_model_name(estimator: Any) -> str:
    """从 estimator 类名推断算法名。

    导入时不采用用户上传的文件名（不可信，可能含路径穿越），而是看 bundle
    里实际是什么模型，落盘名因此必然落在白名单内。
    """
    cls_name = type(estimator).__name__
    name = _ESTIMATOR_CLASS_MAP.get(cls_name)
    if name is None:
        raise BizException(
            CODE_PARAM_ERROR,
            f"无法识别的模型类型: {cls_name}，仅支持 {SUPPORTED_MODELS}",
            400,
        )
    return name


def _latest_experiment(db: Session, model_name: str) -> Experiment:
    """取指定算法最新一条实验记录。无记录抛 3002。"""
    exp = (
        db.query(Experiment)
        .filter(Experiment.model_name == model_name)
        .order_by(Experiment.created_at.desc(), Experiment.id.desc())
        .first()
    )
    if exp is None:
        raise BizException(
            CODE_MODEL_UNAVAILABLE, f"模型 {model_name} 尚无实验记录，请先训练", 400
        )
    return exp


def _latest_per_model(db: Session) -> List[Experiment]:
    """每个算法各取最新一条实验记录，按算法名稳定排序。

    跨模型对比图只应展示每个算法的最新结果；若把历史多轮全画进去，
    同名曲线会重叠成一团。
    """
    rows = (
        db.query(Experiment)
        .order_by(Experiment.created_at.desc(), Experiment.id.desc())
        .all()
    )
    latest: Dict[str, Experiment] = {}
    for exp in rows:
        latest.setdefault(exp.model_name, exp)
    return [latest[k] for k in sorted(latest)]


def _experiment_params(exp: Experiment) -> Dict[str, Any]:
    """反序列化 `experiments.params`。缺失或损坏抛 3002。"""
    if not exp.params:
        raise BizException(
            CODE_MODEL_UNAVAILABLE,
            f"实验记录 {exp.id} 缺少 params 数据，请重新训练",
            400,
        )
    try:
        parsed = json.loads(exp.params)
    except (TypeError, ValueError) as exc:
        raise BizException(
            CODE_MODEL_UNAVAILABLE,
            f"实验记录 {exp.id} 的 params 解析失败，请重新训练",
            400,
        ) from exc
    if not isinstance(parsed, dict):
        raise BizException(
            CODE_MODEL_UNAVAILABLE, f"实验记录 {exp.id} 的 params 结构异常", 400
        )
    return parsed


def _resolve_experiment(db: Session, model_name: Optional[str]) -> Experiment:
    """定位要用于预测的实验记录并校验模型文件可用。

    `model_name` 为空取 `is_best`，否则取该模型最新一条。排序与 `/model/best`
    保持一致（`created_at desc, id desc` + `first()`），规避 `is_best` 多条为真
    时 `one()` 抛异常（P0 Gate WARNING 5-C）。

    Raises
    ------
    BizException
        模型名不在白名单 → 1001；无实验记录 / 文件丢失 → 3002。
    """
    if model_name is not None and model_name not in SUPPORTED_MODELS:
        raise BizException(
            CODE_PARAM_ERROR,
            f"不支持的模型: {model_name}，可选 {SUPPORTED_MODELS}",
            400,
        )
    query = db.query(Experiment)
    if model_name:
        query = query.filter(Experiment.model_name == model_name)
    else:
        query = query.filter(Experiment.is_best.is_(True))
    exp = query.order_by(Experiment.created_at.desc(), Experiment.id.desc()).first()
    if exp is None:
        hint = f"模型 {model_name} 尚未训练" if model_name else "暂无最佳模型，请先训练"
        raise BizException(CODE_MODEL_UNAVAILABLE, hint, 400)
    if not exp.model_path or not os.path.exists(exp.model_path):
        raise BizException(
            CODE_MODEL_UNAVAILABLE,
            f"模型文件丢失: {exp.model_path or '(未记录路径)'}，请重新训练",
            400,
        )
    return exp


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
    # ----- P1-05：实验记录分页 -----

    @staticmethod
    def list_experiments(
        db: Session,
        page: int = 1,
        per_page: int = 50,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """GET /model/experiments（docs/03 §3.2）。

        per_page 上限与 P1-02 客户分页保持一致（200），避免一次拉全表。
        """
        if per_page > _MAX_PER_PAGE:
            per_page = _MAX_PER_PAGE
        if per_page < 1:
            per_page = 1
        if page < 1:
            page = 1
        if model_name and model_name not in SUPPORTED_MODELS:
            raise BizException(
                CODE_PARAM_ERROR,
                f"不支持的模型: {model_name}，可选 {SUPPORTED_MODELS}",
                400,
            )
        items, total = Experiment.paginate(
            db, page=page, per_page=per_page, model_name=model_name
        )
        pages = (total + per_page - 1) // per_page if total > 0 else 0
        return {
            "items": [e.to_dict() for e in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    # ----- P1-05：最佳模型 -----

    @staticmethod
    def get_best(db: Session) -> Dict[str, Any]:
        """GET /model/best（docs/03 §3.3）。无最佳模型抛 3002。"""
        best = (
            db.query(Experiment)
            .filter(Experiment.is_best.is_(True))
            .order_by(Experiment.created_at.desc(), Experiment.id.desc())
            .first()
        )
        if best is None:
            raise BizException(
                CODE_MODEL_UNAVAILABLE, "暂无最佳模型，请先训练", 400
            )
        return {
            "model_name": best.model_name,
            "roc_auc": best.roc_auc,
            "experiment_id": best.id,
        }

    # ----- P1-06：全量预测 -----

    @staticmethod
    def predict(db: Session, model_name: Optional[str] = None) -> Dict[str, Any]:
        """POST /model/predict（docs/03 §3.4）。

        加载 joblib bundle（缺省用最佳模型），复用其中的 scaler 做 transform，
        对全量客户 `predict_proba` 取正类概率并回写 `customers.predicted_prob`。

        Returns
        -------
        dict
            `{model_name, predicted_count}`

        Raises
        ------
        BizException
            无最佳模型 / 模型文件丢失 / 预测异常 → 3002；无客户数据 → 2001。
        """
        exp = _resolve_experiment(db, model_name)
        bundle = _load_bundle(exp.model_path)
        model = bundle["model"]
        scaler = bundle["scaler"]

        # 读全量客户（预测不需要标签，with_target=False）
        customers = db.query(Customer).order_by(Customer.id).all()
        if not customers:
            raise BizException(CODE_NOT_FOUND, "暂无客户数据，请先上传", 400)
        df = pd.DataFrame([c.to_dict() for c in customers])

        try:
            X, _, _ = prepare_features(df, with_target=False)
            # scaler 只 transform，绝不 fit（docs/02 §2.6）
            proba = model.predict_proba(scaler.transform(X))[:, 1]
        except BizException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise BizException(
                CODE_MODEL_UNAVAILABLE, f"预测失败: {exc}", 500
            ) from exc

        # 分批回写，避免一次性生成过大的 UPDATE 语句
        mappings = [
            {"id": int(cid), "predicted_prob": float(p)}
            for cid, p in zip(df["id"].tolist(), proba)
        ]
        for i in range(0, len(mappings), _BATCH_SIZE):
            db.bulk_update_mappings(Customer, mappings[i : i + _BATCH_SIZE])
        db.commit()

        return {"model_name": exp.model_name, "predicted_count": len(mappings)}

    # ----- P1-07：上传数据预测（不入库） -----

    @staticmethod
    def predict_upload(
        db: Session, file_storage: Any, model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """POST /model/predict_upload（docs/03 §3.5）。

        对上传的新一批客户预测并直接返回，**不写库**，不覆盖训练数据。

        与 `/data/upload` 的差异：本接口不要求标签列 `Response`，只校验 10 个
        特征列；因此不复用 `check_required_columns`（那个函数服务于入库场景，
        必须有 Response）。

        Returns
        -------
        dict
            `{model_name, total_count, statistics, predictions}`

        Raises
        ------
        BizException
            解析失败 → 2002；缺特征列 → 1001；模型不可用 → 3002。
        """
        exp = _resolve_experiment(db, model_name)
        bundle = _load_bundle(exp.model_path)

        df = read_excel_to_df(file_storage)
        if df.empty:
            raise BizException(CODE_EXCEL_PARSE_ERROR, "Excel 无数据行", 400)

        # 预测场景不强制要求标签列，只校验特征列
        X, _, _ = prepare_features(df, with_target=False)

        try:
            proba = bundle["model"].predict_proba(bundle["scaler"].transform(X))[:, 1]
        except BizException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise BizException(
                CODE_MODEL_UNAVAILABLE, f"预测失败: {exc}", 500
            ) from exc

        # id 列可选：缺失时用行号（1-based）兜底，保证 predictions 可追溯
        if "id" in df.columns:
            ids = [int(v) for v in pd.to_numeric(df["id"], errors="coerce").fillna(0)]
        else:
            ids = list(range(1, len(df) + 1))

        predictions = [
            {"id": cid, "predicted_prob": round(float(p), 6)}
            for cid, p in zip(ids, proba)
        ]
        # 按概率倒序：本接口的价值在排序而非二分（docs/02 §2.7）
        predictions.sort(key=lambda r: r["predicted_prob"], reverse=True)

        return {
            "model_name": exp.model_name,
            "total_count": len(predictions),
            "statistics": _prob_statistics(proba),
            "predictions": predictions,
        }

    # ----- P1-08：模型评估可视化 -----

    @staticmethod
    def visualization(
        db: Session, chart_type: str, model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """GET /model/visualization/{chart_type}（docs/03 §3.6）。

        数据全部来自 `experiments.params`（P1-04 训练时落库），因此绘图不需要
        重新训练、也不加载模型文件。

        - `roc_curve` / `metrics_comparison`：跨模型对比，取每个算法最新一条实验；
        - `confusion_matrix` / `feature_importance`：单模型，`model_name` 必填。

        Raises
        ------
        BizException
            未知 chart_type / 缺 model 参数 / 模型名非法 → 1001；
            无实验记录或 params 缺失 → 3002。
        """
        if chart_type not in MODEL_CHART_TYPES:
            raise BizException(
                CODE_PARAM_ERROR,
                f"未知图表类型: {chart_type}，可选 {list(MODEL_CHART_TYPES)}",
                400,
            )
        if chart_type in MODEL_REQUIRED_CHARTS and not model_name:
            raise BizException(
                CODE_PARAM_ERROR,
                f"图表 {chart_type} 需要 model 参数",
                400,
            )
        if model_name is not None and model_name not in SUPPORTED_MODELS:
            raise BizException(
                CODE_PARAM_ERROR,
                f"不支持的模型: {model_name}，可选 {SUPPORTED_MODELS}",
                400,
            )

        if chart_type in MODEL_REQUIRED_CHARTS:
            exp = _latest_experiment(db, model_name)
            params = _experiment_params(exp)
            if chart_type == "confusion_matrix":
                matrix = params.get("confusion_matrix")
                if not matrix:
                    raise BizException(
                        CODE_MODEL_UNAVAILABLE,
                        f"实验记录缺少混淆矩阵数据: {exp.model_name}",
                        400,
                    )
                image = confusion_matrix_png(matrix, exp.model_name)
            else:
                names = params.get("feature_names")
                values = params.get("feature_importances")
                if not names or not values or len(names) != len(values):
                    raise BizException(
                        CODE_MODEL_UNAVAILABLE,
                        f"实验记录缺少特征重要性数据: {exp.model_name}",
                        400,
                    )
                image = feature_importance_png(values, names, exp.model_name)
        else:
            experiments = _latest_per_model(db)
            if not experiments:
                raise BizException(
                    CODE_MODEL_UNAVAILABLE, "暂无实验记录，请先训练", 400
                )
            if chart_type == "roc_curve":
                series: List[Dict[str, Any]] = []
                for exp in experiments:
                    roc = (_experiment_params(exp) or {}).get("roc") or {}
                    fpr, tpr = roc.get("fpr"), roc.get("tpr")
                    if not fpr or not tpr or len(fpr) != len(tpr):
                        continue
                    series.append({
                        "model_name": exp.model_name,
                        "fpr": fpr,
                        "tpr": tpr,
                        "roc_auc": float(exp.roc_auc),
                    })
                if not series:
                    raise BizException(
                        CODE_MODEL_UNAVAILABLE, "实验记录缺少 ROC 数据，请重新训练", 400
                    )
                image = roc_curve_png(series)
            else:
                rows = [{
                    "model_name": e.model_name,
                    "accuracy": e.accuracy,
                    "precision": e.precision,
                    "recall": e.recall,
                    "f1_score": e.f1_score,
                    "roc_auc": e.roc_auc,
                } for e in experiments]
                image = metrics_comparison_png(rows)

        return {"chart_type": chart_type, "image_base64": image, "format": "png"}

    # ----- P1-09：模型导出 / 导入 -----

    @staticmethod
    def export_model(model_name: str) -> Dict[str, str]:
        """GET /model/export/{model_name} 的路径解析（docs/03 §3.7）。

        只返回文件信息，实际 `send_file` 由路由层负责（Service 不碰 HTTP）。

        安全要点：`model_name` 来自 URL 路径，必须走白名单而非直接拼接，
        否则 `../../.env` 之类的输入会造成目录穿越。白名单校验后再做一次
        路径归属检查，双重防御。

        Returns
        -------
        dict
            `{model_name, path, filename}`

        Raises
        ------
        BizException
            模型名非法 → 1001；文件不存在 → 3002。
        """
        if model_name not in SUPPORTED_MODELS:
            raise BizException(
                CODE_PARAM_ERROR,
                f"不支持的模型: {model_name}，可选 {SUPPORTED_MODELS}",
                400,
            )
        model_dir = settings.model_dir_abs
        filename = f"{model_name}.joblib"
        path = os.path.abspath(os.path.join(model_dir, filename))
        # 二次防御：解析后的路径必须仍在 MODEL_DIR 之内
        if os.path.commonpath([path, os.path.abspath(model_dir)]) != os.path.abspath(model_dir):
            raise BizException(CODE_PARAM_ERROR, "非法的模型路径", 400)
        if not os.path.exists(path):
            raise BizException(
                CODE_MODEL_UNAVAILABLE,
                f"模型文件不存在: {filename}，请先训练该模型",
                400,
            )
        return {"model_name": model_name, "path": path, "filename": filename}

    @staticmethod
    def import_model(file_storage: Any) -> Dict[str, str]:
        """POST /model/import（docs/03 §3.8）。

        校验顺序：扩展名 → 真正 joblib.load 校验 bundle 结构 → 落盘。

        只看扩展名是不够的：任意文件改名成 `.joblib` 也能通过。因此先写入
        临时文件用 `_load_bundle` 验证内含 `model` 与 `scaler`，通过后才
        覆盖到 `MODEL_DIR`，避免坏文件污染已有模型。

        落盘文件名由 bundle 内的模型类型推断并限定在白名单内，不采用用户
        上传的原始文件名，杜绝路径穿越。

        Returns
        -------
        dict
            `{model_name, path}`

        Raises
        ------
        BizException
            非 .joblib / 结构不符 / 无法识别模型类型 → 1001。
        """
        filename = getattr(file_storage, "filename", "") or ""
        if not filename.lower().endswith(".joblib"):
            raise BizException(CODE_PARAM_ERROR, "仅支持 .joblib 格式", 400)

        model_dir = settings.model_dir_abs
        os.makedirs(model_dir, exist_ok=True)

        # 先落到临时文件校验，避免坏文件直接覆盖已有模型
        tmp_path = os.path.join(model_dir, f".import_tmp_{uuid.uuid4().hex}.joblib")
        try:
            file_storage.save(tmp_path)
            try:
                bundle = _load_bundle(tmp_path)
            except BizException as exc:
                # 导入场景属于「用户上传了不合格文件」，归 1001 而非 3002
                raise BizException(CODE_PARAM_ERROR, exc.message, 400) from exc

            model_name = _infer_model_name(bundle["model"])
            target = os.path.join(model_dir, f"{model_name}.joblib")
            os.replace(tmp_path, target)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        return {"model_name": model_name, "path": target}
