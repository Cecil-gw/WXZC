import math

def flower(start,end):
    for i in range(start, end+1):
        s = str(i)
        a = int(s[0])  # 百位
        b = int(s[1])  # 十位
        c = int(s[2])  # 个位
        if a**3 + b**3 + c**3 == i:
            print(i)

def main(start, end):
    flower(start, end)

if __name__ == '__main__':
    main(100, 999)