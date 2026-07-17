class CallCounter:
    def __init__(self, func):
        self.count=0
        self.func=func

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.func(*args, **kwargs)

    def get_count(self):
        return self.count

@CallCounter
def hello():
    print("Hello World")

hello()
hello()
hello()

# 外部调用装饰器实例的方法
print("总调用次数：", hello.get_count())