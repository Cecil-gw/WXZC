"""数据层：6 张 ORM 表。

导入顺序：先定义无外键依赖的模型（User, Customer, PromptTemplate），
再定义包含外键的模型（Experiment, EmailRecord, OperationLog），
避免 SQLAlchemy 字符串解析开销。

所有模型导入后，`Base.metadata` 即包含全部表的 DDL 信息，
`create_all()` 可一次性建表。
"""

from app.models.user import User
from app.models.customer import Customer
from app.models.prompt_template import PromptTemplate
from app.models.experiment import Experiment
from app.models.email_record import EmailRecord
from app.models.operation_log import OperationLog

__all__ = [
    "User",
    "Customer",
    "PromptTemplate",
    "Experiment",
    "EmailRecord",
    "OperationLog",
]
