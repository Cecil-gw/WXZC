import sys
import random
import threading
from pathlib import Path
import os

sys.path.append(str(Path(__file__).parent.parent))
import grade_utils

sys.path.append("./subjects") 
from subjects import BaseExam, Chinese, Math, English

def main(all_student_data):
    # 1. 测试得分率
    print("测试得分率")
    math_obj = Math("数学", 100, all_student_data[1][0])
    # 通过实例调用方法
    math_obj.set_bonus_points(30)
    print(f" {all_student_data[1][0]}的数学得分率为：{grade_utils.calc_percentage(all_student_data[1][2]+math_obj.get_bonus_points(), 150)}")

    #2 成绩保存与读取测试
    for student_data in all_student_data:
        student_name = student_data[0]
        subject_name = student_data[1]
        score = student_data[2]
        bonus_points = 0
        if len(student_data) > 3:
            bonus_points = sum(student_data[3:])
        if subject_name == "语文":
            chinese_obj = Chinese(subject_name, 150, student_name)
            chinese_obj.set_essay_score(student_data[3])
            chinese_obj.input_score(student_data[2])
            chinese_obj.print_report_card()
        elif subject_name == "数学":
          math_obj = Math(subject_name, 100, student_name) # 数学满分100，删掉150
          bonus_points= random.randint(0, 10)*5
          math_obj.set_bonus_points(bonus_points)
          math_obj.input_score(student_data[2])
          math_obj.get_score()
          math_obj.print_report_card()
        elif subject_name == "英语":
           # subject_name == "英语"分支
            listen = student_data[2]
            read = student_data[3]
            write = student_data[4]
            english_obj = English(subject_name, 100, student_name, float(listen), float(read), float(write))
            english_obj.print_report_card()
        # 拼接成 姓名,科目,分数 格式字符串
        line = f"{student_data[0]},{student_data[1]},{student_data[2]}"
        grade_utils.save_record(line)

    # 3. 多线程录入测试
    def save_thread_task(data):
        name, sub, base = data[0], data[1], data[2]
        grade_utils.save_record(f"{name},{sub},{base}")

    thread_list = []
    for data in all_student_data:
        t = threading.Thread(target=save_thread_task, args=(data,))
        thread_list.append(t)
        t.start()
    # 等待所有线程结束
    for t in thread_list:
        t.join()
    print("多线程录入全部完成\n")

    # 4。 设置pass_rate
    print("=====4. 设置及格率0.55=====")
    temp_chinese = Chinese("语文", 150, "临时")
    temp_chinese.set_passing_rate(0.55)
    print(f"当前系统及格率：{temp_chinese.passing_rate}\n")

    # ===================== 5. 语文专项测试 =====================
    print("=====5. 语文测试（创建、录入成绩、查看作文分、评定等级、保存记录）=====")
    test_chs = Chinese("语文", 150, "测试学生_语文")
    # 录入卷面基础分
    test_chs.input_score(82)
    # 设置作文分
    test_chs.set_essay_score(46)
    # 查看作文分
    print(f"作文分数：{test_chs.essay_score}")
    # 获取总分并评定等级
    total_chs = test_chs.get_score()
    grade_chs = test_chs.get_grade(total_chs)
    print(f"语文总分：{total_chs}，对应等级：{grade_chs}")
    # 保存记录
    grade_utils.save_record(f"测试学生_语文,语文,{total_chs}")

    # ===================== 6. 数学专项测试 =====================
    print("=====6. 数学测试（创建、录入成绩、设置附加分、查看加权分、保存记录）=====")
    test_math = Math("数学", 100, "测试学生_数学")
    # 录入基础分
    test_math.input_score(85)
    # 设置附加分
    add_score = 20
    test_math.set_bonus_points(add_score)
    # 获取附加分 + 70%加权分
    now_add = test_math.get_bonus_points()
    weight_score = test_math.calc_weighted_score(0.7)
    print(f"数学附加分：{now_add}，70%加权分数：{weight_score}")
    # 保存记录
    grade_utils.save_record(f"测试学生_数学,数学,{test_math.get_score()}")
    print("数学成绩记录已保存\n")

    # ===================== 7. 英语专项测试 =====================
    print("=====7. 英语测试（创建、打印分项成绩单、评定等级、保存记录）=====")
    test_eng = English("英语", 100, "测试学生_英语", 26, 34, 22)
    # 打印分项成绩单
    test_eng.print_report_card()
    # 评定等级
    total_eng = test_eng.get_score()
    grade_eng = test_eng.get_grade(total_eng)
    print(f"英语总分：{total_eng}，等级：{grade_eng}")
    # 保存记录
    grade_utils.save_record(f"测试学生_英语,英语,{total_eng}")
    print("英语成绩记录已保存\n")

    print("=====8. 优秀学生筛选测试=====")
    student_total_dict = {}
    # 遍历所有学生组装 {姓名:总分} 字典
    for data in all_student_data:
        name = data[0]
        sub = data[1]
        if sub == "语文":
            obj = Chinese(sub, 150, name)
            obj.input_score(data[2])
            obj.set_essay_score(data[3])
            total = obj.get_score()
        elif sub == "数学":
            obj = Math(sub, 100, name)
            obj.input_score(data[2])
            obj.set_bonus_points(0)
            total = obj.get_score()
        else:
            l, r, w = float(data[2]), float(data[3]), float(data[4])
            obj = English(sub, 100, name, l, r, w)
            total = obj.get_score()
        student_total_dict[name] = total
    # 列表推导式筛选总分≥90优秀学生
    excellent_stu = [name for name, score in student_total_dict.items() if score >= 90]
    print("总分≥90优秀学生名单：", excellent_stu, "\n")

    # ===================== 9. 成绩单生成器测试 =====================
    print("=====9. 成绩单生成器测试=====")
    def report_generator(stu_list):
        for item in stu_list:
            yield f"【{item[0]}】科目:{item[1]} 卷面基础分:{item[2]}"
    # 生成器遍历输出
    gen = report_generator(all_student_data[:6])
    for msg in gen:
        print(msg)
    print("\n")

    # ===================== 10. 批量多态测试（统一调用calc_weighted_score） =====================
    print("=====10. 批量统计多态测试=====")
    exam_chs = Chinese("语文", 150, "多态演示")
    exam_chs.input_score(80)
    exam_chs.set_essay_score(40)

    exam_math = Math("数学", 100, "多态演示")
    exam_math.input_score(86)
    exam_math.set_bonus_points(10)

    exam_eng = English("英语", 100, "多态演示", 25, 32, 20)
    exam_list = [exam_chs, exam_math, exam_eng]
    for exam in exam_list:
        w_score = exam.calc_weighted_score(0.7)
        print(f"{exam.subject_name} 70%加权分：{w_score}")

    
  

