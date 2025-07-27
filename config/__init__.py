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

# 如果有 settings.py，匯入它
try:
    from .settings import Settings, get_settings, get_config as settings_get_config
    HAS_SETTINGS = True
except ImportError:
    HAS_SETTINGS = False

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent

# 預設配置值
DEFAULT_CONFIG = {
    "LLM_PROVIDER": "openai",
    "VECTOR_DB": "chroma",
    "EMBED_PROVIDER": "openai",
    "CHUNK_SIZE": 1000,
    "CHUNK_OVERLAP": 100,
    "LOG_LEVEL": "INFO",
    "MAX_FILE_SIZE": 200,  # MB
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
    # 如果有 settings.py，優先使用它
    if HAS_SETTINGS:
        try:
            return settings_get_config(key, default)
        except:
            pass
    
    # 否則使用環境變數
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
    
    # 檢查缺失的配置
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        raise ValueError(f"缺少必要的環境變數: {', '.join(missing_keys)}")


# 匯出的公開 API
__all__ = [
    "get_config",
    "validate_config",
    "PROJECT_ROOT",
    "DEFAULT_CONFIG",
]

# 如果有 settings.py，也匯出它的內容
if HAS_SETTINGS:
    __all__.extend(["Settings", "get_settings"])