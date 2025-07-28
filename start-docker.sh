#!/bin/bash

echo "🚀 啟動 RAG Docker 系統"
echo "===================="

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 優雅地停止本地 Ollama 服務
echo -e "${YELLOW}檢查並停止本地 Ollama 服務...${NC}"

# 檢查 Ollama 是否在運行
if command -v ollama &> /dev/null; then
    # 嘗試使用 systemctl（如果是系統服務）
    if systemctl is-active --quiet ollama; then
        echo "停止 Ollama systemd 服務..."
        sudo systemctl stop ollama
        sleep 2
    fi
    
    # 檢查是否有 ollama serve 進程
    if pgrep -f "ollama serve" > /dev/null; then
        echo "發現 Ollama 進程，正在優雅停止..."
        # 先嘗試發送 SIGTERM（優雅停止）
        pkill -TERM -f "ollama serve"
        
        # 等待最多 5 秒讓進程優雅退出
        for i in {1..5}; do
            if ! pgrep -f "ollama serve" > /dev/null; then
                echo -e "${GREEN}✓ Ollama 已優雅停止${NC}"
                break
            fi
            echo "等待 Ollama 停止... ($i/5)"
            sleep 1
        done
        
        # 如果還在運行，使用 SIGKILL
        if pgrep -f "ollama serve" > /dev/null; then
            echo -e "${YELLOW}強制停止 Ollama...${NC}"
            pkill -KILL -f "ollama serve"
            sleep 1
        fi
    fi
    
    # 檢查端口是否仍被占用
    if lsof -i :11434 > /dev/null 2>&1; then
        echo -e "${YELLOW}端口 11434 仍被占用，檢查占用進程...${NC}"
        echo "占用端口的進程："
        lsof -i :11434
        
        # 詢問是否要停止占用端口的進程
        read -p "是否要停止占用端口 11434 的進程？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # 獲取 PID 並停止
            PID=$(lsof -t -i:11434)
            if [ ! -z "$PID" ]; then
                kill -TERM $PID
                sleep 2
                # 如果還在運行，強制停止
                if lsof -i :11434 > /dev/null 2>&1; then
                    kill -KILL $PID
                fi
                echo -e "${GREEN}✓ 已停止占用端口的進程${NC}"
            fi
        else
            echo -e "${RED}[ERROR] 端口 11434 仍被占用，無法繼續${NC}"
            echo "請手動停止占用端口的進程或修改 docker-compose.yml"
            exit 1
        fi
    fi
else
    echo "未檢測到本地 Ollama 安裝"
fi

# 2. 檢查所有必要的端口
echo -e "\n${YELLOW}檢查端口可用性...${NC}"
PORTS=(8501 11434 5432 6379)
PORT_NAMES=("Streamlit" "Ollama" "PostgreSQL" "Redis")
PORT_STATUS=0

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}
    
    if lsof -i :$PORT > /dev/null 2>&1; then
        echo -e "${RED}[ERROR] 端口 $PORT ($NAME) 已被占用！${NC}"
        echo "占用進程："
        lsof -i :$PORT | grep -v "^COMMAND"
        PORT_STATUS=1
    else
        echo -e "${GREEN}✓ 端口 $PORT ($NAME) 可用${NC}"
    fi
done

if [ $PORT_STATUS -eq 1 ]; then
    echo -e "\n${RED}[ERROR] 有端口被占用，請先釋放端口${NC}"
    echo "建議操作："
    echo "1. 停止其他 Docker 容器: docker-compose down"
    echo "2. 檢查並停止占用端口的服務"
    echo "3. 或修改 docker-compose.yml 使用其他端口"
    
    read -p "是否仍要繼續？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 3. 檢查 Docker 服務
echo -e "\n${YELLOW}檢查 Docker 服務...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}[ERROR] Docker 服務未運行！${NC}"
    echo "請先啟動 Docker Desktop 或 Docker 服務"
    exit 1
fi
echo -e "${GREEN}✓ Docker 服務正常${NC}"

# 4. 檢查 docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}未找到 docker-compose，嘗試使用 docker compose...${NC}"
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# 5. 停止現有的容器（如果有）
echo -e "\n${YELLOW}停止現有容器...${NC}"
$COMPOSE_CMD down

# 6. 清理未使用的資源（可選）
read -p "是否要清理未使用的 Docker 資源？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "清理未使用的資源..."
    docker system prune -f
fi

# 7. 智能構建和啟動服務
echo -e "\n${YELLOW}檢查是否需要構建...${NC}"

# 檢查映像是否存在
IMAGE_EXISTS=$(docker images -q rag-app:latest 2> /dev/null)

# 檢查是否有代碼變更（可選）
BUILD_NEEDED=false

if [ -z "$IMAGE_EXISTS" ]; then
    echo "映像不存在，需要構建"
    BUILD_NEEDED=true
else
    # 檢查 Dockerfile 或 requirements.txt 是否有更新
    if [ -f .docker-build-time ]; then
        # 檢查關鍵文件是否比上次構建時間新
        if [ Dockerfile -nt .docker-build-time ] || [ requirements.txt -nt .docker-build-time ]; then
            echo "檢測到 Dockerfile 或 requirements.txt 有更新"
            BUILD_NEEDED=true
        fi
    else
        # 沒有構建時間記錄，詢問用戶
        echo -e "${GREEN}✓ 映像已存在${NC}"
        read -p "是否要重新構建映像？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            BUILD_NEEDED=true
        fi
    fi
fi

# 根據需要構建或直接啟動
if [ "$BUILD_NEEDED" = true ]; then
    echo -e "${YELLOW}構建 Docker 映像...${NC}"
    if $COMPOSE_CMD build; then
        # 記錄構建時間
        touch .docker-build-time
        echo -e "${GREEN}✓ 構建成功${NC}"
    else
        echo -e "${RED}[ERROR] 構建失敗${NC}"
        exit 1
    fi
fi

# 啟動服務（不帶 --build）
echo -e "\n${YELLOW}啟動 Docker 服務...${NC}"
$COMPOSE_CMD up -d

# 8. 等待服務啟動
echo -e "\n${YELLOW}等待服務啟動...${NC}"
sleep 10

# 9. 檢查服務狀態
echo -e "\n${YELLOW}檢查服務狀態...${NC}"
$COMPOSE_CMD ps

# 10. 檢查 Ollama 是否需要下載模型
echo -e "\n${YELLOW}檢查 Ollama 模型...${NC}"
if ! $COMPOSE_CMD exec -T ollama ollama list | grep -q "llama3"; then
    echo "下載 llama3 模型（首次需要幾分鐘）..."
    $COMPOSE_CMD exec -T ollama ollama pull llama3
else
    echo -e "${GREEN}✓ llama3 模型已存在${NC}"
fi

# 11. 顯示訪問信息
echo -e "\n${GREEN}✅ RAG 系統已啟動！${NC}"
echo "========================"
echo "📊 服務訪問地址："
echo "- Web UI: http://localhost:8501"
echo "- Ollama API: http://localhost:11434"
echo ""
echo "📝 常用命令："
echo "- 查看日誌: $COMPOSE_CMD logs -f app"
echo "- 停止服務: $COMPOSE_CMD down"
echo "- 重啟服務: $COMPOSE_CMD restart"
echo ""
echo "💡 提示：如果無法訪問，請稍等片刻讓服務完全啟動"