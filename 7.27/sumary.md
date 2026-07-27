## 7.28 数据可视化与EDA

### 1.数据可视化介绍

##### 1.1 定义

###### 核心： 把数据转化为视觉信息，降低信息理解门槛，支撑数据分析与决策。

    数据可视化，是借助图形、图表、地图、仪表盘等可视化载体，将抽象、海量、难以直接阅读的原始数据进行可视化呈现的技术与方法。
    
    原始数据大多以表格、文本、数字形式存在，人类很难快速发现其中规律、趋势、异常点；而可视化利用人眼对图形、色彩、形状快速识别的视觉优势，把数据蕴含的信息直观展现出来。



##### 1.2 EDA（探索性数据分析，Exploratory Data Analysis）

###### EDA 即**探索性数据分析**，是拿到数据集后，正式建模之前开展的分析流程。核心思路：不预先设定假设，通过统计计算 + 数据可视化，主动认识数据、挖掘特征信息。区别于验证性数据分析（先有猜想再验证），EDA 重在**探索、发现问题**

    拿到原始数据，正式做模型、写结论之前，先把数据摸透，找出数据里的各种问题和规律。
    EDA = 认识数据 + 排查脏数据 + 寻找规律
    而数据可视化就是 EDA 最主要的工具，看图比干看数字更容易发现问题。

##### 1.3 可视化工具

###### 1.3.1 matlab和seaborn

    eaborn 是基于 Matplotlib 的 Python 高级可视化库，专门服务于数据分析、EDA 探索性数据分析。
    
    ATLAB 是商用科学计算软件，自带完整绘图模块。
    语言环境：MATLAB 自有脚本语言

###### 1.3.2 Matplotlib

    Python 底层绘图库，Seaborn 的基础
    特点：自由度极高，可以自定义图表每一处细节；支持 2D、简单 3D 绘图
    适用：定制化图表、学术论文绘图
    缺点：原生代码繁琐，默认样式简陋

##### 1.4  Matplotlib语法

    atplotlib 采用面向对象 /pyplot 两种写法，日常多用plt简易接口。
    通用流程：
    导入库
    准备数据
    创建画布 / 绘图
    设置标题、坐标轴、图例
    展示 / 保存图像
    
    import matplotlib.pyplot as plt
    
    # 通用配置
    plt.title("图表标题")        # 设置标题
    plt.xlabel("X轴名称")       # X轴标签
    plt.ylabel("Y轴名称")       # Y轴标签
    plt.legend()                # 显示图例
    plt.grid(alpha=0.3)         # 显示网格，alpha透明度
    plt.show()

#### 1.4.2 常用图表代码示例

    折线图 plt.plot ()
    
    import matplotlib.pyplot as plt
    x = [1,2,3,4,5]
    y = [2,4,1,5,3]
    plt.plot(x, y, color="red", marker="o", label="数据")
    plt.title("折线图")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.legend()
    plt.show()
    
    柱状图 plt.bar ()
    
    
    cate = ["A","B","C","D"]
    num = [15,28,12,22]
    plt.bar(cate, num, color="steelblue")
    plt.title("柱状图")
    plt.show()
    
    水平柱状图 plt.barh ()
    
    
    cate = ["A","B","C","D"]
    num = [15,28,12,22]
    plt.barh(cate, num)
    plt.show()
    
    散点图 plt.scatter () 
    
    x = [1,2,3,4,5,6]
    y = [2,3,5,4,6,7]
    plt.scatter(x,y, s=60, c="orange") # s控制点大小
    plt.title("散点图")
    plt.show()
    
    直方图 plt.hist ()
    
    data = [12,15,14,18,16,15,17,14,19]
    plt.hist(data, bins=4) # bins分组数量
    plt.title("直方图")
    plt.show()
    
    饼图 plt.pie ()
    
    nums = [30,20,40,10]
    labels = ["一类","二类","三类","四类"]
    plt.pie(nums, labels=labels, autopct="%.1f%%")
    plt.title("饼图")
    plt.show()
    
    箱线图 plt.boxplot ()
    
    data = [[12,15,17,20,35],[8,11,14,16,19]]
    plt.boxplot(data)
    plt.title("箱线图")
    plt.show()

