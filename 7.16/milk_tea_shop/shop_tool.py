import threading
#全局共享库存（全局变量，所有线程都公用，必须提前定义）
stock_lock = threading.Lock()
global_stock =  {"珍珠奶茶": 50, "杨枝甘露": 30, "芝士葡萄": 40, "美式咖啡": 60}


def save_order_with_with(oder_info:str):
    with open("order.txt", "a", encoding="utf-8") as f:
        f.write(oder_info + "\n")
    print("订单保存成功,文件已自动关闭")

def read_all_orders():
    """
    读取所有订单
    """
    with open("order.txt", "r", encoding="utf-8") as f:
        content = f.readlines()
    return content

#输入({"珍珠奶茶": 12, "杨枝甘露": 16, "芝士葡萄": 15, "美式咖啡": 10},14)，返回['珍珠奶茶', '美式咖啡']
def get_cheap_drinks(drink_dict:list, limit:int) -> list:
    """
    获取价格低于等于limit的饮料
    """
    if not isinstance(drink_dict,dict):
        raise TypeError("drink_dict必须是字典类型")
    cheap_data = {name:p for name, p in drink_dict.items() if p <= limit}
    return list(cheap_data.keys())

#输入[("珍珠奶茶", 2, 24), ("杨枝甘露", 1, 16)]，每次返回"饮品：珍珠奶茶,数量：2, 总价：24"和"饮品：杨枝甘露,数量：1, 总价：16"
def order_record_generator(order_list:list):
    for order in order_list:
        yield f"饮品：{order[0]},数量：{order[1]}, 总价：{order[2]}"

# ==================== 多线程库存管理 ====================
def sell_drink_thread_safe(drink_name: str, sell_num: int):
    """
    安全售卖饮品，使用线程锁保证库存安全
    """
    with stock_lock:
        if drink_name not in global_stock:
            print(f"饮品{drink_name}不存在")
            return False
        if global_stock[drink_name] < sell_num:
            print(f"库存不足，无法售卖{sell_num}杯{drink_name}")
            return False
        # 模拟售卖过程
        global_stock[drink_name] -= sell_num
        print(f"成功售卖{sell_num}杯{drink_name},剩余库存：{global_stock[drink_name]}")
        return True

def multi_thread_sell():
    """
    多线程安全售卖
    """
    # 创建多个线程，模拟多个顾客同时购买
    threads = []
    for i in range(10):
        t = threading.Thread(target=sell_drink_thread_safe, args=("珍珠奶茶", 1))
        threads.append(t)
        t.start()
    # 等待所有线程执行完毕
    for t in threads:
        t.join()


       
# ==================== 模块测试代码 ====================
# 以下代码仅在直接运行 shop_tools.py 时执行（python shop_tools.py）
# 被其他文件导入时不会执行
if __name__ == "__main__":
    #1.测试文件操作
    save_order_with_with("珍珠奶茶,2,24")
    save_order_with_with("杨枝甘露,1,16")
    orders = read_all_orders()
    print(orders)

    #2.测试列表推导式
    print(get_cheap_drinks({"珍珠奶茶": 12, "杨枝甘露": 16, "芝士葡萄": 15, "美式咖啡": 10},14))

    #3.测试生成器
    for record in order_record_generator([("珍珠奶茶", 2, 24), ("杨枝甘露", 1, 16)]):
        print(record)        
    # order_record_generator([("珍珠奶茶", 2, 24), ("杨枝甘露", 1, 16)])


    # 6. 测试线程锁
    print("\n--- 测试6：多线程安全售卖 ---")
    print(f"售卖前珍珠奶茶库存：{global_stock['珍珠奶茶']}")
    multi_thread_sell()
    print(f"售卖后珍珠奶茶库存：{global_stock['珍珠奶茶']}")
