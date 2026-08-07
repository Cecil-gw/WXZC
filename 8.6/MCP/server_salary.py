from fastmcp import FastMCP

mcp = FastMCP("salary-server")

@mcp.tool()
def calc_salary(base: float, experience_years: int) -> float:
    """
    计算逐年涨薪后的薪资，每年涨幅8%
    Args:
        base: 基础月薪
        experience_years: 工作年数
    """
    print(f"[server_salary] call base={base}, experience_years={experience_years}")
    salary = base * pow(1.08, experience_years)
    return round(salary, 2)

if __name__ == "__main__":
    mcp.run(transport="stdio")