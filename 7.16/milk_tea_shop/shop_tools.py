import threading as thr
from datetime import datetime as d

stock_lock = thr.Lock()
threading_task=[]

global_stock = {
    "珍珠奶茶": 50, "杨枝甘露": 30, "芝士葡萄": 40, "美式咖啡": 60,
    "卡布奇诺": 20, "拿铁": 25, "摩卡": 30, "焦糖玛奇朵": 35,
    "抹茶拿铁": 28, "红茶拿铁": 22, "柠檬红茶": 18, "蜂蜜柚子茶": 20,
    "芒果冰沙": 25, "草莓冰沙": 30, "蓝莓冰沙": 28, "西瓜冰沙": 22,
    "百香果冰沙": 24, "巧克力冰沙": 26, "香草冰沙": 27,
    "抹茶冰沙": 29, "咖啡冰沙": 31
}

sell_price = {
    "珍珠奶茶": 12, "杨枝甘露": 14, "芝士葡萄": 16, "美式咖啡": 15,
    "卡布奇诺": 18, "拿铁": 20, "摩卡": 22, "焦糖玛奇朵": 24,
    "抹茶拿铁": 19, "红茶拿铁": 17, "柠檬红茶": 15, "蜂蜜柚子茶": 16,
    "芒果冰沙": 18, "草莓冰沙": 20, "蓝莓冰沙": 19, "西瓜冰沙": 17,
    "百香果冰沙": 18, "巧克力冰沙": 21, "香草冰沙": 22,
    "抹茶冰沙": 23, "咖啡冰沙": 25
}


# 创建订单
def create_order(customer: str, drink: str, num: int):
    return [customer, drink, num]


# 检查订单
def check_order(order):
    customer, drink, num = order

    if drink not in global_stock:
        print(f"尊敬的{customer}，饮品{drink}不存在")
        return False

    if global_stock[drink] < num:
        print(f"尊敬的{customer}，库存还有{global_stock[drink]}，目前数量不足，无法售卖{num}杯{drink}")
        return False
    if num <= 0:
        print(f"尊敬的{customer}，数量不能小于等于0")
        return False
    

    return True

def check_positive(num):
    """
    检查数字是否为正数
    :param num: 数字
    :return: True如果是正数，否则False
    """
    return isinstance(num, (int, float)) and num > 0

# 计算价格
def price_calculate(order):
    customer, drink, num = order
    return sell_price[drink] * num


# 更新库存
def update_stock(order):
    customer, drink, num = order
    with stock_lock:#加锁
        global_stock[drink] -= num


# 写入订单
def order_record(order, total_price):
    customer, drink, num = order

    with open("order.txt", "a", encoding="utf-8") as f:
        f.write(
            f"顾客：{customer} "
            f"饮品：{drink} "
            f"数量：{num} "
            f"总价：{total_price} "
            f"下单时间：{d.now()}\n"
        )


# 读取订单
def read_order():
    with open("order.txt", "r", encoding="utf-8") as f:
        content = f.readlines()

    return content


# 点单mian()
def serial_order(order):
   if check_order(order):
       total_price = price_calculate(order)
       update_stock(order)
       order_record(order, total_price)
       print(f"尊敬的{order[0]}，您已成功购买{order[1]}{order[2]}杯，共计{total_price}元")
       return True
       
   else:
       raise ValueError("订单不合法，无法处理")
       
