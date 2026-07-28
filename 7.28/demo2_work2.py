import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

np.random.seed(42)
n_samples = 1000

# 数值特征
age = np.random.randint(18, 70, n_samples)
money = np.random.exponential(200, n_samples).astype(int)  # 平均200
use_month = np.random.randint(1, 60, n_samples)
fuck_numbers = np.random.poisson(0.5, n_samples)

# 类别特征
sex = np.random.choice(['男', '女'], n_samples, p=[0.55, 0.45])

# 构造流失标签（基于特征的非线性组合 + 随机噪声）
score = (
    (age > 50).astype(int) * 1.5 +
    (money < 100).astype(int) * 2.0 +
    (use_month < 12).astype(int) * 1.8 +
    (fuck_numbers > 1).astype(int) * 2.5
)
prob = 1 / (1 + np.exp(-(score - 2.5)))  # 逻辑函数转为概率
if_over = np.random.binomial(1, prob)

data = pd.DataFrame({
    'age': age,
    'money': money,
    'use_month': use_month,
    'fuck_numbers': fuck_numbers,
    'sex': sex,
    'if_over': if_over
})
print(data.head())
print("\n流失分布:\n", data['if_over'].value_counts())


from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# 特征与标签
X = data.drop('if_over', axis=1)
y = data['if_over']

# 区分列类型
numeric_features = ['age', 'money', 'use_month', 'fuck_numbers']
categorical_features = ['sex']

# 预处理流水线
numeric_transformer = StandardScaler()
categorical_transformer = OneHotEncoder(drop='first')  # 避免虚拟变量陷阱

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

# 数据集划分（分层抽样保持类别比例）
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_curve, auc, ConfusionMatrixDisplay)

models = {
    '逻辑回归': LogisticRegression(max_iter=1000, random_state=42),
    '支持向量机': SVC(probability=True, random_state=42),  # probability=True 用于绘制ROC曲线
    '随机森林': RandomForestClassifier(n_estimators=100, random_state=42)
}

# 存储结果
results = {}
roc_data = {}

plt.figure(figsize=(8, 6))

for name, model in models.items():
    # 创建管道：预处理 + 分类器
    pipe = Pipeline(steps=[('preprocessor', preprocessor),
                           ('classifier', model)])
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)[:, 1]  # 正类概率

    # 评估指标
    report = classification_report(y_test, y_pred, target_names=['未流失', '流失'])
    cm = confusion_matrix(y_test, y_pred)

    # 混淆矩阵可视化（单独显示，这里只存储矩阵文本）
    print(f"========== {name} ==========")
    print(report)
    print("混淆矩阵:\n", cm)

    # ROC曲线数据
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    roc_data[name] = (fpr, tpr, roc_auc)
    results[name] = {'report': report, 'confusion_matrix': cm, 'auc': roc_auc}

    # 绘制ROC曲线
    plt.plot(fpr, tpr, lw=2, label=f'{name} (AUC = {roc_auc:.3f})')

# 绘制对角线
plt.plot([0, 1], [0, 1], color='gray', linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve')
plt.legend(loc="lower right")
plt.show()