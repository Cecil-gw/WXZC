import threading as thr
import datetime 
import time as t

student_records = {}# 全局共享成绩字典，格式：{"张三": {"语文": 0, "数学": 0}}
record_lock = thr.Lock()

def check_valid_score(score, max_score):
  if score < 0 or score > max_score:
    print("Invalid score: ", score, "Max score: ", max_score)
    return False
  return True

def calc_percentage(score, max_score):
  return round((score/max_score) * 100,2)

def save_record(record_info):
  with open("exam_records.txt","a") as f:
    f.write(record_info + "\n")

def read_all_records() :
  with open("exam_records.txt","r") as f:
    return f.readlines()
  
def  get_excellent_students(score_dict, threshold):
  return [item for item in score_dict.items() if item[1] >= threshold]

def report_card_generator(student_list):
    for name, score in student_list:
        # 格式化成绩单文本
        info = f"【成绩单】学生：{name}，分数：{score}"
        # yield 产出这一条字符串，函数暂停
        yield info

def input_score_thread_safe(student_name, subject, score):
  
  line = f"{student_name},{subject},{score}\n"
  with record_lock:
    save_record(line)

def multi_thread_input_test():
  print("多线程输入成绩测试开始...")
  save_record("张三,语文,90\n")
  save_record("李四,数学,85\n")

  t1 = thr.Thread(target=input_score_thread_safe, args=("王五", "数学", 95))
  t2 = thr.Thread(target=input_score_thread_safe, args=("赵六", "数学", 85))

  t1.start()
  t2.start()

  t1.join()
  t2.join()