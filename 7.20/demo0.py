import time
import threading
from datetime import datetime
import asyncio 

class AIModel:
    def __init__(self, name, model_type):
        self.name = name
        self.model_type = model_type

    def predict(self, input_data):
        print(f"{self.name}收到输入：{input_data}")
        return "父类默认结果"


class TextModel(AIModel):
    def predict(self, input_data):
        print(f"文本模型{self.name}生成中...")
        time.sleep(1)
        return f"文本结果: {input_data}"


class ImageModel(AIModel):
    def predict(self, input_data):
        print(f"图像模型{self.name}识别中...")
        time.sleep(2)
        return f"图像结果: {input_data}"


records = []
lock = threading.Lock()


def user_request(user_name, model, input_data):
    start = datetime.now()
    result = model.predict(input_data)
    end = datetime.now()
    cost = (end - start).total_seconds()
    with lock:
        records.append({
            "user": user_name,
            "model": model.name,
            "cost": cost,
            "result": result
        })


text_model = TextModel("GPT小助手", "文本生成")
image_model = ImageModel("图像识别器", "图像识别")

total_start = datetime.now()
threads = [
    threading.Thread(target=user_request, args=("用户A", text_model, "写首诗")),
    threading.Thread(target=user_request, args=("用户B", text_model, "讲个笑话")),
    threading.Thread(target=user_request, args=("用户C", image_model, "cat.jpg")),
    threading.Thread(target=user_request, args=("用户D", image_model, "dog.jpg")),
]
for t in threads:
    t.start()
    t.join()

    
total_end = datetime.now()

print("\n=== 请求明细 ===")
for r in records:
    print(f"{r['user']} -> {r['model']}，耗时{r['cost']:.2f}秒，结果：{r['result']}")

print(f"\n串行总耗时：{(total_end - total_start).total_seconds():.2f}秒")