### 2 项目实例

#### 基础语法

* `plot()`：用于绘制线图和散点图
* `scatter()`：用于绘制散点图
* `bar()`：用于绘制垂直条形图和水平条形图
* `hist()`：用于绘制直方图
* `pie()`：用于绘制饼图
* `imshow()`：用于绘制图像
* `subplots()`：用于创建子图

##### 2.1 基本导入

    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    
    # 解决中文、负号乱码（Windows）
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False

##### 2.2 数据集导入

    方式①：外部 CSV 真实数据（项目使用）
    
    df = pd.read_csv(r"文件路径.csv", encoding="utf-8-sig")
    
    方式②：代码生成模拟测试数据（调试、可视化演示）
    
    np.random.seed(42)  # 固定随机种子，每次图形一致
    normal_data = np.random.normal(loc=40, scale=10, size=80)
    outliers = np.array([92, 95, 12, 8])
    data = np.concatenate([normal_data, outliers])
    df = pd.DataFrame({"value": data})

##### 2.3 直方图

###### ax1.hist(df["math_score"], bins=12, alpha=0.5, edgecolor="black", label="math score", color="red")

    第一行：画数学分数的直方图
    ax1.hist(...)：在第 1 个子图上绘制直方图（hist = histogram）
    df["math_score"]：绘图用的数据来源 —— 数据表里所有学生的数学分数这一列
    bins=12：把分数的整个范围，平均切成 12 个分数段，对应 12 根柱子
    alpha=0.5：柱子填充色的透明度，0 = 完全透明，1 = 完全不透明；0.5 是半透明，后面叠阅读、写作的柱子时能互相透出来
    edgecolor="black"：每根柱子的描边颜色设为黑色
    label="math score"：给这组柱子起一个标签名，后面图例里会用到
    color="red"：柱子的填充颜色设为红色
    
    ax1.set_title("三科考试分数分布直方图")
    给第一个子图的顶部加上标题文字。
    5. 设置 X 轴标签
    python
    运行
    ax1.set_xlabel("分数")
    给 X 轴（水平轴）加说明文字，表示横轴代表的是考试分数。
    6. 设置 Y 轴标签
    python
    运行
    ax1.set_ylabel("学生人数")
    给 Y 轴（垂直轴）加说明文字，表示纵轴代表的是每个分数段对应的学生数量。
    7. 开启网格线
    python
    运行
    ax1.grid(True, alpha=0.3)
    True：打开背景的网格辅助线
    alpha=0.3：网格线设为浅淡的半透明，不遮挡柱子，只做读数参考
    8. 显示图例
    python
    运行
    ax1.legend()
    把之前每个 hist 里设置的 label 展示出来，用颜色 + 文字告诉你哪根柱子对应哪个科目。
    9. 弹出图表窗口
    python
    运行
    plt.show()

    ax1.hist(df["math_score"],bins=12,alpha=0.5,edgecolor="black",label="math score", color="red")
    
    **ax1.hist(df["reading_score"], bins=12, alpha=0.4, edgecolor="black", label="阅读")**
    
    **ax1.hist(df["writing_score"], bins=12, alpha=0.4, edgecolor="black", label="写作")**
    
    **ax1.set_title("三科考试分数分布直方图")**
    
    **ax1.set_xlabel("分数")**
    
    **ax1.set_ylabel("学生人数")**
    
    **ax1.grid(True, alpha=0.3)**
    
    **ax1.legend()** 第二行：画阅读分数的直方图 ax1.hist(df["reading_score"], bins=12, alpha=0.4, edgecolor="black", label="阅读") 和上一行逻辑完全一样，只是： 数据源换成了阅读分数列 标签名改成 “阅读” 透明度 0.4，和数学区分开 3. 第三行：画写作分数的直方图 ax1.hist(df["writing_score"], bins=12, alpha=0.4, edgecolor="black", label="写作") 同理，数据源换成写作分数，标签改成 “写作”。 连续调用三次 hist，就把三科的分布叠在了同一张子图里。 4. 设置子图标题 ax1.set_title("三科考试分数分布直方图") 给第一个子图的顶部加上标题文字。 5. 设置 X 轴标签 ax1.set_xlabel("分数") 给 X 轴（水平轴）加说明文字，表示横轴代表的是考试分数。 6. 设置 Y 轴标签 ax1.set_ylabel("学生人数") 给 Y 轴（垂直轴）加说明文字，表示纵轴代表的是每个分数段对应的学生数量。 7. 开启网格线 ax1.grid(True, alpha=0.3) True：打开背景的网格辅助线 alpha=0.3：网格线设为浅淡的半透明，不遮挡柱子，只做读数参考 8. 显示图例 ax1.legend() 把之前每个 hist 里设置的 label 展示出来，用颜色 + 文字告诉你哪根柱子对应哪个科目。 9. 弹出图表窗口 plt.show()

