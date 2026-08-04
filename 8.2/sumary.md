## 8.2

### docker

##### 一.为什么要docker

* **传统虚拟机**：你打包一个 CentOS 镜像给测试，测试在上面跑。但如果你的代码依赖了某个系统库，而虚拟机里没装，测试依然会挂。

* **Docker 的做法**：它不光打包代码，**连代码运行的操作系统底层配置（环境变量、系统库、依赖版本）一起打包进镜像**。测试、运维拉走这个镜像，跑起来的容器**和你本地完全一致**。从此，没人能拿“环境问题”来催你改烂代码，你只管对逻辑负责。

#### 1. 虚拟机 vs Docker 容器

### 虚拟机（VMware、Hyper-V）

完整模拟一整台电脑：包含**独立内核、操作系统、驱动、应用**

✅优点：隔离极强

❌缺点：占用内存、CPU、磁盘资源巨大，启动慢，笨重

### Docker 容器

**不虚拟硬件、不装完整操作系统**

共用宿主机（你的 Windows/Linux）的系统内核！

只打包：程序 + 程序运行需要的依赖库、配置

✅优点：启动秒级、资源开销极小、轻便



##### 2.三大核心概念

###### 2.1 镜像（Image）

    定义：**只读模板、静态文件包**
    
    里面包含：代码、运行环境、依赖库、配置、命令。
    
    ⚠️ 镜像本身**不能直接运行**！

###### 2.2 容器（Container）

    定义：镜像运行起来之后产生的实例（动态正在运行的程序）
    拿镜像作为模板，启动之后，就生成容器。
    一个镜像 可以同时启动成千上百个容器
    容器拥有独立网络、独立文件空间，互相隔离

###### 2.3 仓库（Registry）

    存放镜像的远程服务器，用来上传、下载镜像。
    类比 GitHub
    GitHub 存放代码；
    Docker 仓库（Docker Hub / 阿里云镜像仓库）存放镜像

#### 3.Docker 完整工作流程（页面底部流程

    构建 / 拉取镜像
    要么自己写 Dockerfile 打包生成镜像，要么从远程仓库 pull 下载现成镜像
    根据镜像启动容器
    docker run 命令，以镜像为模板创建容器实例
    容器启动成功，内部程序运行，对外提供接口 / 服务（比如你的 Flask 后端）
    日常管理：停止容器、重启、删除、查看日志等

##### 3.1 基础语法

**镜像 (image)：静态模板 | 容器 (container)：镜像运行实例 | 仓库 registry：存放镜像**

> 规范：所有命令格式

bash
    docker [命令] [参数]
一、镜像相关命令（操作模板）

--------------

### 1. 查看本地所有镜像

bash
    docker images
    # 精简模式
    docker images -q

### 2. 远程搜索镜像（很少用，一般去官网查）

bash
    docker search python

### 3. 拉取镜像（下载）

bash
    # docker pull 名称:版本号，不加tag默认latest最新版
    docker pull python:3.11-slim

### 4. 删除本地镜像

bash
    docker rmi 镜像ID/镜像名
    # 强制删除
    docker rmi -f python:3.11-slim

### 5. 构建镜像（重点！打包你的 Flask 项目）

需要项目里新建 `Dockerfile`

bash
    # . 代表当前目录寻找Dockerfile
    docker build -t flask-insurance:v1 .
    # -t 给镜像起名:版本

### 6. 镜像导出 / 导入（离线迁移）

bash
    # 导出镜像为压缩包
    docker save flask-insurance:v1 -o insurance.tar
    # 导入
    docker load -i insurance.tar

* * *

二、容器核心命令（最高频）
-------------

### 1. 启动容器（最重要命令 docker run）

基础模板

bash
    docker run [参数] 镜像名称 [启动命令]

常用参数讲解：

* `-d` 后台运行（守护进程）
* `-p 宿主机端口:容器内端口` **端口映射**（你的 flask 必须配置！）
* `--name` 给容器自定义名字
* `-v` 文件挂载（持久化数据）
* `--rm` 容器停止后自动删除
* `-it` 交互式进入容器终端

示例：启动 python 容器

