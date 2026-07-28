## 7.28

#### 1。数据可视化continue

     五、课后练习（10 道）
    
    请使用 `tips.csv` 和 `iris.csv` 完成以下绘图任务，并将图片保存在 `exercise_output` 文件夹中。
    
    1. **习题 1**：绘制小费金额 (`tip`) 的分布直方图，要求包含核密度曲线，分箱数为 30。
    2. **习题 2**：绘制总账单 (`total_bill`) 的核密度图，按是否吸烟 (`smoker`) 分组对比。
    3. **习题 3**：绘制箱线图，X 轴为用餐时段 (`time`)，Y 轴为小费 (`tip`)，按性别 (`sex`) 分组颜色。
    4. **习题 4**：绘制小提琴图，X 轴为星期 (`day`)，Y 轴为小费 (`tip`)，按时段 (`time`) 分组并分割显示 (`split=True`)。
    5. **习题 5**：绘制柱状图，X 轴为星期 (`day`)，Y 轴为小费 (`tip`)，**不显示误差线**。
    6. **习题 6**：计算数值列的相关系数，绘制热力图，要求显示数值 (`annot=True`)，配色使用 `coolwarm`。
    7. **习题 7**：绘制回归图，X 轴为账单，Y 轴为小费。要求按吸烟情况 (`smoker`) 分别画出两条回归线进行对比。
    8. **习题 8**：使用尾花数据 (`iris`)，选取 `sepal_length`, `sepal_width`, `petal_length` 和 `species` 字段，绘制配对散点矩阵 (`pairplot`)。
    9. **习题 9**：创建一个 2 行 1 列的子图画布：
      * 上图：账单密度的核密度图。
      * 下图：男女平均小费的柱状图。
    10. **习题 10（综合）**：创建一个 1 行 2 列的子图画布：
      * 左图：男女消费金额分布的小提琴图。
      * 右图：一周每日平均消费的柱状图。
    
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

### 二.机器学习

#### 1.概论：机器学习，是让计算机不靠人写死全部规则，通过大量数据自动学习规律、完成预测 / 判断的技术。

    大量历史数据 + 算法 → 机器自动学到规律（模型）
    新输入数据 + 训练好的模型 → 输出结果
    例：给机器成千上万条【账单 - 小费】记录，它自动算出账单和小费的关系，不用你写计算公式。

#### 2.类型：

- 监督学习 
  
  * 数据**带有标准答案（标签）**，机器对照答案学习
  
  * 1）**回归任务**：预测连续数值例子：预测房价、预测小费、预测销量
  
  * 2）**分类任务**：预测离散类别例子：判断鸢尾花品种、判断邮件是否垃圾邮件*
    
    

- 无监督学习
  
  - 数据**没有标准答案**，机器自主挖掘数据内在结构，常见：聚类、降维
  
  - 例子：根据用户消费习惯自动划分客户群体

- 强化学习
  
  - 智能体不断和环境交互，通过「奖励 / 惩罚」持续优化行为
  
  - 例子：AI 下棋、自动驾驶、游戏 AI

##### 深度学习属于**机器学习的一个分支**，使用多层神经网络；大模型LLM是深度学习的产物

## 三.线性回归

#### 1.线性回归属于监督学习 — 回归任务

    目标：学习特征与目标值之间的线性关系，预测连续数值
    公式（一元）：\(y = w\cdot x + b\)
    多元：\(y = w_1x_1+w_2x_2+...+w_nx_n + b\)
    💡区分：
    逻辑回归是分类；线性回归是回归预测，二者不要混淆。

#### 2.线性回归在机器学习中的两大核心作用

- 作用 1：基线模型（Baseline）
  
  - 训练任何复杂模型（随机森林、XGBoost、神经网络）前，**先用线性回归跑一遍**
    
    * 作用：提供最低效果基准；
    * 如果复杂模型效果和线性回归差不多，说明特征质量差，没必要上复杂模型。

- 作用 2：特征解读、因果分析
  
  - 线性回归输出权重 w：权重正负代表**正向 / 负向影响**，权重大小代表影响强弱。
  
  - 例：房价模型，面积权重为正，房龄权重为负，方便业务解释。
    树模型很难清晰量化每个特征影响力，这是线性回归巨大优势。

#### 3. 损失函数（Loss Function）

###### 线性回归：均方误差 MSE 公式：(Loss = \frac{1}{n}\sum_{i=1}^n (y_i-\hat{y}_i)^2\)

