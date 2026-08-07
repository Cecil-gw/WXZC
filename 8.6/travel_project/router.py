# router.py
from config import llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

route_prompt = ChatPromptTemplate.from_messages([
    ("system", """
你是任务路由分发器，禁止回答用户旅游问题，只做意图识别。
可选顾问：
destination：目的地景点
budget：预算规划
transportation：交通方案
food：美食推荐
culture：民俗文化

根据用户问题选出需要启用的顾问，严格输出JSON：{{"advisors":["xxx","xxx"]}}
示例1：用户：长沙有什么好吃的 → {{"advisors":["food"]}}
示例2：用户：西安3天2500元怎么玩 → {{"advisors":["destination","budget","transportation","food","culture"]}}
"""),
    ("human", "用户问题：{user_query}")
])

route_chain = route_prompt | llm | JsonOutputParser()

async def get_advisor_list(user_query: str):
    """输入用户问题，返回要调用的顾问名字列表，并且打印分发决策"""
    res = await route_chain.ainvoke({"user_query": user_query})
    call_list = res["advisors"]
    print(f"【分发决策】本次调用顾问：{call_list}")
    return call_list

# 单元测试
if __name__ == "__main__":
    import asyncio
    async def test():
        lst = await get_advisor_list("长沙有什么好吃的？")
        print(lst)
    asyncio.run(test())