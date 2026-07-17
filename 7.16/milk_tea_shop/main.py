import shop_tools
import time as t
import goods.base_drink


coffee = ["美式咖啡","卡布奇诺", "拿铁", "摩卡", "焦糖玛奇朵","抹茶拿铁", "红茶拿铁"]

fruit_tea = ["珍珠奶茶", "杨枝甘露", "芝士葡萄", "柠檬红茶", "蜂蜜柚子茶"]

def main():
    name = input("请输入您的姓名：")
    count = 0

    while True:
        t.sleep(0.5)

        print("\n========== 奶茶店 ==========")
        if count > 0:
            print(f"尊敬的{name}，您已下单 {count} 次。")

        print("1. 下单")
        print("2. 查看订单")
        print("3. 退出")

        choice = input("请输入您的选择：")

        # ---------------- 下单 ----------------
        if choice == "1":
            print("\n===== 饮品菜单 =====")
            j = 0
            for drink, price in shop_tools.sell_price.items():
                print(f"{drink}:{price}元", end="\t")
                j += 1
                if j % 3 == 0:
                    print()

            drink = input("\n请输入饮品名称：")
            try:
                num = int(input("请输入购买数量："))
            except ValueError:
                print("数量必须输入数字！")
                continue

            # 区分咖啡/普通奶茶，创建对应对象计算折后价
            if drink in coffee:
                obj = coffee(drink, shop_tools.sell_price[drink])
                total_price = obj.get_final_price(num)
            elif drink in fruit_tea:
                obj = fruit_tea(drink, shop_tools.sell_price[drink])
                total_price = obj.get_final_price(num)
            
            else:
                # 普通饮品只参与店铺折扣
                single_price = shop_tools.sell_price[drink]
                total_price = round(single_price * num * goods.base_drink.shop_discount, 2)

            # 生成订单、扣库存、写入订单日志
            order = shop_tools.create_order(name, drink, num)
            try:
                if shop_tools.check_order(order):
                    shop_tools.update_stock(order)
                    shop_tools.order_record(order, total_price)
                    print(f"尊敬的{name}，您已成功购买{drink}{num}杯，折后共计{total_price}元")
                    count += 1
                else:
                    print("订单校验失败")
            except Exception as e:
                print(e)

        # ---------------- 查看订单 ----------------
        elif choice == "2":

            orders = shop_tools.read_order()

            if len(orders) == 0:
                print("暂无订单。")
            else:
                print("\n===== 全部订单 =====")
                for line in orders:
                    print(line, end="")

        # ---------------- 退出 ----------------
        elif choice == "3":
            print("欢迎下次光临！")
            break

        else:
            print("输入有误，请重新选择！")


if __name__ == "__main__":
    main()