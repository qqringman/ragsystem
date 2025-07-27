import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Ollama

# 嘗試使用 config 模組，如果失敗則使用環境變數
try:
    from config import get_config
    USE_CONFIG = True
except ImportError:
    USE_CONFIG = False

def get_llm(provider=None):
    # 使用配置系統或環境變數
    if USE_CONFIG:
        provider = provider or get_config("LLM_PROVIDER", "openai")
    else:
        provider = provider or os.getenv("LLM_PROVIDER", "openai")
    
    if provider in ["claude", "anthropic"]:
        if USE_CONFIG:
            api_key = get_config("ANTHROPIC_API_KEY")
        else:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        return ChatAnthropic(
            model="claude-3-opus-20240229",
            anthropic_api_key=api_key,
            temperature=0.7,
        )
    
    elif provider == "openai":
        if USE_CONFIG:
            api_key = get_config("OPENAI_API_KEY")
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            openai_api_key=api_key,
            temperature=0.7,
        )
    
    elif provider == "ollama":
        return Ollama(
            model="llama3",
            temperature=0.7,
        )
    
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")