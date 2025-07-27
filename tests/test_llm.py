"""
LLM 提供者測試

測試所有支援的 LLM 提供者：
- OpenAI
- Anthropic Claude
- Ollama
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from llm.provider_selector import get_llm
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Ollama


class TestLLMProvider:
    """LLM 提供者選擇器測試"""
    
    def setup_method(self):
        """每個測試方法執行前的設置"""
        # 儲存原始環境變數
        self.original_env = os.environ.copy()
        
    def teardown_method(self):
        """每個測試方法執行後的清理"""
        # 恢復原始環境變數
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_get_openai_llm(self):
        """測試獲取 OpenAI LLM"""
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = "test-key"
        
        llm = get_llm()
        
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-3.5-turbo"
        assert llm.temperature == 0.7
    
    def test_get_claude_llm(self):
        """測試獲取 Claude LLM"""
        os.environ["LLM_PROVIDER"] = "claude"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
        
        llm = get_llm(provider="claude")
        
        assert isinstance(llm, ChatAnthropic)
        assert llm.model == "claude-3-opus-20240229"
        assert llm.temperature == 0.7
    
    def test_get_anthropic_llm(self):
        """測試使用 'anthropic' 作為提供者名稱"""
        os.environ["LLM_PROVIDER"] = "anthropic"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
        
        llm = get_llm()
        
        assert isinstance(llm, ChatAnthropic)
    
    def test_get_ollama_llm(self):
        """測試獲取 Ollama LLM"""
        os.environ["LLM_PROVIDER"] = "ollama"
        
        llm = get_llm(provider="ollama")
        
        assert isinstance(llm, Ollama)
        assert llm.model == "llama3"
        assert llm.temperature == 0.7
    
    def test_missing_openai_api_key(self):
        """測試缺少 OpenAI API 金鑰時的錯誤"""
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ.pop("OPENAI_API_KEY", None)
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
            get_llm()
    
    def test_missing_anthropic_api_key(self):
        """測試缺少 Anthropic API 金鑰時的錯誤"""
        os.environ["LLM_PROVIDER"] = "claude"
        os.environ.pop("ANTHROPIC_API_KEY", None)
        
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
            get_llm()
    
    def test_unsupported_provider(self):
        """測試不支援的 LLM 提供者"""
        with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
            get_llm(provider="unsupported")
    
    def test_provider_override(self):
        """測試參數覆蓋環境變數"""
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        
        llm = get_llm(provider="claude")
        
        assert isinstance(llm, ChatAnthropic)


class TestLLMFunctionality:
    """測試 LLM 功能"""
    
    @patch('llm.provider_selector.ChatOpenAI')
    def test_openai_predict(self, mock_openai):
        """測試 OpenAI 預測功能"""
        # 設置 mock
        mock_instance = Mock()
        mock_instance.predict.return_value = "這是一個測試回答"
        mock_openai.return_value = mock_instance
        
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = "test-key"
        
        llm = get_llm()
        result = llm.predict("測試問題")
        
        assert result == "這是一個測試回答"
        mock_instance.predict.assert_called_once_with("測試問題")
    
    @patch('llm.provider_selector.ChatAnthropic')
    def test_claude_predict(self, mock_claude):
        """測試 Claude 預測功能"""
        # 設置 mock
        mock_instance = Mock()
        mock_instance.predict.return_value = "Claude 的測試回答"
        mock_claude.return_value = mock_instance
        
        os.environ["LLM_PROVIDER"] = "claude"
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        
        llm = get_llm()
        result = llm.predict("測試問題")
        
        assert result == "Claude 的測試回答"
        mock_instance.predict.assert_called_once_with("測試問題")
    
    @patch('llm.provider_selector.Ollama')
    def test_ollama_predict(self, mock_ollama):
        """測試 Ollama 預測功能"""
        # 設置 mock
        mock_instance = Mock()
        mock_instance.predict.return_value = "Ollama 的測試回答"
        mock_ollama.return_value = mock_instance
        
        os.environ["LLM_PROVIDER"] = "ollama"
        
        llm = get_llm()
        result = llm.predict("測試問題")
        
        assert result == "Ollama 的測試回答"
        mock_instance.predict.assert_called_once_with("測試問題")


class TestLLMIntegration:
    """LLM 整合測試"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY", "").startswith("sk-"),
        reason="需要真實的 OpenAI API 金鑰"
    )
    def test_real_openai_call(self):
        """測試真實的 OpenAI API 調用"""
        llm = get_llm(provider="openai")
        result = llm.predict("說 '測試成功'")
        
        assert "測試成功" in result
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-"),
        reason="需要真實的 Anthropic API 金鑰"
    )
    def test_real_claude_call(self):
        """測試真實的 Claude API 調用"""
        llm = get_llm(provider="claude")
        result = llm.predict("說 '測試成功'")
        
        assert "測試成功" in result


# 測試用的 fixtures
@pytest.fixture
def mock_llm_response():
    """模擬 LLM 回應"""
    return {
        "default": "這是預設的測試回應",
        "rag_query": "根據提供的文件，答案是...",
        "sql_query": "SELECT * FROM products WHERE category = 'electronics'",
    }


@pytest.fixture
def mock_llm_instance():
    """模擬 LLM 實例"""
    mock = Mock()
    mock.predict = Mock(return_value="模擬回應")
    mock.temperature = 0.7
    mock.model_name = "test-model"
    return mock