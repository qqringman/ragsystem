# config/settings.py - 集中管理配置
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_provider: str = "claude"
    vector_db: str = "chroma"
    chunk_size: int = 1000
    chunk_overlap: int = 100
    
    class Config:
        env_file = ".env"

settings = Settings()