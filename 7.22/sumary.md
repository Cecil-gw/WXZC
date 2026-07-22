## 7.22 工作日志

### 1. 复习：

##### 1.1 SQLALkemy

    环境：pip install sqlalchemy pymysql（mysql 驱动）
    
    核心组件
    create_engine：数据库连接引擎
    declarative_base：模型基类（表映射父类）
    Column、Integer、String、DateTime：字段类型
    Session：会话，所有增删改查都靠会话
    
    ### 
    from sqlalchemy import create_engine, Column, Integer, String
    from sqlalchemy.orm import declarative_base, sessionmaker
    
    # 1. 创建引擎
    # mysql+pymysql://账号:密码@地址:端口/库名
    DB_URL = "mysql+pymysql://root:123456@127.0.0.1:3306/testdb"
    engine = create_engine(DB_URL, echo=False) # echo=True打印SQL语句
    
    # 2. 基类
    Base = declarative_base()
    
    # 3. 定义数据表模型
    class User(Base):
        __tablename__ = "user"  # 数据库真实表名
    
        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String(50), nullable=False)
        age = Column(Integer)
    
    # 4. 创建所有表（不存在才创建）
    Base.metadata.create_all(engine)
    
    # 5. 创建会话工厂
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal() # 获取会话
    
     # 如果写异步额外装
    pip install aiomysql
    
    from sqlalchemy import create_engine, Column, Integer, String, select
    from sqlalchemy.orm import DeclarativeBase, sessionmaker
    
    # 1. 数据库连接地址
    DB_URL = "mysql+pymysql://root:密码@127.0.0.1:3306/test_db"
    
    # 2. 创建引擎
    engine = create_engine(
        DB_URL,
        echo=False,  # echo=True 打印执行的SQL，调试打开
        pool_recycle=3600
    )
    
    # 3. 声明基类【2.0新版：DeclarativeBase，替代老的declarative_base()】
    class Base(DeclarativeBase):
        pass
    
    # 4. 定义模型（映射数据表）
    class User(Base):
        __tablename__ = "user"
    
        id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
        name = Column(String(50), nullable=False, comment="姓名")
        age = Column(Integer, nullable=True, comment="年龄")
    
    # 5. 根据模型创建表（不存在才创建，不会覆盖已有表）
    Base.metadata.create_all(bind=engine)
    
    # 6. 创建会话工厂
    SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    # 获取会话
    db = SessionFactory()

###### 

### 2.http协议和爬虫

##### 2.1 全球请求网址：http：//httpbin.org/get

    from urllib import request
    
    # 发送请求
    response = request.urlopen('http://www.baidu.com')
    # 获取响应内容
    html = response.read().decode('utf-8')
    print(html)
    
    url="http://httpbin.org/get"
    response = request.urlopen(url)
    print(response.read().decode('utf-8'))
    
    
    
    
    
    
    
    {
      "args": {}, 
      "headers": {
        "Accept-Encoding": "identity", 
        "Host": "httpbin.org", 
        "User-Agent": "Python-urllib/3.13", 
        "X-Amzn-Trace-Id": "Root=1-6a602267-193d872d72037ef747d032b7"
      }, 
      "origin": "171.212.113.141", 
      "url": "http://httpbin.org/get"
    }



##### 2.2 HTTP 协议工作流程

##### 

* **DNS 解析**：域名解析为服务器 IP 地址
  
      当你在地址栏输入 www.example.com，浏览器首先要找到这台服务器的"门牌号"（IP 地址）。
      解析流程（逐级缓存查询）：
      plain
      浏览器缓存 → 操作系统缓存（hosts 文件）→ 本地 DNS 服务器（ISP/路由器）
          ↓
      根域名服务器（.）→ 顶级域名服务器（.com）→ 权威域名服务器（example.com）
          ↓
      返回 IP 地址（如 93.184.216.34）
      优化手段：
      DNS 预解析：<link rel="dns-prefetch" href="//cdn.example.com">
      HTTPDNS：绕过运营商 DNS，直接用 HTTP 协议向 DNS 服务商查询，防止劫持

