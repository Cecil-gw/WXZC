### 7.23 Flask介绍和实战，Postman，fastapi的mvc

### 1.复习与整理

##### 1.1 爬虫



##### 1.2 HTML





##### 1.3 css

    CSS 完整核心知识点（精炼版，适合快速复习）
    一、CSS 三种引入方式
    内联样式（行内）
    html
    预览
    <div style="color:red">文本</div>
    优先级最高；缺点：无法复用、结构样式混杂。
    内部样式表（style 标签）
    html
    预览
    <style>
    div { color: red; }
    </style>
    写在 <head> 内，仅当前页面生效。
    外部样式表（推荐）
    html
    预览
    <link rel="stylesheet" href="style.css">
    独立 .css 文件，多页面复用，项目标准写法。
    补充：@import 引入 css（不推荐，会阻塞渲染）
    二、选择器（上一轮简版扩充）
    基础
    * 通配符、标签选择器、.class、#id
    组合
    div p 后代（所有子孙）
    div > p 直接子元素
    h1 + p 紧邻下一个兄弟
    h1 ~ p 后面所有同级兄弟
    h1,h2 群组选择器（同时选中）
    div.box 交集：既是 div 又有 box 类
    属性选择器
    [attr] [attr="val"] ^=开头 $=结尾 *=包含
    伪类 :（匹配元素状态）
    :hover :active :focus
    :first-child :last-child
    :nth-child(n) :nth-of-type()
    :not(选择器) 取反
    伪元素 ::（生成虚拟元素）
    ::before ::after（必须写 content）
    ::first-line ::first-letter
    选择器权重（优先级）
    !important > 行内样式 (1000) > id (100) > class / 属性 / 伪类 (10) > 标签 / 伪元素 (1)
    权重不会进位；后写的样式会覆盖同等权重样式
    三、盒子模型（重中之重）
    元素尺寸计算公式：
    总宽度 = width + padding + border + margin
    plaintext
    content 内容宽高
    padding 内边距（背景延伸到padding）
    border 边框
    margin 外边距（透明，盒子之间间距）
    css
    /* 标准盒模型（默认） */
    box-sizing: content-box;
    
    /* IE怪异盒模型（常用！width包含padding+border） */
    box-sizing: border-box;
    margin 塌陷
    垂直方向相邻块元素 margin 会合并，取最大值；父子元素不加 border/padding 时，子 margin 会作用到父盒子。
    解决：BFC、padding、border。
    四、文档流、显示模式 display
    块级 block
    div、p、h1、ul
    独占一行；可设置宽高；默认宽度 100%
    行内 inline
    span、a、em
    不独占一行；不能设置宽高
    行内块 inline-block
    img、input
    同行显示，支持宽高；存在空白间隙（解决方案：父元素 font-size:0）
    常用值：
    display:none 隐藏，不占空间
    visibility:hidden 隐藏，保留位置
    五、浮动 float
    css
    float: left / right / none;
    作用：让块元素横向排列
    特点：
    脱离普通文档流
    文字环绕浮动元素
    父盒子高度塌陷（核心问题）
    清除浮动方案：
    父元素 overflow:hidden（简单场景）
    伪元素清除浮动（工程常用）
    css
    .clearfix::after{
      content:"";
      display:block;
      clear:both;
    }
    六、定位 position
    css
    position: static;    /* 默认，正常文档流 */
    position: relative; /* 相对自身原位置，不脱标 */
    position: absolute; /* 绝对定位，脱标；找最近已定位父级 */
    position: fixed;    /* 固定定位，相对于视口 */
    position: sticky;   /* 粘性定位，滚动吸附 */
    搭配 top left right bottom z-index
    z-index 只对已定位元素生效；层级越高越在上层
    七、BFC 块级格式化上下文
    BFC 独立渲染区域
    触发条件：
    float 不为 none
    overflow 不为 visible
    display:inline-block/flex/grid
    position:absolute/fixed
    作用：清除浮动、解决 margin 塌陷、阻止文字环绕。
    八、Flex 弹性布局（现代布局首选）
    父容器（弹性容器）
    css
    display:flex;
    flex-direction: row/column; /* 主轴方向 */
    justify-content: center;    /* 主轴对齐 */
    align-items: center;        /* 侧轴对齐 */
    flex-wrap: wrap;            /* 自动换行 */
    gap: 间距;
    子元素（弹性项）
    css
    flex: 1;    /* 等分剩余空间 */
    align-self: 单独控制侧轴对齐
    order: 排序
    九、Grid 网格布局（二维布局）
    css
    display:grid;
    grid-template-columns: 1fr 1fr 1fr; /* 三列等分 */
    gap: 间距;
    适合整体页面栅格、卡片多列布局。
    十、样式三大模块
    1. 文本样式
    css
    color 文字颜色
    font-size 字号
    font-family 字体
    font-weight 字重
    text-align 水平对齐
    line-height 行高（垂直居中常用）
    text-decoration: none; /* 去掉下划线 */
    text-indent 首行缩进
    2. 背景
    css
    background-color
    background-image: url()
    background-repeat
    background-position
    background-size: cover / contain
    3. 边框、圆角、阴影
    css
    border: 1px solid #000;
    border-radius: 圆角
    box-shadow: 盒子阴影
    text-shadow: 文字阴影
    十一、过渡、动画
    transition 过渡（状态变化平滑）
    css
    transition: all 0.3s;
    @keyframes 动画 animation
    css
    @keyframes move{
      from{}
      to{}
    }
    animation: move 2s infinite alternate;
    十二、响应式基础
    媒体查询
    css
    @media (max-width:768px){
      /* 手机样式 */
    }
    十三、常见注意点
    行内元素 margin 上下不生效，优先转 block/inline-block
    浮动、绝对定位元素会自动转为块级
    尽量少用 id 选择器写样式，便于后期覆盖
    能用 flex/grid 就尽量不用浮动布局
    box-sizing: border-box; 全局推荐重置

