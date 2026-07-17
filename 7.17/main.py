from fastapi import FastAPI
import asyncio # 导入fastapi
import time

# 创建服务实例app
app = FastAPI()

# 根路径GET接口
@app.get("/")
async def root():
    return {
        "message": "AI Agent启动成功"
    }

#=============================================\

async def get_weather():
    await asyncio.sleep(3)
    return "qingdao weather: 30℃"

async def search_knowledge():
    await asyncio.sleep(5)
    return "kownlege: python"

async def call_LLM():
    await asyncio.sleep(2)
    return "LLM: GPT-4"


#=============================================\

@app.get("/agent")
async def agent():
    # 获取天气
    start_time = time.time()
    # 串行依次执行，2+4+6=12秒
    weather, knowledge, answer = await asyncio.gather(
        get_weather(),
        search_knowledge(),
        call_LLM()
    )
    total_cost = round(time.time() - start_time)
    return {
        "weather": weather,
        "knowledge": knowledge,
        "answer": answer,
        "time": total_cost
    }

