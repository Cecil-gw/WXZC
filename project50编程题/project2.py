import math

def main(start, end):
    if start <= 2:
      print("2 是质数")
      start = 3
    for j in range(start if start%2==1 else start+1, end, 2):
        max_div = int(math.sqrt(j))
        flag = True
        for i in range(3, max_div+1, 2):
            if j % i == 0:
                flag = False
                break
        if flag:
            print(f"{j} 是质数")

if __name__ == "__main__":
    main(101, 200)