##### 2.4 分组并列柱状图

###### 

    # 1. 数据预处理：按辅导状态分组，计算三科平均分
    prep_group = df.groupby("test_preparation_course")[["math_score", "reading_score", "writing_score"]].mean()
    # 提取两组对比数据
    none_scores = prep_group.loc["none"]       # 未参加辅导的三科平均分
    completed_scores = prep_group.loc["completed"]  # 完成辅导的三科平均分
    
    # 2. 定义x轴基准位置与单根柱子宽度
    x = np.arange(3)       # 3个科目对应3个基准中心点
    width = 0.35           # 单根柱子宽度
    
    # 3. 绘制两组并列柱子
    ax2.bar(x - width/2, none_scores, width=width, label="未参加辅导", color="steelblue")
    ax2.bar(x + width/2, completed_scores, width=width, label="完成辅导", color="indianred")
    
    # 4. 替换x轴刻度为中文科目名称
    ax2.set_xticks(x)
    ax2.set_xticklabels(["数学", "阅读", "写作"])
    
    # 5. 子图基础装饰
    ax2.set_title("有无考前辅导各科平均分对比")
    ax2.set_xlabel("科目")
    ax2.set_ylabel("平均分")
    ax2.set_ylim(0, 100)
    ax2.grid(axis="y", alpha=0.3)
    ax2.legend()
    
    # 6. 柱子顶部标注具体分数
    for bar in ax2.patches:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h, f"{h:.1f}", ha="center", va="bottom")

#### 2.5 散点图

    作用：展示两个数值型变量之间的相关关系，直观观察数据的分布趋势与关联强度。本实例展示数学分数与阅读分数的相关性。
    完整项目代码
    
    # 绘制散点图
    ax3.scatter(df["math_score"], df["reading_score"], 
                s=20, alpha=0.6, color="coral", edgecolor="white")
    
    # 子图装饰
    ax3.set_title("数学与阅读分数相关性散点图")
    ax3.set_xlabel("数学分数")
    ax3.set_ylabel("阅读分数")
    ax3.grid(True, alpha=0.3)
    
    
    ax3.scatter(df["math_score"], df["reading_score"], 
                s=20, alpha=0.6, color="coral", edgecolor="white")
    ax3.scatter(...)：在第 3 个子图上绘制散点图
    第一个参数 df["math_score"]：x 轴数据，用所有学生的数学分数作为横坐标
    第二个参数 df["reading_score"]：y 轴数据，用所有学生的阅读分数作为纵坐标，两个数组长度必须一致
    s=20：散点的大小，数值越大数据点越大，默认 20
    alpha=0.6：点的透明度，数据密集时调低透明度可避免重叠遮挡，看清分布密度
    color="coral"：散点的填充颜色
    edgecolor="white"：散点的描边颜色，加白色边框可让密集的点更清晰可辨
    
    
    ax3.set_title("数学与阅读分数相关性散点图")
    给子图添加标题，说明图表主题
    python
    运行
    ax3.set_xlabel("数学分数")
    ax3.set_ylabel("阅读分数")
    分别设置 x 轴、y 轴的说明文字，明确两个轴代表的含义
    python
    运行
    ax3.grid(True, alpha=0.3)
    添加浅淡网格线，辅助读取坐标数值
    

