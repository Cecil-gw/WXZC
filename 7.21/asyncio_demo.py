import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, text
from typing import AsyncGenerator

# 数据库配置
DB_USER = "root"
DB_PWD = "123456"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "job_db"

# 1. 无数据库的根连接，用来新建数据库
ROOT_DB_URL = f"mysql+aiomysql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4"
# 2. 业务库连接（需要job_db存在）
ASYNC_DB_URL = f"mysql+aiomysql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# ---------------- 第一步：先自动创建数据库 job_db ----------------
async def create_database_if_not_exists():
    # 临时根引擎，不指定数据库
    root_engine = create_async_engine(ROOT_DB_URL, echo=False)
    async with root_engine.connect() as conn:
        # 执行建库SQL，不存在则创建
        await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4;"))
        print(f"数据库 {DB_NAME} 校验/创建完成")
    await root_engine.dispose()

# ---------------- 业务引擎、会话、ORM基类、模型 ----------------
engine = create_async_engine(
    ASYNC_DB_URL,
    echo=True,
    pool_size=10
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

class JobPost(Base):
    __tablename__ = "job_post"

    id = Column(
        Integer, primary_key=True, autoincrement=True, comment="主键自增ID"
    )
    title = Column(String(30), nullable=False, comment="岗位标题")
    company = Column(String(50), nullable=False, comment="公司名称")
    salary = Column(Integer, comment="薪资")

# ---------------- 创建数据表 ----------------
async def create_tables():
    async with engine.begin() as conn:
        # 测试环境清空旧表，正式项目删掉 drop_all 这一行
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("数据表 job_post 创建完成")

# 获取会话（FastAPI 依赖注入用）
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# 程序入口
if __name__ == "__main__":
    # 先建库，再建表，顺序不能颠倒
    asyncio.run(create_database_if_not_exists())
    asyncio.run(create_tables())