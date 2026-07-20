import time
import threading
from datetime import datetime
import asyncio 


class AIModel:
    def __init__(self, name, model_type):
        self.name = name
        self.model_type = model_type

    async def predict(self, input_data):
        print(f"{self.name}收到输入：{input_data}")
        return "父类默认结果"

class TextModel(AIModel):
    async def predict(self, input_data):
        print(f"文本模型{self.name}生成中...")
        await asyncio.sleep(1)
        return f"文本结果: {input_data}"

class ImageModel(AIModel):
    async def predict(self, input_data):
        print(f"图像模型{self.name}识别中...")
        await asyncio.sleep(2)
        return f"图像结果: {input_data}"

records = []

# 关键修复：添加 await
async def user_request(user_name, model, input_data):
    start = datetime.now()
    result = await model.predict(input_data)  # 此处补 await
    end = datetime.now()
    cost = (end - start).total_seconds()
    records.append({
        "user": user_name,
        "model": model.name,
        "cost": cost,
        "result": result
    })


async def main():
    text_model = TextModel("GPT小助手", "文本生成")
    image_model = ImageModel("图像识别器", "图像识别")

    total_start = datetime.now()
    # 创建异步任务
    tasks = [
        user_request("用户A", text_model, "写首诗"),
        user_request("用户B", text_model, "讲个笑话"),
        user_request("用户C", image_model, "cat.jpg"),
        user_request("用户D", image_model, "dog.jpg"),
    ]
    await asyncio.gather(*tasks)
    total_end = datetime.now()

    print("\n=== 请求明细 ===")
    for r in records:
        print(f"{r['user']} -> {r['model']}，耗时{r['cost']:.2f}秒，结果：{r['result']}")

    print(f"\n异步asyncio总耗时：{(total_end - total_start).total_seconds():.2f}秒")

if __name__ == "__main__":
    asyncio.run(main())
# 实际运行总耗时约 2.00 秒