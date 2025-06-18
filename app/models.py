from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, UniqueConstraint, Index
from sqlalchemy.sql import func
from .database import Base
import hashlib
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    email = Column(String(200), index=True)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))

    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        salt = "PromptLabSalt2024"
        return hashlib.sha256((password + salt).encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        return User.hash_password(password) == password_hash

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    content = Column(Text, nullable=False)
    variables = Column(JSON, default={})
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 创建部分索引，只对未删除的记录生效
    __table_args__ = (
        Index('ix_prompt_templates_name_active', 
              'name',
              unique=True,
              postgresql_where=is_deleted.is_(False),  # PostgreSQL
              sqlite_where=is_deleted.is_(False),      # SQLite
        ),
    ) 