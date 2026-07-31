"""Model 层统一入口

【作用】把所有 ORM 模型在此集中导入，供 create_app 建表、或外部直接 from app.models import User。
- Base.metadata.create_all() 建表时必须 import 过所有模型，否则 SQLAlchemy 找不到
- 新增模型：在这里加一行 import 即可
"""
from app.core.database import Base
from app.models.user import User

__all__ = ["Base", "User"]
