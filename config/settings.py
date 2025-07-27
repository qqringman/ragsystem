"""
系統設定管理

使用 Pydantic V2 進行配置驗證和管理
"""

import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """系統配置類"""
    
    # Pydantic V2 配置
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM 設定
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", alias="OPENAI_MODEL")
    claude_model: str = Field(default="claude-3-opus-20240229", alias="CLAUDE_MODEL")
    ollama_model: str = Field(default="llama3", alias="OLLAMA_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    
    # 向量資料庫設定
    vector_db: str = Field(default="chroma", alias="VECTOR_DB")
    embed_provider: str = Field(default="openai", alias="EMBED_PROVIDER")
    chroma_persist_dir: str = Field(default="vector_db/chroma", alias="CHROMA_PERSIST_DIR")
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    redis_index_name: str = Field(default="rag_index", alias="REDIS_INDEX_NAME")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="rag_collection", alias="QDRANT_COLLECTION")
    
    # SQL 資料庫設定
    db_type: str = Field(default="postgresql", alias="DB_TYPE")
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: str = Field(default="5432", alias="DB_PORT")
    db_user: str = Field(default="raguser", alias="DB_USER")
    db_password: str = Field(default="ragpass", alias="DB_PASSWORD")
    db_name: str = Field(default="ragdb", alias="DB_NAME")
    
    # 應用程式設定
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_file_size: int = Field(default=200, alias="MAX_FILE_SIZE")  # MB
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="CHUNK_OVERLAP")
    search_k: int = Field(default=5, alias="SEARCH_K")
    search_score_threshold: float = Field(default=0.7, alias="SEARCH_SCORE_THRESHOLD")
    
    # 安全設定
    secret_key: str = Field(default="your-secret-key-here", alias="SECRET_KEY")
    allowed_origins: str = Field(
        default="http://localhost:8501,http://localhost:3000",
        alias="ALLOWED_ORIGINS"
    )
    
    # 其他設定
    timezone: str = Field(default="Asia/Taipei", alias="TZ")
    language: str = Field(default="zh-TW", alias="LANGUAGE")
    
    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """驗證 LLM 提供者"""
        valid_providers = ["openai", "claude", "anthropic", "ollama"]
        if v not in valid_providers:
            raise ValueError(f"LLM provider must be one of {valid_providers}")
        return v
    
    @field_validator("vector_db")
    @classmethod
    def validate_vector_db(cls, v: str) -> str:
        """驗證向量資料庫"""
        valid_dbs = ["chroma", "redis", "qdrant"]
        if v not in valid_dbs:
            raise ValueError(f"Vector DB must be one of {valid_dbs}")
        return v
    
    @field_validator("db_type")
    @classmethod
    def validate_db_type(cls, v: str) -> str:
        """驗證資料庫類型"""
        valid_types = ["postgresql", "mysql"]
        if v not in valid_types:
            raise ValueError(f"DB type must be one of {valid_types}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """驗證日誌級別"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @property
    def db_url(self) -> str:
        """生成資料庫連接字串"""
        if self.db_type == "postgresql":
            driver = "postgresql+psycopg2"
            default_port = "5432"
        else:  # mysql
            driver = "mysql+pymysql"
            default_port = "3306"
        
        port = self.db_port or default_port
        return f"{driver}://{self.db_user}:{self.db_password}@{self.db_host}:{port}/{self.db_name}"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """解析允許的來源列表"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    def get_llm_config(self) -> Dict[str, Any]:
        """獲取 LLM 配置"""
        if self.llm_provider == "openai":
            return {
                "api_key": self.openai_api_key,
                "model": self.openai_model,
            }
        elif self.llm_provider in ["claude", "anthropic"]:
            return {
                "api_key": self.anthropic_api_key,
                "model": self.claude_model,
            }
        elif self.llm_provider == "ollama":
            return {
                "model": self.ollama_model,
                "base_url": self.ollama_base_url,
            }
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")
    
    def get_vector_db_config(self) -> Dict[str, Any]:
        """獲取向量資料庫配置"""
        if self.vector_db == "chroma":
            return {
                "persist_directory": self.chroma_persist_dir,
            }
        elif self.vector_db == "redis":
            return {
                "redis_url": self.redis_url,
                "index_name": self.redis_index_name,
            }
        elif self.vector_db == "qdrant":
            return {
                "url": self.qdrant_url,
                "collection_name": self.qdrant_collection,
            }
        else:
            raise ValueError(f"Unknown vector DB: {self.vector_db}")
    
    def validate_api_keys(self):
        """驗證必要的 API 金鑰"""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI")
        
        if self.llm_provider in ["claude", "anthropic"] and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when using Claude")
        
        if self.embed_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")


@lru_cache()
def get_settings() -> Settings:
    """
    獲取系統設定（帶快取）
    
    Returns:
        Settings 實例
    """
    return Settings()


# 便利函數
def get_config(key: str, default: Any = None) -> Any:
    """
    獲取單個配置值
    
    Args:
        key: 配置鍵
        default: 預設值
        
    Returns:
        配置值
    """
    settings = get_settings()
    return getattr(settings, key, default)


# 匯出
__all__ = [
    "Settings",
    "get_settings",
    "get_config",
]