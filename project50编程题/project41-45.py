def demo1():
  for x in range(10, 100):
    if 809 * x == 800 * x + 9 * x + 1:
        if 10 <= 8*x <= 99 and 100 <= 9*x <= 999:
            print(f"两位数?? = {x}")
            print(f"809 * {x} = {809*x}")
def demo2():
  count = 0
  nums = [0,1,2,3,4,5,6,7]
  odd_last = [1,3,5,7]

  # 枚举位数1~8
  for length in range(1,9):
      # 末尾固定奇数
      for last in odd_last:
          if length == 1:
              count +=1
          else:
              # 第一位：不能0、不能末尾数字：6种
              first = 6
              # 中间位：排除首尾两个数字，剩余6个可选
              mid = 6 ** (length-2)
              count += first * mid
  print("0-7能组成的奇数总数：", count)

def is_prime(n):
  if n <2:
       return False
  for i in range(2,int(n**0.5)+1):
      if n%i==0:
        return False
  return True

def goldbach(num):
    if num %2 !=0 or num<4:
        print("请输入≥4的偶数")
        return
    for a in range(2, num//2 +1):
        b = num -a
        if is_prime(a) and is_prime(b):
            print(f"{num} = {a} + {b}")
            return

goldbach(20)
goldbach(100)

def demo5():
   def prime_div_9(p):
    def is_prime(n):
        if n<2:return False
        for i in range(2,int(n**0.5)+1):
            if n%i==0:return False
        return True
    if not is_prime(p):
        print("输入不是素数")
        return
    cnt = 0
    temp = p
    while temp %9 ==0:
        cnt +=1
        temp = temp //9
    print(f"该素数能被{cnt}个9整除")

    prime_div_9(7)

if __name__ == "__main__":
   pass