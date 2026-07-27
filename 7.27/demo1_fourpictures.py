import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 解决中文、负号乱码
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ========== 第一步：读取数据并校验 ==========
# 用你提供的绝对路径读取文件
df = pd.read_csv(r"D:\wx26.7.14\data\data\StudentsPerformance.csv")

# 画布+2行3列子图基础框架
plt.figure(figsize=(10, 6))
ax1 = plt.subplot(2,3,1)
ax2 = plt.subplot(2,3,2)
ax3 = plt.subplot(2,3,3)
ax4 = plt.subplot(2,3,4)
ax5 = plt.subplot(2,3,5)
ax6 = plt.subplot(2,3,6)
ax6.axis("off") 

def plot(ax, x, y, title, xlabel, ylabel):
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.legend()

ax1.hist(df["math_score"],bins=12,alpha=0.5,edgecolor="black",label="math score", color="red")
ax1.hist(df["reading_score"], bins=12, alpha=0.4, edgecolor="black", label="阅读")
ax1.hist(df["writing_score"], bins=12, alpha=0.4, edgecolor="black", label="写作")
ax1.set_title("三科考试分数分布直方图")
ax1.set_xlabel("分数")
ax1.set_ylabel("学生人数")
ax1.grid(True, alpha=0.3)
ax1.legend()



# 2行3列：行索引是none/completed，列是math_score/reading_score/writing_score
prep_group = df.groupby("test_preparation_course")[["math_score", "reading_score", "writing_score"]].mean()
# 未参加辅导的三科平均分
none_scores = prep_group.loc["none"]
# 完成辅导的三科平均分
completed_scores = prep_group.loc["completed"]

# 2. 准备x轴基准位置 + 柱子宽度
x = np.arange(3)       # 3个科目 → 3个基准位置 [0,1,2]
width = 0.35           # 单根柱子宽度，两根并排总宽0.7，科目之间留空隙
# 左柱：未辅导，向左挪半个宽度
ax2.bar(x - width/2, none_scores, width=width, label="未参加辅导", color="steelblue")
# 右柱：已辅导，向右挪半个宽度
ax2.bar(x + width/2, completed_scores, width=width, label="完成辅导", color="indianred")


ax2.set_xticks(x)
ax2.set_xticklabels(["数学", "阅读", "写作"])

ax2.set_title("有无考前辅导各科平均分对比")
ax2.set_xlabel("科目")
ax2.set_ylabel("平均分")
ax2.set_ylim(0, 100)
ax2.grid(axis="y", alpha=0.3)
ax2.legend()

# 柱子顶部标分数
for bar in ax2.patches:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, h, f"{h:.1f}", ha="center", va="bottom")


# 2. 绘制饼图
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


plt.show()