* **TCP 三次握手**：建立客户端与服务器的 TCP 连接
  
  * HTTPS 场景：TCP 连通后，执行**TLS 握手**协商加密，之后传输密文
    （
    
        客户端                    服务器
          |    SYN=1, seq=x      |
          | --------------------> |  （我能连你吗？我的序号是 x）
          |                       |
          |  SYN=1, ACK=1, seq=y, ack=x+1 |
          | <-------------------- |  （能，我的序号是 y，期待你发 x+1）
          |                       |
          |    ACK=1, seq=x+1, ack=y+1 |
          | --------------------> |  （好的，我开始发数据了）
        
        **为什么是三次？**
        * * * 第一次：客户端证明自己能发
        
            * 第二次：服务器证明自己能收、能发
        
            * 第三次：客户端证明自己能收
        
            * **两次不够**：服务器无法确认客户端是否收到了自己的应答；**四次多余**：三次已达成双方收发能力确认）
        
        * 客户端发送 **HTTP 请求报文
    
    * **

* 服务器接收请求，执行业务处理

* 服务器返回 **HTTP 响应报文**
  
      HTTP/1.1 200 OK
      Date: Wed, 22 Jul 2026 11:08:00 GMT
      Content-Type: text/html; charset=UTF-8
      Content-Length: 1234
      Cache-Control: max-age=3600
      Set-Cookie: user_pref=dark_mode; Path=/
      
      <!DOCTYPE html>
      <html>...（响应体）

* 客户端解析响应，渲染资源；页面内继续并发请求图片、JS、CSS 等静态资源
  
      解析 HTML → 构建 DOM 树
      解析 CSS → 构建 CSSOM 树
      合并 DOM + CSSOM → 渲染树（Render Tree）
      布局（Layout/Reflow）：计算每个元素的位置和大小
      绘制（Paint）：把像素画到屏幕上
      合成（Composite）：处理层叠、动画、GPU 加速
      同时，浏览器发现 HTML 中引用的外部资源（图片、JS、CSS、字体），会并发发起新请求（HTTP/1.1 通常 6~8 个 TCP 连接并行；HTTP/2 多路复用，一个连接内并行）。

* 连接处理
  
  * `Connection: keep-alive`：长连接，通道保留，短时间复用多次请求
  * 超时后执行**TCP 四次挥手**，断开连接 

##### 2.3 HTTP 请求报文三大部分：**请求行 + 请求头 + 空行 + 请求体**

    格式：请求方法 资源URL HTTP版本
    示例：GET /index.html HTTP/1.1

##### 2.3.1 请求行

    方法    作用                    特点
    GET    获取资源          无请求体，参数拼接在 URL，用于查询数据
    POST    提交数据          携带请求体，新增、提交表单、上传数据
    PUT    全量更新资源       修改完整一条资源
    PATCH    局部更新资源        只修改部分字段
    DELETE    删除服务器资源         删除指定数据

###### 2.3.2 请求头

    键值对格式，携带客户端附加信息，常见字段：
    Host：目标访问域名（必填）
    User-Agent：客户端类型（浏览器、爬虫、程序）
    Cookie：本地会话凭证
    Accept：客户端能够接收的数据格式
    Referer：上一跳页面地址
    Accept-Encoding：支持的压缩方式（gzip）

###### 2.3.3 请求体

    GET 请求一般没有请求体
    POST/PUT/PATCH 常用请求体传递 JSON、表单数据
    请求头Content-Type用来标记请求体内数据格式：application/json、multipart/form-data（文件上传）

##### 





##### 2.4 HTTP 响应的组成 == 状态行 + 响应头 + 空行 + 响应体

##### 

##### 2.4.1 状态行

    格式：HTTP版本 状态码 描述文字
    示例：HTTP/1.1 200 OK

