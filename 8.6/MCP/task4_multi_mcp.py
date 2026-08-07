import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.prompts import ChatPromptTemplate

load_dotenv(r"D:\wx26.7.14\8.6\MCP\.env", override=True)

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

async def main():
    # SSE模式：需要手动启动3个server终端
    server_configs = {
        "jobs": {
            "transport": "sse",
            "url": "http://127.0.0.1:8001/sse"
        },
        "company": {
            "transport": "sse",
            "url": "http://127.0.0.1:8002/sse"
        },
        "salary": {
            "transport": "sse",
            "url": "http://127.0.0.1:8003/sse"
        },
    }

    client = MultiServerMCPClient(server_configs)
    try:
        tools = await client.get_tools()
        print(f"✅加载MCP工具数量：{len(tools)}")
        tool_names = [t.name for t in tools]
        print(f"✅工具列表: {tool_names}")
        for t in tools:
            print(f"-- {t.name} schema: {t.args_schema}")

        llm = ChatOpenAI(
            api_key=API_KEY,
            base_url=BASE_URL,
            model=MODEL_NAME,
            temperature=0.0
        )

        system_prompt = """
你是企业内部查询助手。
用户询问职位、公司、薪资，必须调用工具，绝对禁止自己编造内容。
不要输出编造的岗位、薪资。
工具清单：
search_jobs(keyword):搜索岗位
get_company_info(company_name):查询公司
calc_salary(base, experience_years):计算薪资，base基础月薪，experience_years工作年数
拿到工具返回结果之后再回答用户。
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{messages}")
        ])

        agent = create_react_agent(llm, tools, prompt=prompt)

        print("\n===== MCP多服务Agent，输入exit退出 =====")
        while True:
            user_input = input("\n👤user：")
            if user_input.strip().lower() == "exit":
                print("👋退出")
                break
            res = await agent.ainvoke({"messages": [("user", user_input)]})
            for msg in res["messages"]:
                if msg.type == "ai" and msg.content:
                    print(f"🤖agent：{msg.content}")
    except Exception as e:
        print(f"\n❌运行异常: {e}")

if __name__ == "__main__":
    asyncio.run(main())