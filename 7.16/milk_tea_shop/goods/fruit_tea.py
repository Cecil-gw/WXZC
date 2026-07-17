import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from random import randint
from shop_tools import global_stock, stock_lock, check_positive
from goods.base_drink import BaseDrink


class FruitTea(BaseDrink):
  def __init__ (self,name:str,price:float):
    super().__init__(name,price)
    self.stock = global_stock.get(name,0)
    self.price = price
    print("今天买三杯水果茶享受9折优惠哦！")
    print("今日特价：",name,":",price,"元/杯")

  def get_final_price(self,buy_num:int)->float:
    if not check_positive(buy_num):
      raise ValueError("购买数量必须为正数")
    if buy_num > self.stock:
      raise ValueError(f"库存不足，当前剩余{self.stock}杯")
    
    if buy_num >= 3:
      return self.price * buy_num * 0.9 * BaseDrink.shop_discount
    else:
      return self.price * buy_num * BaseDrink.shop_discount
    

if __name__ == "__main__":
  fruit_tea = FruitTea("杨枝甘露",16)
  print("2杯杨枝甘露总价：",fruit_tea.get_final_price(2))
  print("3杯杨枝甘露总价：",fruit_tea.get_final_price(3))