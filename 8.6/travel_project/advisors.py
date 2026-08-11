# advisors.py
from config import llm
from langchain_core.prompts import ChatPromptTemplate

dest_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是目的地游玩顾问。只输出景点推荐、游玩顺序、打卡点位。不要输出预算、交通、美食、文化相关内容。用户问题：{query}")
])
dest_chain = dest_prompt | llm

# ========== 2.预算规划师 budget ==========
budget_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是预算规划师。只输出每天的费用拆分，吃、住、行各项花费预估。不要输出景点、美食、交通、文化内容。用户问题：{query}")
])
budget_chain = budget_prompt | llm

# ========== 3.交通顾问 transportation ==========
transport_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是交通顾问。只输出往返大交通、市内出行方案，要给出相关时间安排和最方便的路线。不要输出景点、预算、美食、文化内容。用户问题：{query}")
])
transport_chain = transport_prompt | llm

# ========== 4.美食顾问 food ==========
food_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是美食顾问。只输出当地特色美食、必吃菜品。不要输出景点、预算、交通、文化内容。用户问题：{query}")
])
food_chain = food_prompt | llm

# ========== 5.文化顾问 culture ==========
culture_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是文化顾问。只输出当地民俗、历史、游玩禁忌与注意事项。不要输出景点、预算、交通、美食内容。用户问题：{query}")
])
culture_chain = culture_prompt | llm

# 顾问chain字典，调度层通过key获取chain
advisor_chains = {
    "destination": dest_chain,
    "budget": budget_chain,
    "transportation": transport_chain,
    "food": food_chain,
    "culture": culture_chain
}

# 中文描述，打印分发决策日志用
advisor_desc = {
    "destination": "目的地景点顾问",
    "budget": "预算规划师",
    "transportation": "交通顾问",
    "food": "美食顾问",
    "culture": "文化顾问"
}

# ------------------- 单元测试：单独测试本文件 -------------------
if __name__ == "__main__":
    # 测试美食顾问
    res = food_chain.invoke({"query":"长沙旅游有什么好玩的"})
    print("【美食顾问输出】")
    print(res.content)