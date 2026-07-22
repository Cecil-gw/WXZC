def demo1():
    letter1 = input("请输入星期第一个字母：").upper()
    if letter1 == 'M':
        print("Monday 星期一")
    elif letter1 == 'W':
        print("Wednesday 星期三")
    elif letter1 == 'F':
        print("Friday 星期五")
    elif letter1 == 'T':
        letter2 = input("首字母T，请输入第二个字母：").upper()
        if letter2 == 'U':
            print("Tuesday 星期二")
        elif letter2 == 'H':
            print("Thursday 星期四")
        else:
            print("输入错误")
    elif letter1 == 'S':
        letter2 = input("首字母S，请输入第二个字母：").upper()
        if letter2 == 'A':
            print("Saturday 星期六")
        elif letter2 == 'U':
            print("Sunday 星期日")
        else:
            print("输入错误")
    else:
        print("字母输入错误")

def demo2():
    prime_list = []
    for num in range(2, 101):
        flag = True
        for i in range(2, int(num**0.5)+1):
            if num % i == 0:
                flag = False
                break
        if flag:
            prime_list.append(num)
    print("100以内素数：")
    print(prime_list)

def demo3():
  nums = []
  for i in range(10):
      n = int(input(f"请输入第{i+1}个数字："))
      nums.append(n)

  length = len(nums)
  for i in range(length-1):
      min_index = i  
      for j in range(i+1, length):
          if nums[j] < nums[min_index]:
              min_index = j
      nums[i], nums[min_index] = nums[min_index], nums[i]

  print("升序排序结果：", nums)

def demo4():
  matrix = []
  sum_diag = 0
  # 录入3行3列矩阵
  for i in range(3):
      row = []
      for j in range(3):
          val = int(input(f"输入matrix[{i}][{j}]："))
          row.append(val)
      matrix.append(row)

  # 对角线累加
  for i in range(3):
      sum_diag += matrix[i][i]

  print("3*3矩阵：", matrix)
  print("对角线元素和：", sum_diag)

def demo5():
  arr = [1,3,5,7,9,11,13,15]
  num = int(input("请输入要插入的数字："))

  insert_pos = len(arr)  # 默认插末尾
  # 寻找插入位置
  for index, val in enumerate(arr):
      if val > num:
          insert_pos = index
          break
  # 数组后移+插入
  arr.insert(insert_pos, num)
  print("插入后有序数组：", arr)

if __name__ == "__main__":
    demo1()
    demo2()
    demo3()
    demo4()
    demo5()