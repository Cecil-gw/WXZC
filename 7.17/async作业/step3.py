import asyncio
from datetime import datetime

class AIModel:
    async def predict(self, input_data):
        raise NotImplementedError("子类必须重写predict方法")


class TextModel(AIModel):
    async def predict(self, input_data):
        await asyncio.sleep(1)
        return f"文本结果:{input_data}"

class ImageModel(AIModel):
    async def predict(self, input_data):
        await asyncio.sleep(2)
        return f"图像结果:{input_data}"

async def user_request(user, model, input_data):
    start = datetime.now()
    result = await model.predict(input_data)
    end = datetime.now()
    cost = (end - start).total_seconds()
    info = {
        "user": user,
        "model": model.__class__.__name__,
        "cost_seconds": round(cost, 2),
        "result": result
    }
    print(f"用户{user} | 耗时{cost:.2f}s | {result}")
    return info

async def main():
    # 准备模型
    text_m = TextModel()
    img_m = ImageModel()
    req_list = [
        user_request("用户A", text_m, "你好"),
        user_request("用户B", text_m, "介绍Python"),
        user_request("用户C", img_m, "photo001.jpg"),
        user_request("用户D", img_m, "picture002.png")
    ]
    start_all = datetime.now()
    all_res = await asyncio.gather(*req_list)
    end_all = datetime.now()
    total_cost = (end_all - start_all).total_seconds()
    print(f"\n全部请求完成，整体总耗时：{total_cost:.2f}s")
    return all_res

if __name__ == "__main__":
    asyncio.run(main())