bash
    # 前台交互式
    docker run -it --name py-test python:3.11-slim bash
    # 后台启动flask服务，端口映射 5000:5000
    docker run -d --name insurance-api -p 5000:5000 flask-insurance:v1

### 2. 查看容器

bash
    # 查看正在运行的容器
    docker ps
    # 查看所有（包含已经停止的）
    docker ps -a
    # 只输出容器id
    docker ps -aq

### 3. 启动 / 停止 / 重启容器

bash
    docker start 容器ID/名称
    docker stop 容器ID/名称
    docker restart 容器ID/名称
    # 强制杀死（stop优雅关闭，kill暴力）
    docker kill 容器名

### 4. 删除容器

bash
    docker rm 容器名
    # 删除所有停止的容器
    docker rm $(docker ps -aq)

### 5. 进入正在运行的容器内部

调试用！

bash
    docker exec -it insurance-api bash

### 6. 查看容器运行日志（排错神器）

bash
    docker logs 容器名称
    # 实时持续刷新日志
    docker logs -f insurance-api

### 7. 拷贝 文件：宿主机 ↔ 容器

bash
    # 容器文件复制到本机
    docker cp insurance-api:/app/log.txt ./log.txt
    # 本机文件传到容器
    docker cp ./static insurance-api:/app/

* * *

三、辅助常用命令
--------

bash
    # 查看docker整体信息
    docker info
    # 查看版本
    docker -v
    # 清理无用资源（悬空镜像、停止容器）
    docker system prune



#### 4. 搭建

##### 步骤 1：项目根目录新建 Dockerfile

路径：`D:\wx26.7.14\7.30\Dockerfile`
    # 基础镜像，python运行环境     
    FROM python:3.11-slim     
    # 设置容器内工作目录     
    WORKDIR /app      
    # 1.先复制依赖文件（利用docker缓存，修改代码不用重复装包）     
    COPY requirements.txt .      
    # 安装依赖，使用清华源加速     
    RUN pip install -r requirements.txt  https://pypi.tuna.tsinghua.edu.cn/simple      
    # 2.复制全部项目代码到容器内 /app     
    COPY . .      
    # 声明对外端口（仅仅标记，不会自动映射端口）     
    EXPOSE 5000      
    # 容器启动执行命令     
    CMD ["python", "run.py"]

##### 步骤 2：新建 .dockerignore（重要！减少镜像体积、避免冲突）

同目录创建 `.dockerignore`

plaintext
    __pycache__
    venv
    *.env
    *.git
    *.md
    .DS_Store

> 作用：不要把本地虚拟环境 venv 打包进镜像！很多新手踩这个大坑

###### 步骤 3：打开 PowerShell，进入项目目录

powershell
    cd D:\wx26.7.14\7.30
步骤 4：构建镜像

---------

powershell
    # -t 镜像名称:版本
    docker build -t insurance-flask:v1 .

* 末尾 `.` 代表使用**当前目录**寻找 Dockerfile，不能省略！

* 等待执行完毕，没有报错 = 构建成功
  查看镜像：

powershell
    docker images
步骤 5：启动容器（核心部署命令）

-----------------

powershell
    docker run -d `
    --name insurance-api `
    -p 5000:5000 `
    insurance-flask:v1

参数解释：

* `-d`：后台静默运行
* `--name insurance-api`：自定义容器名字
* `-p 宿主机端口:容器内部端口` 顺序千万别写反

> 容器内程序监听 5000，电脑本机访问 [localhost:5000](https://link.wtturl.cn/?target=https%3A%2F%2Flocalhost%3A5000&scene=im&aid=497858&lang=zh "autolink")

### 常用调试命令

##### powershell     # 查看运行中的容器

##### docker ps     # 实时查看日志（排错最重要）

##### docker logs -f insurance-api      # 进入容器内部终端调试

##### docker exec -it insurance-api bash      # 停止服务

##### docker stop insurance-api      # 删除容器（修改镜像后需要重建容器）     docker rm insurance-api ⚠️ 重点问题：环境变量 .env

现在代码读取 `.env` 文件存放密钥（JWT_SECRET_KEY）

两种方案任选其一：
方案 A（开发简单）挂载.env 文件

-------------------

powershell
    docker run -d `
    --name insurance-api `
    -p 5000:5000 `
    -v ${PWD}/.env:/app/.env `
    insurance-flask:v1

`-v` 挂载：宿主机.env 文件直接映射到容器内部
方案 B（生产推荐）启动时直接注入环境变量，不用.env 文件

-------------------------------

powershell
    docker run -d `
    --name insurance-api `
    -p 5000:5000 `
    -e JWT_SECRET_KEY="dfhawdvawdggqwdiqwcvewfwgdrfsadgerhew" `
    -e ACCESS_TOKEN_EXPIRE_MINUTES=30 `
    insurance-flask:v1
