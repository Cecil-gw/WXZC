import time
import random
import asyncio

# ===================== 公共模型 + 生成模拟数据函数 =====================
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()#diji

class JobPost(Base):
    __tablename__ = "job_post"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    title = Column(String(100), nullable=False, comment="职位名称")
    company = Column(String(100), nullable=False, comment="公司名称")
    salary_min = Column(Float, default=0, comment="最低薪资(k)")
    salary_max = Column(Float, default=0, comment="最高薪资(k)")
    experience = Column(String(50), default="不限", comment="经验要求")
    jd_text = Column(Text, comment="职位描述原文")
    vector_id = Column(String(100), comment="关联向量ID")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<JobPost({self.title})@{self.company}>"

# 题目要求：构造count条模拟岗位数据
def generate_jobs(count=1000):
    title_pool = ["Python开发", "Java后端", "前端开发", "算法工程师", "测试开发", "运维", "Go后端"]
    company_pool = ["字节跳动", "阿里巴巴", "腾讯", "百度", "美团", "华为", "小米"]
    exp_pool = ["1年以内", "1-3年", "3-5年", "5年以上", "不限"]
    data_list = []
    for _ in range(count):
        job = JobPost(
            title=random.choice(title_pool),
            company=random.choice(company_pool),
            salary_min=round(random.uniform(6, 22), 1),
            salary_max=round(random.uniform(22, 55), 1),
            experience=random.choice(exp_pool),
            jd_text="负责后端业务开发，熟练使用MySQL、Redis、消息中间件",
            vector_id=f"vec_{random.randint(10000, 99999)}"
        )
        data_list.append(job)
    return data_list

# ===================== 同步 SQLAlchemy（pymysql） =====================
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SYNC_DB_URL = "mysql+pymysql://root:123456@localhost:3306/job_db?charset=utf8mb4"
sync_engine = create_engine(SYNC_DB_URL, echo=False)
SyncSession = sessionmaker(bind=sync_engine)

def sync_insert_test(total=1000):
    Base.metadata.drop_all(bind=sync_engine)
    Base.metadata.create_all(bind=sync_engine)
    job_list = generate_jobs(count=total)
    session = SyncSession()
    start_time = time.perf_counter()
    for job in job_list:
        session.add(job)
        session.commit()
    end_time = time.perf_counter()
    cost = end_time - start_time
    session.close()
    print(f"【同步逐条插入{total}条】耗时：{cost:.4f} 秒")

# ===================== 异步 SQLAlchemy（aiomysql）【修复bind】 =====================
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

ASYNC_DB_URL = "mysql+aiomysql://root:123456@localhost:3306/job_db?charset=utf8mb4"
async_engine = create_async_engine(ASYNC_DB_URL, echo=False)
# 修复点：只能写 bind= 不能写 engine=
AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

async def async_insert_test(total=1000):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    job_list = generate_jobs(count=total)
    async with AsyncSessionLocal() as db:
        start_time = time.perf_counter()
        for job in job_list:
            db.add(job)
            await db.commit()
        end_time = time.perf_counter()
        cost = end_time - start_time
        print(f"【异步逐条插入{total}条】耗时：{cost:.4f} 秒")
    await async_engine.dispose()

# ===================== 主程序 =====================
if __name__ == "__main__":
    insert_count = 1000
    print("===== 开始测试同步插入 =====")
    sync_insert_test(insert_count)

    print("\n===== 开始测试异步插入 =====")
    asyncio.run(async_insert_test(insert_count))