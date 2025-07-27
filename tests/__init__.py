"""
RAG 系統測試套件

這個測試套件包含所有模組的單元測試和整合測試。
使用 pytest 執行測試：
    pytest tests/
    pytest tests/ -v  # 詳細輸出
    pytest tests/ --cov=.  # 測試覆蓋率
"""

import os
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 測試環境設定
os.environ["TESTING"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"

# 測試用的環境變數
TEST_ENV = {
    "LLM_PROVIDER": "openai",
    "VECTOR_DB": "chroma",
    "DB_TYPE": "postgresql",
    "OPENAI_API_KEY": "test-api-key",
    "ANTHROPIC_API_KEY": "test-anthropic-key",
}

def setup_test_env():
    """設定測試環境變數"""
    for key, value in TEST_ENV.items():
        if key not in os.environ:
            os.environ[key] = value