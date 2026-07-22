import requests as re
url_list = [
    "http://httpbin.org/get",
    "http://httpbin.org/status/200",
    "http://httpbin.org/status/404"
]

success = 0  # 成功计数（状态码200）
fail = 0 

for url in url_list:
    try:
        response = re.get(url)
        if response.status_code == 200:
            success += 1
        else:
            fail += 1
    except:
        fail += 1

print("成功次数：", success)
print("失败次数：", fail)