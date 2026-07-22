import math
import random

def sum_x(num):
  if num==1:
    return 1
  else:
    return num*sum_x(num-1)


def demo1(num):
  sum=0
  for i in range(1,num+1):
    sum+=sum_x(i)
  print(sum)
  return sum

def get_age(n):
    if n == 1:
        return 10
    return get_age(n - 1) + 2

def demo3():
  num = int(input("输入一个不超过5位的正整数："))
  s = str(num)
  length = len(s)
  print(f"该数字是{length}位数")
  reverse_s = s[::-1]
  print("逆序各位数字：", " ".join(reverse_s))


def demo2(num):
  list1=str(num)
  i=0
  j=len(list1)-1
  while True:

    if list1[i]==list1[j]:
      i+=1
      j-=1
    else:
      print("不是回文数")
      return False
    if i>=j:
      print("是回文数")
      return True

if __name__ == '__main__':
  # demo1(20)
  print(sum_x(5))
  print("第五个人年龄：", get_age(5))
  demo2(12321)