###### 2.4.2 状态码

    1xx — 信息响应（Informational）
    100 Continue：继续。客户端应继续请求。
    101 Switching Protocols：切换协议（如 WebSocket 升级）。
    102 Processing：处理中（WebDAV
    
    2xx — 成功（Success）
    200 OK：请求成功。
    201 Created：资源创建成功。
    204 No Content：成功但无返回内容。
    206 Partial Content：部分内容（断点续传）。
    
    
    3xx — 重定向（Redirection）
    301 Moved Permanently：永久重定向。
    302 Found：临时重定向。
    304 Not Modified：缓存未修改，使用缓存。
    307 Temporary Redirect：临时重定向，方法不变。
    308 Permanent Redirect：永久重定向，方法不变。
    
    
    4xx — 客户端错误（Client Error）
    400 Bad Request：请求参数错误。
    401 Unauthorized：未认证。
    403 Forbidden：无权限访问。
    404 Not Found：资源不存在。
    405 Method Not Allowed：请求方法不允许。
    408 Request Timeout：请求超时。
    409 Conflict：资源冲突。
    410 Gone：资源已永久删除。
    413 Payload Too Large：请求体过大。
    429 Too Many Requests：请求过于频繁。
    
    
    5xx — 服务器错误（Server Error）
    500 Internal Server Error：服务器内部错误。
    502 Bad Gateway：网关或代理收到无效响应。
    503 Service Unavailable：服务暂时不可用。
    504 Gateway Timeout：网关或代理超时。

###### 2.4.3 响应头（Response Headers）

    服务器返回的配置信息，结合你刚才抓包案例举例：
    Content-Type: text/html：响应体是 HTML 网页
    Content-Encoding: gzip：内容经过 gzip 压缩
    Content-Length：传输数据字节大小
    Connection: keep-alive：开启长连接
    Set-Cookie：服务器下发 Cookie 到浏览器
    X-cache-lookup: Cache Hit：CDN 缓存命中
    Server：后端服务标识

###### 2.4.4 响应体

    服务器真正返回的数据：HTML 页面、JSON 字符串、图片、文件等。

##### 2.5 完整小请求

###### 2.5.1 GET

    1. GET 请求（对应你抓包里的 favicon.ico）
    Python
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

###### 2.5.2 POST

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

### 3 urllib和requests库

##### 3.1 urllib

    urllib.request：发起请求，核心模块
    urllib.parse：URL 编码、拼接参数
    urllib.error：异常处理
    urllib.robotparser：爬虫协议 robots.txt 解析（很少

###### 3.1.1 GET

    import urllib.request
    
    url = "https://httpbin.org/get"
    # 发起请求
    response = urllib.request.urlopen(url)
    
    # 常用属性
    print(response.status)      # 状态码 200
    print(response.getheaders())# 获取全部响应头
    print(response.getheader("Server")) # 获取单个响应头
    
    # 读取内容（返回bytes，必须decode解码）
    html = response.read().decode("utf-8")
    print(html)
    
    
    import urllib.request
    from urllib.parse import urlencode
    
    params = {
        "name": "小明",
        "age": 20
    }
    # 字典参数转url查询字符串
    query = urlencode(params)
    url = f"https://httpbin.org/get?{query}"
    
    resp = urllib.request.urlopen(url)
    print(resp.read().decode("utf-8"))

##### 3.1.2 自定义请求头（添加 User-Agent）

    import urllib.request
    
    url = "https://httpbin.org/get"
    headers = {
        "User-Agent": "Mozilla/5.0 Windows"
    }
    # 构造请求对象
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req)
    print(resp.read().decode("utf-8"))

##### 3.1.3 POST 请求（表单数据）

    import urllib.request
    from urllib.parse import urlencode
    
    url = "https://httpbin.org/post"
    data = {
        "username":"test",
        "pwd":"123456"
    }
    # post数据必须转bytes
    post_data = urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=post_data, method="POST")
    
    resp = urllib.request.urlopen(req)
    print(resp.read().decode("utf-8"))

#### 3.2 requests 库

##### 3.2.1 GET 请求基础

    import requests
    
    url = "https://httpbin.org/get"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    params = {"name":"张三", "age":18}
    
    resp = requests.get(
        url=url,
        headers=headers,
        params=params,  # 自动拼接url参数
        timeout=10      # 超时时间，必加！防止卡死
    )
    
    # 常用属性
    print(resp.status_code)   # 状态码
    print(resp.headers)       # 响应头
    print(resp.url)           # 最终请求url
    print(resp.text)          # 文本响应（自动编码）
    print(resp.content)       # bytes原始内容（下载图片用）
    print(resp.json())        # 直接解析json → 字典（接口最常用）

