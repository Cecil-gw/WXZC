# scheduler.py
import asyncio
from advisors import advisor_chains


async def run_advisors(advisor_name_list: list[str], user_query: str):
    """
    并发执行指定顾问
    :param advisor_name_list: router返回的顾问名列表，如 ["food","budget"]
    :param user_query: 用户原始提问
    :return: dict，key=顾问名，value=该顾问输出文本
    """
    task_list = []
    for name in advisor_name_list:
        chain = advisor_chains[name]
        task_list.append(chain.ainvoke({"query": user_query}))

    response_list = await asyncio.gather(*task_list)

    result_dict = {}
    for name, resp in zip(advisor_name_list, response_list):
        result_dict[name] = resp.content

    return result_dict


# --------单元测试：单独测试这个文件---------
if __name__ == "__main__":
    async def test_demo():
        # 手动指定两个顾问，模拟router输出的列表
        output = await run_advisors(["food", "destination"], "长沙旅游")
        print("====调度返回结果====")
        print(output)

    asyncio.run(test_demo())