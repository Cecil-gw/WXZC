# -*- coding: utf-8 -*-
"""
课程代码 03: XGBoost 与 LightGBM 对比实战
说明: 直接运行即可,会生成 xgboost_lightgbm_comparison.png
      需要安装: pip install xgboost lightgbm
对应讲义章节: Day1 上午 - 树模型的演进
"""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import time

# 配置中文字体,保证图表中文正常显示
# plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
# plt.rcParams["axes.unicode_minus"] = False
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

print("="*50)
print("XGBoost vs LightGBM 对比实战")
print("="*50)

# 生成较大数据集(模拟工业场景)
X, y = make_classification(
    n_samples=50000,
    n_features=20,
    n_informative=10,
    n_redundant=5,
    random_state=42
)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"\n训练集: {X_train.shape[0]} 样本, {X_train.shape[1]} 特征")
print(f"测试集: {X_test.shape[0]} 样本")

# ============= 1. XGBoost =============
print("\n" + "="*50)
print("1. XGBoost训练")
print("="*50)

try:
    import xgboost as xgb

    start_time = time.time()

    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,  # L1正则化
        reg_lambda=1.0,  # L2正则化
        random_state=42,
        eval_metric='logloss'
    )

    xgb_model.fit(X_train, y_train)
    xgb_time = time.time() - start_time

    xgb_pred = xgb_model.predict(X_test)
    xgb_accuracy = accuracy_score(y_test, xgb_pred)

    print(f"训练时间: {xgb_time:.2f}秒")
    print(f"准确率: {xgb_accuracy:.2%}")
    print(f"\n分类报告:\n{classification_report(y_test, xgb_pred)}")

    # 特征重要性
    xgb_importances = xgb_model.feature_importances_

    xgb_available = True
    print("✅ XGBoost可用")

except ImportError:
    print("❌ XGBoost未安装,请先运行: pip install xgboost")
    xgb_available = False
    xgb_time = 0
    xgb_accuracy = 0
    xgb_importances = np.zeros(20)

# ============= 2. LightGBM =============
print("\n" + "="*50)
print("2. LightGBM训练")
print("="*50)

try:
    import lightgbm as lgb

    start_time = time.time()

    lgb_model = lgb.LGBMClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        num_leaves=31,  # LightGBM特有参数
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42
    )

    lgb_model.fit(X_train, y_train)
    lgb_time = time.time() - start_time

    lgb_pred = lgb_model.predict(X_test)
    lgb_accuracy = accuracy_score(y_test, lgb_pred)

    print(f"训练时间: {lgb_time:.2f}秒")
    print(f"准确率: {lgb_accuracy:.2%}")
    print(f"\n分类报告:\n{classification_report(y_test, lgb_pred)}")

    lgb_importances = lgb_model.feature_importances_

    lgb_available = True
    print("✅ LightGBM可用")

except ImportError:
    print("❌ LightGBM未安装,请先运行: pip install lightgbm")
    lgb_available = False
    lgb_time = 0
    lgb_accuracy = 0
    lgb_importances = np.zeros(20)

# ============= 3. 对比分析 =============
if xgb_available and lgb_available:
    print("\n" + "="*50)
    print("对比总结")
    print("="*50)

    print(f"{'模型':<12} {'准确率':<10} {'训练时间(秒)':<15} {'速度比':<10}")
    print("-" * 50)
    print(f"{'XGBoost':<12} {xgb_accuracy:<10.2%} {xgb_time:<15.2f} {'基准':<10}")
    print(f"{'LightGBM':<12} {lgb_accuracy:<10.2%} {lgb_time:<15.2f} {xgb_time/lgb_time:.1f}x")

    # 可视化对比
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 训练时间对比
    axes[0].bar(['XGBoost', 'LightGBM'], [xgb_time, lgb_time],
                color=['#FF6B6B', '#4ECDC4'], width=0.5)
    axes[0].set_ylabel('训练时间(秒)')
    axes[0].set_title('训练速度对比')
    axes[0].grid(axis='y', alpha=0.3)

    # 准确率对比
    axes[1].bar(['XGBoost', 'LightGBM'], [xgb_accuracy, lgb_accuracy],
                color=['#FF6B6B', '#4ECDC4'], width=0.5)
    axes[1].set_ylabel('准确率')
    axes[1].set_title('准确率对比')
    axes[1].set_ylim([0.85, 1.0])
    axes[1].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig('xgboost_lightgbm_comparison.png', dpi=100)
    plt.close()
    print("\n已保存对比图: xgboost_lightgbm_comparison.png")
