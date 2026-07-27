import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ---------------------- 1. 构造模拟数据 ----------------------
np.random.seed(42)
normal_data = np.random.normal(loc=40, scale=10, size=80)
# 手动添加异常值
outliers = np.array([92, 95, 12, 8])
data = np.concatenate([normal_data, outliers])
df = pd.DataFrame({"value": data})

# ---------------------- 2. 手动计算IQR边界 ----------------------
col = "value"
Q1 = df[col].quantile(0.25)
Q3 = df[col].quantile(0.75)
IQR = Q3 - Q1
scale = 1.5
lower = Q1 - scale * IQR
upper = Q3 + scale * IQR

# 生成异常掩码
outlier_mask = (df[col] < lower) | (df[col] > upper)
df["is_outlier"] = outlier_mask

# ---------------------- 3. 构造两种清洗后数据 ----------------------
# clip 缩尾截断
df_clip = df.copy()
df_clip[col] = df_clip[col].clip(lower, upper)

# drop 删除异常行
df_drop = df[~outlier_mask].copy()

# ---------------------- 4. 绘图展示 ----------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 子图1：原始数据箱线图，标出异常点
ax1 = axes[0, 0]
box = ax1.boxplot(df["value"], patch_artist=True)
for patch in box["boxes"]:
    patch.set_facecolor("#87CEFA")
ax1.axhline(y=upper, color="r", linestyle="--", label=f"上限={upper:.2f}")
ax1.axhline(y=lower, color="g", linestyle="--", label=f"下限={lower:.2f}")
ax1.set_title("原始数据｜箱线图（圆点=异常值）")
ax1.legend()

# 子图2：原始数据散点，区分正常/异常
ax2 = axes[0, 1]
idx_normal = ~outlier_mask
idx_outlier = outlier_mask
ax2.scatter(df.index[idx_normal], df.loc[idx_normal, "value"], c="#2E8B57", s=30, label="正常数据")
ax2.scatter(df.index[idx_outlier], df.loc[idx_outlier, "value"], c="#DC143C", s=60, marker="*", label="异常值")
ax2.axhline(y=upper, color="r", ls="--")
ax2.axhline(y=lower, color="g", ls="--")
ax2.set_title("原始数据｜布尔掩码标记异常点")
ax2.set_xlabel("样本序号")
ax2.legend()

# 子图3：clip缩尾截断后
ax3 = axes[1, 0]
ax3.scatter(df_clip.index, df_clip["value"], c="#4682B4", s=30)
ax3.axhline(y=upper, color="r", ls="--")
ax3.axhline(y=lower, color="g", ls="--")
ax3.set_title("clip模式：异常值强制拉到边界（行数不变）")

# 子图4：drop删除异常行后
ax4 = axes[1, 1]
ax4.scatter(df_drop.index, df_drop["value"], c="#32CD32", s=30)
ax4.axhline(y=upper, color="r", ls="--")
ax4.axhline(y=lower, color="g", ls="--")
ax4.set_title("drop模式：直接移除所有异常样本（行数变少）")

plt.tight_layout()
plt.show()

# 打印信息对照
print(f"IQR边界：lower={lower:.2f}, upper={upper:.2f}")
print(f"原始样本数量：{len(df)}")
print(f"异常样本数量：{outlier_mask.sum()}")
print(f"clip清洗后样本数：{len(df_clip)}（不变）")
print(f"drop清洗后样本数：{len(df_drop)}（减少异常行）")