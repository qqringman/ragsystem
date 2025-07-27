# 🐳 Docker Compose 啟動 Ollama 服務

## 問題說明

`ollama` 服務在 `docker-compose.yml` 中被設定為可選服務（使用 profiles），所以預設不會啟動。

## 解決方案

### 方法 1：使用 Profile 啟動（推薦）

```bash
# 啟動包含 ollama 的服務
docker-compose --profile ollama up -d

# 檢查服務狀態
docker-compose ps

# 然後下載模型
docker-compose exec ollama ollama pull llama3
```

### 方法 2：修改 docker-compose.yml

移除 ollama 服務的 profiles 設定，讓它預設啟動：

```yaml
# 找到 ollama 服務部分，移除或註解 profiles
ollama:
  image: ollama/ollama:latest
  container_name: rag-ollama
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  networks:
    - rag-network
  restart: unless-stopped
  # profiles:      # 註解或刪除這兩行
  #   - ollama
```

然後重新啟動：
```bash
docker-compose up -d ollama
```

### 方法 3：單獨啟動 Ollama 容器

```bash
# 直接運行 ollama 容器
docker run -d \
  --name ollama \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  ollama/ollama:latest

# 下載模型
docker exec ollama ollama pull llama3

# 檢查模型列表
docker exec ollama ollama list
```

### 方法 4：在主機上安裝 Ollama（最簡單）

如果不想使用 Docker 中的 Ollama：

```bash
# 退出 docker 目錄
cd ..

# 在主機上安裝 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 啟動 Ollama 服務
ollama serve &

# 下載模型
ollama pull llama3

# 檢查是否正常
ollama list
```

然後修改 `.env`：
```bash
# 如果使用主機的 Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434  # Docker 內部訪問主機

# 或如果不使用 Docker 運行 RAG
OLLAMA_BASE_URL=http://localhost:11434
```

## 🔍 檢查服務狀態

### 檢查 Docker 服務
```bash
# 查看所有服務（包括 profiles 中的）
docker-compose config --profiles

# 查看運行中的服務
docker-compose ps

# 查看特定 profile 的服務
docker-compose --profile ollama ps
```

### 測試 Ollama 連接
```bash
# 如果 Ollama 在運行，測試 API
curl http://localhost:11434/api/tags

# 應該返回 JSON 格式的模型列表
```

## 📋 完整的啟動流程

### 使用 Docker Compose + Ollama：

```bash
# 1. 啟動所有服務（包含 ollama）
docker-compose --profile ollama up -d

# 2. 等待服務啟動
sleep 10

# 3. 檢查服務狀態
docker-compose ps

# 4. 下載 llama3 模型
docker-compose exec ollama ollama pull llama3

# 5. 驗證模型
docker-compose exec ollama ollama list

# 6. 測試模型
docker-compose exec ollama ollama run llama3 "Hello, how are you?"
```

### 或使用本地 Ollama（更簡單）：

```bash
# 1. 安裝 Ollama（如果還沒安裝）
curl -fsSL https://ollama.com/install.sh | sh

# 2. 啟動 Ollama
ollama serve &

# 3. 下載模型
ollama pull llama3

# 4. 啟動 RAG 系統（不使用 ollama 容器）
docker-compose up -d app postgres redis

# 或直接在本地運行
streamlit run app.py
```

## 💡 建議

1. **開發環境**：使用本地安裝的 Ollama 更方便
2. **生產環境**：使用 Docker 容器化部署
3. **資源考量**：Ollama 需要較多資源，確保有足夠的 RAM

## 🔧 故障排除

### 如果 Ollama 容器啟動失敗：

1. **檢查端口占用**：
   ```bash
   lsof -i :11434
   ```

2. **檢查 Docker 資源**：
   ```bash
   docker system df
   docker system prune  # 清理不用的資源
   ```

3. **查看容器日誌**：
   ```bash
   docker-compose --profile ollama logs ollama
   ```

### 如果模型下載失敗：

1. **檢查網路連接**
2. **確保有足夠的硬碟空間**（llama3 約需 5GB）
3. **嘗試使用較小的模型**：
   ```bash
   ollama pull gemma:2b  # 只需要約 1.5GB
   ```

---

選擇最適合你的方法，通常**方法 4**（在主機上安裝 Ollama）是最簡單的。