import requests
from lxml import etree

headers = {
    "User-Agent": "Mozilla/5.0 Chrome/150.0.0"
}
url = "https://www.ccps.gov.cn/tpxw/202606/t20260630_171435.html"
resp = requests.get(url, headers=headers, timeout=5)
print(resp.status_code)
# print(resp.text)
resp.encoding = "utf-8"

html = etree.HTML(resp.text)
# print(html)
# 获取标题
title = html.xpath("//div[@class='article']/h1/text()")
print(title)
# 获取正文
content = html.xpath("//div[@class='article']/div[@class='content']/p/text()")
print(content)  