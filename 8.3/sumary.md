### 8.2 pytorch

#### 一.复习

##### 1.训练流程：

    #模型定义
    class MyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.module1 = nn.xxx
            self.module2 = nn.其余部件
            # 堆叠网络层：线性层、卷积层等
    
        def forward(self,x):
            x = self.module1(x)
            x = self.module2(x)
            return x 
    
    #数据集与加载器
    dataset = TensorDataset(X_tensor, Y_tensor)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    #TensorDataset：把特征 X、标签 Y 打包成数据集样本
    #DataLoader：分批、打乱、并行取数据
    #batch_size=32：一次拿 32 条样本
    #shuffle=True：每个 epoch 开始打乱数据，防止模型记住样本顺序
    
    
    #训练组件初始化
    model = MyModel()
    criterion = nn.CrossEntropyLoss()       # 损失函数
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3) # 优化器
    num_epochs=50
    
    
    #核心训练循环（重中之重）
    
    for epoch in range(num_epochs):
        for batch_x, batch_y in dataloader:
            # 1.前向传播，得到预测结果
            output = model(batch_x)
            # 2.计算损失
            loss = criterion(output, batch_y)
    
            # 3.反向传播 + 参数更新三板斧
            optimizer.zero_grad()    # 清零梯度
            loss.backward()          # 自动求导，计算梯度
            optimizer.step()         # 根据梯度更新权重)         
    
    optimizer.zero_grad()
    梯度会累加，每一轮训练前必须清空上一轮梯度，否则梯度叠加导致训练异常。
    loss.backward()
    反向传播，自动沿着计算图求导，给所有参数算出梯度，存在 .grad 属性。
    optimizer.step()
    优化器使用梯度，按照学习率更新网络权重。# 根据梯度更新权重

### 2. RNN(循环神经网络)

##### 2.1 core

    普通全连接网络、CNN：输入长度固定，数据之间互相独立
    RNN：专门处理时序数据（前后有依赖关系）
    例子：文本、语音、时间序列预测、股票数据
    核心思想：循环单元共享权重，把上一刻的记忆传递给下一刻

    基础结构原理时序展开形式：
    \(x_t\)：t 时刻输入
    \(h_t\)：t 时刻隐藏状态（记忆）
    \(h_{t-1}\)：上一时刻记忆
    公式：
    
    \(h_t = \tanh(W_{hh}h_{t-1} + W_{xh}x_t + b_h)\)
    \(y_t = W_{hy}h_t + b_y\)📌关键特点：
    权重共享：每一个时间步使用同一套 W 参数
    隐藏状态 \(h_t\) = 网络的 “短期记忆”，保存历史信息
    激活函数一般 tanh，把数值约束在 [-1,1]
    三、致命缺陷（必考点）梯度消失 / 梯度爆炸
    序列很长时，链式求导不断连乘，梯度要么趋近 0（消失），要么无限变大（爆炸）
    → 改进方案：LSTM / GRU（引入门控机制，解决长距离依赖）
    RNN 只适合短序列；长序列几乎不用原生 RNN

##### 2.2 LSTM VS GRU

    1. 原生 RNN只有短期隐藏状态 \(h_t\)，时序反向传播时，梯度反复和 tanh 导数相乘，序列一长梯度快速趋近于 0，历史久远的信息学不到。
    
    2. LSTM两大核心：
    Cell State（传送带）：信息沿着序列平缓流动，少量加减操作，梯度不容易消失；
    三门控控制信息流通：
    遗忘门：丢弃旧记忆
    输入门：存入新信息
    输出门：控制细胞状态输出到隐藏态
    3. GRU做减法优化：
    遗忘门 + 输入门合并为 更新门
    去掉独立 Cell State，只用隐藏状态
    新增 重置门，控制历史信息多大程度参与当前计算
    
    
    优点：更少参数、更快收敛；代价：长距离信息承载上限略低于 LSTM

<style> table { border-collapse: collapse; width: 100%; } th, td { border: 1px solid #ccc; padding: 8px; text-align: left; } </style>

<style> table { border-collapse: collapse; width: 100%; } th, td { border: 1px solid #ccc; padding: 8px; text-align: left; } </style>

| 模型         | 核心结构                                            | 核心优势                                | 致命短板                    | 适用场景                |
| ---------- | ----------------------------------------------- | ----------------------------------- | ----------------------- |:-------------------:|
| **原生 RNN** | 单一循环单元，仅隐藏状态 ht​，公式 ht​=tanh(Whh​ht−1​+Wxh​xt​) | 结构最简单、参数量最少、训练速度最快                  | **长序列梯度消失严重**，无法捕捉远距离依赖 | 超短序列、教学演示，工程几乎不使用   |
| **LSTM**   | 引入**细胞状态 Cell State**；3 个门控：遗忘门、输入门、输出门         | 依靠细胞状态长线传递信息，**有效缓解长距离梯度消失**，记忆能力最强 | 门控多，参数量大，训练耗时更高         | 长文本、长时序、对记忆精度要求高的任务 |
| **GRU**    | 简化 LSTM；合并为**更新门、重置门**，移除独立 Cell State          | 参数量更少，训练速度快，效果接近 LSTM               | 长距离依赖捕捉能力略弱于 LSTM       | 工业主流，平衡性能与训练成本      |

### 三. NLP

##### 3.1 NLP 任务层级划分

-  1. 词级别（最小粒度）

分词、POS 词性标注、NER 命名实体识别

-  2. 句级别（单条句子）

文本分类、情感分析、机器翻译

- 3.篇章级别（长文本、多轮内容）
  
  文本摘要、问答系统、对话生成

##### 3.2 核心任务对照表梳理

<style> table { border-collapse: collapse; width: 100%; } th, td { border: 1px solid #ccc; padding: 8px; text-align: left; } </style>

| 任务名称       | 核心作用            | 通俗例子                 |
| ---------- | --------------- | -------------------- |
| 文本分类       | 给整句 / 整篇分配标签    | 情感正负判断、垃圾短信识别、意图识别   |
| NER 命名实体识别 | 标出文本关键片段 + 类别   | 人名、地名、机构、时间、疾病       |
| 关系抽取       | 抽取**两个实体之间的联系** | 张三 → 就职于 → 阿里巴巴（三元组） |
| 事件抽取       | 提取完整事件要素        | 发生事件、时间、地点、参与主体      |
| POS 词性标注   | 给每个词语标注词性       | 名词、动词、形容词、副词         |
| 文本相似度匹配    | 判断两段文本语义是否接近    | FAQ 问答召回、重复文案过滤      |
| 机器翻译       | 跨语言互译           | 中译英、多语言转换            |
| 文本摘要生成     | 长文本压缩成简短摘要      | 新闻摘要、会议纪要提取          |
| 对话生成       | 人机多轮交互          | 客服机器人、聊天助手           |

> 存储工具常用：Neo4j 图数据库。

###### 3.3 任务上下游关联（面试常问）

1. 搭建知识图谱标准流水线：
   文本 → NER 识别实体 → 关系抽取 → 构建`(实体1,关系,实体2)`三元组 → 存入 Neo4j 知识图谱

2. 大模型 RAG 场景：知识图谱可以用来做精准检索，减少模型幻觉

###### 3.4 标注工具补充说明

表格里`Label Studio`是工业最常用开源标注平台，不同任务对应独立标注模板，做 NLP 项目数据集标注基本都会用到
