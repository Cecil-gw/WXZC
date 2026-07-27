import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ===================== 全局配置：中文、负号乱码修复 =====================
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ===================== 1. 读取数据（使用你提供的完整路径） =====================
df = pd.read_csv(R"D:\wx26.7.14\data\data\StudentsPerformance.csv")
print("数据集所有列名：", df.columns.tolist())

# 自定义家长学历从低到高顺序
edu_sort = [
    "some high school",
    "high school",
    "some college",
    "associate's degree",
    "bachelor's degree",
    "master's degree"
]

# ===================== 2. 创建画布与2行3列子图 =====================
plt.figure(figsize=(16, 10))
ax1 = plt.subplot(2, 3, 1)  # 直方图
ax2 = plt.subplot(2, 3, 2)  # 分组柱状图
ax3 = plt.subplot(2, 3, 3)  # 散点图+拟合线
ax4 = plt.subplot(2, 3, 4)  # 饼图
ax5 = plt.subplot(2, 3, 5)  # 多折线图
ax6 = plt.subplot(2, 3, 6)  # 空白子图
ax6.axis("off")

# ===================== 子图1：三科成绩叠加直方图 =====================
ax1.hist(df["math_score"], bins=12, alpha=0.4, edgecolor="black", label="数学")
ax1.hist(df["reading_score"], bins=12, alpha=0.4, edgecolor="black", label="阅读")
ax1.hist(df["writing_score"], bins=12, alpha=0.4, edgecolor="black", label="写作")
ax1.set_title("三科考试分数分布直方图")
ax1.set_xlabel("分数")
ax1.set_ylabel("学生人数")
ax1.grid(True, alpha=0.3)
ax1.legend()

# ===================== 子图2：考前辅导分组并列柱状图 =====================
prep_group = df.groupby("test_preparation_course")[["math_score", "reading_score", "writing_score"]].mean()
# 未参加辅导的三科平均分
none_scores = prep_group.loc["none"]
# 完成辅导的三科平均分
completed_scores = prep_group.loc["completed"]
x = np.arange(3)
width = 0.35  
ax2.bar(x - width/2, none_scores, width=width, label="未参加辅导", color="steelblue")
ax2.bar(x + width/2, completed_scores, width=width, label="完成辅导", color="indianred")

ax2.set_xticks(x)
ax2.set_xticklabels(["数学", "阅读", "写作"])
ax2.set_ylim(0, 100)
ax2.set_title("有无考前辅导各科平均分对比")
ax2.set_xlabel("考前辅导状态")
ax2.set_ylabel("平均分数")
ax2.grid(axis="y", alpha=0.3)
ax2.legend()

# 柱子顶部标注数值
# 柱子顶部标注具体分数
for bar in ax2.patches:
    h = bar.get_height()
    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        h,
        f"{h:.1f}",
        ha="center",
        va="bottom"
    )
# ===================== 子图3：读写散点图+区分性别+拟合线 =====================
male_data = df[df["gender"] == "male"]
female_data = df[df["gender"] == "female"]

# 男女散点
ax3.scatter(male_data["reading_score"], male_data["writing_score"], c="blue", alpha=0.5, label="男生")
ax3.scatter(female_data["reading_score"], female_data["writing_score"], c="red", alpha=0.5, label="女生")

# 全局拟合直线
all_x = df["reading_score"]
all_y = df["writing_score"]
z = np.polyfit(all_x, all_y, 1)
p_func = np.poly1d(z)
ax3.plot(all_x, p_func(all_x), c="black", linewidth=2, label="趋势拟合线")

# pandas计算相关系数，无需scipy
r = df[["reading_score", "writing_score"]].corr().iloc[0, 1]
ax3.text(22, 92, f"皮尔逊相关系数 r = {r:.3f}", fontsize=11)

ax3.set_title("阅读与写作分数相关性（区分性别）")
ax3.set_xlabel("阅读分数")
ax3.set_ylabel("写作分数")
ax3.grid(True, alpha=0.3)
ax3.legend()

# ===================== 子图4：午餐类型占比饼图 =====================
lunch_count = df["lunch"].value_counts()
labels = lunch_count.index
nums = lunch_count.values

# 数量最多类别突出
explode = [0, 0]
max_pos = np.argmax(nums)
explode[max_pos] = 0.1

ax4.pie(
    nums,
    explode=explode,
    labels=labels,
    autopct="%.2f%%",
    shadow=True,
    colors=["#55aaff", "#ff8888"],
    startangle=90
)
ax4.set_title("学生午餐类型样本占比")
ax4.legend()

# ===================== 子图5：家长学历-三科平均分折线图 =====================
edu_mean = df.groupby("parental_level_of_education")[["math_score", "reading_score", "writing_score"]].mean()
edu_mean = edu_mean.reindex(edu_sort)  # 强制学历升序

ax5.plot(edu_mean.index, edu_mean["math_score"], marker="o", color="#1f77b4", label="数学")
ax5.plot(edu_mean.index, edu_mean["reading_score"], marker="s", color="#ff7f0e", label="阅读")
ax5.plot(edu_mean.index, edu_mean["writing_score"], marker="^", color="#2ca02c", label="写作")

ax5.tick_params(axis="x", rotation=45)
ax5.set_title("家长学历与学生三科平均分趋势")
ax5.set_xlabel("家长学历水平")
ax5.set_ylabel("平均分数")
ax5.grid(True, alpha=0.3)
ax5.legend()

# ===================== 全局排版与保存高清图 =====================
plt.tight_layout()
plt.savefig("学生成绩综合可视化大图.png", dpi=300)
plt.show()