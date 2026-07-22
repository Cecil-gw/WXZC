from urllib import request
import urllib.request

# url = "https://www.ccps.gov.cn/"

# 发送请求
response = request.urlopen('http://www.baidu.com')
# 获取响应内容
html = response.read().decode('utf-8')
print(html)

url="http://httpbin.org/get"
response = request.urlopen(url)
print(response.read().decode('utf-8'))

import requests

# ========== 请求行 ==========
# 方法 GET + URL + HTTP版本(底层自动处理)
url = "https://www.ccps.gov.cn/favicon.ico"

# ========== 请求头 ==========
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://www.ccps.gov.cn/",  # 上一跳页面
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# 发送请求
response = requests.get(url, headers=headers)

# ========== 响应状态行 ==========
print(response.status_code)        # 404  ← 对应抓包 Status Code: 404 Not Found
print(response.reason)             # Not Found

# ========== 响应头 ==========
print(response.headers.get("Content-Type"))      # text/html  ← content-type
print(response.headers.get("Content-Encoding"))  # gzip       ← content-encoding
print(response.headers.get("Server"))            # Lego Server
print(response.headers.get("X-Cache-Lookup"))    # Cache Hit

# ========== 响应体 ==========
print(len(response.content))       # 167  ← content-length (压缩后的大小)
print(response.text)               # 解压后的 HTML 内容

import requests

# ========== 请求行 ==========
url = "https://httpbin.org/post"  # 方法 POST + URL + HTTP/1.1

# ========== 请求头 ==========
headers = {
    "Host": "httpbin.org",                    # 目标域名
    "User-Agent": "python-requests/2.31.0",   # 客户端标识
    "Content-Type": "application/json",       # 请求体格式 ← 关键！
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIs...",  # 认证token
    "Cookie": "session_id=abc123; user_id=456",         # 会话凭证
}

# ========== 请求体 ==========
data = {
    "username": "admin",
    "password": "123456",
    "captcha": "a3f8"
}

# 发送请求：json= 会自动序列化 + 自动加 Content-Type: application/json
response = requests.post(url, headers=headers, json=data)

# ========== 响应 ==========
print(f"状态码: {response.status_code}")           # 200
print(f"响应头 Content-Type: {response.headers.get('Content-Type')}")
print(f"响应体: {response.json()}")                 # 自动解析 JSON