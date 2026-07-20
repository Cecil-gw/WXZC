def slight(grade):
    return "优秀" if grade >= 90 else "良好" if grade >= 80 else "中等" if grade >= 70 else "及格" if grade >= 60 else "不及格"


def main():
    grade = float(input("请输入成绩："))
    print(slight(grade))


if __name__ == '__main__':
    main()