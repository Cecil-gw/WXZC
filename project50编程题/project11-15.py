count = 0  
print("所有符合条件的三位数：")
for a in range(1, 5):
    for b in range(1, 5):
        for c in range(1, 5):
            if a != b and a != c and b != c:
                num = a * 100 + b * 10 + c
                print(num, end=" ")
                count += 1
print(f"\n总共有{count}个")


I = float(input("请输入当月利润(万元)："))
bonus = 0.0

if I <= 10:
    bonus = I * 0.1
elif I <= 20:
    bonus = 10 * 0.1 + (I - 10) * 0.075
elif I <= 40:
    bonus = 10*0.1 + 10*0.075 + (I - 20)*0.05
elif I <= 60:
    bonus = 10*0.1 + 10*0.075 + 20*0.05 + (I - 40)*0.03
elif I <= 100:
    bonus = 10*0.1 + 10*0.075 + 20*0.05 + 20*0.03 + (I - 60)*0.015
else:
    bonus = 10*0.1 + 10*0.075 + 20*0.05 + 20*0.03 + 40*0.015 + (I - 100)*0.01

print(f"应发放奖金：{bonus:.2f} 万元")

import math

# 遍历10万以内整数
for n in range(100000):
    x = n + 100
    y = n + 100 + 168
    m1 = math.sqrt(x)
    m2 = math.sqrt(y)
    if m1 == int(m1) and m2 == int(m2):
        print("满足条件的整数为：", n)
        break
    

year = int(input("请输入年份："))
month = int(input("请输入月份："))
day = int(input("请输入日期："))

# 每月天数，下标0占位
month_day = [0, 31,28,31,30,31,30,31,31,30,31,30,31]
total = 0

# 累加前month-1个月天数
for i in range(1, month):
    total += month_day[i]
# 加上当月日期
total += day

# 判断闰年
leap = False
if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
    leap = True

if leap and month > 2:
    total += 1

print(f"该日期是当年第{total}天")


x = int(input("请输入第一个整数："))
y = int(input("请输入第二个整数："))
z = int(input("请输入第三个整数："))

# 第一步：确保x最小
if x > y:
    x, y = y, x
if x > z:
    x, z = z, x
# 第二步：确保y < z
if y > z:
    y, z = z, y

print("从小到大：", x, y, z)