##### 3.2.2 POST 请求

    ① 表单格式 
    data=
    data = {"user":"admin","pass":"123"}
    resp = requests.post(url, data=data, headers=headers)
    
    ② JSON 格式（前后端接口最常用）
    json=
    payload = {"username":"test","password":"666"}
    resp = requests.post(url, json=payload)



##### 3.2.3 Session 会话（保持 Cookie，模拟登录）

    session = requests.Session()
    # 登录请求
    session.post(login_url, data={"user":"xxx","pwd":"xxx"})
    # 后续请求自动带上登录Cookie
    res = session.get(personal_url)

#### 3.3 区别

    urllib 是 Python 内置的网络请求标准库，使用繁琐；requests 基于 urllib 封装，语法简洁，提供会话保持、自动 json 解析等能力，日常开发优先使用 requests。可以发送 GET/POST 请求，携带请求头、URL 参数、请求体，常用于接口调用、网络爬虫。

### 4 cookie

##### 4.1 定义

    ookie 是服务器发送给客户端（浏览器），由客户端本地保存的一小块文本数据（键值对形式）；
    客户端后续访问同一域名的请求时，会自动带上 Cookie发给服务器，用来维持客户端身份、保存状态信息。
    核心背景：HTTP 协议本身是无状态协议，服务器无法区分两次请求是不是同一个用户；Cookie 就是用来弥补无状态缺陷的方案。

##### 4.2 用途

    Cookie 只能保存字符串键值对，容量受限（单条 ≤4KB），不适合存大量、复杂数据。
    常见存储内容：
    会话标识（最常用）
    sessionid、token、登录凭证
    服务器靠这个识别你是不是已登录用户。
    用户偏好设置
    网页语言：lang=zh-CN
    主题模式：theme=dark
    页面布局、记住视图设置
    追踪统计标识
    第三方埋点、广告统计 ID，用于访问行为统计。
    临时标记
    记住弹窗是否关闭、勾选 “记住我”、验证码标识等。
    ⚠重要提醒：
    不会直接存放敏感明文（账号密码、身份证）！
    真要保存身份只会存凭证 id，原始密码绝不存入 Cookie。

##### 4.3 语法



    import requests
    
    # 手动拼 Cookie 请求头（对应 Cookie: name=value）
    headers = {"Cookie": "a=1; b=2"}
    
    # Session 自动管理 Set-Cookie 和 Cookie
    session = requests.Session()
    session.get("https://example.com")  # 收到 Set-Cookie 自动存
    session.get("https://example.com/api")  # 自动带 Cookie: xxx



## 5.1 requests

    requests.get()    # 查询数据（网页、接口查询）
    requests.post()   # 提交表单/JSON（登录、新增数据）
    requests.put()    # 全量更新资源
    requests.patch()  # 局部更新资源
    requests.delete() # 删除数据
    requests.head()   # 只拿响应头，不下载页面内容（轻量化检测）
    requests.options()# 查看服务器支持哪些请求方法（跨域调试）

    地址：
    import requests
    
    resp = requests.get(
        url="目标网址",                # 必传，必须带 http/https
        params={"key1": "值1"},       # GET URL拼接参数，自动编码
        headers={},                   # 请求头，伪装浏览器核心
        cookies={},                    # 单次临时Cookie
        timeout=(3, 10),              # 超时：连接3秒，读取10秒
        proxies={},                    # 代理IP，防封禁
        allow_redirects=True,         # 是否自动跟随301/302重定向
        verify=True,                  # HTTPS证书校验，测试可关闭
        stream=False,                 # 大文件流式下载开关
    )

### 5.2 x_path

    XPath 是什么
    全称：XML Path Language，XML 路径语言，同时兼容 HTML（HTML 是类 XML 结构）
    作用：根据标签层级、属性、文本快速定位页面元素，爬虫解析网页必备，配合 lxml / parsel 使用
    对比正则：XPath 专门处理标签结构，比正则简单精准；正则适合无规则纯文本
    Python 依赖库：lxml（最主流）
    安装：
    bash
    运行
    pip install lxml

