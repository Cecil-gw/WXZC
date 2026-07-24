import pandas as pd
import numpy as np

# ==================== 原始基础数据 ====================
df_origin = pd.DataFrame({
    "姓名": ["张三", "张三", "李四", "王五", "赵六",np.nan],
    "籍贯": ["北京", "北京", "上海", "京", "北京", "深圳"],
    "年龄": [25, 25, 150, -5, 28,25],
    "薪资": [8000, 8000, 12000, "10k", 15000,10000]
})
print("="*50)
print("【0.原始数据】")
print(df_origin)

# 统一薪资清洗逻辑（所有副本都需要）
def clean_salary(temp_df):
    temp_df["薪资"] = temp_df["薪资"].str.replace("k","000")
    temp_df["薪资"] = pd.to_numeric(temp_df["薪资"], errors="coerce")
    return temp_df

# ==================== 1. 查找异常数据 ====================
df1 = df_origin.copy()
df1 = clean_salary(df1)
abnormal_age = df1[(df1["年龄"] <= 0) | (df1["年龄"] >= 120)]
print("="*50)
print("【1.筛选年龄异常数据】")
print(abnormal_age)

abnormal_salary = df1[df1["薪资"] < 0]
print("\n【1.筛选薪资负数异常】")
print(abnormal_salary)

# ==================== 方案1：直接删除异常行 ====================
df_plan1 = df_origin.copy()
df_plan1 = df_plan1[(df_plan1["年龄"] > 0) & (df_plan1["年龄"] < 120)]
print("="*50)
print("【方案1：删除年龄异常行】")
print(df_plan1)

# ==================== 方案2：异常改为NaN + 均值填充 ====================
df_plan2 = df_origin.copy()
df_plan2.loc[(df_plan2["年龄"] <=0)|(df_plan2["年龄"]>=120), "年龄"] = np.nan
df_plan2["年龄"] = df_plan2["年龄"].fillna(df_plan2["年龄"].mean())
print("="*50)
print("【方案2：异常值均值填充】")
print(df_plan2)

# ==================== 方案3：异常统一替换固定值30 ====================
df_plan3 = df_origin.copy()
df_plan3.loc[(df_plan3["年龄"] <=0)|(df_plan3["年龄"]>=120), "年龄"] = 30
print("="*50)
print("【方案3：异常替换为固定值30】")
print(df_plan3)

# ==================== 方案4：新增标签标记异常，原始数据不变 ====================
df_plan4 = df_origin.copy()
df_plan4["年龄是否异常"] = ((df_plan4["年龄"] <= 0) | (df_plan4["年龄"] >= 120))
print("="*50)
print("【方案4：新增列标记异常】")
print(df_plan4)
print("="*50)