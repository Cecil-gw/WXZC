from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

# 1. 加载环境变量
load_dotenv(r"D:\wx26.7.14\8.5\langchain\.env", override=True)

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

print(f"API_KEY: {api_key[:10]}...")   # 仅打印前10位以防泄露
print(f"BASE_URL: {base_url}")
print(f"MODEL_NAME: {model_name}")

# 2. 初始化模型（与您原来的完全一致）
llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
    temperature=0.7,
)

# 3. 定义提示模板（包含背景知识和用户问题）
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一位知识渊博的助手，请根据以下背景知识回答用户的问题。如果背景知识中没有相关信息，请直接说“我不知道”。\n\n背景知识：\n{context}"),
    ("user", "{question}")
])

# 4. 构建问答链（LCEL 风格）
qa_chain = prompt | llm

# 5. 准备测试数据
context = """
人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。
深度学习是机器学习的一个子集，它使用多层神经网络来学习数据的表示。
自然语言处理（NLP）是AI的一个领域，专注于使计算机能够理解、解释和生成人类语言。
"""
question = "什么是深度学习？"

# 6. 方式一：一次性获取完整回答（invoke）
print("=== 完整回答（invoke）===")
response = qa_chain.invoke({"context": context, "question": question})
print(response.content)
print("\n")

# 7. 方式二：流式输出（逐词打印）
print("=== 流式回答（stream）===")
for chunk in qa_chain.stream({"context": context, "question": question}):
    print(chunk.content, end="", flush=True)
print()  # 换行