##### 1.4 js

    JavaScript 核心知识点速讲（前端配套 CSS，面试 / 开发通用）
    一、JS 三种引入方式
    行内 JS（不推荐）
    html
    预览
    <button onclick="alert('hello')">点击</button>
    内部脚本
    html
    预览
    <script>
    console.log('内部js');
    </script>
    外部文件（推荐）
    html
    预览
    <script src="main.js"></script>
    <!-- defer：HTML解析完再执行，不阻塞页面 -->
    <script src="main.js" defer></script>
    <!-- async：下载完成立刻执行，顺序不可控 -->
    <script src="main.js" async></script>
    注意：script 默认阻塞 HTML 解析，放在 body 底部或加 defer。
    二、变量、数据类型
    1. 变量声明
    var：函数作用域，存在变量提升，可重复声明
    let：块级作用域，不能重复声明，存在暂时性死区
    const：块级作用域，常量，不能重新赋值（对象 / 数组内部属性可修改）
    ✅ 开发规范：优先 const，需要修改再用 let，不用 var
    2. 数据类型
    原始类型（值类型）
    String、Number、Boolean、Null、Undefined、Symbol、BigInt
    引用类型
    Object、Array、Function、Date、RegExp
    区分方式：
    js
    运行
    typeof 变量; // 基础检测（typeof null === 'object' 经典bug）
    Object.prototype.toString.call(val); // 精准类型判断
    三、运算符
    算术 + - * / % ++ --
    比较 > < >= <= == === != !==
    == 会隐式类型转换；=== 严格相等（推荐永远用三等号）
    逻辑 && || !
    三元 条件 ? a : b
    空值合并 ??、可选链 ?.（ES6 + 高频）
    js
    运行
    let name = user?.info?.name ?? "默认名称";
    四、流程控制
    js
    运行
    if / else if / else
    switch(值){ case: break; }
    for / for(let i of arr) / for(let key in obj)
    while / do while
    break continue
    for in 遍历对象键；for of 遍历数组 / 可迭代对象（推荐数组使用）
    五、函数
    1. 函数三种写法
    js
    运行
    // 函数声明（存在提升）
    function fn(){}
    // 函数表达式
    const fn = function(){}
    // 箭头函数
    const fn = () => {}
    箭头函数重点特性
    没有自己的 this，继承外层 this
    不能作为构造函数 new
    没有 arguments
    不能使用 yield
    this 指向（重中之重）
    普通函数调用：this → window(浏览器)
    对象方法调用：this → 对象本身
    new 构造函数：this 指向新实例
    call / apply / bind 手动修改 this
    箭头函数：this = 定义时外层上下文，调用方式无法改变
    六、数组常用 API
    改变原数组
    push pop shift unshift splice reverse sort
    返回新数组（不污染原数组）⭐项目常用
    js
    运行
    map()    // 映射，一一转换
    filter() // 筛选符合条件元素
    reduce() // 累加、求和、统计、数组转对象
    slice()  // 截取
    concat() // 合并
    查找：find findIndex includes some every
    七、对象
    js
    运行
    const obj = { name:"张三" }
    obj.name  // .访问
    obj["name"] // []访问，支持动态变量
    ES6 简写、解构赋值、展开运算符 ...
    js
    运行
    const {name} = obj;
    const newObj = {...obj, age:18}
    八、ES6+ 高频语法
    解构赋值（对象、数组）
    展开运算符 ...
    模板字符串 `hello ${name}`
    默认参数
    Promise 异步
    async / await（Promise 语法糖）
    class 类
    import / export 模块化
    九、异步 JS（前端核心难点）
    1. 异步发展路线
    回调函数 → Promise → async/await
    Promise
    三种状态：pending 等待、fulfilled 成功、rejected 失败
    js
    运行
    new Promise((resolve,reject)=>{
      // 异步操作
    }).then(res=>{}).catch(err=>{})
    async await
    js
    运行
    async function load(){
      const res = await fetch('/api');
    }
    await 只能写在 async 函数内部
    常见异步场景
    定时器 setTimeout setInterval、AJAX/fetch 请求、事件、文件读写
    十、DOM 操作（JS 和页面交互，搭配 CSS）
    DOM：文档对象模型，JS 用来操控 HTML 结构
    js
    运行
    // 获取元素
    document.querySelector('.box')   // 推荐，支持CSS选择器
    document.querySelectorAll('.item')
    
    // 修改内容
    el.innerText  // 纯文本
    el.innerHTML  // 识别html标签
    
    // 修改样式（对应CSS）
    el.style.color = 'red'
    
    // 操作类名（推荐！不要直接写style）
    el.classList.add('active')
    el.classList.remove('active')
    el.classList.toggle('active')
    
    // 增删节点
    appendChild removeChild cloneNode
    十一、BOM 浏览器对象
    js
    运行
    window // 全局对象
    location.href // 页面跳转
    location.search // 获取url参数
    history // 前进后退
    setTimeout / setInterval
    十二、事件
    js
    运行
    // 绑定事件
    el.addEventListener('click', function(e){
      e.preventDefault() // 阻止默认行为（a跳转、表单提交）
      e.stopPropagation() // 阻止事件冒泡
    })
    事件流：捕获 → 目标 → 冒泡
    事件委托：利用冒泡，给父元素绑定事件，代理子元素（性能优化）
    十三、同步、异步、宏任务、微任务（面试高频）
    宏任务：script 整体代码、setTimeout、setInterval、AJAX
    微任务：Promise.then/catch、await 后面代码
    执行顺序：
    同步代码 → 所有微任务 → 一个宏任务 → 再清空微任务…… 循环
    十四、JSON 数据交互
    js
    运行
    JSON.stringify(obj)  // 对象转字符串
    JSON.parse(str)      // 字符串转回对象
    十五、垃圾回收 & 闭包
    闭包
    函数嵌套，内层函数引用外层变量，内层暴露到外部。
    作用：保存私有变量、实现数据持久；
    弊端：内存无法释放，容易内存泄漏。
    十六、AJAX / Fetch（前后端通信）
    Fetch（现代推荐）
    js
    运行
    fetch('/api/list')
    .then(res=>res.json())
    .then(data=>console.log(data))
    十七、JS 配合 CSS 实现响应式（联动你上一个问题）
    两种常用场景：
    单纯布局：优先 CSS @media，不用 JS
    需要复杂逻辑时，JS 判断屏幕宽度
    js
    运行
    window.addEventListener('resize',()=>{
      const width = document.documentElement.clientWidth;
      if(width <= 768){
        // 移动端逻辑
      }
    })