if __name__ == '__main__':
    all_student_data = [
    # 1. 张三
    ("张三", "语文", 78, 54),
    ("张三", "数学", 89),
    ("张三", "英语", 28, 42, 22),
    # 2. 李四
    ("李四", "语文", 66, 48),
    ("李四", "数学", 76),
    ("李四", "英语", 22, 35, 21),
    # 3. 王五
    ("王五", "语文", 56, 32),
    ("王五", "数学", 55),
    ("王五", "英语", 16, 26, 16),
    # 4. 赵六
    ("赵六", "语文", 80, 56),
    ("赵六", "数学", 94),
    ("赵六", "英语", 30, 44, 22),
    # 5. 钱七
    ("钱七", "语文", 70, 42),
    ("钱七", "数学", 68),
    ("钱七", "英语", 20, 32, 20),
    # 6. 孙八
    ("孙八", "语文", 60, 38),
    ("孙八", "数学", 62),
    ("孙八", "英语", 18, 30, 17),
    # 7. 周九
    ("周九", "语文", 70, 51),
    ("周九", "数学", 82),
    ("周九", "英语", 26, 40, 22),
    # 8. 吴十
    ("吴十", "语文", 78, 29),
    ("吴十", "数学", 45),
    ("吴十", "英语", 14, 24, 14),
    # 9. 郑十一
    ("郑十一", "语文", 75, 58),
    ("郑十一", "数学", 97),
    ("郑十一", "英语", 29, 41, 21),
    # 10. 陈十二
    ("陈十二", "语文", 86, 49),
    ("陈十二", "数学", 73),
    ("陈十二", "英语", 21, 34, 21),
]
    main(all_student_data)
   