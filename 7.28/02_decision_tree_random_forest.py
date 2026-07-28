# -*- coding: utf-8 -*-
"""
课程代码 02: 决策树与随机森林实战
说明: 直接运行即可,会生成 decision_tree.png 和 feature_importance.png
对应讲义章节: Day1 上午 - 决策树与随机森林
"""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 配置中文字体,保证图表中文正常显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 加载数据
iris = load_iris()
X = iris.data
y = iris.target
feature_names = iris.feature_names

# 划分数据集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# ============= 决策树 =============
print("="*50)
print("决策树分类器")
print("="*50)

# 训练决策树(限制深度防止过拟合)
dt_clf = DecisionTreeClassifier(max_depth=3, random_state=42)
dt_clf.fit(X_train, y_train)

# 预测
y_pred_dt = dt_clf.predict(X_test)
accuracy_dt = accuracy_score(y_test, y_pred_dt)
print(f"决策树准确率: {accuracy_dt:.2%}")

# 可视化决策树
plt.figure(figsize=(12, 8))
plot_tree(dt_clf, feature_names=feature_names,
          class_names=iris.target_names, filled=True)
plt.title('决策树可视化')
plt.savefig('decision_tree.png', dpi=100, bbox_inches='tight')
plt.close()
print("已保存决策树可视化: decision_tree.png\n")

# ============= 随机森林 =============
print("="*50)
print("随机森林分类器")
print("="*50)

# 训练随机森林
rf_clf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
rf_clf.fit(X_train, y_train)

# 预测
y_pred_rf = rf_clf.predict(X_test)
accuracy_rf = accuracy_score(y_test, y_pred_rf)
print(f"随机森林准确率: {accuracy_rf:.2%}")

# 特征重要性
importances = rf_clf.feature_importances_
indices = np.argsort(importances)[::-1]

plt.figure(figsize=(10, 6))
plt.title('特征重要性')
plt.bar(range(X.shape[1]), importances[indices])
plt.xticks(range(X.shape[1]), [feature_names[i] for i in indices])
plt.xlabel('特征')
plt.ylabel('重要性')
plt.savefig('feature_importance.png', dpi=100)
plt.close()
print("已保存特征重要性图: feature_importance.png")

# 对比两种模型
print(f"\n{'='*50}")
print("模型对比")
print(f"{'='*50}")
print(f"决策树准确率: {accuracy_dt:.2%}")
print(f"随机森林准确率: {accuracy_rf:.2%}")
print(f"提升: {(accuracy_rf - accuracy_dt)/accuracy_dt*100:.1f}%")
