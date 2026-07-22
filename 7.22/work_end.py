import requests
from lxml import etree
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import pymysql
import time

# ===================== SQLAlchemy SQLite配置 =====================
engine = create_engine(r"sqlite:///D:/wx26.7.14/7.22/quote.db", echo=False)
Base = declarative_base()

class Quote(Base):
    """
    Quote类，数据模型
    """
    __tablename__ = "quote"
    id = Column(Integer, primary_key=True)
    quote = Column(String)
    author = Column(String)
    link = Column(String)

# 创建表（不存在则新建）
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0"
}

START_PAGE = 1
# END_PAGE = 3  # 不再固定结束页码，改为自动识别末尾
all_data = []
db = SessionLocal()

try:
    page = START_PAGE
    while True:
        url = f"http://quotes.toscrape.com/page/{page}/"
        resp = requests.get(url=url, headers=headers, timeout=5)
        print(f"第{page}页，状态码：{resp.status_code}")

        # 页面不存在/请求异常，终止分页循环
        if resp.status_code != 200:
            print("页面不存在，结束分页")
            break

        tree = etree.HTML(resp.text)
        quote_list = tree.xpath('//span[@class="text"]/text()')
        author_list = tree.xpath('//small[@class="author"]/text()')
        link_list = tree.xpath('//span/a/@href')

        # 当前页面没有数据 → 到达最后一页，退出循环
        if not quote_list:
            print("当前页面无数据，分页爬取完成")
            break

        print(f"====正在抓取第 {page} 页数据====")
        for q, a, l in zip(quote_list, author_list, link_list):
            print(f"{q}, {a} \n,{l}")
            one_data = Quote(quote=q, author=a, link=l)
            db.add(one_data)
            all_data.append((q, a, l))

        page += 1
        time.sleep(0.3)  # 分页间隔，友好爬虫

    # 全部页面抓取完成统一提交
    db.commit()
    print("====SQLite commit执行完毕====")

except requests.exceptions.Timeout:
    print("请求超时！")
except Exception as e:
    print("爬虫异常：", e)
    db.rollback()
finally:
    db.close()

# ===================== MySQL同步入库 =====================
if all_data:
    try:
        conn = pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            password="123456",
            database="quote",
            charset="utf8mb4"
        )
        cursor = conn.cursor()
        insert_sql = "insert into quote(quote, author, link) values(%s, %s, %s)"
        cursor.executemany(insert_sql, all_data)
        conn.commit()
        print(f"成功向MySQL插入 {len(all_data)} 条数据")
        cursor.close()
        conn.close()
    except Exception as err:
        print("MySQL写入失败：", err)
else:
    print("没有抓取到数据，跳过MySQL写入")