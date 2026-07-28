import numpy as np
import seaborn as sns
import pandas as pd
import os
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]   # Windows黑体
plt.rcParams["axes.unicode_minus"] = False     # 解决负号显示异常

    
def demo1(df, out_dir):
  plt.figure(figsize=(8, 5))

  sns.histplot(data=df,x="tip",bins=30,kde=True)

  plt.title("小费金额tip分布直方图（含核密度曲线）")
  plt.xlabel("小费 tip")
  plt.ylabel("数量")

  save_path = os.path.join(out_dir, "ex1_tip_hist_kde.png")
  plt.savefig(save_path, dpi=300, bbox_inches="tight")
  plt.show()
  plt.close()
  print(f"习题1图片已保存：{save_path}")

def demo2(df, out_dir):
  plt.figure(figsize=(8,5))
  sns.kdeplot(
      data=df,
      x="total_bill",
      hue="smoker",
      fill=True   # 曲线下方填充颜色，可选
  )
  save_path = os.path.join(out_dir, "ex2_tip_hist_kde.png")
  plt.savefig(save_path, dpi=300, bbox_inches="tight")
  plt.title("总账单密度，按吸烟分组")
  plt.xlabel("总账单")
  plt.ylabel("密度")
  plt.show()

def demo3(df, out_dir):
  plt.figure(figsize=(8,5))
  sns.boxplot(data=df, x="time", y="tip", hue="sex")
  save_path = os.path.join(out_dir, "ex3_tip_hist_kde.png")
  plt.savefig(save_path, dpi=300, bbox_inches="tight")
  plt.title("小费金额tip分布直方图（含核密度曲线）")
  plt.xlabel("小费 tip")
  plt.ylabel("数量")
  plt.show()

def demo4(df, out_dir):
    plt.figure(figsize=(9,5))
    sns.violinplot(data=df, x="day", y="tip", hue="time", split=True)

    plt.title("各星期小费小提琴图（按时段分割对比）")
    plt.xlabel("星期 day")
    plt.ylabel("小费 tip")

    save_path = os.path.join(out_dir, "ex4_day_tip_violin.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()
    print(f"习题4图片已保存：{save_path}")  

def demo5(df, out_dir):
    plt.figure(figsize=(9,5))
    sns.barplot(data=df, x="day", y="tip", errorbar=None)

    plt.title("各星期平均小费柱状图（无误差线）")
    plt.xlabel("星期 day")
    plt.ylabel("小费 tip")

    save_path = os.path.join(out_dir, "ex5_day_tip_bar.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()
    print(f"习题5图片已保存：{save_path}")

def demo6(df, out_dir):
    plt.figure(figsize=(6,5))
    corr = df[["total_bill", "tip", "size"]].corr()
    sns.heatmap(corr, annot=True, cmap="coolwarm")

    plt.title("数值变量相关系数热力图")

    save_path = os.path.join(out_dir, "ex6_corr_heatmap.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()
    print(f"习题6图片已保存：{save_path}")

def demo7(df, out_dir):
    g = sns.lmplot(data=df, x="total_bill", y="tip", hue="smoker", height=5)
    g.fig.suptitle("账单与小费回归图（按吸烟分组）", y=1.02)

    save_path = os.path.join(out_dir, "ex7_reg_smoker.png")
    g.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()
    print(f"习题7图片已保存：{save_path}")

def demo8(iris_df, out_dir):
    sub_df = iris_df[["sepal_length", "sepal_width", "petal_length", "species"]]
    g = sns.pairplot(data=sub_df, hue="species")
    g.fig.suptitle("鸢尾花配对散点矩阵", y=1.02)

    save_path = os.path.join(out_dir, "ex8_iris_pairplot.png")
    g.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()
    print(f"习题8图片已保存：{save_path}")


def demo9(df, out_dir):
    plt.figure(figsize=(8, 10))
    # 上图
    plt.subplot(2,1,1)
    sns.kdeplot(data=df, x="total_bill")
    plt.title("总账单核密度图")
    plt.xlabel("total_bill")

    # 下图
    plt.subplot(2,1,2)
    sns.barplot(data=df, x="sex", y="tip", errorbar=None)
    plt.title("男女平均小费柱状图")
    plt.xlabel("性别 sex")
    plt.ylabel("小费 tip")

    plt.tight_layout()
    save_path = os.path.join(out_dir, "ex9_subplot_2row.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()
    print(f"习题9图片已保存：{save_path}")

def demo10(df, out_dir):
    plt.figure(figsize=(12,5))
    # 左图：1行2列，第1个子图
    plt.subplot(1,2,1)
    sns.violinplot(data=df, x="sex", y="total_bill",hue="sex")
    plt.title("男女消费金额小提琴图")
    plt.xlabel("性别")
    plt.ylabel("总账单")

    # 右图：1行2列，第2个子图
    plt.subplot(1,2,2)
    sns.kdeplot(data=df, x="tip", hue="time", fill=True)
    plt.title("小费核密度图（按时段分组）")
    plt.xlabel("小费 tip")
    plt.ylabel("密度")

    plt.tight_layout()
    save_path = os.path.join(out_dir, "ex10_subplot_1row2col.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()
    print(f"习题10图片已保存：{save_path}")

if __name__ == '__main__':

  # 生成数据
  df = pd.read_csv(R'D:\wx26.7.14\7.28\data\tips.csv',encoding='gbk')
  df2= pd.read_csv(R'D:\wx26.7.14\7.28\data\iris.csv',encoding='gbk')
  out_dir = R'D:\wx26.7.14\7.28\output'
  if not os.path.exists(out_dir):
      os.makedirs(out_dir)

  # demo1(df, out_dir)
  # demo2(df, out_dir)
  # demo3(df, out_dir)
  # demo4(df, out_dir)
  # demo5(df, out_dir)
  # demo6(df, out_dir)
  # demo7(df, out_dir)
  # demo8(df2, out_dir)
  # demo9(df, out_dir)
  demo10(df, out_dir)