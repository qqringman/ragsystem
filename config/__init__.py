"""
配置管理模組

提供系統配置的集中管理，包括：
- 環境變數管理
- 預設值設定
- 配置驗證
"""

from pathlib import Path
import os
from typing import Optional
from dotenv import load_dotenv

# 載入 .env 檔案（這很重要！）
load_dotenv()

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent

# 預設配置值 - 改為使用免費服務
DEFAULT_CONFIG = {
    "LLM_PROVIDER": "ollama",  # 改為預設使用 Ollama
    "OLLAMA_MODEL": "llama3",
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "VECTOR_DB": "chroma",
    "EMBED_PROVIDER": "huggingface",  # 預設使用免費的 HuggingFace
    "HUGGINGFACE_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
    "CHUNK_SIZE": 1000,
    "CHUNK_OVERLAP": 100,
    "LOG_LEVEL": "INFO",
    "MAX_FILE_SIZE_MB": 200,
    "SEARCH_K": 5,
}


def get_config(key: str, default: Optional[str] = None) -> str:
    """
    獲取配置值
    
    Args:
        key: 配置鍵
        default: 預設值
    
    Returns:
        配置值
    """
    return os.getenv(key, default or DEFAULT_CONFIG.get(key, ""))


def validate_config():
    """驗證必要的配置是否存在"""
    required_keys = []
    
    # 根據 LLM 提供者檢查必要的 API 金鑰
    llm_provider = get_config("LLM_PROVIDER")
    if llm_provider == "openai":
        required_keys.append("OPENAI_API_KEY")
    elif llm_provider in ["claude", "anthropic"]:
        required_keys.append("ANTHROPIC_API_KEY")
    # Ollama 不需要 API key
    
    # 根據嵌入提供者檢查
    embed_provider = get_config("EMBED_PROVIDER")
    if embed_provider == "openai":
        required_keys.append("OPENAI_API_KEY")
    # HuggingFace 不需要 API key
    
    # 檢查缺失的配置
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        raise ValueError(f"缺少必要的環境變數: {', '.join(missing_keys)}")


def is_free_mode() -> bool:
    """檢查是否在免費模式下運行（使用 Ollama + HuggingFace）"""
    return (get_config("LLM_PROVIDER") == "ollama" and 
            get_config("EMBED_PROVIDER") == "huggingface")


# 匯出的公開 API
__all__ = [
    "get_config",
    "validate_config",
    "is_free_mode",
    "PROJECT_ROOT",
    "DEFAULT_CONFIG",
]