![6ba5f621-f5fd-4f2c-a888-56a987559fc4](file:///C:/Users/HP/Pictures/Typedown/6ba5f621-f5fd-4f2c-a888-56a987559fc4.png)
    y：真实值；yi^模型预测值
    含义：衡量预测结果和真实标签差距，训练目标就是最小化损失。
    求解方法：最小二乘法 / 梯度下降。

#### 4.多重共线性（Multicollinearity）

###### **多个特征之间存在高度线性相关**。

    带来的问题：
    参数权重 w 不稳定，微小扰动数据，系数剧烈波动；
    权重符号反常，和业务常识冲突；
    无法分辨到底哪个特征真正影响目标；
    标准误差变大，模型难以解释。

#### 5.正则化（Regularization）

###### 核心目的：**防止过拟合**

- 过拟合现象：模型在训练集效果极好，测试集很差；往往权重 w 取值过大。

- 正则化思路：在原始损失函数基础上**增加惩罚项，约束参数大小**。 

- \(\lambda\) 越大，惩罚力度越强：
  
  * \(\lambda=0\) → 等价普通线性回归；
  * \(\lambda \uparrow\) → 权重约束更强，降低过拟合风险。

![fa69e78d-6e46-4bba-a4fe-a43114d2a95b](file:///C:/Users/HP/Pictures/Typedown/fa69e78d-6e46-4bba-a4fe-a43114d2a95b.png)

![835fdbd5-9144-44cb-a9fd-6850ad290aa2](file:///C:/Users/HP/Pictures/Typedown/835fdbd5-9144-44cb-a9fd-6850ad290aa2.png)

![ad4ea980-b5cf-4bcc-8d2a-12572078b123](file:///C:/Users/HP/Pictures/Typedown/ad4ea980-b5cf-4bcc-8d2a-12572078b123.png)

## 四.树算法

#### 1.集成学习（Ensemble Learning）

###### 不只用单个模型，同时训练多个基础模型，把多个模型的预测结果结合起来，得到最终预测。

###### 集成学习两大主流流派

- **Bagging（并行）** → 代表：随机森林

- **Boosting（串行 / 提升树）** → 代表：AdaBoost、XGBoost、LightGBM
  
  - XGBoost 和 LightGBM 都属于梯度提升决策树（GBDT的工业优化版本。
    **它们训练的本质是：串行生成一整队决策树（你代码里是 100 棵），每一棵新树都专门去拟合前面所有树预测错的部分，最终把所有树的结果叠加，得到最终预测。**
  
  - 提升树通用训练流程（XGB/LGB 底层逻辑完全一致）
     用通俗的「改错迭代」逻辑拆解：
     初始基准：先给一个最朴素的预测值（比如分类任务先猜 “所有样本的平均概率”），这时候预测误差很大。
     第 1 轮迭代：
     计算当前预测和真实标签的差距（专业叫负梯度 / 残差，通俗说就是 “算错了多少”）；
     训练第 1 棵决策树，目标不是直接预测标签，而是预测这个 “错误值”；
     把这棵树的结果加到原来的预测上，整体错误就变小了。
     第 2 轮迭代：
     用更新后的预测值，重新计算新一轮的错误；
     训练第 2 棵决策树，专门拟合这一轮剩下的错误；
     再把结果叠加上去，错误进一步缩小。
     循环往复：重复这个过程，一共训练 100 轮，生成 100 棵树；每加一棵树，模型在训练集上的误差就更低一点。
     防过拟合控制：通过树深、正则、学习率、采样等参数，防止树太复杂，把训练集的噪声也学进去。
     生活化类比：你做一套题，第一遍做完错很多；第二遍专门改第一遍的错题；第三遍改第二遍剩下的错题…… 改 100 遍，正确率越来越高。

#### 2、决策树（Decision Tree）

###### 模仿人类`if-else`判断逻辑，一层一层划分样本。

###### 结构：根节点 → 内部判断节点 → 叶子节点（输出预测结果）



#### 3.XGBoost

    XGBoost 是经典 GBDT 的强化版，核心优化方向是更准、更稳，训练细节上有几个关键特点：
    
    二阶泰勒展开
    普通 GBDT 只用一阶梯度（只知道误差方向），XGBoost 同时用一阶梯度 + 二阶梯度（还知道误差的曲率），找最优分裂点更精准，收敛速度更快。
    
    内置正则惩罚
    每棵树的复杂度（叶子数量、叶子权重大小）会直接加入损失函数，对应你代码里的 reg_alpha（L1 正则）、reg_lambda（L2 正则），从训练根源上抑制过拟合。
    
    层优先生长（Level-wise）
    树的生长是整层整层分裂的 —— 同一深度的所有叶子节点，全部同时做分裂。
    好处：深度好控制（对应 max_depth=6），生长均衡，不容易过拟合；
    坏处：很多增益很小的叶子也会被分裂，存在大量无效计算，训练速度偏慢。
    
    精确分裂查找
    默认用贪心算法遍历所有可能的分裂阈值，找信息增益最大的点；大数据场景下也支持近似直方图算法加速。

#### 4.LightGBM

    LightGBM 核心优化方向是在尽量不掉精度的前提下，大幅提升训练速度、降低内存占用，训练逻辑和 XGB 有几个核心区别：
    
    叶子优先生长（Leaf-wise）
    不是整层一起分裂，而是每次只挑全树里 “分裂收益最大” 的那一个叶子节点做分裂。
    好处：同样分裂次数下，精度更高、计算量更少、速度更快；
    坏处：容易长出不平衡的树，更容易过拟合，所以必须用 max_depth 和 num_leaves 同时限制（你代码里 num_leaves=31 就是干这个的）。
    
    直方图算法（Histogram）
    不遍历每个特征的所有数值，而是把连续特征分成若干个 “箱子”（直方图），直接在箱子层面找最优分裂点。
    这是 LightGBM 速度快、内存省的最核心原因，计算量比精确查找低一个数量级。
    
    GOSS 梯度单边采样
    梯度大的样本（错得离谱的样本）对训练更重要，LightGBM 会保留全部高梯度样本，随机丢弃一部分低梯度样本，在几乎不损失精度的前提下进一步提速。
    
    EFB 互斥特征捆绑
    把稀疏特征里 “不会同时非零” 的特征捆绑成一个特征，减少特征数量，降低计算量。

Q1：随机森林和 GBDT 有什么区别？
--------------------

1. **集成策略不同**
   随机森林属于 **Bagging（并行）**；GBDT 属于 **Boosting（串行）**。
* 随机森林：多棵树独立并行训练，树之间互不影响；预测结果投票 / 取平均。

* GBDT：串行迭代训练，后一棵树拟合前面所有树的**残差**，不断修正错误。
2. **优化目标**
* Bagging：主要**降低方差**，缓解单棵决策树过拟合；

* Boosting：主要**降低偏差**，持续减少整体预测误差。
3. **样本选择方式**
   随机森林：bootstrap 有放回随机采样；
   GBDT 默认使用全部样本训练每一棵树（XGB/LGB 可以开启采样）。

4. **过拟合特性**
   随机森林依靠多树平均抑制过拟合；
   GBDT 持续学习残差，更容易学进噪声，需要严格调参防过拟合。

> 极简记忆：随机森林「大家各自独立投票」；GBDT「知错就改，持续改错」。

* * *

Q2：XGBoost 为什么比原生 GBDT 更快？
--------------------------

原生 GBDT 只用一阶梯度，XGBoost 在算法与工程上做多重优化：

1. **二阶泰勒展开**
   同时利用一阶、二阶梯度信息，收敛更快，同等效果下需要的树更少。

2. **预排序 + 近似分裂算法**
   支持近似直方图分裂，不用遍历全部特征阈值，减少计算量。

3. **内置正则项**
   损失函数加入 L1、L2 正则，降低过拟合，减少迭代轮数。

4. **并行优化**
   **单棵树内部特征分裂可以并行计算**（注意：树与树之间依旧串行）。

5. **缓存访问优化、缺失值自动分裂策略**
   工程层面优化内存读写，提升运算速度。

⚠️ 区分：XGB 只是**优于原始 GBDT**；LightGBM 相比 XGB 又增加直方图、GOSS 等进一步提速。

* * *

Q3：LightGBM 的 Leaf-wise 和 XGBoost 的 Level-wise 有什么区别？
-----------------------------------------------------

1. **Level-wise（XGBoost 默认，按层生长）**
   每一层所有叶子节点全部尝试分裂，一层一层向下扩展。
   ✅ 优点：树深度均衡，容易控制、不容易严重过拟合；
   ❌ 缺点：很多增益很小的叶子也要分裂，产生大量无效计算。

2. **Leaf-wise（LightGBM 默认，按叶子生长）**
   每次只选择**全局收益最大的那一个叶子节点**进行分裂。
   ✅ 优点：同等叶子数量下精度更高，计算量更小，训练更快；
   ❌ 缺点：容易生成很深的不平衡树，**更容易过拟合**，必须配合`num_leaves`限制最大叶子数。

一句话总结：

Level-wise = 整层一起扩；Leaf-wise = 择优单独扩叶子。

* * *

Q4：为什么 Kaggle 表格竞赛中树模型（XGB/LGB）比深度学习更常用？
----------------------------------------

1. **数据特性**
   Kaggle 结构化表格数据居多；深度学习更适合图像、文本这类原始稠密数据。表格数据很难发挥神经网络优势。

2. **数据规模门槛**
   深度学习需要海量数据；中小数据集上，XGBoost/LightGBM 效果普遍优于神经网络。

3. **特征工程友好**
   树模型不需要特征标准化，天然处理非线性、特征交互；对缺失值、异常值鲁棒。

4. **训练成本低**
   不需要 GPU，CPU 就能快速训练、调参；调参链路成熟稳定。

5. **可解释性**
   可以输出特征重要性，方便验证特征有效性；神经网络黑盒难以排查问题。

6. **竞赛实践**
   树模型稳定、基线强；一般先用 LGB/XGB 拿到高分基线，再考虑融合深度学习。

> 补充：如果是超大样本、百万级以上带原始文本 / 图像的多模态赛道，深度学习才会占优。

* * *

Q5：XGBoost 如何处理类别特征？
--------------------

先说结论：**原生 XGBoost 不支持直接输入字符串类别特征，必须提前编码**。

主流三种处理方式：

1. **独热编码 OneHotEncoder**
   适合低基数类别（类别数量很少）；类别基数很大时，产生大量稀疏特征，维度爆炸，不推荐。

2. **标签编码 LabelEncoder**
   把类别映射为 0,1,2,3……
   ⚠️ 缺陷：人为引入大小顺序，树模型可能错误学习虚假大小关系；

3. **目标编码 TargetEncoding（竞赛最常用）**
   利用类别对应的目标均值编码，保留类别与标签的关联信息。

💡对比 LightGBM：

LightGBM 原生支持类别特征，只需设置`categorical_feature`，内部实现最优划分，不需要手动复杂编码。

### 拓展面试追问

问：高基数类别特征（如用户 ID）怎么处理？

答：不建议直接编码，优先做统计特征（点击率、均值等），或者使用目标编码。 



## 五。SVM和KNM

#### 1.SVM（支持向量机，Support Vector Machine）

    1. 核心思想
    在特征空间里找一个间隔最大的分隔超平面，把两类样本尽可能稳妥地分开。
    超平面：分界线（二维是直线，三维是平面，更高维叫超平面）
    支持向量：离超平面最近的那些样本点，它们决定了分界线的位置
    最大间隔：让分界线到两侧最近样本的距离都尽可能大，分类鲁棒性最强
    
    2. 怎么训练
    线性可分场景：通过求解一个凸优化问题，直接算出最大间隔超平面；
    线性不可分场景：引入核函数（最常用 RBF 高斯核），把低维数据映射到高维空间，让数据在高维里变得线性可分，再找超平面。
    核函数是 SVM 的精髓：不用真的把数据升到高维，通过数学公式就能算出高维空间的样本相似度，避免计算爆炸。
    
    3. 关键参数
    C：惩罚系数。C 越大越不能容忍分错样本，容易过拟合；C 越小容错越高，容易欠拟合
    kernel：核函数。linear线性核、rbf高斯核（处理非线性数据最常用）
    gamma：RBF 核参数，控制单个样本的影响范围，值越大越容易过拟合
    4. 优缺点与适用场景
    ✅ 优点：高维小样本效果出色；有严格数学理论支撑；泛化能力强；对噪声相对不敏感
    ❌ 缺点：大数据集训练极慢；对参数和核函数选择敏感；原生多分类实现麻烦
    📍 适用场景：特征维度高、样本量中等偏小的任务，比如早期文本分类、生物信息数据分类

#### 2.KNN（K 近邻，K-Nearest Neighbors）

    1. 核心思想
    物以类聚，近朱者赤
    预测一个未知样本的类别时，找到离它最近的 K 个已知样本，这 K 个邻居里哪一类占多数，就把它判为哪一类。
    
    2. 怎么训练 / 预测
    没有训练过程！ 属于「懒惰学习」
    训练阶段只是把数据集存起来，不做任何计算；
    预测时才开始计算：
    计算当前样本和所有训练样本的距离（一般用欧氏距离），选出最近的 K 个邻居，投票决定类别。
    
    3. 关键参数
    K 值：邻居数量
    K 太小：容易受单个异常值干扰，过拟合
    K 太大：邻居范围太广，类别边界模糊，欠拟合
    实战一般取奇数，避免平票
    距离度量：欧氏距离（最常用）、曼哈顿距离
    4. 优缺点与适用场景
    ✅ 优点：原理极其简单、好理解；不用训练，开箱即用；天然支持多分类
    ❌ 缺点：预测速度极慢（每个新样本都要和所有训练样本算距离）；对特征量纲敏感（必须先做标准化）；样本不平衡时效果差；高维数据效果暴跌（维度灾难）
    📍 适用场景：小数据集、基线模型、教学演示，工业大样本场景很少作为主模型

## 六。特征工程和评估指标

#### 特征工程 ：特征工程是机器学习里最重要的一环。

1.特征缩放：

* 标准化：(x - 均值) / 标准差`,让数据服从标准正态分布

* 归一化：(x - 最小值) / (最大值 - 最小值)`,把数据压缩到[0,1]区间

* 适用场景：SVM/KNN/神经网络等对特征尺度敏感的算法

2.特征编码：

* 独热编码one-hot：把类别转换成二进制向量，比如红，蓝，绿转成[1,0,0][0,1,0][0,0,1]

* 标签编码：把类别转成数字，普通，不错，优秀->1，2，3，注意：只适合有序类别

3.特征选择：

* 过滤法：根据特征和目标的相关性选择

* 包装法：用模型性能来评估特征子集

* 嵌入法：模型训练中自动选择，（如L1正则化，树模型的特征重要性）

4.特征构造：

* 多项式构造：比如把x变成x, x², x³, x1×x2等

* 时间特征：从日期里提取年月日星期数，是否周末等

* 文本特征：TF-IDF，词嵌入embedding
  
  

##### 分类任务的评估指标：混淆矩阵confusion matrix

                  预测为正    预测为负
    真实为正      TP          FN      ← 真实正类 = TP + FN
    真实为负      FP          TN      ← 真实负类 = FP + TN
                  ↑ 预测正类    ↑ 预测负类
                = TP + FP   = FN + TN

###### 注意，矩阵

* **TP(真正例,True Positive)**: 真实是正,预测也是正。✅ 判对了
* **TN(真负例,True Negative)**: 真实是负,预测也是负。✅ 判对了
* **FP(假正例,False Positive)**: 真实是负,预测成了正。❌ 误报(冤枉好人)
* **FN(假负例,False Negative)**: 真实是正,预测成了负。❌ 漏报(放走坏人)



![48beb1ee-cec7-4e10-b5c3-671f7af1f8dd](file:///C:/Users/HP/Pictures/Typedown/48beb1ee-cec7-4e10-b5c3-671f7af1f8dd.png)



#### 回归任务的评估指标

* **MSE/MAE**: 预测误差。MSE 对大误差敏感(平方放大),MAE 更鲁棒。
* **R²**: 模型解释的方差比例,越接近1越好。R²<0 说明模型还不如直接用均值预测。



#### 七。 4 个基础概念

###### 

* **TP**：真实正例，预测为正
* **FP**：真实负例，预测为正（误报）
* **FN**：真实正例，预测为负（漏报）
* **TN**：真实负例，预测为负 



##### 1. Recall 召回率（查全率）

![b6981617-633f-4d47-b1b8-a09e880dafdb](file:///C:/Users/HP/Pictures/Typedown/b6981617-633f-4d47-b1b8-a09e880dafdb.png)

##### 2.Precision 精确率（查准率）

![5aecda11-0aea-4ac4-91b4-1c9893750703](file:///C:/Users/HP/Pictures/Typedown/5aecda11-0aea-4ac4-91b4-1c9893750703.png)

##### 3.Accuracy 准确率

![fde5f7db-f572-4868-89af-b4e57869e013](file:///C:/Users/HP/Pictures/Typedown/fde5f7db-f572-4868-89af-b4e57869e013.png)

##### 样本不平衡指分类数据集中不同类别样本数量差距巨大。模型容易偏向数量多的多数类，单纯依靠准确率评估存在欺骗性，需要更换评估指标，同时采用重采样、类别权重等手段优化模型。



##### 4. F1-Score

![f7a79ad1-a0bb-41d3-9c45-08daf78f359c](file:///C:/Users/HP/Pictures/Typedown/f7a79ad1-a0bb-41d3-9c45-08daf78f359c.png)

##### 5.AUC / PR-AUC

    AUC（ROC-AUC）
    
    描述模型整体排序能力；
    ⚠️ 缺陷：极度样本不平衡时，ROC-AUC 容易虚高。
    PR-AUC（Precision-Recall 曲线下面积）
    不平衡数据集首选，比 ROC-AUC 更客观。
