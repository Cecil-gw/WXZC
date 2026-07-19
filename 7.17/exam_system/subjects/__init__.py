# subjects/__init__.py
from .base_exam import BaseExam
from .chinese import Chinese
from .math import Math
from .english import English

# 对外暴露的名称
__all__ = ["BaseExam", "Chinese", "Math", "English"]