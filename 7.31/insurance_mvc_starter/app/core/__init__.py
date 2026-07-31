"""基础设施层统一入口

【为什么不在 import 期提前 export？】
如果这里写 from .config import settings 之类，会在「import app 包」时立刻触发 Settings() 实例化
+ security/database 等所有子模块的顶层代码执行。一旦某个子模块在加载期出现任何依赖/路径问题，
整个 app 包的加载就会被打断，表现为 "cannot import name 'create_app' from 'app' (unknown location)"。

所以这里保持空（不做导出），真正需要 settings 时显式 from app.core.config import settings，
需要 hash_password 时 from app.core.security import hash_password——按需导入更稳定。
"""
