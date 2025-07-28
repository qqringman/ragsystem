# 📊 使用 RAG 系統分析 Log 檔案指南

## 系統能力

本 RAG 系統已經優化支援大型 log 檔案分析，包括：

### 支援的 Log 類型
- **通用 Log**：應用程式日誌、系統日誌
- **Android ANR**：Application Not Responding traces
- **Android Tombstone**：崩潰 dumps
- **自定義格式**：可擴展支援其他格式

### 檔案大小支援
- ✅ 支援 2MB+ 的 log 檔案
- ✅ 智能分塊，保持上下文完整性
- ✅ 自動識別 log 類型並使用對應解析器

## 📝 使用步驟

### 1. 上傳 Log 檔案

```python
# 透過 Web UI
1. 開啟 http://localhost:8501
2. 點擊上傳檔案
3. 選擇你的 .log 或 .txt 檔案
4. 系統會自動識別並解析
```

### 2. 查詢範例

#### 通用 Log 分析
```
# 錯誤分析
- "分析這個 log 中的所有錯誤"
- "找出最常見的錯誤類型"
- "這個錯誤的根本原因是什麼"

# 時間分析
- "錯誤發生的時間分布"
- "系統在什麼時間段最不穩定"

# 模式識別
- "識別異常模式"
- "找出重複出現的問題"
```

#### Android ANR 分析
```
# ANR 診斷
- "分析這個 ANR 的原因"
- "哪個線程造成了阻塞"
- "是否有死鎖風險"
- "主線程在做什麼"

# 性能分析
- "哪些操作導致了 ANR"
- "建議如何優化"
```

#### Android Tombstone 分析
```
# 崩潰診斷
- "這個崩潰的根本原因"
- "崩潰發生在哪個函數"
- "是空指針還是記憶體錯誤"

# 堆疊分析
- "解釋這個 backtrace"
- "哪個庫導致了崩潰"
```

## ⚙️ 優化配置

### 環境變數設定 (.env)

```bash
# Log 檔案的特殊設定
CHUNK_SIZE=2000          # 較大的分塊大小
CHUNK_OVERLAP=200        # 更多重疊確保上下文
SEARCH_K=10              # 返回更多相關片段

# 使用較強的模型分析複雜 log
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3      # 或 mistral 用於技術分析
```

### 程式碼層級優化

如果需要處理更大的 log 檔案（10MB+），可以修改：

```python
# base_log_parser.py
def __init__(self, chunk_size: int = 3000, chunk_overlap: int = 300):
    """增加 chunk size 用於大檔案"""
    
# 在 .env 中
MAX_FILE_SIZE_MB=500    # 支援更大檔案
```

## 🎯 進階功能

### 1. 自定義 Log 解析器

創建新的解析器來支援特定格式：

```python
# loader/custom_log_parser.py
from .base_log_parser import BaseLogParser

class CustomLogParser(BaseLogParser):
    def get_log_type(self) -> str:
        return "custom_format"
    
    def can_parse(self, file_path: str, content_sample: str) -> bool:
        # 實現識別邏輯
        return "YOUR_LOG_PATTERN" in content_sample
    
    # 實現其他必要方法...
```

### 2. 批次分析

分析多個 log 檔案：

```python
# 上傳多個檔案
files = ["app.log", "error.log", "anr_trace.txt"]

# 跨檔案查詢
"比較這些 log 中的錯誤模式"
"找出所有檔案中的共同問題"
```

### 3. 時間序列分析

```python
# 查詢範例
"繪製錯誤數量的時間趨勢"
"哪個時間段問題最多"
"錯誤是否有週期性模式"
```

## 🔍 Log 分析最佳實踐

### 1. 準備階段
- 確保 log 檔案編碼為 UTF-8
- 如果檔案很大，考慮先按日期分割
- 移除敏感資訊（如密碼、token）

### 2. 分析策略
- **先總覽**：先問整體情況
- **再深入**：針對具體問題深入分析
- **找模式**：識別重複出現的問題
- **看趨勢**：分析時間上的變化

### 3. 問題定位
```
1. "這個 log 的整體健康狀況如何"
2. "最嚴重的錯誤是什麼"
3. "這個錯誤的完整上下文"
4. "類似錯誤還有哪些"
5. "建議的解決方案"
```

## 📊 性能指標

對於 2MB log 檔案：
- 解析時間：< 5 秒
- 查詢響應：< 3 秒
- 記憶體使用：< 500MB

## 🛠️ 故障排除

### 問題：檔案太大導致記憶體不足
```bash
# 解決方案：增加 Docker 記憶體限制
docker-compose.yml:
  app:
    mem_limit: 4g
```

### 問題：解析速度慢
```bash
# 解決方案：使用更快的嵌入模型
EMBED_PROVIDER=huggingface
HUGGINGFACE_MODEL=all-MiniLM-L6-v2  # 較小較快
```

### 問題：無法識別 log 格式
```python
# 解決方案：檢查 log 格式
# 在 general_log_parser.py 中添加新的模式
patterns['your_pattern'] = r'your_regex'
```

## 💡 提示

1. **使用正確的解析器**：系統會自動選擇，但你可以在檔名中包含提示（如 `app_anr_trace.log`）

2. **利用元數據**：解析器會提取重要元數據（時間、錯誤級別、線程等），可以在查詢中引用

3. **增量分析**：可以持續上傳新的 log 檔案，系統會保留之前的分析結果

4. **導出結果**：重要發現可以透過 Streamlit 下載或複製

---

有了這些優化，你的 RAG 系統完全可以處理 2MB 的 log 檔案分析需求！