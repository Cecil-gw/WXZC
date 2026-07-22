import math

def main():
  for i in range (1,10):
    for j in range(1,i+1):
      print(j,"*",i,"=",i*j,end="\t")
    print()

def demo1(day):
  return 2**(day-1)

def demo2():
  team_b = ['x', 'y', 'z']
  for i in team_b:
      for j in team_b:
          for k in team_b:
              if i != j and j != k and i != k:
                  if i != 'x' and k != 'x' and k != 'z':
                      print(f"a 的对手：{i}")
                      print(f"b 的对手：{j}")
                      print(f"c 的对手：{k}")

def demo3(num):
  count=0
  if num%2!=0:
    for i in range(1,(num+1)//2+1):
        count=2*i-1
        print("*"*(2*i-1))
    for i in range((num+1)//2+1,num+1):
        print("*"*(count-2*(i-(num+1)//2)))
  else:
    for i in range(1,num//2+1):
        count=2*i
        print("*"*count)
    for i in range(num//2+1,num+1):
        print("*"*(count-2*(i-(num//2+1))))

def demo4():
  pass

if __name__ == '__main__':
  main()
  print(demo1(10))
  demo2()
  demo3(10)

# 2
