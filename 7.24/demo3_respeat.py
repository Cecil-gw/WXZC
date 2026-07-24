import pandas as pd
import numpy as np
# df = pd.DataFrame({
#     "姓名": ["张三", "张三", "李四", "王五", "赵六",np.nan],
#     "籍贯": ["北京", "北京", "上海", "京", "北京", "深圳"],
#     "年龄": [25, 25, 150, -5, 28,25],
#     "薪资": [8000, 8000, 12000, "10k", 15000,10000]
# })

# # 按id、name两列去重，保留重复组最后一行
# df = df.drop_duplicates(subset=["姓名"], keep="last")
# print(df)

data = {
    "姓名": ["张三", "张三", "张三", "李四", "王五"],
    "城市": ["成都", "成都", "上海", "北京", "成都"],
    "薪资": [9000, 9000, 11000, 15000, 12000]
}
df = pd.DataFrame(data)
print("====原始数据====")
print(df)

print(df.duplicated())

repeat_data= df[df.duplicated()]
print("====重复数据====")
print(repeat_data)

print("\n====2.整行去重，保留第一条====")
df1 = df.drop_duplicates()
print(df1)

print("\n====3.整行去重，保留最后一条====")
df2 = df.drop_duplicates(keep="last")
print(df2)

print("\n====4.指定列去重，保留第一条====")
df3 = df.drop_duplicates(subset=["姓名"], keep="first")
print(df3)

df = pd.DataFrame({
    "姓名": ["张三", "张三", "李四", "王五", "赵六",np.nan],
    "籍贯": ["北京", "北京", "上海", "京", "北京", "深圳"],
    "年龄": [25, 25, 150, -5, 28,25],
    "薪资": [8000, 8000, 12000, "10k", 15000,10000]
})
print("====原始数据====")
print(df)

abnormal_age = df[(int(df["年龄"]) <= 0) | (int(df["年龄"]) >= 120)]
print("年龄异常数据：")
print(abnormal_age)

# 筛选薪资负数（你课堂任务用过！）
abnormal_salary = df[int(df["薪资"]) < 0]