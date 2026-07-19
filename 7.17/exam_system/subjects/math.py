from .base_exam import BaseExam


class Math(BaseExam):
    def __init__(self,  subject_name: str, max_score: float, student_name: str):
        super().__init__(subject_name, max_score, student_name)
        self.__bonus_points = 0

    def get_bonus_points(self):
        return self.__bonus_points
    
    def set_bonus_points(self, bonus_points):
        self.__bonus_points = bonus_points

    def get_score(self) -> float:
        base_score = super().get_score()
        return base_score+self.get_bonus_points()

    def get_grade(self,score) -> str:
    # 不要自己再加bonus，get_score已经包含加分
        real_score = self.get_score()
        if real_score >= 135:
            return "excellent"
        elif real_score >= 120:
            return "good"
        elif real_score >= 90:
            return "pass"
        else:
            return "fail"
         
         
    