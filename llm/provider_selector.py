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
        """直接調用 Ollama HTTP API"""
        try:
            # 嘗試 generate endpoint
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": 2048,  # 增加最大輸出長度
                    "stop": ["<|im_end|>", "</s>"]  # 停止標記
                }
            }
            
            if stream:
                # 流式響應
                response = requests.post(url, json=payload, stream=True, timeout=300)
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if 'response' in data:
                                    yield data['response']
                                if data.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    yield f"Ollama API 錯誤: {response.status_code}"
            else:
                # 非流式響應
                response = requests.post(url, json=payload, timeout=300)
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
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
                        return chat_result.get("message", {}).get("content", "")
                    else:
                        return f"Ollama API 錯誤: {response.status_code} - {response.text[:200]}"
                        
        except requests.exceptions.ConnectionError as e:
            if stream:
                yield f"無法連接到 Ollama 服務 ({self.base_url})，請確保 Ollama 正在運行。錯誤: {str(e)}"
            else:
                return f"無法連接到 Ollama 服務 ({self.base_url})，請確保 Ollama 正在運行。錯誤: {str(e)}"
        except requests.exceptions.Timeout:
            if stream:
                yield "Ollama 請求超時，可能是模型載入時間過長，請稍後再試"
            else:
                return "Ollama 請求超時，可能是模型載入時間過長，請稍後再試"
        except Exception as e:
            if stream:
                yield f"Ollama 錯誤: {type(e).__name__}: {str(e)}"
            else:
                return f"Ollama 錯誤: {type(e).__name__}: {str(e)}"
    
    def __call__(self, prompt):
        """支援函數調用方式"""
        return self.predict(prompt)
    
    def invoke(self, prompt):
        """兼容 LangChain 的 invoke 方法"""
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