### 2.Flask

##### 2.1 环境搭建

###### 2.1.1 常用python后端：Flask-->fastapi-->tornado-->Django

###### 2.1.2 web 服务器：

    Web 服务器本质是持续运行的程序，监听本机端口（如 80、5000），专门接收浏览器（客户端）发来的 HTTP 请求，处理后返回 HTTP 响应。
    通信流程：
    浏览器 → HTTP 请求 → Web 服务器 → HTTP 响应 → 浏览器渲染页面
    
    静态 Web 服务器（只处理静态资源）
    只能够直接返回文件：html、图片、css、js
    例子：Nginx、Apache
    缺陷：不能执行 Python 代码，无法动态生成页面，不能操作数据库。
    动态 Web 服务器（需要配合程序）
    想要运行 Flask/Django 这类 Python 代码，单纯 Nginx 做不到。
    于是诞生规范：WSGI
    
    WSGI（重点！Flask 核心）
    全称：Web Server Gateway Interface
    中文：Web 服务器网关接口
    作用：一套统一标准，打通 Web 服务器 ↔ Python Web 程序（Flask）
    Web 服务器收到 HTTP 请求
    通过 WSGI 协议把请求转发给 Flask 应用
    Flask 运行代码生成响应
    再原路返回给服务器，交给浏览器

