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
PORTS=(7777 11434 5432 6379)
PORT_NAMES=("FastAPI" "Ollama" "PostgreSQL" "Redis")
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

# 其餘部分保持不變，但修改顯示訊息：

# 11. 顯示訪問信息
echo -e "\n${GREEN}✅ RAG 系統已啟動！${NC}"
echo "========================"
echo "📊 服務訪問地址："
echo "- Web UI: http://localhost:7777"
echo "- API Docs: http://localhost:7777/docs"
echo "- Ollama API: http://localhost:11434"
echo ""
echo "📝 常用命令："
echo "- 查看日誌: $COMPOSE_CMD logs -f app"
echo "- 停止服務: $COMPOSE_CMD down"
echo "- 重啟服務: $COMPOSE_CMD restart"
echo ""
echo "💡 提示：如果無法訪問，請稍等片刻讓服務完全啟動"