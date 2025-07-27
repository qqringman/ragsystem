"""
LLM (Large Language Model) 提供者模組

支援多種 LLM 提供者：
- OpenAI GPT
- Anthropic Claude
- Ollama (本地模型)
"""

from .provider_selector import get_llm

# 版本資訊
__version__ = "1.0.0"

# 支援的 LLM 提供者
SUPPORTED_PROVIDERS = ["openai", "claude", "anthropic", "ollama"]

# 預設模型設定
DEFAULT_MODELS = {
    "openai": "gpt-3.5-turbo",
    "claude": "claude-3-opus-20240229",
    "anthropic": "claude-3-opus-20240229",
    "ollama": "llama3",
}

# 匯出的公開 API
__all__ = [
    "get_llm",
    "SUPPORTED_PROVIDERS",
    "DEFAULT_MODELS",
]