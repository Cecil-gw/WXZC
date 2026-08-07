# main.py
import asyncio
from config import llm
from router import get_advisor_list
from scheduler import run_advisors
from advisors import advisor_desc, advisor_chains


async def chat_entry(user_input: str):
    """普通用户提问入口"""
    print(f"\n===== 用户提问：{user_input} =====")
    call_advisors = await get_advisor_list(user_input)
    advisor_result = await run_advisors(call_advisors, user_input)
    for name, content in advisor_result.items():
        print(f"\n----------【{advisor_desc[name]}】----------")
        print(content)
    return advisor_result


async def generate_travel_plan(destination: str, days: int, budget: int):
    """旅行计划生成器：不走路由，强制调用全部顾问，最后汇总"""
    user_query = f"前往{destination}，游玩{days}天，总预算{budget}元，请规划旅行。"
    print(f"\n=====【旅行计划生成器】=====")
    print(f"输入参数：{user_query}")

    force_advisors = list(advisor_chains.keys())
    print(f"【分发决策】强制调用全部顾问：{[advisor_desc[n] for n in force_advisors]}")
    advisor_out = await run_advisors(force_advisors, user_query)
    merge_prompt = f"""
                    整合下面各个专业顾问输出内容，输出一份通顺完整的旅行计划报告。
                    ---景点信息---
                    {advisor_out['destination']}
                    ---预算信息---
                    {advisor_out['budget']}
                    ---交通信息---
                    {advisor_out['transportation']}
                    ---美食信息---
                    {advisor_out['food']}
                    ---文化提示---
                    {advisor_out['culture']}
                """
    final_response = await llm.ainvoke(merge_prompt)
    print(final_response.content)
    return final_response.content


async def main():
    await chat_entry("长沙有什么好吃的？")
    await chat_entry("重庆4天3000元怎么玩？")
    await generate_travel_plan(destination="厦门", days=3, budget=2200)


if __name__ == "__main__":
    asyncio.run(main())