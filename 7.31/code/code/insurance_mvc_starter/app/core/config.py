'''
    本项目的配置：
    1. 数据库配置：连接到数据库的地址，例如 SQLite 数据库的路径。
    2. JWT认证配置： 用于生成和验证JWT令牌的配置，例如密钥、过期时间等。
    3. 其他配置： 其他配置项，例如日志级别、缓存配置等。
'''
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
       应用配置类：包含数据库地址、JWT认证配置等。
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "保险精准营销系统"
    DATABASE_URL: str = "sqlite:///./instance/starter.db"
    # JWT认证
    JWT_SECRET_KEY: str = "your_jwt_secret_key"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24小时过期
    JWT_ALGORITHM: str = "HS256" # 验证和签名JWT令牌的算法，默认使用HS256算法
    LOG_LEVEL: str = "INFO"

# 模块实例化：import本模块时立即创造一个全局单例
settings = Settings()
'''
1. **配置和代码分离**
数据库地址、密钥这类配置不硬写死在业务代码里，修改配置不用改动源代码。本地、测试、线上环境切换，只改外部配置，不改代码。
2. **保护敏感信息**
密钥、密码放在`.env`，该文件不提交 Git，避免密钥上传代码仓库造成泄露；源代码只放安全兜底默认值。
3. **统一管理 + 自动类型校验**`Settings`类集中定义全部配置项、数据类型。读取配置时自动校验类型，配置写错程序直接报错，不会静默出现诡异 bug；项目所有地方统一导入同一个`settings`对象，不会到处散落配置。
4. **多环境友好，分工清晰**`config.py`提供默认值，没`.env`项目也能直接运行；`.env`用于本机个性化覆盖；服务器部署还可以直接用系统环境变量覆盖配置，适配开发、测试、线上不同场景。
5. **团队协作减少冲突**
公共配置模板提交 Git，每个人本地自己的环境差异写在本地`.env`，不用修改公共代码文件，减少 Git 代码冲突。
'''