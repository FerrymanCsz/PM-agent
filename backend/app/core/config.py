"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用信息
    APP_NAME: str = "面试模拟Agent系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 9000
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./interview_agent.db"
    
    # ChromaDB配置
    CHROMA_DB_PATH: str = "./chroma_db"
    
    # 知识库路径
    KNOWLEDGE_BASE_PATH: str = "./knowledge_base"
    
    # 上传文件配置
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 默认LLM配置（仅用于系统级操作，用户可配置自己的）
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    DEFAULT_LLM_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_LLM_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（缓存）"""
    return Settings()


settings = get_settings()
