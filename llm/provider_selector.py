import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Ollama

def get_llm(provider=None):
    # 使用環境變數或參數
    provider = provider or os.getenv("LLM_PROVIDER", "openai")
    
    if provider in ["claude", "anthropic"]:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        return ChatAnthropic(
            model="claude-3-opus-20240229",
            anthropic_api_key=api_key,
            temperature=0.7,
        )
    
    elif provider == "openai":
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