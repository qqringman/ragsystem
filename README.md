# RAG 全功能系統 - 安裝與使用指南

## 系統架構概述

這是一個支援多資料來源的 RAG (Retrieval-Augmented Generation) 問答系統，具有以下特點：

- 🚀 支援多種 LLM：OpenAI GPT、Claude、Ollama
- 📚 支援多種文件格式：PDF、Word、Excel、Markdown、HTML、JSON
- 🗄️ 支援多種向量資料庫：Chroma、Redis、Qdrant
- 💾 支援 SQL 資料庫查詢：PostgreSQL、MySQL
- 🖥️ 友善的 Streamlit 網頁介面

## 安裝需求

### 系統需求
- Docker 20.10+ 和 Docker Compose 2.0+
- 或 Python 3.12+（本地安裝）
- 至少 4GB RAM
- 10GB 可用硬碟空間

### API 金鑰需求
根據你選擇的 LLM，需要準備對應的 API 金鑰：
- OpenAI GPT：需要 `OPENAI_API_KEY`
- Claude：需要 `ANTHROPIC_API_KEY`
- Ollama：不需要 API 金鑰（本地運行）

## Docker 安裝方式（推薦）

### 1. 環境需求
- Docker 20.10+ 和 Docker Compose 2.0+
- 至少 8GB RAM（Ollama 需要較多記憶體）
- 15GB 可用硬碟空間（包含模型）

### 2. 快速啟動

```bash
# 克隆專案
git clone <your-repo-url>
cd rag-system

# 設定環境變數
cp .env.example .env

# 一鍵啟動所有服務（包含 Ollama）
docker-compose up -d

# 首次需要下載 Ollama 模型（約 5GB）
docker-compose exec ollama ollama pull llama3

# 檢查服務狀態
docker-compose ps

# 查看啟動日誌
docker-compose logs -f app
```

### 3. 服務說明

啟動後會運行以下服務：

| 服務 | 容器名稱 | 端口 | 說明 |
|------|----------|------|------|
| RAG 應用 | rag-app | 8501 | Streamlit Web UI |
| Ollama | rag-ollama | 11434 | LLM 服務 |
| PostgreSQL | rag-postgres | 5432 | 關聯式資料庫 |
| Redis | rag-redis | 6379 | 向量資料庫快取 |

### 4. 訪問系統

- **Web UI**: http://localhost:8501
- **Ollama API**: http://localhost:11434
- **健康檢查**: http://localhost:8501/_stcore/health

### 5. 基本操作

```bash
# 停止服務
docker-compose stop

# 重啟服務
docker-compose restart

# 查看日誌
docker-compose logs -f [service_name]

# 完全移除（保留資料）
docker-compose down

# 完全移除（包含資料）⚠️ 警告
docker-compose down -v
```

### 6. 更換 Ollama 模型

```bash
# 列出可用模型
docker-compose exec ollama ollama list

# 下載其他模型
docker-compose exec ollama ollama pull mistral    # 7B 參數
docker-compose exec ollama ollama pull gemma:2b   # 2B 參數（較小）
docker-compose exec ollama ollama pull llama2:13b # 13B 參數（較大）

# 在 .env 中更換模型
OLLAMA_MODEL=mistral
```

## 本地安裝方式

### 1. 安裝系統依賴

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3-pip
sudo apt-get install -y tesseract-ocr poppler-utils libmagic1
```

**macOS:**
```bash
brew install python@3.12 tesseract poppler libmagic
```

### 2. 設定 Python 環境

```bash
# 創建虛擬環境
python3.12 -m venv venv

# 啟動虛擬環境
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 升級 pip
pip install --upgrade pip
```

### 3. 安裝 Python 套件

```bash
pip install -r requirements.txt
```

### 4. 設定環境變數

複製並編輯環境變數檔案：
```bash
cp .env.example .env
# 編輯 .env 檔案，填入你的 API 金鑰
```

### 5. 啟動系統

```bash
# 啟動 Streamlit 介面
streamlit run app.py

