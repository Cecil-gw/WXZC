import json
import random
#1.字典初始化角色属性

player={
    "name": "",
    "hp":100,
    "attack":10,
    "defence":5,
    "rate":0.1,
    "level":1
}

enermy_01={
    "name": "sunshine",
    "hp":50,
    "attack":12,
    "defence":3,
    "rate":0.2,
    "level":1
}

#2.装饰器：双倍伤害的挂件

def double_damage(fn):

    def inner(*args, **kwargs):

        normal_damage = fn(*args, **kwargs)

        print("普通伤害：", normal_damage)

        double = normal_damage * 2

        print("🔥触发双倍伤害BUFF！")
        print("最终伤害：", double)

        return double

    return inner

    

#3.lambda建议基础伤害计算

#atk 攻击力 ， rate技能倍率,dfn 防御
damage_cal = lambda atk,rate,dfn : atk*(1+rate)-dfn

#4.生成器：批量产出buff效果，每次轮询一次

def buff_generator ():
    yield "攻击提升"
    yield "暴击率提升"
    yield "格挡提升"

#5.列表推导式，生成合法加点范围

points = [i for i in range (random.randint(1,6))]

#6.通用属性加点函数


def add_point(player,value):
    while value>0:
        print(f"你可以分配的点数有{value}")
        choice=input("你想添加什么属性？hp，atk，dfn or rate?")
        
        number=int(input(f"想分配多少点数？要小于{value}哦"))
        while number>value:
            number=int(input(f"点数不够哦？要小于{value}哦"))
        
        if choice == "hp":
            player["hp"]+=number*50
        elif choice == "atk":
            player["attack"]+=number
        elif choice == "dfn":
            player["defence"]+=number
        elif choice == "rate":
            player["rate"]+=number*0.01
        else:
            break
        value -= number
    return 1

#7.绑定装饰器的技能伤害函数

@double_damage
def skill(atk, rate,dfn):
    # 返回基础伤害
    return damage_cal(atk, rate,dfn)

#8.with实现角色数据存档
def save_player():
    with open("player.json", "w", encoding="utf-8") as file:
        json.dump(player, file, ensure_ascii=False, indent=4)

    print("角色数据保存成功！")

#9.实现对战效果
def fight(player,enermy):
    while(player["hp"]>0 and enermy["hp"] >0):
        # 玩家攻击
        damage = skill(
            player["attack"],
            player["rate"],
            enermy["defence"]
        )

        enermy["hp"] = int(enermy["hp"]-damage)

        print(f"{player['name']}造成{damage}点伤害")
        print(f"{enermy['name']}剩余血量：{enermy['hp']}")

        # 判断敌人是否死亡
        if enermy["hp"] <= 0:
            print("敌人被击败！")
            break

        # 敌人攻击
        damage = damage_cal(
            enermy["attack"],
            enermy["rate"],
            player["defence"]
        )

        player["hp"] = int( player["hp"]-damage)

        print(f"{enermy['name']}造成{damage}点伤害")
        print(f"{player['name']}剩余血量：{player['hp']}")

        # 判断玩家是否死亡
        if player["hp"] <= 0:
            print("你失败了！")
            break

#10.主函数：交互菜单
def main():
    print("======角色信息======")
    print("请输入您的姓名")
    name=input()
    player["name"]=name
    print("name:",player["name"])
    print("hp:",player["hp"])
    print("attack:",player["attack"])
    print("defence:",player["defence"])
    print("rate:",player["rate"])

    print("\n======属性加点======")
    print("可加点：", points[-1])

    add_point(player, points[-1])

    print("\n======BUFF效果======")
    buffs = buff_generator()

    for buff in buffs:
        print("获得BUFF：", buff)

    print("\n======技能伤害======")
    print("敌人属性:")
    print("姓名：", enermy_01["name"])
    print("血量：", enermy_01["hp"])
    print("攻击：", enermy_01["attack"])
    print("防御：", enermy_01["defence"])
    print("暴击率：", enermy_01["rate"])
    print("\n======开始战斗======")
    fight(player, enermy_01)


    print("\n======保存数据======")
    save_player()


#程序入口：
if __name__ == "__main__":
    main()


