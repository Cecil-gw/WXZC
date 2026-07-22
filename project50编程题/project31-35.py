import math

def reverse(list1):
    return list1[::-1]

def demo1(a):
    a>>4
    b=~(~0<<4)
    print(a&b)
    return a&b

def demo2(n):
    total = n
    triangle = []
    for i in range(n):
        row = [1] * (i + 1)
        for j in range(1, i):
            row[j] = triangle[i-1][j-1] + triangle[i-1][j]
        triangle.append(row)

        # 计算最后一行字符串长度，作为居中基准宽度
        last_row_str = " ".join(map(str, triangle[-1]))
        max_width = len(last_row_str)

    for row in triangle:
        line = " ".join(map(str, row))
        # center(总宽度) 自动前后补空格居中
        print(line.center(max_width))

def demo3():
    # 输入三个数字
    a = int(input("请输入数字a："))
    b = int(input("请输入数字b："))
    c = int(input("请输入数字c："))

    # 交换函数，模拟指针交换效果
    def swap(x, y):
        return y, x

    # 让a存最大值
    if a < b:
        a, b = swap(a, b)
    if a < c:
        a, c = swap(a, c)
    # 让b大于c
    if b < c:
        b, c = swap(b, c)

    print(f"从大到小排序：{a} {b} {c}")

def demo5(arr):

  # 1. 找到最大值下标，和第一个元素交换
  max_idx = arr.index(max(arr))
  arr[0], arr[max_idx] = arr[max_idx], arr[0]

  # 2. 交换完最大值后，重新找最小值下标，防止下标错乱
  min_idx = arr.index(min(arr))
  arr[-1], arr[min_idx] = arr[min_idx], arr[-1]

  print("处理后的数组：", arr)

if __name__ == '__main__':
    demo1(12121214)
    demo2(5)