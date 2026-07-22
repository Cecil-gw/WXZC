def demo1(list1,n):
  for i in range(n):
    temp=list1[-1]
    list1.pop()
    list1.insert(0,temp)

def demo2(list2, n):
    cur = 0
    while len(list2) > 1:
        cur = (cur + n - 1) % len(list2)
        list2.pop(cur)
    print(list2[0])
    return list2[0]
def demo2_1(m, n):
    cur = 0
    list2=[]
    for i in range(m):
        list2.append(i+1)
    while len(list2) > 1:
        cur = (cur + n - 1) % len(list2)
        list2.pop(cur)
    print(list2[0])
    return list2[0]

def demo3(string1):
   return len(string1)

def demo4(n):
   if n%2==0:
      if n==2:
         return 0.5
      return 1/n + demo4(n-2)
   else:
      if n==1:
         return 1
      return 1/n + demo4(n-2)
  
def find_min_peach():
    y = 1
    while True:
        temp = y
        flag = True
        # 反向推导5轮
        for _ in range(5):
            # 上一轮数量 = 5*当前/4 + 1
            if (temp * 5) % 4 != 0:
                flag = False
                break
            temp = (5 * temp) // 4 + 1
        if flag:
            return temp
        y += 1



if __name__ == "__main__":
  # list1 = [1,2,3,4,5,6,7,8,9]
  # n = int(input("请输入数字n："))
  # demo1(list1,n)
  # print(list1)

  # list2 = [1,2,3,4,5,6,7]
  # n = int(input("请输入数字n："))
  # demo2(list2,n)
  # m = int(input("请输入数字m："))
  # n = int(input("请输入数字n："))
  # demo2_1(m,n)

  string1 = input("请输入字符串：")
  print(demo3(string1))

  n = int(input("请输入数字n："))
  print(demo4(n))

  res = find_min_peach()
  print("原来最少桃子数量：", res)