###### 2.1.3 构建实例

    from flask import Flask
    
    #  创建 Flask 引用实例
    app = Flask(__name__)

##### 2.2 路由装饰器

###### 2.2.1     @app.route(‘/’)

    @app.route('/'):当前用户访问首页的，执行以下函数
    
    def index():随便取，如果是首页一般默认写index
    
    return 函数返回的内容会直接显示在浏览器里面
    
    @app.route('/')  #127.0.0.1:5000/
    def index():
        return "<h1>🚀 欢迎进入 Flask 世界！</h1>"



##### 2.3 Flask 动态路由详解

    @app.route('/greet/<name>')
    def greet(name):
        return f"你好，{name}! 欢迎来到空间站
    
    <name> 是占位符：URL 中这一段会被捕获，作为变量传入视图函数
    ⚠️ 硬性规则：视图函数的参数名必须和占位符名称完全一致
    访问示例：http://127.0.0.1:5000/greet/小明 → name="小明"。"

###### 2.3.1 实例

    <int:id>    /user/100    只能是整数，/user/abc 404
    <float:price>    /price/9.99    只能是小数，整数无法匹配
    <path:filename>    /file/a/b/test.txt    可以捕获包含/的路径，普通占位符做不到
    <uuid:id>    /item/550e8400-e29b    严格匹配标准 UUID 字符串



###### 2.3.2 启动器

    if __name__ == '__main__':
        app.run(host='127.0.0.1', port=5000, debug=True
     
    )
    
    host='127.0.0.1'
    只允许自己电脑本机访问；
    想要同一 WiFi 下手机 / 其他电脑访问，改为 host="0.0.0.0"
    port=5000
    端口号，浏览器访问地址最后的数字；可以改成 8080、3000 等未被占用端口
    debug=True
    调试模式：修改代码保存，服务器自动重启；
    ❗ 重要警告：正式上线必须关闭，存在安全风险！

### 2.4 路由配置

