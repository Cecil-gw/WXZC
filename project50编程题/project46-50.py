def demo1(s1:str,s2:str):
  return s1+s2

def demo2():
  for i in range(7):
    val = int(input(f"输入第{i+1}个数字(1-50)："))
    print("*" * val)

def encrypt(num):
    s = list(f"{num:04d}")
    arr = [int(c) for c in s]
    # 每位+5取模
    for i in range(4):
        arr[i] = (arr[i] +5) %10
    # 交换1、4
    arr[0], arr[3] = arr[3], arr[0]
    # 交换2、3
    arr[1], arr[2] = arr[2], arr[1]
    return "".join(map(str,arr))

def demo3():
  s = input("主字符串：")
  sub = input("子串：")
  cnt = s.count(sub)
  print(f"子串出现次数：{cnt}")
  
def demo5():
   with open("stud.txt", "w", encoding="utf-8") as f:
    for i in range(5):
        id_ = input(f"\n第{i+1}个学生学号：")
        name = input("姓名：")
        s1 = int(input("科目1成绩："))
        s2 = int(input("科目2成绩："))
        s3 = int(input("科目3成绩："))
        avg = (s1+s2+s3)/3
        line = f"学号:{id_} 姓名:{name} 三科:{s1},{s2},{s3} 平均分:{avg:.2f}\n"
        f.write(line)
    print("数据已存入文件stud.txt")

if __name__ =="__main__":

  print(encrypt(1234))