🚨数据库注意事项（你的项目关键点）
==================

情况 1：**SQLite 本地文件数据库**

容器删除后数据丢失！必须挂载数据库文件持久化：

powershell
    -v ${PWD}/data:/app/data

情况 2：**MySQL 外部数据库**

不要把 MySQL 放进容器，连接地址不要写 `127.0.0.1`

> docker 容器内的 127.0.0.1 是容器自己，**不是你的电脑本机**
> 
> Windows 宿主机地址固定使用：`host.docker.internal`

### 开发迭代流程（以后改代码标准操作）

1. 修改代码
2. 停止 + 删除旧容器

powershell
    docker stop insurance-api
    docker rm insurance-api

3. 重新构建镜像

powershell
    docker build -t insurance-flask:v1 .

4. 重新 run 启动容器

### 进阶：一键管理 docker-compose（推荐！）

项目新建 `docker-compose.yml`，以后只需要一句 `docker-compose up -d`

yaml
    version: "3.8"
    services:
      api:
        image: insurance-flask:v1
        build: .
        ports:
          - "5000:5000"
        volumes:
          - ./.env:/app/.env
        restart: always # 容器意外崩溃自动重启

启动：

powershell
    docker-compose up -d

停止：

powershell
    docker-compose down



---



# 深度学习



#### 一、网络基础结构

**网络层级**：输入层 → 隐藏层 → 输出层  
整套训练循环由【前向传播】+【反向传播】+【参数更新】构成



##### 1. 前向传播

数据从输入层开始，逐层计算，最终得到预测输出。  
**逐层公式**：