#### 2.6 饼图

    作用：展示不同类别在总体中的占比结构，直观体现各部分的比例关系。本实例展示学生性别的分布占比。
    完整项目代码
    
    # 1. 数据统计：计算性别人数
    gender_count = df["gender"].value_counts()
    
    # 2. 绘制饼图
    ax4.pie(gender_count, 
            labels=gender_count.index,
            autopct="%1.1f%%",
            startangle=90,
            colors=["lightskyblue", "lightcoral"])
    
    # 3. 装饰与规范
    ax4.set_title("学生性别分布占比")
    ax4.axis("equal")  # 保证饼图为正圆形
    
    数据统计
    gender_count = df["gender"].value_counts()
    统计 gender 列中每个类别的数量，得到「男 / 女」对应的人数
    结果为一个带索引的序列，索引是类别名称，值是对应人数
    绘制饼图核心代码
    python
    运行
    ax4.pie(gender_count, 
            labels=gender_count.index,
            autopct="%1.1f%%",
            startangle=90,
            colors=["lightskyblue", "lightcoral"])
    ax4.pie(...)：在第 4 个子图上绘制饼图
    第一个参数 gender_count：用于计算占比的数值数据
    labels=gender_count.index：每个扇形对应的标签文字，这里用性别名称
    autopct="%1.1f%%"：在扇形内部显示百分比，%1.1f%% 表示保留 1 位小数的百分比格式
    startangle=90：饼图的起始旋转角度，90 度表示从正上方开始排列扇形，视觉更美观
    colors=[...]：按顺序指定每个扇形的填充颜色
    规范设置
    python
    运行
    ax4.axis("equal")

#### 2.7 箱线图

    # 1. 数据分组：按家长学历分组，提取每组的数学分数列表
    edu_math = df.groupby("parental_level_of_education")["math_score"].apply(list)
    
    # 2. 绘制箱线图
    ax5.boxplot(edu_math.values, 
                labels=edu_math.index,
                patch_artist=True,
                showmeans=True)
    
    # 3. 装饰优化
    ax5.set_title("不同家长学历的数学分数分布")
    ax5.set_ylabel("数学分数")
    ax5.tick_params(axis="x", rotation=30)  # x轴标签旋转30度，避免文字重叠
    ax5.grid(axis="y", alpha=0.3)

    数据分组处理
    python
    运行
    edu_math = df.groupby("parental_level_of_education")["math_score"].apply(list)
    按家长学历分组，将每组学生的数学分数汇总成一个列表
    结果：索引是学历名称，每个索引对应一个分数列表，箱线图需要每组传入一组原始数据
    绘制箱线图核心代码
    python
    运行
    ax5.boxplot(edu_math.values, 
                labels=edu_math.index,
                patch_artist=True,
                showmeans=True)
    ax5.boxplot(...)：在第 5 个子图上绘制箱线图
    第一个参数 edu_math.values：传入每组的分数数据列表
    labels=edu_math.index：每个箱子对应的 x 轴标签，即家长学历名称
    patch_artist=True：允许对箱子填充颜色，默认是空心线框，设为 True 后才能设置填充色
    showmeans=True：在图中额外显示均值点，方便对比均值与中位数的差异
    优化装饰
    python
    运行
    ax5.tick_params(axis="x", rotation=30)
    分类名称较长时，将 x 轴标签旋转 30 度，避免文字重叠挤在一起
    

