from typing import TypedDict, Annotated, Literal
import operator
from langgraph.graph import StateGraph, START, END

# ========== 1.定义全局状态（保存所有节点输出、重试计数） ==========
class AgentState(TypedDict):
    log: Annotated[list, operator.add]   # 所有节点输出日志
    topic: str                           # 项目需求主题
    marketing_output: str                # 营销部输出
    ui_output: str                       # UI设计输出
    frontend_output: str                 # 前端输出
    backend_output: str                  # 后端输出
    pm_vote: Literal["pass","reject"]    # 产品经理一票否决
    test_error_num: int                  # 测试报错数量
    test_retry_cnt: int                  # 测试环节重试计数器

# ========== 2.各个部门Agent节点函数 ==========
def agent_marketing(state:AgentState):
    """营销部Agent，生成营销方案"""
    return {
        "log":["✅营销部：输出营销推广方案"],
        "marketing_output":"营销推广方案完成"
    }

def agent_ui(state:AgentState):
    """UI设计部Agent"""
    return {
        "log":["✅UI设计部：输出界面设计稿"],
        "ui_output":"UI界面设计稿完成"
    }

def agent_frontend(state:AgentState):
    """前端部Agent"""
    return {
        "log":["✅前端部：完成前端页面代码"],
        "frontend_output":"前端代码已编写"
    }

def agent_backend(state:AgentState):
    """后端部Agent"""
    return {
        "log":["✅后端部：完成后端接口代码"],
        "backend_output":"后端接口开发完成"
    }

def agent_pm(state:AgentState):
    """扩展：产品经理，对UI+前端一票否决，这里模拟随机否决，你可以手动改pass/reject"""
    # 模拟：这里可以切换 reject / pass，测试退回逻辑
    vote = "pass"
    # vote = "reject"
    if vote == "reject":
        log_msg = "⚠️产品经理否决UI/前端，退回重做"
    else:
        log_msg = "✅产品经理审核通过UI、前端"
    return {
        "log":[log_msg],
        "pm_vote": vote
    }

def agent_test(state:AgentState):
    """测试部Agent，模拟报错数量"""
    # 模拟报错数，修改数字测试逻辑，比如4触发退回
    error_count = 4
    new_retry = state["test_retry_cnt"] + 1
    return {
        "log":[f"🧪测试部：发现{error_count}个bug"],
        "test_error_num": error_count,
        "test_retry_cnt": new_retry
    }

def agent_project_manager(state:AgentState):
    """项目经理Agent，项目收尾"""
    return {
        "log":["📋项目经理：汇总全部输出，项目收尾"]
    }

# ========== 3.条件边路由函数（核心扩展任务） ==========
def pm_route(state:AgentState) -> Literal["frontend","agent_test"]:
    """产品经理条件路由：reject→退回前端重做；pass→进入测试"""
    if state["pm_vote"] == "reject":
        return "frontend"
    else:
        return "agent_test"

def test_route(state:AgentState) -> Literal["frontend_backend_rework","project_done"]:
    """测试节点条件路由：报错>=3，且重试不超限，退回前后端；否则结束"""
    err = state["test_error_num"]
    retry = state["test_retry_cnt"]
    max_loop = 5
    if err >=3 and retry <= max_loop:
        return "frontend_backend_rework"
    else:
        return "project_done"

# ========== 4.构建图，对齐流程图 + 扩展逻辑 ==========
builder = StateGraph(AgentState)

# 添加全部节点
builder.add_node("agent_marketing", agent_marketing)
builder.add_node("agent_ui", agent_ui)
builder.add_node("agent_frontend", agent_frontend)
builder.add_node("agent_backend", agent_backend)
builder.add_node("agent_pm", agent_pm)
builder.add_node("agent_test", agent_test)
builder.add_node("agent_project_manager", agent_project_manager)

# 主流程边：START→营销→UI；UI同时输出到前端、产品经理审核
builder.add_edge(START, "agent_marketing")
builder.add_edge("agent_marketing", "agent_ui")
builder.add_edge("agent_ui", "agent_frontend")
builder.add_edge("agent_ui", "agent_backend")

# 前端完成后交给产品经理审核
builder.add_edge("agent_frontend", "agent_pm")

# 产品经理【条件边】：否决退回前端，通过进入测试
builder.add_conditional_edges(
    "agent_pm",
    pm_route,
    {
        "frontend":"agent_frontend",
        "agent_test":"agent_test"
    }
)

# 后端并行开发完成，等待测试；测试完成执行条件判断
builder.add_edge("agent_backend", "agent_test")

builder.add_conditional_edges(
    "agent_test",
    test_route,
    {
        "frontend_backend_rework":"agent_frontend", #报错多，退回前端（顺带重跑后端）
        "project_done":"agent_project_manager"
    }
)

builder.add_edge("agent_project_manager", END)

graph = builder.compile()

# ========== 5.运行测试 ==========
if __name__ == "__main__":
    init_state = {
        "log":[],
        "topic":"电商小程序开发",
        "marketing_output":"",
        "ui_output":"",
        "frontend_output":"",
        "backend_output":"",
        "pm_vote":"pass",
        "test_error_num":0,
        "test_retry_cnt":0
    }
    result = graph.invoke(init_state)
    print("\n=======工作流完整执行日志=======")
    for item in result["log"]:
        print(item)