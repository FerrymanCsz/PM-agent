"""
数据库模型定义
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, ForeignKey, Integer
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from app.core.config import settings


class Base(AsyncAttrs, DeclarativeBase):
    """基础模型类"""
    pass


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    llm_configs = relationship("LLMConfig", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    knowledge_docs = relationship("KnowledgeDoc", back_populates="user", cascade="all, delete-orphan")
    job_configs = relationship("JobConfig", back_populates="user", cascade="all, delete-orphan")


class LLMConfig(Base):
    """LLM配置表"""
    __tablename__ = "llm_configs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)  # 配置名称
    provider = Column(String, nullable=False)  # openai, anthropic, deepseek, etc.
    base_url = Column(String, nullable=False)
    api_key = Column(String, nullable=False)  # 加密存储
    model = Column(String, nullable=False)
    temperature = Column(SQLiteJSON, default=0.7)
    max_tokens = Column(Integer, default=4096)
    timeout = Column(Integer, default=60)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="llm_configs")


class Session(Base):
    """会话表"""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, default="新面试")
    status = Column(String, default="active")  # active, completed, paused
    job_info = Column(SQLiteJSON, default=dict)  # 岗位信息
    llm_config_id = Column(String, ForeignKey("llm_configs.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # 'user'(面试官), 'assistant'(Agent面试者), 'system'
    content = Column(Text, nullable=False)
    meta_data = Column(SQLiteJSON, default=dict)  # 思考过程、工具调用等
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("Session", back_populates="messages")


class Resume(Base):
    """简历表"""
    __tablename__ = "resumes"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    parsed_data = Column(SQLiteJSON, default=dict)  # 解析后的结构化数据
    is_active = Column(Boolean, default=True)  # 是否当前使用的简历
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="resumes")


class KnowledgeDoc(Base):
    """知识库文档表"""
    __tablename__ = "knowledge_docs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=True)  # 个人介绍、项目经历、技术知识等
    parent_id = Column(String, ForeignKey("knowledge_docs.id"), nullable=True)
    file_path = Column(String, nullable=True)  # Markdown文件路径
    embedding_ids = Column(SQLiteJSON, default=list)  # ChromaDB文档IDs
    is_auto_generated = Column(Boolean, default=False)
    source_session_id = Column(String, nullable=True)  # 来源会话ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="knowledge_docs")
    parent = relationship("KnowledgeDoc", remote_side=[id], backref="children")


class JobConfig(Base):
    """岗位配置表"""
    __tablename__ = "job_configs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company = Column(String, nullable=True)
    position = Column(String, nullable=False)
    department = Column(String, nullable=True)
    level = Column(String, nullable=True)
    job_description = Column(Text, nullable=True)
    requirements = Column(SQLiteJSON, default=list)  # 核心要求列表
    skills = Column(SQLiteJSON, default=list)  # 技能要求
    interview_focus = Column(SQLiteJSON, default=list)  # 面试重点
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="job_configs")


# 数据库引擎和会话
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