#### 2.8 水平条形图

    # 1. 数据计算：按家长学历分组求数学平均分，按分数升序排序
    edu_mean = df.groupby("parental_level_of_education")["math_score"].mean().sort_values()
    
    # 2. 绘制水平条形图
    ax6.barh(edu_mean.index, edu_mean.values, color="seagreen", height=0.6)
    
    # 3. 柱子右侧标注分数
    for bar in ax6.patches:
        w = bar.get_width()
        ax6.text(w + 0.5, bar.get_y() + bar.get_height()/2, 
                 f"{w:.1f}", va="center", ha="left")
    
    # 4. 子图装饰
    ax6.set_title("不同家长学历的数学平均分")
    ax6.set_xlabel("数学平均分")
    ax6.set_xlim(0, 80)
    ax6.grid(axis="x", alpha=0.3)

    数据计算与排序
    python
    运行
    edu_mean = df.groupby("parental_level_of_education")["math_score"].mean().sort_values()
    按家长学历分组计算数学平均分
    sort_values()：按分数升序排列，水平条形图从上到下分数由低到高，视觉更有序
    绘制水平条形图核心代码
    python
    运行
    ax6.barh(edu_mean.index, edu_mean.values, color="seagreen", height=0.6)
    ax6.barh(...)：在第 6 个子图上绘制水平条形图（h = horizontal）
    第一个参数 edu_mean.index：y 轴的分类标签（家长学历）
    第二个参数 edu_mean.values：条形的长度（平均分），对应 x 轴数值
    color="seagreen"：条形填充颜色
    height=0.6：单根条形的高度（对应垂直柱状图的 width），数值越小条形越细
    柱子右侧标注数值
    python
    运行
    for bar in ax6.patches:
        w = bar.get_width()
        ax6.text(w + 0.5, bar.get_y() + bar.get_height()/2, 
                 f"{w:.1f}", va="center", ha="left")
    遍历所有条形，获取每根条形的宽度（即分数值）
    在条形右侧的居中位置标注分数，w + 0.5 留出一点空隙避免文字贴住条形
    va="center"：垂直方向居中对齐，保证文字在条形的中间高度
    

#### 2.9 折线图

    # 1. 数据处理：数学分数分箱，计算每个分数段的平均阅读分
    df["math_bin"] = pd.cut(df["math_score"], bins=10)
    bin_reading_mean = df.groupby("math_bin")["reading_score"].mean()
    
    # 2. 绘制折线图
    ax.plot(bin_reading_mean.index.astype(str), bin_reading_mean.values,
            marker="o", linestyle="-", color="royalblue", linewidth=2)
    
    # 3. 子图装饰
    ax.set_title("数学分数段对应的平均阅读分数趋势")
    ax.set_xlabel("数学分数段")
    ax.set_ylabel("平均阅读分数")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, alpha=0.3)

    逐行代码详解
    数据分箱处理
    python
    运行
    df["math_bin"] = pd.cut(df["math_score"], bins=10)
    bin_reading_mean = df.groupby("math_bin")["reading_score"].mean()
    
    pd.cut(...)：将数学分数连续值切成 10 个等宽的分数段，给每个学生打上所属分段标签
    按分数段分组，计算每个分段内学生的平均阅读分数，得到分段对应的趋势数据
    绘制折线图核心代码
    python
    运行
    ax.plot(bin_reading_mean.index.astype(str), bin_reading_mean.values,
            marker="o", linestyle="-", color="royalblue", linewidth=2)
    
    ax.plot(...)：绘制折线图
    第一个参数：x 轴数据，这里是分数段名称
    第二个参数：y 轴数据，对应每个分段的平均阅读分数
    marker="o"：每个数据点用圆形标记突出显示，方便看清每个分段的具体数值
    linestyle="-"：折线样式，- 实线、-- 虚线、: 点线
    linewidth=2：折线的粗细，数值越大线条越粗
