from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

# 1. 加载环境变量
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

# ========== 第3步 LCEL 生成自我介绍 ==========
intro_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的人力资源顾问，擅长帮人写简洁有力的自我介绍"),
    ("human", "请根据以下信息，帮我写一段 50 字以内的自我介绍。姓名：{name}，职位：{job}，技能：{skills}")
])

intro_chain = intro_prompt | llm | StrOutputParser()

# ========== 第4步 PromptTemplate 生成slogan ==========
slogan_template = PromptTemplate(
    input_variables=["name", "job"],
    template="请根据以下信息，生成一句 15 字以内的个人 slogan，要求朗朗上口。姓名：{name}，职位：{job}"
)
class Card(BaseModel):
    name: str = Field(description="姓名")
    job: str = Field(description="职位")
    intro: str = Field(description="自我介绍")
    slogan: str = Field(description="个人slogan")
    skills: List[str] = Field(description="技能列表")

card_parser = JsonOutputParser(pydantic_object=Card)

card_prompt = ChatPromptTemplate.from_messages([
    ("system", "{format_instructions}"),
    ("human", "姓名：{name}，职位：{job}，技能：{skills}。生成完整的名片JSON数据")
])

card_chain = card_prompt | llm | card_parser


if __name__ == "__main__":
    # 测试数据
    test_name = "张三"
    test_job = "Python 开发工程师"
    test_skills = "Python, LangChain, FastAPI"

    # 3.生成自我介绍
    intro_result = intro_chain.invoke({
        "name": test_name,
        "job": test_job,
        "skills": test_skills
    })
    print("【自我介绍】", intro_result, type(intro_result))

    # 4.生成slogan
    slogan_prompt_val = slogan_template.format(name=test_name, job=test_job)
    slogan_result = llm.invoke(slogan_prompt_val).content
    print("【Slogan】", slogan_result)

    # 5.生成结构化JSON名片
    card_data = card_chain.invoke({
        "format_instructions": card_parser.get_format_instructions(),
        "name": test_name,
        "job": test_job,
        "skills": test_skills
    })
    print("【结构化名片字典】", card_data, type(card_data))

    # 6.格式化打印名片
    print("============================")
    print("        AI 智能名片")
    print("============================")
    print(f"姓名：{card_data['name']}")
    print(f"职位：{card_data['job']}")
    print(f"自我介绍：{card_data['intro']}")
    print(f"个人 slogan：{card_data['slogan']}")
    print(f"技能：{', '.join(card_data['skills'])}")
    print("============================")