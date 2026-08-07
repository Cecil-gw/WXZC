from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from typing import List
import requests
import ast
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

load_dotenv(r"D:\wx26.7.14\8.5\langchain\.env", override=True)

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

print("===环境变量校验===")
print(f"API_KEY前缀：{API_KEY[:10]}")
print(f"BASE_URL：{BASE_URL}")
print(f"接入点ID：{MODEL_NAME}")
print("==================")

llm = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
    temperature=0.3
)

# ==================== 工具函数定义 ====================

@tool
def query_order(order_id: str) -> str:
    """
    根据订单号查询订单的当前状态和详细信息。

    该函数模拟从订单系统获取订单数据，返回包含订单状态、物流信息、商品列表等内容的描述。
    支持常见状态：已下单、已付款、已发货、已签收、已取消。

    参数:
        order_id (str): 订单编号，格式例如 'ORD20260805001'

    返回:
        str: 包含订单状态、物流单号、商品清单的格式化字符串。
             若订单不存在，返回 "订单未找到"。
    """
    print(f"🔧【调用工具 query_order】 参数 order_id = {order_id}")
    # 模拟数据（实际生产环境会查询数据库或API）
    mock_orders = {
        "ORD20260805001": {
            "status": "已发货",
            "tracking": "SF1234567890",
            "items": ["手机壳 x2", "数据线 x1"],
            "total": 89.90
        },
        "ORD20260805002": {
            "status": "已签收",
            "tracking": "YT9876543210",
            "items": ["蓝牙耳机 x1"],
            "total": 299.00
        },
        "ORD20260805003": {
            "status": "已付款",
            "tracking": None,
            "items": ["运动鞋 x1"],
            "total": 459.00
        }
    }
    order = mock_orders.get(order_id)
    if not order:
        return f"订单 {order_id} 未找到，请确认订单号是否正确。"
    return (f"订单 {order_id} 状态：{order['status']}\n"
            f"物流单号：{order['tracking'] or '暂无'}\n"
            f"商品：{', '.join(order['items'])}\n"
            f"总金额：¥{order['total']:.2f}")

@tool
def calculate_refund(original_price: float, discount: float, days_since_purchase: int) -> str:
    """
    根据原始价格、折扣金额和购买天数计算可退款的金额。

    退款规则模拟：
        - 7天内无理由退货，全额退款（原价 - 折扣）
        - 8~15天内退货，扣除 10% 折旧费
        - 16~30天内退货，扣除 30% 折旧费
        - 超过30天不予退款

    参数:
        original_price (float): 商品原价，例如 299.00
        discount (float): 已享受的优惠金额，例如 30.00
        days_since_purchase (int): 距离购买日期的天数

    返回:
        str: 退款金额（保留两位小数）以及计算说明。
    """
    print(f"🔧【调用工具 calculate_refund】 参数 original_price = {original_price}, discount = {discount}, days_since_purchase = {days_since_purchase}")
    base_price = original_price - discount  # 实际支付金额
    if days_since_purchase <= 7:
        refund = base_price
        reason = "7天内无理由退货，全额退款"
    elif days_since_purchase <= 15:
        refund = base_price * 0.9
        reason = "8~15天内退货，扣除10%折旧费"
    elif days_since_purchase <= 30:
        refund = base_price * 0.7
        reason = "16~30天内退货，扣除30%折旧费"
    else:
        return "购买超过30天，不支持退款。"
    return f"退款金额：¥{refund:.2f}（{reason}）"

