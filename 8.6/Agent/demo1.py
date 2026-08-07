from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from typing import List
import requests
import ast
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent


load_dotenv(r"D:\wx26.7.14\8.5\langchain\.env", override=True)

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

print("===环境变量校验===")
print(f"API_KEY前缀：{API_KEY[:10]}")
print(f"BASE_URL：{BASE_URL}")
print(f"接入点ID：{MODEL_NAME}")
print("==================")

llm = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
    temperature=0.3
)


@tool 
def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息
    """
    print(f"🔧【调用工具 get_weather】 参数 city = {city}")  
    weather_key = "7e42250bc86c488d99522459260608"
    url = "https://api.weatherapi.com/v1/current.json"
    params = {
        "key": weather_key,
        "q": city,
        "aqi": "no"
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        if "error" in data:
            return f"天气查询失败：{data['error']['message']}"

        loc = data["location"]
        curr = data["current"]
        location_name = loc["name"]
        region = loc["region"]
        country = loc["country"]
        temp_c = curr["temp_c"]
        feelslike_c = curr["feelslike_c"]
        condition_text = curr["condition"]["text"]
        wind_kph = curr["wind_kph"]
        wind_dir = curr["wind_dir"]
        humidity = curr["humidity"]

        return (
            f"【{location_name}, {region}, {country}】\n"
            f"天气状况：{condition_text}\n"
            f"实时温度：{temp_c} ℃，体感温度：{feelslike_c} ℃\n"
            f"风向风速：{wind_dir} {wind_kph} km/h\n"
            f"湿度：{humidity}%"
        )
    except Exception as e:
        print(f"❌天气接口异常: {repr(e)}")
        return f"天气接口请求异常：{str(e)}"
@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """
    货币汇率换算，把一种货币转换成另一种货币
    Args:
        amount: 换算金额，数字
        from_currency: 源货币代码，例如 CNY、USD、EUR
        to_currency: 目标货币代码，例如 CNY、USD、EUR
    """
    print(f"🔧【调用工具 convert_currency】 amount={amount}, from={from_currency}, to={to_currency}")
    try:
        resp = requests.get(f"https://open.er-api.com/v6/latest/{from_currency.upper()}", timeout=10)
        data = resp.json()
        if data["result"] != "success":
            return "汇率获取失败"
        rate = data["rates"][to_currency.upper()]
        result = amount * rate
        return f"{amount} {from_currency} = {result:.2f} {to_currency}"
    except Exception as e:
        return f"货币换算出错：{str(e)}"


@tool
def get_joke() -> str:
    """获取一条随机笑话"""
    print(f"🔧【调用工具 get_joke】")
    import random
    joke_list = [
        "为什么程序员分不清万圣节和圣诞节？因为 Oct 31 = Dec 25",
        "世界上有10种人，懂二进制的和不懂二进制的。",
        "程序员为什么讨厌大自然？BUG太多。",
        "程序有两种bug：一种是已知的，一种是未知的。"
    ]
    return f"笑话：{random.choice(joke_list)}"


@tool
def calculate(expression: str) -> str:
    """
    安全数学计算器，计算数学表达式，支持加减乘除括号。只做数学运算，不要执行其他代码。
    Args:
        expression: 数学表达式字符串，例如 "(10+20)*3"
    """
    print(f"🔧【调用工具 calculate】 expression = {expression}")
    safe_nodes = {ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp,
                  ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub}
    try:
        tree = ast.parse(expression, mode="eval")
        for node in ast.walk(tree):
            if type(node) not in safe_nodes:
                return "表达式包含不安全运算，拒绝计算"
        res = eval(compile(tree, filename="<ast>", mode="eval"))
        return f"计算结果 {expression} = {res}"
    except Exception as e:
        return f"计算错误：{str(e)}"

# 工具列表
tools = [get_weather, convert_currency, get_joke, calculate]

agent = create_react_agent(model=llm, tools=tools)

if __name__ == "__main__":
  print("\n=====多功能生活助手启动，输入exit退出=====")
  while True:
      user_input = input("\n👤你：")
      if user_input.strip().lower() == "exit":
          print("👋退出助手")
          break
      result = agent.invoke({"messages": [("user", user_input)]})
      final_msg = result["messages"][-1]
      print(f"🤖助手：{final_msg.content}")