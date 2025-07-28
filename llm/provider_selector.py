# llm/provider_selector.py
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from config import get_config
import requests
import json
import os

class SimpleOllama:
    """完全獨立的 Ollama 客戶端，不使用任何 LangChain 基類"""
    def __init__(self, model="llama3", base_url="http://localhost:11434", temperature=0.7):
        self.model = model
        # 智能處理 URL - 在 Docker 環境中自動替換 localhost
        if "localhost" in base_url and (os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER")):
            base_url = base_url.replace("localhost", "ollama")
            print(f"🐳 Docker 環境檢測：自動切換到 {base_url}")
        self.base_url = base_url
        self.temperature = temperature
        print(f"🤖 初始化 Ollama: {model} @ {self.base_url}")
    
    def predict(self, prompt, stream=False):
        """直接調用 Ollama HTTP API - 確保總是返回字串"""
        try:
            # 強制 stream 為 False 以避免返回 generator
            stream = False
            
            # 嘗試 generate endpoint
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,  # 強制非流式
                "options": {
                    "temperature": self.temperature,
                    "num_predict": 2048,
                    "stop": ["<|im_end|>", "</s>"]
                }
            }
            
            response = requests.post(url, json=payload, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                # 確保返回字串
                return str(result.get("response", ""))
            else:
                # 如果 generate 失敗，嘗試 chat endpoint
                chat_url = f"{self.base_url}/api/chat"
                chat_payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": self.temperature}
                }
                
                chat_response = requests.post(chat_url, json=chat_payload, timeout=300)
                if chat_response.status_code == 200:
                    chat_result = chat_response.json()
                    # 確保返回字串
                    message_content = chat_result.get("message", {}).get("content", "")
                    return str(message_content)
                else:
                    error_msg = f"Ollama API 錯誤: {response.status_code} - {response.text[:200]}"
                    print(f"❌ {error_msg}")
                    return error_msg
                    
        except requests.exceptions.ConnectionError as e:
            error_msg = f"無法連接到 Ollama 服務 ({self.base_url})，請確保 Ollama 正在運行。錯誤: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
        except requests.exceptions.Timeout:
            error_msg = "Ollama 請求超時，可能是模型載入時間過長，請稍後再試"
            print(f"❌ {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"Ollama 錯誤: {type(e).__name__}: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def __call__(self, prompt):
        """支援函數調用方式"""
        return self.predict(prompt)
    
    def invoke(self, prompt):
        """兼容 LangChain 的 invoke 方法"""
        # 如果 prompt 是 BaseMessage 或其他 LangChain 物件
        if hasattr(prompt, 'content'):
            prompt = prompt.content
        elif hasattr(prompt, 'messages'):
            # 如果是訊息列表
            messages = prompt.messages
            if messages:
                prompt = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
            else:
                prompt = str(prompt)
        else:
            prompt = str(prompt)
        
        return self.predict(prompt)
    
    @property
    def _llm_type(self):
        """返回 LLM 類型"""
        return "ollama"

def get_llm(provider=None):
    """
    獲取 LLM 實例
    
    Args:
        provider: LLM 提供者，可選 'openai', 'claude', 'anthropic', 'ollama'
                 如果不指定，從環境變數讀取
    
    Returns:
        LLM 實例
    """
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
        
        # 使用簡單的 Ollama 實現，完全避開 LangChain 的 Ollama 類
        return SimpleOllama(
            model=model,
            base_url=base_url,
            temperature=0.7
        )
    
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}. Supported: openai, claude, anthropic, ollama")