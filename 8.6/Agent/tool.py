from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from typing import List
import requests
# 1. 加载环境变量
# load_dotenv(r"D:\wx26.7.14\8.5\langchain\.env", override=True)

# API_KEY = os.getenv("API_KEY")
# BASE_URL = os.getenv("BASE_URL")
# MODEL_NAME = os.getenv("MODEL_NAME")

# print("===环境变量校验===")
# print(f"API_KEY前缀：{API_KEY[:10]}")
# print(f"BASE_URL：{BASE_URL}")
# print(f"接入点ID：{MODEL_NAME}")
# print("==================")

# llm = ChatOpenAI(
#     api_key=API_KEY,
#     base_url=BASE_URL,
#     model=MODEL_NAME,
#     temperature=0.3
# )

weather_key = "7e42250bc86c488d99522459260608"
url = "https://api.weatherapi.com/v1/current.json"
params = {
    "key": weather_key,
    "q": "London",
    "aqi": "no"
}

resp = requests.get(url, params=params, timeout=15)
print("HTTP状态码：", resp.status_code)
print("返回JSON：")
print(resp.json())