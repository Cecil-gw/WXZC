from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from typing import List
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

products = {
        "编程书": [{"name": "Python入门", "price": 59}, {"name": "LangChain实战", "price": 89}],
        "AI书": [{"name": "智能体开发", "price": 129}, {"name": "大模型原理", "price": 99}],
        "工具书": [{"name": "Git实战", "price": 49}, {"name": "Docker入门", "price": 69}],
    }

@tool
def get_course_info(keyword:str):
    """
    模拟课程数据库，根据关键词返回相关课程
    Args:
        keyword: 查询课程的关键词，例如 "编程书"、"AI书"、"工具书"
    """
    print(f"🔧【调用工具 get_course_info】 参数 keyword = {keyword}")
    if keyword in products:
        print(f"课程介绍：名字:{products[keyword][0]['name']}，价格:{products[keyword][0]['price']}元")
        return products[keyword]
    else:
        return f"未找到与'{keyword}'相关的课程信息。"

@tool
def assess_level(current, target):
    """
    评估学生当前水平到目标水平的学习差距
    Args:
        current: 学生当前掌握水平，例如 "零基础"、"会Python基础"
        target: 想要达到的目标水平，例如 "AI智能体开发"
    """
    print(f"🔧【调用工具 assess_level】 参数 current = {current}, target = {target}")
    gap_map = {
        ("零基础", "Python入门"): "差距较小，需要掌握变量、循环、函数基础语法",
        ("会Python基础", "LangChain实战"): "差距中等，需要学习大模型调用、提示词、Agent基础",
        ("会Python基础", "AI智能体开发"): "差距较大，需要学习LangGraph、工具调用、多轮会话架构"
    }
    key = (current, target)
    if key in gap_map:
        return f"水平评估结果：当前【{current}】→目标【{target}】，差距描述：{gap_map[key]}"
    else:
        return f"水平评估结果：当前【{current}】→目标【{target}】，需要系统学习对应课程补齐知识缺口。"

    
def assess_level(current: str, target: str):
    """
    评估学生当前水平到目标水平的学习差距
    Args:
        current: 学生当前掌握水平，例如 "零基础"、"会Python基础"
        target: 想要达到的目标水平，例如 "AI智能体开发"
    """
    print(f"🔧【调用工具 assess_level】 参数 current = {current}, target = {target}")
    # 纯本地简单评估逻辑，不要调用agent、不要调用其他tool
    gap_map = {
        ("零基础", "Python入门"): "差距较小，需要掌握变量、循环、函数基础语法",
        ("会Python基础", "LangChain实战"): "差距中等，需要学习大模型调用、提示词、Agent基础",
        ("会Python基础", "AI智能体开发"): "差距较大，需要学习LangGraph、工具调用、多轮会话架构"
    }
    key = (current, target)
    if key in gap_map:
        return f"水平评估结果：当前【{current}】→目标【{target}】，差距描述：{gap_map[key]}"
    else:
        return f"水平评估结果：当前【{current}】→目标【{target}】，需要系统学习对应课程补齐知识缺口。"


@tool
def generate_study_plan(hours_per_day: float, total_days: int):
    """
    根据每天学习小时数和总天数生成学习计划表
    Args:
        hours_per_day: 每天投入学习小时数
        total_days: 总的学习天数
    """
    print(f"🔧【调用工具 generate_study_plan】 参数 hours_per_day = {hours_per_day}, total_days = {total_days}")
    total_hours = hours_per_day * total_days
    plan = f"""
    =====学习计划表=====
    每日学习时长：{hours_per_day} 小时
    总学习天数：{total_days} 天
    合计总学时：{total_hours} 小时
    阶段1(前{total_days//3}天)：基础概念学习，完成课程例题
    阶段2(中间{total_days//3}天)：项目实操练习，动手写代码
    阶段3(剩余{total_days - 2*(total_days//3)}天)：综合项目复盘、查漏补缺
    """
    return plan.strip()

tools = [get_course_info, assess_level, generate_study_plan]
agent = create_react_agent(model=llm, tools=tools)

if __name__ == "__main__":
    messages = []

    while True:
        user_input = input("\n👤用户：")
        # 退出判断
        if user_input.lower() in ["exit", "quit"]:
            print("👋会话结束")
            break

        # 1.把新用户消息追加进历史列表
        messages.append(("user", user_input))

        # 2.invoke传入全部历史消息
        result = agent.invoke({"messages": messages})

        # 3.拿回执行完毕后的完整消息，更新历史（包含工具调用、工具返回、AI回答）
        messages = result["messages"]

        # 取最后一条消息，就是agent最终输出
        final_msg = messages[-1]
        print(f"🤖学习规划师：{final_msg.content}")