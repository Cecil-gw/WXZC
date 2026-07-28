# 导入必要的库
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# 设置中文显示（如果系统支持）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def train_target(df):
    # 1. 分离特征和目标
    X = df.drop("median_house_value", axis=1)
    y = df["median_house_value"]
    
    # 2. 独热编码
    X_encoded = pd.get_dummies(X, columns=['ocean_proximity'], drop_first=True)
    
    # 3. 特征选择（删除 total_bedrooms，如果决定这样做）
    X_selected = X_encoded.drop('total_bedrooms', axis=1)
    
    # 4. 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X_selected, y, test_size=0.2, random_state=42
    )
    
    # 5. 标准化
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 6. 返回处理好的数据（可以打包成字典或直接返回多个值）
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, X_selected.columns


def train(X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_names):
  lr = LinearRegression()
  lr.fit(X_train_scaled, y_train)
  y_train_pred_lr = lr.predict(X_train_scaled)
  y_test_pred_lr = lr.predict(X_test_scaled)

  # 决策树
  dt = DecisionTreeRegressor(max_depth=10, random_state=42)
  dt.fit(X_train_scaled, y_train)
  y_train_pred_dt = dt.predict(X_train_scaled)
  y_test_pred_dt = dt.predict(X_test_scaled)

  # 随机森林
  rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
  rf.fit(X_train_scaled, y_train)
  y_train_pred_rf = rf.predict(X_train_scaled)
  y_test_pred_rf = rf.predict(X_test_scaled)

  return lr, dt, rf, y_train, y_test, y_train_pred_lr, y_test_pred_lr, y_train_pred_dt, y_test_pred_dt, y_train_pred_rf, y_test_pred_rf

if __name__ == '__main__':
    housing = pd.read_csv(r'D:\wx26.7.14\7.28\data\california_housing.csv')
    
    print("数据形状:", housing.shape)
    print(housing.info())
    print(housing["median_house_value"].describe())
    
    # ---------- 任务1：探索性分析 ----------
    plt.figure(figsize=(8,4))
    plt.hist(housing["median_house_value"], bins=50, edgecolor='k', alpha=0.7)
    plt.title('房价中位数分布 (median_house_value)')
    plt.xlabel('房价中位数（美元）')
    plt.ylabel('街区数量')
    plt.show()
    numeric_cols = housing.select_dtypes(include=[np.number]).columns.tolist()
    corr_data = housing[numeric_cols].copy()
    corr_matrix = corr_data.corr()
    plt.figure(figsize=(10,6))
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm')
    plt.title('数值特征相关性热图（含目标）')
    plt.show()

    # 1.3 文本特征 ocean_proximity 与房价的箱线图
    plt.figure(figsize=(8,5))
    sns.boxplot(x='ocean_proximity', y='median_house_value', data=housing)
    plt.xticks(rotation=45)
    plt.title('离海距离类别 vs 房价中位数')
    plt.show()

    # ---------- 任务2：特征工程 + 划分 + 标准化 ----------
    X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_names = train_target(housing)
    print("训练集形状:", X_train_scaled.shape)
    print("特征名称:", feature_names.tolist())

    # ---------- 任务3：训练三个模型 ----------
    (lr, dt, rf, 
     y_train, y_test, 
     y_train_pred_lr, y_test_pred_lr, 
     y_train_pred_dt, y_test_pred_dt, 
     y_train_pred_rf, y_test_pred_rf) = train(X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_names)

    # ---------- 任务4：性能比较（MSE 和 R²） ----------
    results = pd.DataFrame({
        '模型': ['线性回归', '决策树', '随机森林'],
        '训练MSE': [
            mean_squared_error(y_train, y_train_pred_lr),
            mean_squared_error(y_train, y_train_pred_dt),
            mean_squared_error(y_train, y_train_pred_rf)
        ],
        '测试MSE': [
            mean_squared_error(y_test, y_test_pred_lr),
            mean_squared_error(y_test, y_test_pred_dt),
            mean_squared_error(y_test, y_test_pred_rf)
        ],
        '训练R²': [
            r2_score(y_train, y_train_pred_lr),
            r2_score(y_train, y_train_pred_dt),
            r2_score(y_train, y_train_pred_rf)
        ],
        '测试R²': [
            r2_score(y_test, y_test_pred_lr),
            r2_score(y_test, y_test_pred_dt),
            r2_score(y_test, y_test_pred_rf)
        ]
    })
    print("\n===== 模型性能对比 =====")
    print(results.to_string(index=False))

    # 可视化对比（测试集 R² 柱状图）
    plt.figure(figsize=(8,4))
    plt.bar(results['模型'], results['测试R²'], color=['skyblue', 'lightgreen', 'salmon'])
    plt.title('三种模型测试集 R² 对比')
    plt.ylabel('R²')
    for i, v in enumerate(results['测试R²']):
        plt.text(i, v + 0.01, f'{v:.3f}', ha='center', fontsize=11)
    plt.show()

    # ---------- 任务5：特征重要性排序 ----------
    # 使用随机森林的特征重要性
    rf_importances = rf.feature_importances_
    # 线性回归的系数绝对值（标准化后可比）
    lr_importances = np.abs(lr.coef_)
    # 决策树特征重要性
    dt_importances = dt.feature_importances_

    importance_df = pd.DataFrame({
        '特征': feature_names,
        '线性回归系数': lr_importances,
        '决策树重要性': dt_importances,
        '随机森林重要性': rf_importances
    }).sort_values('随机森林重要性', ascending=False)

    print("\n===== 特征重要性排序（按随机森林） =====")
    print(importance_df[['特征', '随机森林重要性']].to_string(index=False))

    # 画随机森林特征重要性水平条形图
    plt.figure(figsize=(10,6))
    plt.barh(importance_df['特征'][::-1], importance_df['随机森林重要性'][::-1], color='coral')
    plt.title('随机森林特征重要性')
    plt.xlabel('Importance')
    plt.tight_layout()
    plt.show()