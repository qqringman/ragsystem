# RAG 系統測試指南

## 測試架構概述

本測試套件使用 pytest 框架，包含單元測試和整合測試，涵蓋系統的所有主要模組。

## 測試檔案結構

```
tests/
├── __init__.py          # 測試套件初始化
├── test_llm.py          # LLM 提供者測試
├── test_loader.py       # 文件載入器測試
├── test_vectorstore.py  # 向量資料庫測試
├── test_db.py           # SQL 資料庫測試
├── pytest.ini           # Pytest 配置檔案
├── run_tests.py         # 測試執行腳本
└── README.md            # 測試文檔
```

## 快速開始

### 安裝測試依賴

```bash
# 安裝測試相關套件
pip install pytest pytest-cov pytest-asyncio pytest-mock
```

### 執行測試

```bash
# 執行所有測試
pytest

# 執行特定模組的測試
pytest tests/test_llm.py

# 執行帶覆蓋率的測試
pytest --cov=. --cov-report=html

# 執行並顯示詳細輸出
pytest -vv

# 使用測試執行腳本
python run_tests.py --coverage
```

## 測試類別

### 1. 單元測試

單元測試專注於測試單個函數或類別的功能，使用 mock 來隔離依賴。

```python
# 標記為單元測試
@pytest.mark.unit
def test_get_openai_llm():
    """測試獲取 OpenAI LLM"""
    pass
```

### 2. 整合測試

整合測試測試多個組件之間的互動，可能需要真實的服務連接。

```python
# 標記為整合測試
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY", "").startswith("sk-"),
    reason="需要真實的 API 金鑰"
)
def test_real_openai_call():
    """測試真實的 API 調用"""
    pass
```

## 各模組測試說明

### test_llm.py - LLM 測試

測試內容：
- ✅ LLM 提供者選擇（OpenAI、Claude、Ollama）
- ✅ API 金鑰驗證
- ✅ 錯誤處理
- ✅ Mock 預測功能
- ✅ 真實 API 調用（整合測試）

### test_loader.py - 文件載入測試

測試內容：
- ✅ 各種文件格式載入（PDF、Word、Excel、Markdown、HTML、JSON）
- ✅ 文字分割功能
- ✅ 元資料保留
- ✅ 多檔案處理
- ✅ 錯誤處理

### test_vectorstore.py - 向量資料庫測試

測試內容：
- ✅ 向量資料庫選擇（Chroma、Redis、Qdrant）
- ✅ 嵌入模型選擇（OpenAI、HuggingFace）
- ✅ 文件添加和檢索
- ✅ 相似度搜尋
- ✅ 真實向量操作（整合測試）

### test_db.py - 資料庫測試

測試內容：
- ✅ 資料庫配置（PostgreSQL、MySQL）
- ✅ 自然語言轉 SQL
- ✅ SQL 注入防護
- ✅ 查詢執行
- ✅ 連接測試

## 測試最佳實踐

### 1. 使用 Fixtures

```python
@pytest.fixture
def mock_llm_response():
    """提供測試用的 LLM 回應"""
    return {
        "default": "這是預設的測試回應",
        "rag_query": "根據提供的文件，答案是...",
    }
```

### 2. Mock 外部服務

```python
@patch('llm.provider_selector.ChatOpenAI')
def test_openai_predict(self, mock_openai):
    """測試 OpenAI 預測功能"""
    mock_instance = Mock()
    mock_instance.predict.return_value = "測試回答"
    mock_openai.return_value = mock_instance
```

### 3. 參數化測試

```python
@pytest.mark.parametrize("provider,expected_class", [
    ("openai", ChatOpenAI),
    ("claude", ChatAnthropic),
    ("ollama", Ollama),
])
def test_llm_providers(provider, expected_class):
    """測試不同的 LLM 提供者"""
    llm = get_llm(provider=provider)
    assert isinstance(llm, expected_class)
```

### 4. 跳過條件測試

```python
@pytest.mark.skipif(
    not os.path.exists("/usr/local/lib/python3.12/site-packages/chromadb"),
    reason="需要安裝 chromadb"
)
def test_real_chroma_operations():
    """測試真實的 Chroma 操作"""
    pass
```

## 測試環境變數

測試時會自動設定以下環境變數：

```python
TESTING=true
LOG_LEVEL=DEBUG
OPENAI_API_KEY=test-api-key  # 如果未設定
ANTHROPIC_API_KEY=test-anthropic-key  # 如果未設定
```

## 執行特定測試

```bash
# 只執行單元測試
pytest -m unit

# 只執行整合測試
pytest -m integration

# 執行包含特定關鍵字的測試
pytest -k "openai"

# 執行特定測試函數
pytest tests/test_llm.py::TestLLMProvider::test_get_openai_llm
```

## 測試覆蓋率

```bash
# 生成覆蓋率報告
pytest --cov=. --cov-report=html --cov-report=term

# 查看 HTML 報告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

目標覆蓋率：
- 單元測試：> 80%
- 整合測試：> 60%
- 總體覆蓋率：> 70%

## 持續整合（CI）

### GitHub Actions 範例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 常見問題

### 1. ImportError

確保專案根目錄在 Python 路徑中：
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### 2. API 金鑰錯誤

設定測試用的 API 金鑰：
```bash
export OPENAI_API_KEY=test-key
export ANTHROPIC_API_KEY=test-key
```

### 3. 資料庫連接錯誤

確保測試資料庫正在運行：
```bash
docker-compose up -d postgres redis
```

## 開發新測試

1. **命名規範**
   - 測試檔案：`test_*.py`
   - 測試類別：`Test*`
   - 測試函數：`test_*`

2. **測試結構**
   ```python
   class TestNewFeature:
       def setup_method(self):
           """每個測試前執行"""
           pass
       
       def teardown_method(self):
           """每個測試後執行"""
           pass
       
       def test_feature_success(self):
           """測試成功案例"""
           # Arrange
           # Act
           # Assert
           pass
       
       def test_feature_error(self):
           """測試錯誤案例"""
           with pytest.raises(ExpectedException):
               # Test code
   ```

3. **文檔字串**
   為每個測試函數寫清楚的文檔字串，說明測試的目的。

## 測試維護

1. **定期執行**：每次提交前執行測試
2. **更新測試**：功能變更時同步更新測試
3. **審查覆蓋率**：定期檢查並提升測試覆蓋率
4. **清理測試資料**：使用 `python run_tests.py --clean`

---

如有問題或需要新增測試，請參考現有測試範例或聯繫開發團隊。