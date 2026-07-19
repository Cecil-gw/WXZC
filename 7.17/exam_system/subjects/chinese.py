# subjects/chinese.py
from .base_exam import BaseExam

class Chinese(BaseExam):
  
  def __init__ (self, subject_name: str, max_score: float, student_name: str):
    super().__init__(subject_name, max_score, student_name)
    self.essay_score:float = 0.0

  def set_essay_score(self, essay_score):
    self.essay_score = essay_score

  def get_score(self) -> float:
    base_score = super().get_score()
    return base_score + self.essay_score

  def  get_grade(self,score) -> str :
    real_score = self.get_score()
    if real_score >= 135:
        return "excellent"
    elif real_score >= 120:
        return "good"
    elif real_score >= 90:
        return "pass"
    else:
        return "fail"
    