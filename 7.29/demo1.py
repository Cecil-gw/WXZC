import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler
import time
import xgboost as xgb

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


MODEL_DIR= r"D:\wx26.7.14\7.29\model"
SAVE_DIR = r"D:\wx26.7.14\7.29\data"
CLEANED_FILE = os.path.join(SAVE_DIR, "data_cleaned.csv")
PHOTO_DIR =r"D:\wx26.7.14\7.29\photo"


def print_step(msg):
    """打印步骤提示，带时间戳"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def data_clean(df):
    # 先判断清洗后文件是否存在
    if os.path.exists(CLEANED_FILE):
        print_step(f"检测到已存在清洗文件 {CLEANED_FILE}，直接读取，跳过清洗")
        df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
        return df

    df = df.copy()

    # ========== 1. 删除无用列 ==========
    print_step("开始清洗: 删除id列...")
    df.drop('id', axis=1, inplace=True)
    print_step("✓ 删除id列完成")

    # ========== 2. 文本列数值化 ==========
    print_step("文本列数值化: Gender...")
    df['Gender'] = df['Gender'].map({'Male': 1, 'Female': 0})

    print_step("文本列数值化: Vehicle_Damage...")
    df['Vehicle_Damage'] = df['Vehicle_Damage'].map({'Yes': 1, 'No': 0})

    print_step("文本列数值化: Vehicle_Age...")
    df['Vehicle_Age'] = df['Vehicle_Age'].map({'< 1 Year': 0, '1-2 Year': 1, '> 2 Years': 2})
    print_step("✓ 文本列数值化完成")

    # ========== 3. 异常值检查 ==========
    print_step("检查Age分布...")
    print(df['Age'].describe())

    print_step("检查Annual_Premium分布...")
    print(df['Annual_Premium'].describe())
    print("分位数:", df['Annual_Premium'].quantile([0.90, 0.95, 0.97, 0.99]).values)

    print_step("检查Vintage分布...")
    print(df['Vintage'].describe())

    # ========== 4. 保费盖帽处理 ==========
    print_step("保费盖帽处理...")
    premium_cap = df['Annual_Premium'].quantile(0.99)
    print(f"  → 盖帽阈值(99%): {premium_cap:.0f}")
    df['Annual_Premium'] = df['Annual_Premium'].clip(upper=premium_cap)
    print_step(f"✓ 盖帽完成, 最大值: {df['Annual_Premium'].max():.0f}")

    # ========== 5. 唯一值检查 ==========
    print_step("检查类别变量...")
    print(f"  Region_Code 唯一值: {df['Region_Code'].nunique()}")
    print(f"  Policy_Sales_Channel 唯一值: {df['Policy_Sales_Channel'].nunique()}")

    # ========== 6. 合并低频渠道 ==========
    print_step("合并低频渠道...")
    channel_counts = df['Policy_Sales_Channel'].value_counts()
    threshold = 0.005 * df.shape[0]
    low_channels = channel_counts[channel_counts < threshold].index
    print(f"  → 低频渠道数: {len(low_channels)}")
    df['Policy_Sales_Channel'] = df['Policy_Sales_Channel'].replace(low_channels, 999)
    print_step(f"✓ 合并完成, 唯一值: {df['Policy_Sales_Channel'].nunique()}")

    # ========== 7. 保存数据 ==========
    print_step("保存清洗后数据...")
    os.makedirs(SAVE_DIR, exist_ok=True)
    df.to_csv(CLEANED_FILE, index=False, encoding="utf-8-sig")
    print_step("✓ 数据已保存为 data_cleaned.csv")

    return df


def visualization(df):
    # 确保图片保存目录存在
    os.makedirs(PHOTO_DIR, exist_ok=True)
    
    # ===== 图1：Response 分布 =====
    print(df['Response'].value_counts())
    print(df['Response'].value_counts(normalize=True))
    
    plt.figure(figsize=(6, 4))
    sns.countplot(x='Response', data=df, palette=['#ff9999', '#66b3ff'])
    plt.title('Response 分布（0=未购买，1=购买）')
    plt.xlabel('是否购买车险')
    plt.ylabel('数量')
    plt.savefig(os.path.join(PHOTO_DIR, '1_Response分布.png'), dpi=300, bbox_inches='tight')
    plt.show()
    
    # ===== 图2：数值特征箱线图 =====
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    sns.boxplot(x='Response', y='Age', data=df, ax=axes[0], palette=['#ff9999', '#66b3ff'])
    axes[0].set_title('年龄 vs 是否购买')
    axes[0].set_xticklabels(['未购买', '购买'])
    
    sns.boxplot(x='Response', y='Annual_Premium', data=df, ax=axes[1], palette=['#ff9999', '#66b3ff'])
    axes[1].set_title('每年保费 vs 是否购买')
    axes[1].set_xticklabels(['未购买', '购买'])
    
    sns.boxplot(x='Response', y='Vintage', data=df, ax=axes[2], palette=['#ff9999', '#66b3ff'])
    axes[2].set_title('参保天数 vs 是否购买')
    axes[2].set_xticklabels(['未购买', '购买'])
    
    plt.tight_layout()
    plt.savefig(os.path.join(PHOTO_DIR, '2_数值特征箱线图.png'), dpi=300, bbox_inches='tight')
    plt.show()
    
    # ===== 图3：分类特征堆叠柱状图 =====
    categorical_features = ['Gender', 'Driving_License', 'Previously_Insured', 'Vehicle_Damage', 'Vehicle_Age']
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    for i, feature in enumerate(categorical_features):
        ct = pd.crosstab(df[feature], df['Response'], normalize='index')
        ct.plot(kind='bar', stacked=True, ax=axes[i],
                color=['#ff9999', '#66b3ff'], edgecolor='black')
        axes[i].set_title(f'{feature} vs Response')
        axes[i].set_xlabel(feature)
        axes[i].set_ylabel('比例')
        axes[i].legend(['未购买', '购买'])
        axes[i].set_xticklabels(axes[i].get_xticklabels(), rotation=0)
    
    fig.delaxes(axes[5])
    plt.tight_layout()
    plt.savefig(os.path.join(PHOTO_DIR, '3_分类特征堆叠图.png'), dpi=300, bbox_inches='tight')
    plt.show()
    
    print_step(f"✅ 所有图片已保存到 {PHOTO_DIR}")


def feature_engineering(df):
    preprocessed_file = os.path.join(SAVE_DIR, "data_preprocessed.csv")
    if os.path.exists(preprocessed_file):
        print_step(f"检测到已存在预处理文件 {preprocessed_file}，直接读取，跳过特征工程")
        df = pd.read_csv(preprocessed_file, encoding="utf-8-sig")
        X = df.drop('Response', axis=1)
        y = df['Response']
        return X, y, None

    X = df.drop('Response', axis=1)
    y = df['Response']

    print(f"原始特征数: {X.shape[1]}")

    # ========== 2. 数值特征标准化 ==========
    scaler = StandardScaler()
    num_cols = ['Age', 'Annual_Premium', 'Vintage']
    X_num = scaler.fit_transform(X[num_cols])
    X_num = pd.DataFrame(X_num, columns=num_cols)
    print(f"标准化后数值特征: {X_num.shape}")

    # ========== 3. 二值列 ==========
    binary_cols = ['Gender', 'Driving_License', 'Previously_Insured', 'Vehicle_Damage']
    X_binary = X[binary_cols].copy()
    print(f"二值特征: {X_binary.shape}")

    # ========== 4. 有序分类 ==========
    X_vehicle_age = X[['Vehicle_Age']].copy()
    print(f"有序分类特征: {X_vehicle_age.shape}")

    # ========== 5. 无顺序分类 -> One‑Hot 编码 ==========
    multi_cols = ['Region_Code', 'Policy_Sales_Channel']
    X_onehot = pd.get_dummies(X[multi_cols], drop_first=True)
    print(f"One‑Hot 后特征数: {X_onehot.shape[1]}")

    # ========== 6. 合并所有特征 ==========
    X_final = pd.concat([
        X_num,
        X_binary,
        X_vehicle_age,
        X_onehot
    ], axis=1)

    print(f"最终特征数: {X_final.shape[1]}")

    # ========== 7. 保存处理后的数据 ==========
    df_final = pd.concat([X_final, y.reset_index(drop=True)], axis=1)
    os.makedirs(SAVE_DIR, exist_ok=True)
    df_final.to_csv(preprocessed_file, index=False, encoding="utf-8-sig")
    print("特征工程完成，已保存为 data_preprocessed.csv")

    return X_final, y, scaler


def train_model(X, y):
    model_path = os.path.join(MODEL_DIR, "xgboost_model.json")
    # 无论是否加载缓存，每次都划分数据集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"训练集大小: {X_train.shape[0]}, 测试集大小: {X_test.shape[0]}")

    if os.path.exists(model_path):
        print_step(f"检测到已训练模型 {model_path}，直接加载，跳过训练")
        model = xgb.XGBClassifier()
        model.load_model(model_path)
    else:
        print_step("开始训练XGBoost模型...")
        # ========== 处理样本不平衡 ==========
        neg_count = len(y_train[y_train == 0])
        pos_count = len(y_train[y_train == 1])
        scale_pos_weight = neg_count / pos_count
        print(f"正负样本比例: {pos_count}:{neg_count}，scale_pos_weight = {scale_pos_weight:.2f}")

        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        model.fit(X_train, y_train)
        os.makedirs(MODEL_DIR, exist_ok=True)
        model.save_model(model_path)
        print(f"✓ 模型已保存到 {model_path}")

    # 加载缓存模型 OR 新训练模型，都会走到这里做评估
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n===== 模型评估 =====")
    print(f"准确率: {accuracy_score(y_test, y_pred):.4f}")
    print(f"AUC: {roc_auc_score(y_test, y_prob):.4f}")
    print("\n分类报告:")
    print(classification_report(y_test, y_pred, target_names=['未购买', '购买']))

    # ========== 5. 特征重要性 ==========
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    print("\n===== Top 10 重要特征 =====")
    print(feature_importance.head(10))

    return model, X_test, y_test, y_prob


def predict_high_value(model, X, y=None, top_n=1000, output_path=None):
    """
    预测高潜用户（购买概率最高的用户）
    """
    if output_path is None:
        output_path = os.path.join(SAVE_DIR, "high_value_customers.csv")

    prob = model.predict_proba(X)[:, 1]

    results = X.copy()
    results['Response_Prob'] = prob

    if y is not None:
        results['True_Response'] = y.values

    results = results.sort_values('Response_Prob', ascending=False).head(top_n)
    results.insert(0, 'rank', range(1, top_n + 1))

    results.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✅ 高潜用户名单已保存到 {output_path}")
    print(f"共 {len(results)} 条，购买概率范围: {results['Response_Prob'].min():.2%} ~ {results['Response_Prob'].max():.2%}")
    return results


if __name__ == '__main__':
    # 读取原始数据
    print_step("读取原始数据...")
    data = pd.read_excel(r'D:\wx26.7.14\7.29\data\data.xlsx')
    print_step("✓ 读取完成")

    df_clean = data_clean(data)

    print_step("最终数据预览:")
    print(df_clean.head())
    print(f"\nResponse分布:\n{df_clean['Response'].value_counts()}")
    print_step("===== 清洗流程全部完成 =====")

    visualization(df_clean)

    X, y, scaler = feature_engineering(df_clean)
    print_step("开始训练模型...")
    model, X_test, y_test, y_prob = train_model(X, y)
    print_step("✓ 模型训练/加载完成")

    print_step("预测高潜用户...")
    high_value = predict_high_value(
        model=model,
        X=X,
        y=y,
        top_n=1000
    )
    print_step("✓ 高潜用户预测完成")