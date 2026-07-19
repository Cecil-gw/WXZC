from abc import ABC, abstractmethod
import threading as thr
import exam_system.grade_utils as grade_utils

class BaseExam(ABC):

  passing_rate = 0.6

  
  def __init__(self, subject_name: str, max_score: float, student_name: str):
       # 实例公有属性
      self.subject_name = subject_name
      self.max_score = max_score
      self.student_name = student_name
      # 私有成绩，外部不能直接访问
      self.__score = 0.0

  def check_valid_score(self, val: float) -> bool:
        return 0 <= val <= self.max_score

  def get_score(self):
      return self.__score
  
  def input_score(self,score):
     if self.check_valid_score(score):
        self.__score = score
        return True
     else:
        raise ValueError(f"成绩非法，必须介于0~{self.max_score}")
     
  @classmethod
  def set_passing_rate(cls, rate):
      if 0.0 <= rate <= 1.0:
          cls.passing_rate = rate
      else:
          raise ValueError("及格率必须介于0~1之间")
      
  @staticmethod
  def check_student_name(name: str) -> bool:
      return isinstance(name,str) and len(name.strip())>0
  
  @abstractmethod
  def  get_grade(score) -> str :
    if score >= 90:
        return "excellent"
    elif score >= 75:
        return "good"
    elif score >= 60:
        return "pass"
    else:
        return "fail"

  def calc_weighted_score(self,weight) -> float:
      return self.get_score() * weight

  def print_report_card(self) :
    score = self.get_score()
    weighted_70 = self.calc_weighted_score(0.7)
    pass_line = self.max_score * self.passing_rate
    grade = self.get_grade(score)
    print("===== 成绩单 =====")
    print(f"学生：{self.student_name}")
    print(f"学科：{self.subject_name} 满分：{self.max_score}")
    print(f"原始分数：{score} 等级：{grade}")
    print(f"70%加权分：{weighted_70:.1f}")
    score=weighted_70+30
    print(f"及格线：{pass_line}，折算分：{score:.1f},是否及格：{score >= pass_line}")