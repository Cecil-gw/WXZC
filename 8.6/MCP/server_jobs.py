from fastmcp import FastMCP

mcp = FastMCP("job-server")

@mcp.tool()
def search_jobs(keyword: str) -> str:
    """
    根据关键词搜索岗位职位
    Args:
        keyword: 岗位关键词
    """
    print(f"[server_jobs] call keyword={keyword}")
    mock_db = {
        "Python工程师": "Python工程师，负责后端开发、大模型应用开发，基础月薪20000",
        "Java工程师": "Java工程师，后端业务开发，基础月薪22000"
    }
    return mock_db.get(keyword, f"未查询到岗位：{keyword}")

if __name__ == "__main__":
    mcp.run(transport="stdio")