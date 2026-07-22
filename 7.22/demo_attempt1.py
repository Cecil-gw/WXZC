import requests
from lxml import etree
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import pymysql
import time

engine = create_engine(r"sqlite:///D:/wx26.7.14/7.22/quote.db", echo=False)
Base = declarative_base()

class Quote(Base):

    """
    Quote类，用于定义引用(Quote)的数据模型
    继承自Base类，使用SQLAlchemy ORM映射到数据库表
    """
    __tablename__ = "quote"  # 指定数据库表名为"quote"
    id = Column(Integer, primary_key=True)  # 定义id列，整数类型，作为主键
    quote = Column(String)  # 定义quote列，字符串类型，存储引用内容
    author = Column(String)  # 定义author列，字符串类型，存储引用作者
    link = Column(String)  # 定义link列，字符串类型，存储引用来源链接

Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0"
}

START_PAGE = 1
END_PAGE = 3
all_data = []

try:
    for page in range(START_PAGE, END_PAGE + 1):
        url = f"http://quotes.toscrape.com/page/{page}/"
        resp = requests.get(url=url, headers=headers, timeout=5)
        print("状态码：", resp.status_code)

        if resp.status_code != 200:
            continue

        tree = etree.HTML(resp.text)
        quote_list = tree.xpath('//span[@class="text"]/text()')
        author_list = tree.xpath('//small[@class="author"]/text()')
        link_list = tree.xpath('//span/a/@href')

        for q, a, l in zip(quote_list, author_list, link_list):
            print(f"{q}, {a} \n,{l}")
            one_data = Quote(quote=q, author=a, link=l)
            db.add(one_data)
            all_data.append((q, a, l))
    db.commit()
    print("====SQLite commit执行完毕====")

except requests.exceptions.Timeout:
    print("请求超时！")
except Exception as e:
    print("爬虫异常：", e)
    db.rollback()  
finally:
    db.close()

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