## 7.17





### 一.类装饰器

##### 1. 定义

    将自定义类作为装饰器，使用 `@类名` 修饰普通函数。

#### 2 强制前提：必须实现两个魔法方法

* `__init__(self, func)`
  
  * 执行时机：**仅初始化时执行 1 次**，函数加载阶段触发
  * 作用：接收被装饰的原函数，将函数保存为实例属性 `self.func`

* `__call__(self, *args, **kwargs)`
  
  * 执行时机：**每次调用被装饰函数时触发**
  * 作用：让类的实例变成可调用对象；内部编写函数执行前后的拓展逻辑，再调用原函数

#### 

#### 3. 实例：

    # 1. 写装饰器类
    class LogDecorator:
        def __init__(self, func):
            print("===== 初始化阶段，只跑一次 =====")
            self.func = func  # 保存被装饰的函数
    
        def __call__(self, *args, **kwargs)://*args 和 **kwargs 是干嘛的？
                    如果不写这两个，你的装饰器只能装饰固定参数数量的函数，通用性极差。
                    原函数 2 个参数：add(a,b) → args 装 2 个值
                    原函数 3 个参数：calc(a,b,c) → args 装 3 个值
                    原函数带关键字传参：calc(a=1,b=2) → kwargs 装键值对
            print("【前置逻辑】函数马上要运行")
            # 执行原本的函数
            result = self.func(*args, **kwargs)
            print("【后置逻辑】函数运行结束")
            return result
    
    # 2. 用@装饰函数
    @LogDecorator
    def add(x, y):
        print(f"原函数计算：{x}+{y}")
        return x + y
    <==>
    ```
    @LogDecorator
    def add(...):...
    # 完全等价于这行代码：
    add = LogDecorator(add)
    ````
    
    # 3. 调用函数
    print(add(10, 20))
    print("-"*20)
    print(add(1, 2))
    
    class 外层装饰器类:
        # 第一层：接收装饰器自定义参数
        def __init__(self, 自定义参数):
            self.param = 自定义参数
    
        # 第二层：接收被装饰的目标函数
        def __call__(self, func):
            # 内层包装函数，每次调用原函数执行
            def wrapper(*args, **kwargs):
                # 前置逻辑，可使用self.param配置
                res = func(*args, **kwargs)
                # 后置逻辑
                return res
            return wrapper
    
    # 使用语法（括号传参）
    @外层装饰器类(自定义参数)
    def 目标函数():
        ...class TipDecorator:
        # 接收装饰器传入的提示文本
        def __init__(self, tip):
            self.tip_msg = tip
    
        # 接收被装饰函数
        def __call__(self, func):
            def wrapper(*args, **kwargs):
                print(f"【{self.tip_msg}】开始执行")
                result = func(*args, **kwargs)
                print(f"【{self.tip_msg}】执行结束\n")
                return result
            return wrapper
    
    # 装饰时传入自定义参数
    @TipDecorator(tip="奶茶订单结算")
    def calc_total(price, num):
        return price * num
    
    calc_total(12, 3)
    calc_total(15, 2)

#### 2.5 实现缓存管理

##### 1.方案 1：无参类装饰器（基础缓存，自动复用计算结果）

     class CacheManager:
        def __init__(self, func):
            self.func = func
            # 缓存容器：key=参数标识，value=函数返回结果
            self.cache = {}
    
        def __call__(self, *args, **kwargs):
            # 将位置参数、关键字参数转为唯一可哈希key
            cache_key = (args, frozenset(kwargs.items()))
            # 命中缓存：直接返回，不执行原函数
            if cache_key in self.cache:
                print(f"✅ 缓存命中，直接读取结果")
                return self.cache[cache_key]
            # 未命中缓存：执行原函数计算
            print(f"❌ 无缓存，执行函数计算")
            result = self.func(*args, **kwargs)
            # 存入缓存，下次同参数直接读取
            self.cache[cache_key] = result
            return result
    
    # 测试：模拟高耗时计算函数
    @CacheManager
    def calc_square_sum(a, b):
        print("正在执行复杂平方运算...")
        return a**2 + b**2
    
    # 第一次调用：无缓存，执行计算
    print(calc_square_sum(3, 4))
    print("-" * 40)
    # 第二次同参数：命中缓存，跳过计算
    print(calc_square_sum(3, 4))
    print("-" * 40)
    # 新参数：重新计算并存入缓存
    print(calc_square_sum(2, 5))
    # 查看全部缓存数据
    print("当前全部缓存：", calc_square_sum.cache)

#### 2.方案 2：带参数类装饰器（可自定义缓存最大容量，自动淘汰旧缓存）

    class CacheLimit:
        # 第一层：接收装饰器自定义参数（缓存最大容量）
        def __init__(self, max_size):
            self.max_size = max_size
    
        # 第二层：接收被装饰的业务函数
        def __call__(self, func):
            # 内部包装类，存储缓存与调用顺序
            class CacheWrapper:
                def __init__(self, f):
                    self.func = f
                    self.cache = {}  # 缓存存储
                    self.record_order = []  # 记录参数调用顺序，用于淘汰旧数据
    
                def __call__(self, *args, **kwargs):
                    cache_key = (args, frozenset(kwargs.items()))
                    # 1. 缓存命中
                    if cache_key in self.cache:
                        self.record_order.remove(cache_key)
                        self.record_order.append(cache_key)
                        print("✅ 缓存命中")
                        return self.cache[cache_key]
                    # 2. 无缓存，执行计算
                    res = self.func(*args, **kwargs)
                    # 3. 缓存已满，删除最早存入的数据
                    if len(self.cache) >= self.max_size:
                        old_key = self.record_order.pop(0)
                        del self.cache[old_key]
                        print(f"⚠️ 缓存已满，清理旧参数：{old_key}")
                    # 4. 新结果存入缓存
                    self.cache[cache_key] = res
                    self.record_order.append(cache_key)
                    print("📦 新增缓存")
                    return res
            return CacheWrapper(func)
    
    # 使用：设置最多保存2条缓存
    @CacheLimit(max_size=2)
    def calc(x):
        print(f"执行计算 x={x}")
        return x * 10
    
    calc(1)
    calc(2)
    calc(3)  # 超出容量，删除1的缓存
    calc(1)  # 重新计算，新增缓存
    print("缓存数据：", calc.cache)

## 

## 二.异步

##### 1.异步：程序执行某个耗时任务时，不等待它完成，而是继续执行后面的代码，等任务完成后再回来处理结果。

    点奶茶
    ↓
    拿号码牌
    ↓
    去逛街
    ↓
    奶茶好了通知你
    ↓
    回来拿
    等待期间可以干其他事情。

#### 2.. 为什么需要异步

    因为程序中有大量耗时操作：
    
    例如：
    
    网络请求
    文件读写
    数据库查询
    API调用
    爬虫
    AI模型调用

#### 3.Python异步核心语

    （1）async 定义异步函数：
    （2）await 等待异步任务完成
    （3）asyncio 运行异步程序
    
    async def：定义异步函数，直接调用只会生成协程对象，不会执行逻辑
    await：只能写在 async 函数内，交出事件循环，等待异步 IO 完成；不能跟同步阻塞函数（time.sleep），需用asyncio.sleep
    asyncio：内置异步库，asyncio.run()启动事件循环，asyncio.gather()实现多任务并发执行
    
    ！1！：：
    import asyncio
    
    # 定义异步函数，模拟耗时IO
    async def drink_water():
        print("开始接水，等待2秒")
        await asyncio.sleep(2)  # 异步等待，不阻塞程序
        print("接水完成")
        return "一杯温水"
    
    # 主协程，统一调度
    async def main():
        print("准备喝水")
        res = await drink_water()  # 等待任务执行完毕
        print(f"拿到：{res}")
    
    # 程序入口
    asyncio.run(main())

    import asyncio
    import time
    
    # 三个模拟IO任务
    async def task_sleep1():
        await asyncio.sleep(2)
        print("任务1完成（2s）")
    
    async def task_sleep2():
        await asyncio.sleep(4)
        print("任务2完成（4s）")
    
    async def task_sleep3():
        await asyncio.sleep(6)
        print("任务3完成（6s）")
    
    async def main():
        start = time.time()
        # 并发同时启动三个任务
        await asyncio.gather(
            task_sleep1(),
            task_sleep2(),
            task_sleep3()
        )
        end = time.time()
        print(f"异步并发总耗时：{round(end-start)} 秒")
    
    asyncio.run(main())
