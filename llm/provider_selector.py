from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Ollama
from config import get_config

def get_llm(provider=None):
    # 使用配置系統
    provider = provider or get_config("LLM_PROVIDER")
    
    if provider in ["claude", "anthropic"]:
        api_key = get_config("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        model = get_config("CLAUDE_MODEL", "claude-3-opus-20240229")
        
        return ChatAnthropic(
            model=model,
            anthropic_api_key=api_key,
            temperature=0.7,
        )
    
    elif provider == "openai":
        api_key = get_config("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        model = get_config("OPENAI_MODEL", "gpt-3.5-turbo")
        
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=0.7,
        )
    
    elif provider == "ollama":
        model = get_config("OLLAMA_MODEL", "llama3")
        base_url = get_config("OLLAMA_BASE_URL", "http://localhost:11434")
        
        return Ollama(
            model=model,
            base_url=base_url,
            temperature=0.7,
        )
    
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")