### 多态

##### 1.1 定义：同一个方法不同对象调用，表现不一样的行为就是多态

##### 1.2 前提：①： 存在**继承**：子类继承父类

                    ②：子类**重写父类方法**：子类写了和父类一模一样名字的方法

    class AIModel:
        # 父类通用方法
        def predict(self):
            print("通用模型推理")
    
    # 子类1：文本模型，重写predict
    class TextModel(AIModel):
        def predict(self):
            print("生成文本内容")
    
    # 子类2：图像模型，重写predict
    class ImageModel(AIModel):
        def predict(self):
            print("识别图片内容")
    
    # 统一处理函数：只要求传入AIModel类型的对象
    def run_model(model: AIModel):
        # 同一个predict，不同对象行为不同 → 多态
        model.predict()
    
    # 调用
    run_model(TextModel())   # 输出：生成文本内容
    run_model(ImageModel())  # 输出：识别图片内容

### 2.数据库的使用



### 3.SQLAlchemy ORM 知识点映射



##### 3.1 ORM 定义与映射关系

### 概念

ORM = 对象关系映射（Object Relational Mapping），核心作用：**Python 对象 ↔ 关系型数据库表自动映射**，开发者无需手写原生 SQL，用面向对象语法操作数据库。

### 三层核心映射对应

1. Python 类 → 数据库**数据表**（一张类对应一张物理表）
2. 类属性 → 数据表**字段 / 列**（类内定义的 Column 映射表字段、类型、约束）
3. 类实例对象 → 表中**单行数据**（实例 = 一条记录，修改实例属性等价于 update 行数据）





##### 3.2 选择 SQLAlchemy 的 4 大核心优势

1. **多数据库兼容**
   支持 MySQL / SQLite / PostgreSQL，切换底层数据库仅需修改连接串，业务 CRUD 代码完全不用改动；PostgreSQL 可搭配 pgvector 扩展实现向量存储。

2. **防 SQL 注入，安全性更高**
   ORM 底层使用参数化预编译语句，不会直接拼接用户输入字符串，从根源杜绝 SQL 注入漏洞，优于手动拼接原生 SQL。

3. **面向对象，代码易维护**
   抛弃复杂 SQL 字符串，用类、对象、方法完成增删改查，可读性强，大型项目维护成本更低。

4. **全 Python 后端生态标配**
   
   * Web 框架：Flask、FastAPI、Django（Django 自带 ORM，但外部项目通用 SQLAlchemy）
   * 其他场景：爬虫数据持久化、数据分析存储、微服务数据层

#### 3.3 SQLAlchemy 三大核心组件（2.0 声明式用法）

###### 1. `create_engine`

    数据库连接引擎，整个 ORM 的入口；负责管理连接池、驱动、数据库地址、字符集，所有操作都基于引擎建立连接。
    示例：
    
    python
    
    运行 from sqlalchemy import create_engine engine = create_engine("mysql+pymysql://user:pass@127.0.0.1:3306/test_db")



### 2. `declarative_base`

    模型基类，所有自定义数据表模型类**必须继承这个基类**；Base 会自动收集所有子类，统一管理表结构，可一键创建 / 删除全部数据表。示例：
    
    python
    
    运行 from sqlalchemy.orm import declarative_base Base = declarative_base() # 自定义表模型 class User(Base): __tablename__ = "user" # 映射数据库真实表名 id = Column(Integer, primary_key=True) name = Column(String(50))



###### 3. `sessionmaker`

    
