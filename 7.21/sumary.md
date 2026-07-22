### 7.21

    导入库 import pymysql
    建立数据库连接 pymysql.connect()
    创建游标对象 cursor = conn.cursor()（用来执行 SQL）
    写 SQL 语句，cursor.execute(sql) 执行
    查询语句用 fetchall()/fetchone() 拿结果；增删改要 conn.commit()
    收尾：先关游标，再关连接
    
    
    import pymysql
    
    # 1.连接
    conn = pymysql.connect(host="localhost",port=3306,user="root",password="123456",database="text",charset="utf8mb4")
    cursor = conn.cursor()
    
    # 2.执行查询sql
    sql = "SELECT * FROM teacher;"
    cursor.execute(sql)
    
    # 3.取出全部结果
    data = cursor.fetchall()
    print(data)
    
    # 4.关闭
    cursor.close()
    conn.close()
    
    #插入
    
    
    import pymysql
    conn = pymysql.connect(host="localhost",port=3306,user="root",password="123456",database="text",charset="utf8mb4")
    cursor = conn.cursor()
    
    # 占位符%s防注入，不要字符串拼接
    sql = "INSERT INTO teacher(tname,subject,salary) VALUES (%s,%s,%s)"
    cursor.execute(sql, ("张三","数学",8000))
    
    # 提交保存！不写数据库无数据
    conn.commit()
    
    cursor.close()
    conn.close()
    
    #删改
    
    
    sql = "UPDATE teacher SET salary=9000 WHERE tid=%s"
    cursor.execute(sql, (1,))
    conn.commit()
    
    sql2 = "DELETE FROM teacher WHERE tid=%s"
    cursor.execute(sql2, (1,))
    conn.commit()
    
    #建表
    
    create_sql = """
    CREATE TABLE IF NOT EXISTS teacher(
        tid INT PRIMARY KEY AUTO_INCREMENT,
        tname VARCHAR(20)
    )
    """
    cursor.execute(create_sql)
    
    一、创建数据库
    python
    运行
    # IF NOT EXISTS 避免重复创建报错
    create_db_sql = "CREATE DATABASE IF NOT EXISTS text DEFAULT CHARSET utf8mb4;"
    cursor.execute(create_db_sql)
    
    # 切换到新建的库，后续操作表都要先选库
    cursor.execute("USE text;")
    二、创建数据表 teacher
    python
    运行
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS teacher (
        tid INT PRIMARY KEY AUTO_INCREMENT COMMENT '教师编号',
        tname VARCHAR(20) NOT NULL COMMENT '姓名',
        subject VARCHAR(20) COMMENT '科目',
        salary INT COMMENT '薪资',
        entry_time DATETIME DEFAULT NOW()
    );
    """
    cursor.execute(create_table_sql)
    print("表创建完成")
    三、增加数据 INSERT（必须 commit）
    单条插入
    python
    运行
    insert_sql = "INSERT INTO teacher(tname, subject, salary) VALUES (%s, %s, %s)"
    cursor.execute(insert_sql, ("张三", "语文", 7500))
    conn.commit()  # 增删改必须提交
    批量插入
    python
    运行
    data_list = [
        ("李四", "数学", 8200),
        ("王五", "英语", 7800)
    ]
    cursor.executemany(insert_sql, data_list)
    conn.commit()
    四、查询数据 SELECT（不用 commit）
    python
    运行
    select_sql = "SELECT * FROM teacher;"
    cursor.execute(select_sql)
    
    # 1. 取全部数据
    all_data = cursor.fetchall()
    print("全部数据：", all_data)
    
    # 2. 只取第一条
    one_data = cursor.fetchone()
    # 3. 取前2条
    two_data = cursor.fetchmany(2)
    
    # 条件查询
    sql2 = "SELECT tname,salary FROM teacher WHERE salary > %s"
    cursor.execute(sql2, (8000,))
    print("高薪老师：", cursor.fetchall())
    五、修改数据 UPDATE
    python
    运行
    update_sql = "UPDATE teacher SET salary=%s WHERE tid=%s"
    cursor.execute(update_sql, (9000, 1))
    conn.commit()
    print(f"修改行数：{cursor.rowcount}")
    六、删除数据 DELETE
    python
    运行
    delete_sql = "DELETE FROM teacher WHERE tid=%s"
    cursor.execute(delete_sql, (3,))
    conn.commit()
    print(f"删除行数：{cursor.rowcount}")
    七、收尾释放资源
    python
    运行
    cursor.close()
    conn.close()

### 3. SQLAIchemyORM

##### 3.1 常见字段类型（Python ↔ MySQL 映射）

    SQLAlchemy 类型   MySQL对应类型        使用场景                        补充说明
    Integer              int      主键 ID、数字编号       整数类型，主键默认搭配自增
    String               varchar    姓名、手机号、文本短字符串        必须指定长度 String(64)
    Float                float      分数、薪资、小数    ⚠️生产环境不推荐，精度丢失；金额建议用Decimal
    Datetime        datetime      创建时间、更新时间        存储年月日时分秒，可搭配default=datetime.now自动填充时间

##### 3.2 常用字段约束（Column 参数）

    1. primary_key = True
    作用：将当前字段设为主键，表内唯一标识每条数据
    特性：主键自带NOT NULL非空特性，一张表可多字段组成复合主键
    示例：id = Column(Integer, primary_key=True)
    2. autoincrement=True
    作用：开启自增，仅整数主键使用，MySQL 对应AUTO_INCREMENT
    注意：SQLAlchemy 中 Integer 主键默认自动开启自增，可手动关闭autoincrement=False
    3. nullable=False
    作用：非空约束，插入数据时该字段必须传值，数据库禁止存 NULL
    默认值：nullable=True（允许为空）
    4. unique=True
    作用：唯一约束，整张表该字段值不能重复（手机号、用户名、邮箱）
    区分：主键自带唯一，unique 用于非主键字段的唯一性校验
    5. default=默认值
    文档笔误：dafault → 正确拼写 default
    作用：插入数据不传该字段时，自动填充预设值
    两种用法：
    固定值：status = Column(Integer, default=1)
    动态函数（时间）：create_time = Column(Datetime, default=datetime.now)

##### 3.3 数据表创建 / 删除核心方法

    Base.metadata.create_all(bind=engine)
    功能：扫描所有 ORM 模型，只创建不存在的表，已有表不会覆盖、不会删除数据
    参数bind：绑定数据库连接引擎engine，指定要操作的数据库
    使用场景：项目初始化、首次启动建表
    Base.metadata.drop_all(bind=engine)
    功能：删除当前库所有由 Base 管理的数据表，表内数据全部清空，不可恢复
    ⚠️高危警告：仅单元测试、本地调试使用，生产环境绝对禁用

##### 3.4 区分conn与cursor

    1. conn 连接对象（通道）
    python
    运行
    # 初始化创建连接
    self.conn = pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        port=3306,
        charset="utf8mb4"
    )
    conn 专属方法：
    conn.cursor()：生成游标
    conn.commit()：提交事务（保存增删改操作）
    conn.rollback()：回滚事务（撤销未提交操作）
    conn.close()：关闭数据库通道
    
    2. cursor 游标对象（执行工具）
    python
    运行
    self.cursor = self.conn.cursor()
    cursor 专属方法：
    cursor.execute(sql, 参数元组)：执行 SQL 语句
    cursor.fetchone()：查询结果取第一条
    cursor.fetchall()：查询结果取全部
    cursor.rowcount：获取增删改影响的数据行数
    cursor.close()：关闭游标





### 4 异步异步 SQLAlchemy 完整知识点

##### 4.1 定义：

##### SQLAlchemy = Python 操作 MySQL 的**ORM 工具**

* 同步版：普通接口、脚本用，数据库查询时会卡住整个程序，等待数据库返回结果，这段时间程序啥都干不了
* **异步 SQLAlchemy**：搭配 `aiomysql` 驱动，用异步 IO，查数据库的时候程序不会卡死，可以同时处理很多请求，专门给 FastAPI 这种高并发后端接口用。

##### 4.2 作用：

###### 两个核心作用

1. **不用手写原生 SQL 字符串**：写 Python 类 / 对象就能自动映射数据库表，不用拼`INSERT/UPDATE`，减少 SQL 注入、拼写错误；
2. **异步非阻塞**：高并发场景（网站、接口）同时来几百个请求，不会因为查数据库导致服务器卡顿。

##### 4.3 语法’

    # 导入包
    import asyncio
    # 异步专用引擎、异步会话、异步会话工厂
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    # ORM基类
    from sqlalchemy.orm import declarative_base
    # 字段类型
    from sqlalchemy import Column, Integer, String, text
    
    
    ·····
    asyncio：Python 官方异步库，所有异步代码都要靠它运行；
    
    create_async_engine：创建异步数据库连接引擎（相当于和 MySQL 建立通道）；
    
    AsyncSession：异步会话，你所有增删改查操作都要靠会话；
    
    async_sessionmaker：会话工厂，批量生成干净的数据库会话；
    
    declarative_base()：ORM 父类，所有数据表都要继承它；
    
    Column/Integer/String：定义表的字段、字段类型；
    
    text()：用来写原生 SQL 语句（比如我们自动建数据库那段）。
    
    ···

##### 4.4 数据库连接地址 URL

    ROOT_DB_URL = f"mysql+aiomysql://root:123456@localhost:3306/?charset=utf8mb4"
    ASYNC_DB_URL = f"mysql+aiomysql://root:123456@localhost:3306/job_db?charset=utf8mb4
    
    格式拆解：
    驱动://账号:密码@数据库地址:端口/数据库名?编码
    mysql+aiomysql：固定，代表异步连接 MySQL；同步是mysql+pymysql；
    root:123456：你的 MySQL 账号密码；
    localhost:3306：本地数据库，端口默认 3306；
    /job_db：指定要操作的数据库；不带库名就是只登录 MySQL 服务，用来新建数据库。"

##### 4.5 create_async_engine 异步引擎

    engine = create_async_engine(ASYNC_DB_URL, echo=True, pool_size=10)
    
    建立程序和 MySQL 之间的长连接通道，内置连接池，不用每次查库都重新连一次数据库。
    参数：
    echo=True：打印底层执行的 SQL，方便你调试，上线关掉；
    pool_size=10：连接池存 10 条数据库通道，多个请求可以复用。

##### 4.6 async_sessionmaker 异步会话工厂

    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    
    生产数据库会话session，session 是你操作数据库的 “操作台”，新增、查询、修改都要用它。
    关键参数：
    class_=AsyncSession：强制用异步会话，同步 Session 不能在异步代码里跑；
    expire_on_commit=False：异步必配，提交数据后不会清空对象，不然查不到刚插入的数据。

##### 例题：完整可运行异步 SQLAlchemy 例题（包含：自动建库 + 建表 + 增删改查 + 事务回滚）

    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.orm import declarative_base
    from sqlalchemy import Column, Integer, String, text, select, update, delete
    
    # ===================== 数据库配置 =====================
    DB_USER = "root"
    DB_PWD = "123456"
    DB_HOST = "localhost"
    DB_PORT = 3306
    DB_NAME = "job_db"
    
    # 1. 无库连接：用来新建数据库
    ROOT_URL = f"mysql+aiomysql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4"
    # 2. 业务库连接：操作job_db里的表
    DB_URL = f"mysql+aiomysql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    
    # ===================== 1. 异步引擎 =====================
    engine = create_async_engine(
        DB_URL,
        echo=True,
        pool_size=10
    )
    
    # ===================== 2. 异步会话工厂 =====================
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # ===================== 3. ORM基类 =====================
    Base = declarative_base()
    
    # ===================== 4. 数据表模型 JobPost 岗位表 =====================
    class JobPost(Base):
        __tablename__ = "job_post"
    
        id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
        title = Column(String(30), nullable=False, comment="岗位名称")
        company = Column(String(50), nullable=False, comment="公司名")
        salary = Column(Integer, comment="薪资")
    
    # ===================== 工具函数1：自动创建数据库job_db =====================
    async def create_db():
        root_engine = create_async_engine(ROOT_URL, echo=False)
        async with root_engine.connect() as conn:
            # 原生SQL必须用text()包裹
            await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4;"))
            print(f"✅ 数据库 {DB_NAME} 创建/校验完成")
        await root_engine.dispose()
    
    # ===================== 工具函数2：创建数据表 =====================
    async def create_table():
        async with engine.begin() as conn:
            # 测试环境删除旧表，正式项目删掉这行
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("✅ job_post 数据表创建完成")
    
    # ===================== CRUD 增删改查示例 =====================
    # 新增岗位
    async def add_job():
        async with AsyncSessionLocal() as session:
            try:
                job = JobPost(title="Python后端", company="字节跳动", salary=26000)
                session.add(job)
                await session.commit()
                # refresh：从数据库刷新数据，拿到自增id
                await session.refresh(job)
                print(f"✅ 新增成功，岗位ID：{job.id}")
            except Exception as e:
                await session.rollback()
                print(f"❌ 新增失败，已回滚：{e}")
    
    # 查询所有岗位
    async def query_all():
        async with AsyncSessionLocal() as session:
            stmt = select(JobPost)
            result = await session.execute(stmt)
            job_list = result.scalars().all()
            print("\n===== 所有岗位数据 =====")
            for item in job_list:
                print(f"ID:{item.id} | 岗位:{item.title} | 公司:{item.company} | 薪资:{item.salary}")
    
    # 修改岗位薪资
    async def update_job(job_id: int, new_salary: int):
        async with AsyncSessionLocal() as session:
            try:
                stmt = update(JobPost).where(JobPost.id == job_id).values(salary=new_salary)
                await session.execute(stmt)
                await session.commit()
                print(f"\n✅ ID={job_id} 薪资修改完成")
            except Exception as e:
                await session.rollback()
                print(f"❌ 修改失败：{e}")
    
    # 删除岗位
    async def delete_job(job_id: int):
        async with AsyncSessionLocal() as session:
            try:
                stmt = delete(JobPost).where(JobPost.id == job_id)
                await session.execute(stmt)
                await session.commit()
                print(f"\n✅ ID={job_id} 岗位已删除")
            except Exception as e:
                await session.rollback()
                print(f"❌ 删除失败：{e}")
    
    # ===================== 事务演示：全部成功 / 出错全回滚 =====================
    async def transaction_demo():
        async with AsyncSessionLocal() as session:
            try:
                # 操作1：新增一条岗位
                job1 = JobPost(title="Java开发", company="阿里巴巴", salary=30000)
                session.add(job1)
                # 操作2：修改id=1的薪资
                update_stmt = update(JobPost).where(JobPost.id == 1).values(salary=29000)
                await session.execute(update_stmt)
    
                # 手动制造异常，取消注释会触发回滚，两条操作全部失效
                # 1 / 0
    
                await session.commit()
                print("\n✅ 事务全部执行成功，数据已入库")
            except Exception as e:
                await session.rollback()
                print(f"\n❌ 事务异常 {e}，所有操作已回滚，数据库无改动")
    
    # ===================== 统一主入口（只执行一次asyncio.run，解决循环关闭报错） =====================
    async def main():
        # 1. 先建数据库
        await create_db()
        # 2. 建数据表
        await create_table()
        # 3. 增删改查测试
        await add_job()
        await query_all()
        await update_job(job_id=1, new_salary=28000)
        await query_all()
        # 4. 事务测试
        await transaction_demo()
        await query_all()
        # 5. 释放数据库连接
        await engine.dispose()
    
    if __name__ == "__main__":
        asyncio.run(main())

### 5 ORM

##### 5.1 ORM

SQLAlchemy 是 Python 的 **ORM（对象关系映射）** 工具。它的核心思想是：

> **把数据库的"表"映射成 Python 的"类"**
> 
> **把表里的"行"映射成类的"实例"**

这样你就可以用操作 Python 对象的方式，来间接操作数据库。

    ┌─────────────────────────────────────────┐
    │  Base = declarative_base()              │
    │  （地基：所有表模型都要继承它）            │
    └─────────────────────────────────────────┘
                        │
            ┌───────────┼───────────┐
            ▼           ▼           ▼
       ┌────────┐  ┌────────┐  ┌────────┐
       │JobPost │  │  User  │  │ Order  │  ← 类 = 数据库表
       │ 类     │  │  类    │  │  类    │
       └────────┘  └────────┘  └────────┘
            │
       ┌────┴────┬────────┬────────┬────────┐
       ▼         ▼        ▼        ▼        ▼
     Column   Column   Column   Column   Column
       │         │        │        │        │
     Integer   String   Float    Text   DateTime
     (整数)   (字符串)  (小数)  (长文本) (日期时间)
       │         │        │        │        │
      id      title   salary   jd_text  create_time

##### 5.2 asyncio
