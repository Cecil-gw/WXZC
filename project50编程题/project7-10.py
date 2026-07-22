# while 实现版本
s = input("请输入一行字符：")
i = 0
letter = space = digit = other = 0
while i < len(s):
    c = s[i]
    if c.isalpha():
        letter += 1
    elif c == " ":
        space += 1
    elif c.isdigit():
        digit += 1
    else:
        other += 1
    i += 1
print(f"字母:{letter} 空格:{space} 数字:{digit} 其他:{other}")

# 程序8
a = int(input("请输入数字a："))
n = int(input("请输入相加项数："))
total = 0
item = 0
for i in range(n):
    item = item * 10 + a
    total += item
print(f"总和s = {total}")

# 程序9
for num in range(2, 1001):
    factor_sum = 0
    for i in range(1, num // 2 + 1):
        if num % i == 0:
            factor_sum += i
    if factor_sum == num:
        print(num, end=" ")

# 程序10

def demo(h,n,height=0):
    if n==0:
        return h/2
    else:
        return demo(h/2,n-1)

def get_total(h, times):
    if times == 1:
        return h
    # 下落h，反弹h/2再落下h/2，下一轮高度h/2，落地次数-1
    return h + 2*(h/2) + get_total(h/2, times - 1)

print(get_total(100, 10))

print(demo(100, 10))