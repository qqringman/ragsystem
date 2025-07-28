# 🐳 Docker 完整操作指南

## 📋 目錄
- [快速開始](#快速開始)
- [基本操作](#基本操作)
- [進階操作](#進階操作)
- [除錯技巧](#除錯技巧)
- [常見問題](#常見問題)
- [最佳實踐](#最佳實踐)

## 🚀 快速開始

### 首次啟動
```bash
# 1. 複製環境變數檔案
cp .env.example .env

# 2. 構建並啟動所有服務
docker-compose up -d --build

# 3. 等待 Ollama 下載模型（首次需要幾分鐘）
docker-compose exec ollama ollama pull llama3

# 4. 檢查服務狀態
docker-compose ps

# 5. 查看日誌確認啟動成功
docker-compose logs -f app
```

### 快速啟動腳本
創建 `docker-start.sh`：
```bash
#!/bin/bash
echo "🚀 啟動 RAG 系統..."

# 啟動所有服務
docker-compose up -d

# 等待服務就緒
echo "⏳ 等待服務啟動..."
sleep 10

# 檢查 Ollama 模型
if ! docker-compose exec ollama ollama list | grep -q "llama3"; then
    echo "📥 下載 llama3 模型..."
    docker-compose exec ollama ollama pull llama3
fi

# 顯示服務狀態
echo "📊 服務狀態："
docker-compose ps

echo "✅ 系統已就緒！"
echo "🌐 Web UI: http://localhost:8501"
echo "🤖 Ollama API: http://localhost:11434"
```

## 🎮 基本操作

### 啟動服務

```bash
# 啟動所有服務（背景執行）
docker-compose up -d

# 啟動並查看日誌
docker-compose up

# 只啟動特定服務
docker-compose up -d app ollama

# 強制重新創建容器
docker-compose up -d --force-recreate

# 構建後啟動
docker-compose up -d --build
```

### 停止服務

```bash
# 停止所有服務（保留資料）
docker-compose stop

# 停止並移除容器（保留資料卷）
docker-compose down

# 停止並移除所有（包括資料卷）⚠️ 警告：會刪除所有資料
docker-compose down -v

# 停止特定服務
docker-compose stop app

# 優雅地重啟服務
docker-compose restart
```

### 查看狀態

```bash
# 查看運行中的服務
docker-compose ps

# 查看所有服務（包括停止的）
docker-compose ps -a

# 查看服務日誌
docker-compose logs

# 即時查看日誌（follow）
docker-compose logs -f

# 查看特定服務的日誌
docker-compose logs -f app

# 查看最近 100 行日誌
docker-compose logs --tail=100 app
```

## 🔧 進階操作

### 進入容器

```bash
# 進入 app 容器的 bash
docker-compose exec app bash

# 進入 ollama 容器
docker-compose exec ollama bash

# 在容器內執行命令
docker-compose exec app python --version
docker-compose exec ollama ollama list

# 以 root 用戶進入（如果需要）
docker-compose exec -u root app bash
```

### 管理 Ollama 模型

```bash
# 列出已安裝的模型
docker-compose exec ollama ollama list

# 下載新模型
docker-compose exec ollama ollama pull llama3
docker-compose exec ollama ollama pull mistral
docker-compose exec ollama ollama pull gemma:2b

# 刪除模型
docker-compose exec ollama ollama rm llama3

# 測試模型
docker-compose exec ollama ollama run llama3 "Hello, how are you?"
```

### 資料管理

```bash
# 備份 PostgreSQL 資料庫
docker-compose exec postgres pg_dump -U raguser ragdb > backup.sql

# 還原資料庫
docker-compose exec -T postgres psql -U raguser ragdb < backup.sql

# 備份向量資料庫
docker run --rm -v rag-system_vector_db:/data -v $(pwd):/backup alpine tar -czf /backup/vector_db_backup.tar.gz -C /data .

# 查看資料卷
docker volume ls | grep rag-system

# 清理未使用的資料卷
docker volume prune
```

### 容器套件管理

```bash
# 查看容器內已安裝的套件
docker-compose exec app pip list

# 查看特定套件版本
docker-compose exec app pip show numpy

# 匯出當前環境
docker-compose exec app pip freeze > current-packages.txt

# 在容器內更新套件
docker-compose exec app pip install --upgrade numpy

# 檢查過期套件
docker-compose exec app pip list --outdated
```

## 🔍 除錯技巧

### 1. 檢查服務健康狀態

```bash
# 查看健康檢查狀態
docker-compose ps

# 檢查特定服務的健康狀態
docker inspect rag-app | grep -A 10 "Health"

# 手動執行健康檢查
docker-compose exec app curl http://localhost:8501
docker-compose exec ollama curl http://localhost:11434/api/tags
```

### 2. 查看詳細日誌

```bash
# 查看所有服務的日誌
docker-compose logs

# 查看特定時間範圍的日誌
docker-compose logs --since 10m  # 最近 10 分鐘
docker-compose logs --since 2024-01-01  # 特定日期後

# 搜尋錯誤
docker-compose logs | grep -i error
docker-compose logs app | grep -i exception

# 導出日誌到檔案
docker-compose logs > logs_$(date +%Y%m%d_%H%M%S).txt
```

### 3. 監控資源使用

```bash
# 查看容器資源使用情況
docker stats

# 查看特定容器的詳細資訊
docker inspect rag-app

# 查看網路資訊
docker network ls
docker network inspect rag-system_rag-network

# 查看硬碟使用
docker system df
```

### 4. 網路除錯

```bash
# 測試容器間的連接
docker-compose exec app ping ollama
docker-compose exec app curl http://ollama:11434/api/tags

# 查看端口映射
docker-compose port app 8501
docker-compose port ollama 11434

# 檢查網路配置
docker-compose exec app cat /etc/hosts
```

### 5. 常用除錯命令

```bash
# 檢查環境變數
docker-compose exec app env | grep OLLAMA

# 測試資料庫連接
docker-compose exec app python -c "from db.sql_executor import test_connection; print(test_connection())"

# 檢查檔案權限
docker-compose exec app ls -la /app/vector_db

# 查看 Python 套件
docker-compose exec app pip list

# 測試 Ollama 連接
docker-compose exec app curl http://ollama:11434/api/tags
```

## ❓ 常見問題

### Q1: 服務無法啟動
```bash
# 查看詳細錯誤
docker-compose logs app

# 檢查端口占用
lsof -i :8501
lsof -i :11434

# 清理並重新啟動
docker-compose down
docker-compose up -d --build
```

### Q2: Ollama 模型下載失敗
```bash
# 手動重試下載
docker-compose exec ollama ollama pull llama3

# 使用較小的模型
docker-compose exec ollama ollama pull gemma:2b

# 檢查硬碟空間
df -h
docker system df
```

### Q3: 記憶體不足
```bash
# 查看記憶體使用
docker stats

# 限制容器記憶體（在 docker-compose.yml 中）
services:
  app:
    mem_limit: 2g
```

### Q4: 容器間無法通訊
```bash
# 確保在同一網路
docker network inspect rag-system_rag-network

# 重建網路
docker-compose down
docker network prune
docker-compose up -d
```

## 🏆 最佳實踐

### 1. 使用 `.env` 管理配置
```bash
# 永遠不要將 .env 提交到 Git
echo ".env" >> .gitignore

# 為不同環境準備不同的配置
cp .env.example .env.development
cp .env.example .env.production
```

### 2. 定期備份
```bash
# 創建備份腳本 backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p backups/$DATE

# 備份資料庫
docker-compose exec postgres pg_dump -U raguser ragdb > backups/$DATE/database.sql

# 備份向量資料庫
tar -czf backups/$DATE/vector_db.tar.gz -C vector_db .

echo "備份完成: backups/$DATE"
```

### 3. 監控和維護
```bash
# 定期清理
docker system prune -a --volumes  # 小心使用！

# 更新映像
docker-compose pull
docker-compose up -d

# 查看日誌大小
du -sh $(docker inspect --format='{{.LogPath}}' rag-app)
```

### 4. 生產環境建議

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

使用生產配置：
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📊 快速參考表

| 操作 | 命令 | 說明 |
|------|------|------|
| 啟動 | `docker-compose up -d` | 背景啟動所有服務 |
| 停止 | `docker-compose stop` | 停止服務但保留容器 |
| 移除 | `docker-compose down` | 停止並移除容器 |
| 日誌 | `docker-compose logs -f` | 查看即時日誌 |
| 進入 | `docker-compose exec app bash` | 進入容器 |
| 重啟 | `docker-compose restart` | 重啟所有服務 |
| 狀態 | `docker-compose ps` | 查看服務狀態 |
| 構建 | `docker-compose build` | 重新構建映像 |

---

💡 **提示**：建議將常用命令加入到 shell 別名或創建腳本，提高效率。