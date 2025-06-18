from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base, relationship
import datetime
from app.database import Base
import re
from sqlalchemy.sql import func
import hashlib

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

    # 添加关系
    models = relationship("LLMModel", back_populates="user")
    templates = relationship("PromptTemplate", back_populates="user")
    prompts = relationship("Prompt", back_populates="user")
    histories = relationship("PromptHistory", back_populates="user")
    responses = relationship("Response", back_populates="user")
    evaluations = relationship("PromptEvaluation", back_populates="user")
    test_records = relationship("TestRecord", back_populates="user")

    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        salt = "PromptLabSalt2024"
        return hashlib.sha256((password + salt).encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        return User.hash_password(password) == password_hash

class LLMModel(Base):
    __tablename__ = 'llm_models'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    provider = Column(String(50))
    api_key = Column(String(500))
    base_url = Column(String(500))
    user_id = Column(Integer, ForeignKey('users.id'))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    prompts = relationship("Prompt", back_populates="model")
    histories = relationship("PromptHistory", back_populates="model")
    test_records = relationship("TestRecord", back_populates="model")

    # 关系
    user = relationship("User", back_populates="models")

    # 创建复合唯一约束：用户ID+名称+未删除
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_model_user_name'),
        Index('ix_model_user_id_name_is_deleted', 'user_id', 'name', 'is_deleted', unique=True),
    )

    @property
    def has_api_key(self):
        """检查是否配置了有效的API key"""
        if not self.api_key:
            return False
            
        api_key = self.api_key.strip()
        if not api_key:
            return False
            
        # 根据不同的模型类型验证API密钥格式
        if self.provider == "openai" and not api_key.startswith("sk-"):
            return False
        elif self.provider == "anthropic" and not re.match(r"^sk-ant-[a-zA-Z0-9-]+$", api_key):
            return False
        elif self.provider == "deepseek" and not api_key.startswith("sk-"):
            return False
        elif self.provider == "qwen" and len(api_key) < 10:
            return False
        elif self.provider == "doubao" and len(api_key) < 10:
            return False
        elif self.provider == "local":
            return True
            
        return True

class PromptTemplate(Base):
    __tablename__ = 'prompt_templates'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(Text)
    content = Column(Text)
    variables = Column(JSON)
    user_id = Column(Integer, ForeignKey('users.id'))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    prompts = relationship("Prompt", back_populates="template")
    histories = relationship("PromptHistory", back_populates="template")
    test_records = relationship("TestRecord", back_populates="template")

    # 关系
    user = relationship("User", back_populates="templates")

    # 创建复合唯一约束：用户ID+名称+未删除
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_template_user_name'),
        Index('ix_template_user_id_name_is_deleted', 'user_id', 'name', 'is_deleted', unique=True),
    )

class Prompt(Base):
    __tablename__ = 'prompts'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(Text)
    content = Column(Text)
    variables = Column(JSON)
    model_id = Column(Integer, ForeignKey('llm_models.id'))
    template_id = Column(Integer, ForeignKey('prompt_templates.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="prompts")
    model = relationship("LLMModel", back_populates="prompts")
    template = relationship("PromptTemplate", back_populates="prompts")
    responses = relationship("Response", back_populates="prompt")
    histories = relationship("PromptHistory", back_populates="prompt")
    
    # 创建复合唯一约束：用户ID+名称+未删除
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_prompt_user_name'),
        Index('ix_prompt_user_id_name_is_deleted', 'user_id', 'name', 'is_deleted', unique=True),
    )

class PromptHistory(Base):
    __tablename__ = 'prompt_history'
    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey('prompts.id'))
    template_id = Column(Integer, ForeignKey('prompt_templates.id'))
    model_id = Column(Integer, ForeignKey('llm_models.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    variables = Column(JSON)
    rendered_prompt = Column(Text)
    response = Column(Text)
    evaluation = Column(JSON)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="histories")
    prompt = relationship("Prompt", back_populates="histories")
    template = relationship("PromptTemplate", back_populates="histories")
    model = relationship("LLMModel", back_populates="histories")
    evaluations = relationship("PromptEvaluation", back_populates="history")

class PromptEvaluation(Base):
    __tablename__ = 'prompt_evaluations'
    id = Column(Integer, primary_key=True, index=True)
    history_id = Column(Integer, ForeignKey('prompt_history.id'))
    metrics = Column(JSON)
    score = Column(Integer)
    feedback = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="evaluations")
    history = relationship("PromptHistory", back_populates="evaluations")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"))
    content = Column(Text)
    evaluation = Column(JSON)
    user_id = Column(Integer, ForeignKey('users.id'))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="responses")
    prompt = relationship("Prompt", back_populates="responses")

class TestRecord(Base):
    __tablename__ = 'test_records'
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey('llm_models.id'))
    template_id = Column(Integer, ForeignKey('prompt_templates.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    prompt = Column(Text, nullable=False)
    variables = Column(JSON, nullable=True, default=dict)
    response = Column(Text, nullable=False)
    evaluation = Column(JSON, nullable=True, default=dict)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="test_records")
    model = relationship("LLMModel", back_populates="test_records")
    template = relationship("PromptTemplate", back_populates="test_records") 