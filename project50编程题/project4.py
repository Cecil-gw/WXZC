import math


def define(num, res_list):
    if num == 1:
        return
    max_div = int(math.sqrt(num)) + 1
    for k in range(2, max_div):
        if num % k == 0:
            res_list.append(k)
            define(num // k, res_list)
            return
    res_list.append(num)

def main(num):
    if num == 1:
        print([1])
        return
    list1 = []
    define(num, list1)
    print(f"{num} 的质因数分解结果：{list1}")

if __name__ == '__main__':
    main(102)
   