##### 5.2.1 语法

    htnl="""
      <html>
        <body>
          <div class="box">
            <h1 id="title">学习XPath</h1>
            <ul class="list">
              <li class="item">张三</li>
              <li class="item">李四</li>
              <li class="item red">王五</li>
              <li>赵六</li>
            </div>
            <a href="https://www.baidu.com">百度</a>
          </div>
        </body>
      </html>
    """
    
    from lxml import etree
    
    tree=etree.HTML(htnl)
    
    #1. 获取所有的li标签
    result=tree.xpath('//li')
    print(result)
    
    #2. 获取class属性为item的li标签
    result=tree.xpath('//li[@class="item"]')
    print(result)
    
    
    #3. 获取class属性为item的li标签的文本内容
    result=tree.xpath('//li[@class="item"]/text()')
    print(result)

##### 5.2 基础路径语法

###### 5.2.1 节点分隔 / 和 //

    /：绝对路径，从根节点一层一层精准匹配
    xpath
    /html/body/div/h1
    # 精准匹配上面的h1标签
    
    //：相对路径，全局搜索，不用写完整层级（爬虫 99% 用这个）
    xpath
    //h1  # 页面所有h1标签，不管在哪一层
    //li  # 页面所有li标签

###### 5.2.2 .与..

    . 当前节点
    .. 父节点
    xpath
    //li/.    # 当前li节点
    //li/..   # li的父节点ul

###### 5.2.3 提取文本、属性

     text() 提取标签内文字
    xpath
    //h1/text()      # 结果：学习XPath
    //li/text()      # 获取所有li的文字：张三、李四、王五、赵六
     
     
    @属性名 提取标签属性（href、class、id 等）
    xpath
    //a/@href        # 提取链接 https://www.baidu.com
    //h1/@id         # 提取id值 title
    //li/@class      # 提取所有li的class

###### 5.2.4 筛选谓语 `[]`

    根据 id 筛选 [@id="值"]
    xpath
    //h1[@id="title"]   # 只匹配id等于title的h1
    2. 根据 class 筛选
    完全匹配 class
    xpath
    //li[@class="item"]
    # 只会匹配class只有item的张三、李四，王五class是item red 匹配不到
    class 包含某关键词（contains()），爬虫高频
    xpath
    //li[contains(@class, "item")]
    # 只要class里有item就能匹配：张三、李四、王五全部命中
    3. 根据文本内容筛选 text()
    xpath
    //li[text()="王五"]   # 精准匹配文字为王五的li
    //li[contains(text(), "张")] # 文字包含“张”
    4. 按位置筛选（下标，下标从 1 开始，不是 0！）
    xpath
    //ul/li[1]    # 第一个li：张三
    //ul/li[last()] # 最后一个li：赵六
    //ul/li[position()<3] # 前两个li
    5. 多条件 and /or
    xpath
    # class包含item 并且 文字是李四
    //li[contains(@class,"item") and text()="李四"]
    # class=item 或者 文字=赵六
    //li[@class="item" or text()="赵六"]

###### 5.2.5 轴语法

    child:: 子节点（默认可省略，//ul/li = //ul/child::li）
    parent:: 父节点 //li/parent::ul
    following-sibling:: 后面同级兄弟
    xpath
    //li[1]/following-sibling::li  # 张三后面所有li
    preceding-sibling:: 前面同级兄弟

###### 5.2.6 lxml 库 Python 完整使用案例

    #本地 HTML 字符串解析
    from lxml import etree
    
    html = """
    <html>
      <body>
        <div class="box">
          <h1 id="title">学习XPath</h1>
          <ul class="list">
            <li class="item">张三</li>
            <li class="item">李四</li>
            <li class="item red">王五</li>
            <li>赵六</li>
          </ul>
          <a href="https://www.baidu.com">百度</a>
        </div>
      </body>
    </html>
    """
    # 1. 转为可解析对象
    tree = etree.HTML(html)
    
    # 2. xpath查询，返回列表
    # 获取h1文字
    title = tree.xpath("//h1/text()")[0]
    print(title)
    
    # 所有li文本
    name_list = tree.xpath("//li/text()")
    print(name_list)
    
    # 提取a标签链接
    link = tree.xpath("//a/@href")[0]
    print(link)
    
    # 筛选class包含item的li
    target = tree.xpath('//li[contains(@class,"item")]/text()')
    print(target)

##### 5.3 快速查表

    #####  