# 或使用命令列介面
python main.py
```

## 使用教學

### 基本使用流程

1. **輸入問題**：在文字框中輸入你的問題
2. **選擇資料來源**：
   - `docs`：搜尋上傳的文件
   - `db`：查詢資料庫
3. **上傳文件**（可選）：支援 PDF、Word、Excel 等格式
4. **點擊查詢**：系統會自動處理並返回答案

### 進階功能

#### 1. 切換 LLM 模型

編輯 `.env` 檔案中的 `LLM_PROVIDER`：

```bash
# 使用 OpenAI GPT
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# 使用 Claude
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...

# 使用 Ollama（本地模型）
LLM_PROVIDER=ollama
```

#### 2. 切換向量資料庫

編輯 `.env` 檔案中的 `VECTOR_DB`：

```bash
# 使用 Chroma（預設）
VECTOR_DB=chroma

# 使用 Redis
VECTOR_DB=redis
# 需要先啟動 Redis 服務

# 使用 Qdrant
VECTOR_DB=qdrant
# 需要先啟動 Qdrant 服務
```

#### 3. 資料庫查詢功能

如果要使用資料庫查詢功能：

1. 確保資料庫服務正在運行
2. 在 `.env` 中設定資料庫連接資訊
3. 在查詢時勾選「資料庫」選項

### 常見使用案例

#### 案例 1：文件問答

```
問題：這份報告的主要結論是什麼？
操作：
1. 上傳 PDF 報告
2. 選擇「docs」資料來源
3. 輸入問題並查詢
```

#### 案例 2：資料庫查詢

```
問題：查詢上個月的銷售總額
操作：
1. 選擇「db」資料來源
2. 輸入自然語言查詢
3. 系統會自動轉換為 SQL 並執行
```

#### 案例 3：混合查詢

```
問題：對比文件中的預測與資料庫中的實際數據
操作：
1. 上傳相關文件
2. 同時選擇「docs」和「db」
3. 系統會從兩個來源獲取資訊並整合
```

## 故障排除

### 常見問題

1. **API 金鑰錯誤**
   - 檢查 `.env` 檔案中的 API 金鑰是否正確
   - 確保沒有多餘的空格或換行

2. **文件上傳失敗**
   - 檢查檔案格式是否支援
   - 確保檔案大小不超過 200MB
   - 檢查是否安裝了必要的系統依賴

3. **資料庫連接失敗**
   - 確認資料庫服務正在運行
   - 檢查連接參數是否正確
   - 確認防火牆設定

4. **向量資料庫錯誤**
   - 確保選擇的向量資料庫服務正在運行
   - 檢查連接設定是否正確

### 查看日誌

**Docker 方式：**
```bash
docker-compose logs -f app
```

**本地方式：**
查看終端輸出或 Streamlit 的錯誤訊息

## 性能優化建議

1. **使用 GPU 加速**（如果有 NVIDIA GPU）：
   ```bash
   # 安裝 CUDA 版本的套件
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

2. **調整 Chunk 大小**：
   編輯 `loader/doc_parser.py` 中的參數：
   ```python
   chunk_size=1000  # 增加以獲得更多上下文
   chunk_overlap=100  # 增加重疊以確保連續性
   ```

3. **使用本地嵌入模型**：
   設定 `EMBED_PROVIDER=huggingface` 以減少 API 調用

## 系統維護

### 備份資料

```bash
# 備份向量資料庫
docker-compose exec app tar -czf /backup/vectordb.tar.gz /app/vector_db

# 備份環境設定
cp .env .env.backup
```

### 更新系統

```bash
# 拉取最新代碼
git pull origin main

# 重建 Docker 映像
docker-compose build --no-cache

# 重啟服務
docker-compose up -d
```

### 清理資料

```bash
# 清理向量資料庫
rm -rf vector_db/*

# 清理暫存檔案
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete
```

## 安全建議

1. **保護 API 金鑰**
   - 永遠不要將 `.env` 檔案提交到版本控制
   - 定期輪換 API 金鑰

2. **網路安全**
   - 在生產環境中使用 HTTPS
   - 配置防火牆規則
   - 限制資料庫訪問權限

3. **資料安全**
   - 定期備份重要資料
   - 對敏感文件加密
   - 實施訪問控制

## 授權與支援

本專案採用 MIT 授權條款。如有問題，請透過以下方式聯繫：

- GitHub Issues：[your-repo-url]/issues
- Email：your-email@example.com

---

最後更新：2024年12月