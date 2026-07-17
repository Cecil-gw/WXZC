import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abc import ABC, abstractmethod 
from shop_tools import check_positive

class BaseDrink(ABC):
    """基础饮品抽象父类"""
    shop_discount = 1.0

    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price
        self.__stock = 50  # 实例私有库存（本地测试用，业务下单用global_stock）
    
    def get_stock(self) -> int:
        return self.__stock

    def sell(self, num: int):
        if not check_positive(num) or num > self.__stock:
            raise ValueError("数量非法或者库存不足")
        self.__stock -= num
        return f"售出{num}杯{self.name}，剩余{self.__stock}杯"

    @classmethod
    def set_shop_discount(cls, discount: float):
        if 0 < discount <= 1:
            cls.shop_discount = discount
            print(f"设置店铺折扣为{discount}")
        else:
            raise ValueError("折扣必须在0到1之间")

    @staticmethod
    def check_drink_name(name: str):
        if not name or name.isspace():
            raise ValueError("饮品名称不能为空")
        return name

    @abstractmethod
    def get_final_price(self, buy_num: int) -> float:
        pass

    def print_ticket(self, buy_num: int):
        total = self.get_final_price(buy_num)
        print(f"饮品：{self.name},数量：{buy_num}, 总价：{total}")

if __name__ == "__main__":
    print("===== base_drink.py 模块自测 =====\n")

    print("--- 测试1：静态方法（名称校验）---")
    print(BaseDrink.check_drink_name('珍珠奶茶'))

    print(f"初始折扣：{BaseDrink.shop_discount}")
    BaseDrink.set_shop_discount(0.9)
    print(f"设置后折扣：{BaseDrink.shop_discount}")
    BaseDrink.set_shop_discount(1.0)

    print("\n--- 测试3：抽象类实例化限制 ---")
    try:
        test = BaseDrink("奶茶", 10)
    except TypeError as e:
        print(f"抽象类无法实例化：{e}")