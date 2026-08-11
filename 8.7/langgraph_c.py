from typing import TypedDict, Annotated, Sequence
import operator
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage
import os
from dotenv import load_dotenv

# ---------------- 环境配置，读取.env ----------------
load_dotenv(override=True)

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

llm = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
    temperature=0.3
)

#主管节点（低耗模型，做路由决策，温度压低）
supervisor_llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0.1
)

# #第一步：定义状态
class AgentState(TypedDict):
  