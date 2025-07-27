# 🚀 RAG 系統快速開始指南（免費模式）

本指南將幫助你在**完全免費**的情況下運行 RAG 系統，使用 Ollama（本地 LLM）和 HuggingFace（嵌入模型）。

## 📋 前置需求

- Python 3.12+
- 至少 8GB RAM（建議 16GB）
- 約 10GB 硬碟空間（用於模型）

## 🛠️ 快速安裝步驟

### 步驟 1：安裝 Ollama

**macOS / Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
從 [https://ollama.com/download](https://ollama.com/download) 下載並安裝

### 步驟 2：下載專案
```bash
git clone <your-repo-url>
cd rag-system
```

### 步驟 3：設定環境
```bash
# 複製環境變數範例
cp .env.example .env

# 安裝 Python 套件
pip install -r requirements.txt
```

### 步驟 4：啟動 Ollama 並下載模型
```bash
# 給執行權限（Linux/macOS）
chmod +x start_ollama.sh

# 執行啟動腳本
./start_ollama.sh
```

### 步驟 5：運行系統
```bash
# 方式 1：使用 Streamlit 網頁介面
streamlit run app.py

# 方式 2：使用命令列介面
python main.py
```

## 🎯 使用免費模式的優勢

1. **零成本**：不需要任何 API 金鑰或付費服務
2. **隱私保護**：所有資料都在本地處理
3. **離線運行**：下載模型後可完全離線使用
4. **客製化**：可以微調或更換不同的開源模型

## 🔧 進階設定

### 更換 Ollama 模型

編輯 `.env` 檔案：
```bash
# 小型快速模型（約 2.6GB）
OLLAMA_MODEL=gemma:2b

# 中型平衡模型（預設，約 4.7GB）
OLLAMA_MODEL=llama3

# 大型強大模型（約 40GB，需要更多資源）
OLLAMA_MODEL=llama2:70b
```

### 調整嵌入模型

如果想要更好的中文支援：
```bash
# 在 .env 中設定
HUGGINGFACE_MODEL=shibing624/text2vec-base-chinese
```

### 性能優化建議

1. **減少 chunk size**（在 `.env` 中）：
   ```bash
   CHUNK_SIZE=500  # 減少記憶體使用
   ```

2. **限制搜尋結果數量**：
   ```bash
   SEARCH_K=3  # 只返回最相關的 3 個結果
   ```

3. **使用較小的模型**：
   ```bash
   OLLAMA_MODEL=orca-mini  # 輕量級模型
   ```

## 🐳 使用 Docker（最簡單）

如果你偏好使用 Docker，所有服務（包括 Ollama）會自動配置：

### Docker 快速啟動

```bash
# 1. 克隆專案
git clone <your-repo-url>
cd rag-system

# 2. 複製環境變數
cp .env.example .env

# 3. 啟動所有服務
docker-compose up -d

# 4. 等待服務啟動（約 30 秒）
sleep 30

# 5. 下載 Ollama 模型（首次約需 5 分鐘）
docker-compose exec ollama ollama pull llama3

# 6. 訪問系統
open http://localhost:8501  # macOS
# 或
xdg-open http://localhost:8501  # Linux
```

### Docker 環境變數調整

在 `.env` 檔案中，使用 Docker 內部網路名稱：

```bash
# Docker 內部連接設定
OLLAMA_BASE_URL=http://ollama:11434
DB_HOST=postgres
REDIS_URL=redis://redis:6379
```

### 驗證 Docker 服務

```bash
# 檢查所有服務狀態
docker-compose ps

# 應該看到以下服務都是 "Up" 狀態：
# - rag-app (8501)
# - rag-ollama (11434)
# - rag-postgres (5432)
# - rag-redis (6379)

# 測試 Ollama
docker-compose exec ollama ollama list

# 測試應用連接
docker-compose exec app curl http://ollama:11434/api/tags
```

### Docker 常用操作

```bash
# 查看日誌
docker-compose logs -f app

# 重啟服務
docker-compose restart

# 停止服務
docker-compose stop

# 進入容器除錯
docker-compose exec app bash
```

### Docker 資源需求

- **最小配置**：4GB RAM, 10GB 硬碟
- **建議配置**：8GB RAM, 20GB 硬碟
- **GPU 支援**：如有 NVIDIA GPU，可在 docker-compose.yml 中啟用

### 切換到更小的模型（如果記憶體不足）

```bash
# 使用較小的模型
docker-compose exec ollama ollama pull gemma:2b

# 更新 .env
OLLAMA_MODEL=gemma:2b

# 重啟應用
docker-compose restart app
```

## ❓ 常見問題

### Q: Ollama 連接失敗？
A: 確保 Ollama 服務正在運行：
```bash
# 檢查服務狀態
curl http://localhost:11434/api/tags

# 手動啟動服務
ollama serve
```

### Q: 記憶體不足？
A: 嘗試使用較小的模型：
```bash
ollama pull gemma:2b  # 只需要約 1.5GB
```

### Q: 回應速度太慢？
A: 
1. 確保有足夠的 RAM
2. 考慮使用 GPU 加速（如果有 NVIDIA GPU）
3. 減少 `CHUNK_SIZE` 和 `SEARCH_K` 的值

## 📊 模型比較

| 模型 | 大小 | 速度 | 品質 | 建議用途 |
|------|------|------|------|----------|
| gemma:2b | 1.5GB | 極快 | 尚可 | 快速原型、測試 |
| llama3 | 4.7GB | 快 | 好 | 一般使用（推薦） |
| mistral | 4.1GB | 快 | 很好 | 程式碼相關任務 |
| llama2:13b | 7.4GB | 中等 | 很好 | 需要更高品質時 |
| llama2:70b | 40GB | 慢 | 極好 | 專業用途 |

## 🎉 開始使用

現在你的 RAG 系統已經準備就緒！訪問 http://localhost:8501 開始使用。

有問題嗎？查看主要的 README.md 或提交 issue。