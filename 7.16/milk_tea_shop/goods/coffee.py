import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from random import randint
from shop_tools import global_stock, stock_lock, check_positive
from goods.base_drink import BaseDrink

class Coffee(BaseDrink):
    # 实例生成时再随机折扣，每次新建咖啡对象折扣不同
    def __init__(self, name: str, price: float):
        # 严格匹配父类3个参数：people, name, price，无多余/缺失参数
        super().__init__(name, price)
        # 每次实例化生成8~9折
        self.coffee_discount = randint(80, 90) / 100
        print(f"今天{self.name}专属折扣：{self.coffee_discount * 100}%")

    def get_final_price(self, buy_num: int) -> float:
        # 咖啡折扣 + 店铺通用折扣叠加
        return self.price * buy_num * self.coffee_discount * BaseDrink.shop_discount

    # 新增：同步修改全局库存（对接shop_tools下单逻辑）
    def global_sell(self, num: int):
        if not check_positive(num):
            raise ValueError("购买数量必须为正数")
        with stock_lock:
            if global_stock[self.name] < num:
                raise ValueError(f"库存不足，当前剩余{global_stock[self.name]}杯")
            global_stock[self.name] -= num
        print(f"全局库存扣减成功，剩余{global_stock[self.name]}杯")

if __name__ == "__main__":
    # 正确传参：people / name / price 三个参数齐全
    coffee = Coffee("Lihua", "美式咖啡", 15)
    # 计算2杯总价
    print("2杯美式总价：", coffee.get_final_price(2))
    # 测试扣全局库存
    coffee.global_sell(2)
    print("当前全局美式库存：", global_stock["美式咖啡"])