![55d2cb4b-8f19-4fc3-b684-d1fe85f9d599](file:///C:/Users/HP/Pictures/Typedown/55d2cb4b-8f19-4fc3-b684-d1fe85f9d599.png)

##### 2. 损失函数

衡量预测值 y^​ 与真实标签 y 之间的差距。

![eee32073-14de-4d0b-949f-de16ca0b7bfe](file:///C:/Users/HP/Pictures/Typedown/eee32073-14de-4d0b-949f-de16ca0b7bfe.png)



##### 3. 反向传播

利用链式法则，从输出层向输入层逐层计算损失对各参数（权重、偏置）的梯度。

![c079ae80-a63f-48a6-bf2f-f25c5a3baf0d](file:///C:/Users/HP/Pictures/Typedown/c079ae80-a63f-48a6-bf2f-f25c5a3baf0d.png)

##### 4. 参数更新（梯度下降）

![e79b8a0e-8679-4c1f-8df9-2ff06d300ba9](file:///C:/Users/HP/Pictures/Typedown/e79b8a0e-8679-4c1f-8df9-2ff06d300ba9.png)



### 二、激活函数

###### 核心作用（必背）

    **引入非线性**。  
    若无激活函数，多层神经网络等价于单层线性变换，无法拟合复杂函数。激活函数使网络具备非线性表达能力，从而解决非线性分类与回归问题!

1. **Sigmoid**
   公式：![\(\sigma(x)=\frac{1}{1+e^{-x}}\)](file:///C:/Users/HP/Downloads/55f6f0fd-737f-45ad-852d-8ca60ed8f98f.png)
* 曲线：S 形；输出区间 \((0,1)\)
* 特点：非零均值；深层网络两端容易**梯度消失**
2. **Tanh（双曲正切）**
   公式：![\(\tanh(x)=\frac{e^x-e^{-x}}{e^x+e^{-x}}\)](file:///C:/Users/HP/Downloads/712ee5f1-9465-4486-9b4d-1e030b66020c.png)
* 曲线：中心对称 S 型；输出区间 \((-1,1)\)
* 特点：零均值，收敛比 Sigmoid 更快；依然存在梯度消失
3. **ReLU**
   公式：![\(\text{ReLU}(x)=\max(0,x)\)](file:///C:/Users/HP/Downloads/f556d54b-8c98-4cc8-b824-e724b4b965a6.png)
* 曲线：负数直接置 0，正数线性上升
* 特点：计算简单；正数区间梯度恒定，缓解梯度消失；缺点：**神经元死亡**
4. **Leaky ReLU**
   公式：![\(\text{LeakyReLU}(x)=\max(\alpha x,x),\alpha\approx0.01\)](file:///C:/Users/HP/Downloads/9565af12-3fbd-49d0-aa3f-d5bc0574669c.png)
* 曲线：负数保留一条微小斜率直线
* 特点：解决 ReLU 神经元死亡问题

![fb67156d-198e-48c1-b3a1-2f2157668d3e](file:///C:/Users/HP/Downloads/fb67156d-198e-48c1-b3a1-2f2157668d3e.png)

#### 三、损失函数

    给定一个样本，模型输出预测值 y^ ，真实标签为 y，损失函数 L(y^,y) 计算它们之间的差异，结果是一个非负实数：
    
    损失值 → 0：预测完全正确
    
    损失值很大：预测偏差很大
    
    在训练时，我们会计算一个批量样本的平均损失，作为反向传播和参数更新的依据。

###### 3.1 常见的损失函数有哪些

     按任务类型分为三大类：回归损失、二分类损失、多分类损失。

![0d2fffd0-188e-4766-ae69-f6a7e21b3b79](file:///C:/Users/HP/Downloads/0d2fffd0-188e-4766-ae69-f6a7e21b3b79.png)

![1493849b-7bac-4265-82ef-e2e5502ae6e6](file:///C:/Users/HP/Downloads/1493849b-7bac-4265-82ef-e2e5502ae6e6.png)

![e8dd9f50-3e91-468a-803f-3c48b10a1f3e](file:///C:/Users/HP/Downloads/e8dd9f50-3e91-468a-803f-3c48b10a1f3e.png)

![900a88cb-d0fd-43f2-9a17-5065dc6db21b](file:///C:/Users/HP/Downloads/900a88cb-d0fd-43f2-9a17-5065dc6db21b.png)

##### 3.2 怎么使用（以 PyTorch 为例）

    1. 选择合适的损失函数
    回归 → nn.MSELoss()
    
    二分类 → nn.BCEWithLogitsLoss()
    
    多分类 → nn.CrossEntropyLoss()
    
    多标签分类 → nn.BCEWithLogitsLoss()
    
    2. 在训练循环中的基本用法
    python
    import torch
    import torch.nn as nn
    
    # 1. 定义损失函数
    criterion = nn.CrossEntropyLoss()
    
    # 2. 前向传播得到模型输出
    outputs = model(inputs)          # outputs 形状: (batch_size, num_classes)
    loss = criterion(outputs, labels)  # labels 形状: (batch_size,)，每个是类别索引
    
    # 3. 反向传播与优化
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    # 当前损失值可通过 loss.item() 查看
    print(f'Loss: {loss.item():.4f}')
    3. 重要注意事项
    输入要求：CrossEntropyLoss 要求模型输出不要经过 Softmax（它内部已含）；而 BCEWithLogitsLoss 同样不要提前加 Sigmoid。
    
    标签格式：多分类用整数类别索引（如 [2, 0, 1]）；二分类用浮点数 0 或 1；多标签用 0/1 的多维张量。
    
    样本不平衡：可在损失函数中设置 weight 参数，给予小类更大权重，例如 CrossEntropyLoss(weight=class_weights)。
    
    4. 自定义损失函数
    若需特殊逻辑，可继承 nn.Module 并实现 forward 方法。例如带权重的 MSE：
    
    python
    class WeightedMSE(nn.Module):
        def __init__(self, weight):
            super().__init__()
            self.weight = weight
    
        def forward(self, pred, target):
            return torch.mean(self.weight * (pred - target) ** 2)
    总结
    损失函数是模型优化的目标，选对损失函数直接影响收敛效果。
    
    一般原则：回归用 MSE（怕异常值用 Huber），二分类用 BCEWithLogitsLoss，多分类用 CrossEntropyLoss。
    
    使用时注意输入是否已经过激活函数，确保与损失函数要求匹配，并合理处理类别不平衡。

## 五.NLP 系列模型

1. 发展 
   
       NLP 模型经历了从统计语言模型 → 神经语言模型 → 预训练大模型的发展路径：
       
       统计语言模型（n-gram）—— 基于统计频率，无法捕捉长距离依赖
       
       神经语言模型（NNLM, Word2Vec）—— 用神经网络学词向量
       
       序列模型（RNN, LSTM, GRU）—— 处理变长序列，捕捉上下文
       
       编码器-解码器 + 注意力（Seq2Seq, Attention）—— 机器翻译等生成任务突破
       
       纯注意力机制（Transformer）—— 并行计算，长距离建模能力飞跃
       
       预训练 + 微调范式（BERT, GPT, T5）—— 先海量数据预训练，再下游任务微调
       
       大规模语言模型（GPT-3, ChatGPT, LLaMA）—— 涌现能力，上下文学习，多任务通用化
       
       二、基础词表示模型
       1. 神经网络语言模型（NNLM, 2003）
       输入前 n-1 个词，预测下一个词，同时产出词向量。
       
       结构：Embedding → 全连接 → Softmax。
       
       意义：首次用神经网络学出分布式词表示，但计算量大。
       
       2. Word2Vec（2013）
       轻量级，不用隐层，训练效率高。
       
       两种模式：
       
       CBOW：用上下文词预测中心词
       
       Skip-gram：用中心词预测上下文词
       
       训练技巧：负采样（Negative Sampling）、Hierarchical Softmax。
       
       结果：每个词获得固定维度向量，可做语义运算（如 king - man + woman ≈ queen）。
       
       缺点：静态词向量，无法处理一词多义。
       
       3. GloVe
       基于全局词共现矩阵分解，融合了统计信息，类似于矩阵分解与 Word2Vec 的结合。
       
       4. FastText
       引入子词（subword）信息，词向量为字符 n-gram 之和，可生成未登录词向量。
       
       三、序列模型（处理变长文本）
       1. RNN（循环神经网络）
       核心思想：每次输入一个词，隐状态 
       h
       t
       h 
       t
       ​
         融合当前词和过去信息。
       
       h
       t
       =
       tanh
       ⁡
       (
       W
       i
       h
       x
       t
       +
       W
       h
       h
       h
       t
       −
       1
       +
       b
       h
       )
       h 
       t
       ​
        =tanh(W 
       ih
       ​
        x 
       t
       ​
        +W 
       hh
       ​
        h 
       t−1
       ​
        +b 
       h
       ​
        )
       缺陷：梯度消失/爆炸，难以捕捉长距离依赖。
       
       2. LSTM（长短期记忆网络）
       引入三个门：遗忘门、输入门、输出门，以及细胞状态 
       c
       t
       c 
       t
       ​
        。
       
       有效缓解梯度消失，可记忆较长时间信息。
       
       参数多，计算相对复杂。
       
       3. GRU（门控循环单元）
       LSTM 简化版，合并细胞状态与隐状态，只有重置门和更新门。
       
       参数更少，效果接近 LSTM，训练更快。
       
       适用场景：文本分类、序列标注、语言模型等。
       
       四、编码器-解码器 + 注意力
       1. Seq2Seq 模型
       编码器（RNN/LSTM）将源句子压缩为上下文向量 
       c
       c，解码器根据 
       c
       c 逐词生成目标句子。
       
       瓶颈：所有信息压在定长向量 
       c
       c 上，长句效果差。
       
       2. 注意力机制（Attention）
       解码时动态搜索源句中相关部分，加权求和得到上下文向量，不再依赖单一 
       c
       c。
       
       Bahdanau Attention（加法注意力）和 Luong Attention（乘法注意力）。
       
       极大提升机器翻译等生成任务质量。
       
       3. Attention 本质
       Attention
       (
       Q
       ,
       K
       ,
       V
       )
       =
       softmax
       (
       Q
       K
       T
       d
       k
       )
       V
       Attention(Q,K,V)=softmax( 
       d 
       k
       ​
       
       ​
       
       QK 
       T
       
       ​
        )V
       Q（Query）、K（Key）、V（Value）：输入通过线性变换得到。
       
       计算 Q 与所有 K 的相似度（得分），经 softmax 得注意力权重，再对 V 加权求和。
       
       自注意力（Self-Attention）：Q, K, V 均来自同一输入，捕捉句子内部词与词的依赖关系。
       
       五、Transformer（2017）
       核心创新
       完全摒弃 RNN，仅用注意力机制，实现并行计算，训练速度大幅提升。
       
       位置编码（Positional Encoding）引入位置信息，因为注意力本身无法区分位置。
       
       结构
       编码器：6 个相同层，每层 = 多头自注意力 + 前馈网络，各子层有残差连接 & LayerNorm。
       
       解码器：6 个相同层，带掩码的自注意力 + 编码器-解码器交叉注意力 + 前馈网络。
       
       多头注意力
       多组 Q, K, V 并行注意，不同头关注不同表示子空间，最终拼接。
       
       优势
       长距离依赖直接通过注意力一次性建模，无递推。
       
       可扩展性强，成为预训练大模型的基础架构。
       
       六、预训练大模型（Pre-trained Language Models）
       范式：大规模无监督预训练 + 下游任务微调
       
       1. BERT（2018）
       双向 Transformer 编码器，仅用编码器。
       
       预训练任务：
       
       MLM（掩码语言模型）：随机遮盖部分词，用上下文预测这些词（迫使模型理解双向上下文）。
       
       NSP（下一句预测）：判断两句话是否为连续文本（句子级理解）。
       
       输入形式：[CLS] 句子1 [SEP] 句子2 [SEP]
       
       微调：在 [CLS] 输出上加分类层，或对序列标注使用每个 token 输出。
       
       缺点：预训练与微调不匹配（微调时没有 [MASK]），生成任务受限。
       
       2. GPT 系列
       GPT-1/2：单向（自回归）Transformer 解码器，从左到右预测下一个词。
       
       预训练任务：标准语言模型（给定前文预测下一词）。
       
       GPT-3：1750 亿参数，涌现上下文学习能力（In-context Learning），无需微调，通过提示（Prompt）和示例即可完成多种任务。
       
       ChatGPT/InstructGPT：引入 RLHF（基于人类反馈的强化学习），对齐人类偏好。
       
       生成能力强大，擅长对话、写作、代码生成。
       
       3. T5（Text-to-Text Transfer Transformer）
       将所有 NLP 任务统一为“文本到文本”格式（如翻译："translate English to German: Hello" → "Hallo"）。
       
       编码器-解码器结构，多任务混合预训练。
       
       4. XLNet
       排列语言模型，结合自回归和自编码优势，解决 BERT 预训练微调不一致问题。
       
       5. RoBERTa、ALBERT、ELECTRA
       RoBERTa：更大数据、更久训练、动态掩码等优化，性能超过 BERT。
       
       ALBERT：参数共享降低参数量。
       
       ELECTRA：用判别器代替生成器，提高效率。
       
       七、预训练大模型的应用方式
       微调（Fine-tuning）：在预训练模型上加特定任务层，整体或部分参数继续训练。
       
       特征提取：冻结预训练模型，仅训练附加分类层（类似 ELMo）。
       
       提示学习（Prompt Tuning）：将任务重构为填空或续写形式，不改变模型参数或少调参。
       
       上下文学习（In-Context Learning）：仅通过输入示例让模型“学会”任务，无需参数更新（大模型特有）。
       
       八、核心模型对比表
       模型    架构    方向    预训练任务    擅长任务
       Word2Vec    浅层网络    -    CBOW/Skip-gram    词向量
       LSTM/GRU    循环网络    单向/双向    下一个词预测等    序列标注、分类
       Seq2Seq+Attention    RNN+Attention    单向    条件语言模型    翻译、摘要
       Transformer    自注意力    无方向    随机    几乎所有任务的基础
       BERT    Transformer 编码器    双向    MLM+NSP    文本理解（分类、QA）
       GPT-3/4    Transformer 解码器    单向（自回归）    下一个词预测    生成、对话、通用
       T5    编码器-解码器    双向/单向    多任务 Span 破坏    各类 text2text
       LLaMA    解码器    单向    下一个词预测    开源高效大模型
       九、关键概念补充
       词嵌入与上下文嵌入：Word2Vec 是静态的，BERT/GPT 是动态上下文相关的。
       
       Tokenization：BPE（字节对编码）、WordPiece 等，将词拆分为子词，平衡词表大小与未登录词。
       
       位置编码：绝对位置编码（正余弦）、可学习位置编码、相对位置编码等。
       
       注意力机制变体：多头注意力、稀疏注意力、Flash Attention 等。
       
       缩放定律（Scaling Law）：模型越大、数据越多，性能越好；但存在涌现能力门槛。
       
       此笔记覆盖了从基础词向量到当前主流大模型的完整技术演进，可作为深度学习 NLP 方向的复习框架。需要深入任何具体模型或机制，可以继续拆解。
   
   

##### 2. 基础词表示模型

    . 神经网络语言模型（NNLM, 2003）
    输入前 n-1 个词，预测下一个词，同时产出词向量。
    
    结构：Embedding → 全连接 → Softmax。
    
    意义：首次用神经网络学出分布式词表示，但计算量大。
    
    2. Word2Vec（2013）
    轻量级，不用隐层，训练效率高。
    
    两种模式：
    
    CBOW：用上下文词预测中心词
    
    Skip-gram：用中心词预测上下文词
    
    训练技巧：负采样（Negative Sampling）、Hierarchical Softmax。
    
    结果：每个词获得固定维度向量，可做语义运算（如 king - man + woman ≈ queen）。
    
    缺点：静态词向量，无法处理一词多义。
    
    3. GloVe
    基于全局词共现矩阵分解，融合了统计信息，类似于矩阵分解与 Word2Vec 的结合。
    
    4. FastText
    引入子词（subword）信息，词向量为字符 n-gram 之和，可生成未登录词向量。

##### 3.序列模型（处理变长文本）

1.![da8ab50a-47b6-41e6-aa51-586312245f8e](file:///C:/Users/HP/Downloads/da8ab50a-47b6-41e6-aa51-586312245f8e.png)
    1. RNN（循环神经网络）
    核心思想：每次输入一个词，隐状态 ht
    缺陷：梯度消失/爆炸，难以捕捉长距离依赖。
    2. LSTM（长短期记忆网络）
    引入三个门：遗忘门、输入门、输出门，以及细胞状态 ct
    有效缓解梯度消失，可记忆较长时间信息。

    参数多，计算相对复杂。

    3. GRU（门控循环单元）
    LSTM 简化版，合并细胞状态与隐状态，只有重置门和更新门。

    参数更少，效果接近 LSTM，训练更快。
    适用场景：文本分类、序列标注、语言模型等。

##### 4.**编码器-解码器 + 注意力**

###### 1. Seq2Seq 模型

* 编码器（RNN/LSTM）将源句子压缩为上下文向量 c，解码器根据 c 逐词生成目标句子。

* **瓶颈**：所有信息压在定长向量 c 上，长句效果差。

###### 2. 注意力机制（Attention）

* 解码时动态搜索源句中相关部分，加权求和得到上下文向量，不再依赖单一 c。

* **Bahdanau Attention**（加法注意力）和 **Luong Attention**（乘法注意力）。

* 极大提升机器翻译等生成任务质量。

###### 3. Attention 本质

![e76b38d9-cd59-4c88-bdc4-a7a60c234cbb](file:///C:/Users/HP/Downloads/e76b38d9-cd59-4c88-bdc4-a7a60c234cbb.png)

* Q（Query）、K（Key）、V（Value）：输入通过线性变换得到。

* 计算 Q 与所有 K 的相似度（得分），经 softmax 得注意力权重，再对 V 加权求和。

* 自注意力（Self-Attention）：Q, K, V 均来自同一输入，捕捉句子内部词与词的依赖关系。
  
  

##### 5. Transformer

    核心创新
    完全摒弃 RNN，仅用注意力机制，实现并行计算，训练速度大幅提升。
    
    位置编码（Positional Encoding）引入位置信息，因为注意力本身无法区分位置

    结构
    编码器：6 个相同层，每层 = 多头自注意力 + 前馈网络，各子层有残差连接 & LayerNorm。
    
    解码器：6 个相同层，带掩码的自注意力 + 编码器-解码器交叉注意力 + 前馈网络。

    多头注意力
    多组 Q, K, V 并行注意，不同头关注不同表示子空间，最终拼接。
    
    优势
    长距离依赖直接通过注意力一次性建模，无递推。
    
    可扩展性强，成为预训练大模型的基础架构。



##### 6. 预训练大模型（Pre-trained Language Models）

###### 范式：   ****大规模无监督预训练 + 下游任务微调****

    1. BERT（2018）
    双向 Transformer 编码器，仅用编码器。
    
    预训练任务：
    
    MLM（掩码语言模型）：随机遮盖部分词，用上下文预测这些词（迫使模型理解双向上下文）。
    
    NSP（下一句预测）：判断两句话是否为连续文本（句子级理解）。
    
    输入形式：[CLS] 句子1 [SEP] 句子2 [SEP]
    
    微调：在 [CLS] 输出上加分类层，或对序列标注使用每个 token 输出。
    
    缺点：预训练与微调不匹配（微调时没有 [MASK]），生成任务受限。
    
    2. GPT 系列
    GPT-1/2：单向（自回归）Transformer 解码器，从左到右预测下一个词。
    
    预训练任务：标准语言模型（给定前文预测下一词）。
    
    GPT-3：1750 亿参数，涌现上下文学习能力（In-context Learning），无需微调，通过提示（Prompt）和示例即可完成多种任务。
    
    ChatGPT/InstructGPT：引入 RLHF（基于人类反馈的强化学习），对齐人类偏好。
    
    生成能力强大，擅长对话、写作、代码生成。
    
    3. T5（Text-to-Text Transfer Transformer）
    将所有 NLP 任务统一为“文本到文本”格式（如翻译："translate English to German: Hello" → "Hallo"）。
    
    编码器-解码器结构，多任务混合预训练。
    
    4. XLNet
    排列语言模型，结合自回归和自编码优势，解决 BERT 预训练微调不一致问题。
    
    5. RoBERTa、ALBERT、ELECTRA
    RoBERTa：更大数据、更久训练、动态掩码等优化，性能超过 BERT。
    
    ALBERT：参数共享降低参数量。
    
    ELECTRA：用判别器代替生成器，提高效率。

##### 7.预训练大模型的应用方式

* **微调（Fine-tuning）**：在预训练模型上加特定任务层，整体或部分参数继续训练。

* **特征提取**：冻结预训练模型，仅训练附加分类层（类似 ELMo）。

* **提示学习（Prompt Tuning）**：将任务重构为填空或续写形式，不改变模型参数或少调参。

* **上下文学习（In-Context Learning）**：仅通过输入示例让模型“学会”任务，无需参数更新（大模型特有）。

* * *

##### 八、核心模型对比表

| 模型                | 架构              | 方向      | 预训练任务          | 擅长任务         |
| ----------------- | --------------- | ------- | -------------- | ------------ |
| Word2Vec          | 浅层网络            | -       | CBOW/Skip-gram | 词向量          |
| LSTM/GRU          | 循环网络            | 单向/双向   | 下一个词预测等        | 序列标注、分类      |
| Seq2Seq+Attention | RNN+Attention   | 单向      | 条件语言模型         | 翻译、摘要        |
| Transformer       | 自注意力            | 无方向     | 随机             | 几乎所有任务的基础    |
| BERT              | Transformer 编码器 | 双向      | MLM+NSP        | 文本理解（分类、QA）  |
| GPT-3/4           | Transformer 解码器 | 单向（自回归） | 下一个词预测         | 生成、对话、通用     |
| T5                | 编码器-解码器         | 双向/单向   | 多任务 Span 破坏    | 各类 text2text |
| LLaMA             | 解码器             | 单向      | 下一个词预测         | 开源高效大模型      |

* * *


--------
