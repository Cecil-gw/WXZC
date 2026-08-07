from fastmcp import FastMCP

mcp = FastMCP("company-server")

@mcp.tool()
def get_company_info(company_name: str) -> str:
    """
    查询公司业务信息
    Args:
        company_name: 公司名称
    """
    print(f"[server_company] call company_name={company_name}")
    mock_db = {
        "腾讯": "腾讯：主营社交、云服务、AI大模型，技术岗待遇较好",
        "阿里": "阿里：电商、云计算、大模型业务"
    }
    return mock_db.get(company_name, f"暂无该公司信息：{company_name}")

if __name__ == "__main__":
    mcp.run(transport="stdio")