from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")  # admin / user
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @classmethod #查用户不需要有用户实例，可以直接调用类方法调用，逻辑上的优化
    def find_by_username(cls, db: Session, username: str) -> Optional["User"]:
        """按用户名查用户（登录/注册查重用）"""
        return db.query(cls).filter(cls.username == username).first()

    @classmethod
    def create(cls, db: Session, username: str, password_hash: str, role: str = "user") -> "User":
        # 1. 在内存里构建一个User对象，⚠️此时还没有插入数据库！只是Python内存对象
        user = cls(username=username, password_hash=password_hash, role=role)
        # 2. 把user对象添加到数据库会话中，等待commit
        db.add(user)
        # 3. 提交事务，把user对象插入数据库
        db.commit()
        # 4. refresh：把数据库里最新的数据（自动生成的id、create\_time等）加载回内存user对象
        db.refresh(user)
        # 5. 返回user对象
        return user

    @classmethod
    def all_users(cls, db: Session) -> list["User"]:
        """查所有用户（admin 接口用，按 id 升序）"""
        return db.query(cls).order_by(cls.id).all()    
