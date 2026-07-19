from .base_exam import BaseExam

class English(BaseExam):
  def __init__(self, subject_name: str, max_score: float, student_name: str, listening_score: float, reading_score: float, writing_score: float):
        super().__init__(subject_name, max_score, student_name)
        self.listening_score = listening_score
        self.reading_score = reading_score
        self.writing_score = writing_score

  def get_score(self):
        return self.listening_score + self.reading_score + self.writing_score


  def print_report_card(self):
      super().print_report_card()
      print("===== 听力/阅读/写作分项成绩 =====")
      print("听力：", self.listening_score)
      print("阅读：", self.reading_score)
      print("写作：", self.writing_score)
      print("=================================")

  def get_grade(self, score) -> str:
      s = self.get_score()
      if s >= 90:
             return "excellent"
      elif s >= 75:
            return "good"
      elif s >= 60:
            return "pass"
      else:
            return "fail"   