###### 2.4.1 HTTP 请求方法（GET / POST / PUT / PATCH / DELETE）

    GET：拿数据。只查询，不修改服务器内容。参数拼在网址?xxx后面，能被浏览器收藏、缓存。
    例子：打开文章、搜索商品 /search?keyword=flask
    POST：提交新数据。新增内容，数据放在请求体内，不会显示在网址上。
    例子：登录、注册、发表评论
    PUT：全量更新。把一条数据完整替换
    PATCH：局部更新。只修改其中一部分字段（只改昵称，不改密码）
    DELETE：删除数据。删除文章、注销账号

###### 2.4.2 请求与相应对象

###### ①request

    当用户访问你的网站时，`request` 对象里包含了**所有用户发来的信息**：
    
    | 属性/方法 | 含义  | 使用场景 |
    | --- | --- | --- |
    | `request.method` | 请求方法（GET/POST 等） | 判断用户是查询还是提交 |
    | `request.args` | URL 查询参数 | `?page=1&limit=10` 中的参数 |
    | `request.form` | 表单数据 | 用户填写的登录表单 |
    | `request.get_json()` | JSON 数据 | 前端通过 `fetch` 发送的 JSON |
    | `request.headers` | 请求头 | 获取 User-Agent、Cookie 等 |
    | `request.cookies` | Cookie | 读取用户浏览器的 Cookie |
    
    
    from flask import Flask, request
    
    #  创建 Flask 引用实例
    app = Flask(__name__)
    
    @app.route('/search')
    def search():
        # 用户访问 /search?keyword=python&page=2
        keyword = request.args.get('keyword')  # "python"
        page = request.args.get('page', 1)     # "2"（默认值为 1）
        return f"搜索关键词：{keyword}，第 {page} 页"
    
    
    if __name__ == '__main__':
        app.run(host="127.0.0.1", port=5000, debug=True)   
    
    
    
    
    

###### ② jsonify 对象：返回json数据

    from flask import jsonify
    
    @app.route('/api/user')
    def get_user():
        user = {
            "id": 1,
            "name": "张三",
            "email": "zhangsan@example.com"
        }
        # jsonify 会自动：
        # 1. 把 Python 字典转成 JSON 字符串
        # 2. 设置 Content-Type: application/json 响应头
        return jsonify(user)
    
    

### 3 Postman

### 4 前端接口调用

    

### 5 task

     📦 任务：技术公司官方网站与内容管理系统 (CMS)
    
    ### 📊 项目描述
    
    某科技初创公司需要一个动态官网，用于展示公司简介、新闻公告，并提供后台内容管理功能。
    
    ### 🎯 任务要求
    
    请独立编写 `app_company_cms.py`，实现以下功能：
    
    1. **前台展示接口**：
      
      * `GET /`：展示公司首页（公司简介、最新 3 条新闻）。
      * `GET /api/news`：获取新闻列表（支持按发布时间倒序）。
      * `GET /api/news/<id>`：获取新闻详情。
    2. **后台管理接口（需管理员权限）**：
      
      * 管理员账号预设：`admin / admin123`。
      * `POST /admin/news`：发布新新闻（字段：`title`, `content`, `category`）。
      * `DELETE /admin/news/<id>`：删除指定新闻。
      * 必须实现登录校验装饰器，非 `admin` 角色访问后台接口返回 `403 Forbidden`。
    3. **数据持久化（可选挑战）**：
      
      * 使用 `sqlite3` 或 `SQLAlchemy` 将新闻数据存入本地文件 `cms.db`，替代内存字典，确保重启服务器后数据不丢失。
    4. **测试提交**：
      
      * 提交完整的 `.py` 文件。
      * 附带 Postman 或 Curl 测试截图（包含成功登录、发布新闻、前台获取新闻的完整链路）。
      * 测试接口全部无误后，让ai生成前端页面，完成一个完整的CMS。
    
    * * *
    
    ## 📝 提交要求
    
    1. 所有代码必须包含详细的中文注释。
    2. 运行前请确保已通过 `pip install flask requests` 安装依赖。