@tool
def recommend_product(category: str, budget: float) -> str:
    """
    根据商品品类和预算推荐合适的商品列表。

    模拟推荐逻辑，内置常见品类的热门商品及价格。优先推荐价格在预算范围内且性价比高的商品。

    参数:
        category (str): 商品品类，如 "手机"、"耳机"、"运动鞋"、"电脑"、"家居"。
        budget (float): 用户预算金额，例如 3000.00

    返回:
        str: 推荐的商品名称、价格和推荐理由，若品类无匹配则提示。
    """
    print(f"🔧【调用工具 recommend_product】 参数 category = {category}, budget = {budget}")
    # 模拟商品库
    product_db = {
        "手机": [
            {"name": "Xiaomi 14", "price": 3999, "score": 4.8},
            {"name": "iPhone 15", "price": 5999, "score": 4.9},
            {"name": "Redmi Note 13", "price": 1599, "score": 4.6}
        ],
        "耳机": [
            {"name": "Sony WH-1000XM5", "price": 2499, "score": 4.9},
            {"name": "AirPods Pro 2", "price": 1899, "score": 4.7},
            {"name": "Xiaomi Buds 4", "price": 699, "score": 4.3}
        ],
        "运动鞋": [
            {"name": "Nike Air Max", "price": 899, "score": 4.5},
            {"name": "Adidas Ultraboost", "price": 1299, "score": 4.6},
            {"name": "Li-Ning 飞电", "price": 699, "score": 4.4}
        ],
        "电脑": [
            {"name": "MacBook Air M3", "price": 8999, "score": 4.9},
            {"name": "联想 ThinkPad X1", "price": 7499, "score": 4.7},
            {"name": "华为 MateBook 14", "price": 5999, "score": 4.6}
        ],
        "家居": [
            {"name": "小米智能灯", "price": 199, "score": 4.2},
            {"name": "IKEA 沙发", "price": 3999, "score": 4.5},
            {"name": "戴森吸尘器", "price": 3290, "score": 4.8}
        ]
    }
    products = product_db.get(category)
    if not products:
        return f"抱歉，当前没有 '{category}' 品类的商品推荐。"
    # 筛选预算内且按评分排序
    candidates = [p for p in products if p["price"] <= budget]
    if not candidates:
        # 如果预算不够，推荐最便宜的商品
        cheapest = min(products, key=lambda x: x["price"])
        return f"预算 ¥{budget:.2f} 不足以购买该品类商品，最接近的选择是：{cheapest['name']}，价格 ¥{cheapest['price']:.2f}（评分 {cheapest['score']}）"
    # 按评分降序，取前3
    candidates.sort(key=lambda x: x["score"], reverse=True)
    top = candidates[:3]
    result = f"根据您的预算 ¥{budget:.2f}，为您推荐 '{category}' 品类商品：\n"
    for p in top:
        result += f"  • {p['name']} - ¥{p['price']:.2f}（评分 {p['score']}）\n"
    return result.strip()

@tool
def check_coupon(product_price: float) -> str:
    """
    根据商品价格计算可用的最优优惠券组合，返回折扣后价格和使用的优惠券说明。

    优惠券规则：
        - 满100减10
        - 满200减30
        - 满500减80
    系统自动选择满减力度最大的券（不可叠加，只能选其一）。

    参数:
        product_price (float): 商品原价，例如 250.00

    返回:
        str: 包含最佳优惠券名称、优惠金额、最终支付价格的信息。
    """
    print(f"🔧【调用工具 check_coupon】 参数 product_price = {product_price}")
    coupons = {
        "满100减10": {"threshold": 100, "discount": 10},
        "满200减30": {"threshold": 200, "discount": 30},
        "满500减80": {"threshold": 500, "discount": 80}
    }
    best = None
    best_discount = 0
    for name, info in coupons.items():
        if product_price >= info["threshold"] and info["discount"] > best_discount:
            best = name
            best_discount = info["discount"]
    if best is None:
        return f"商品价格 ¥{product_price:.2f} 未达到任何优惠券门槛，无优惠可用。"
    final_price = product_price - best_discount
    return (f"最佳优惠券：{best}，优惠 ¥{best_discount:.2f}\n"
            f"原价 ¥{product_price:.2f} → 最终支付 ¥{final_price:.2f}")

@tool
def get_shipping_fee(city: str) -> str:
    """
    根据收货城市计算运费。

    模拟运费规则：
        - 一线城市（北京、上海、广州、深圳）：免运费（0元）
        - 二线城市（如杭州、成都、武汉等）：8元
        - 其他城市/偏远地区：15元
        - 特殊区域（西藏、新疆）额外加收10元

    参数:
        city (str): 城市名称，例如 "成都"

    返回:
        str: 运费金额以及说明。
    """
    print(f"🔧【调用工具 get_shipping_fee】 参数 city = {city}")
    # 定义城市分类（实际生产可使用地理编码）
    tier1 = {"北京", "上海", "广州", "深圳"}
    tier2 = {"杭州", "成都", "武汉", "南京", "重庆", "西安", "长沙", "郑州", "东莞", "青岛"}
    special = {"西藏", "新疆", "内蒙古", "青海", "甘肃"}
    city = city.strip()
    if city in tier1:
        fee = 0
        reason = "一线城市免运费"
    elif city in tier2:
        fee = 8
        reason = "二线城市运费8元"
    elif city in special:
        fee = 25  # 15 + 10
        reason = "偏远地区运费15元，额外加收10元"
    else:
        fee = 15
        reason = "标准运费15元"
    return f"收货城市：{city}\n运费：¥{fee:.2f}（{reason}）"

# ==================== Agent 创建 ====================

tools = [query_order, calculate_refund, recommend_product, check_coupon, get_shipping_fee]

agent = create_react_agent(model=llm, tools=tools)

# ==================== 交互循环 ====================

if __name__ == "__main__":
    print("智能客服 Agent 已启动，输入 'exit' 或 'quit' 退出。")
    while True:
        user_input = input("用户输入：")
        if user_input.lower() in ["exit", "quit"]:
            print("感谢使用，再见！")
            break
        response = agent.invoke({"messages": [("user", user_input)]})
        # 提取最后一条消息内容
        if "messages" in response:
            last_msg = response["messages"][-1]
            content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        else:
            content = response.get("output", str(response))
        print(f"代理响应：{content}")