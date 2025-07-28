#!/bin/bash

# RAG System 啟動腳本
# 用於在本地環境直接啟動所有相關服務

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 設定變數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
PID_DIR="$PROJECT_ROOT/.pids"
LOG_DIR="$PROJECT_ROOT/logs"
VENV_DIR="$PROJECT_ROOT/venv"

# 創建必要目錄
mkdir -p "$PID_DIR" "$LOG_DIR" "$PROJECT_ROOT/vector_db" "$PROJECT_ROOT/uploads"

# 載入環境變數
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${BLUE}載入環境變數...${NC}"
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
else
    echo -e "${RED}錯誤：找不到 .env 檔案${NC}"
    echo "請先複製 .env.example 到 .env 並設定必要的環境變數"
    exit 1
fi

# 函數：檢查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}錯誤：找不到 $1 命令${NC}"
        return 1
    fi
    return 0
}

# 函數：檢查端口是否被占用
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}警告：端口 $port ($service) 已被占用${NC}"
        return 1
    fi
    return 0
}

# 函數：啟動服務並記錄 PID
start_service() {
    local name=$1
    local command=$2
    local log_file="$LOG_DIR/${name}.log"
    local pid_file="$PID_DIR/${name}.pid"
    
    # 檢查是否已在運行
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}$name 已在運行 (PID: $pid)${NC}"
            return 0
        fi
    fi
    
    echo -e "${BLUE}啟動 $name...${NC}"
    
    # 啟動服務
    if [ "$name" == "api_server" ]; then
        # FastAPI 特殊處理
        nohup $command > "$log_file" 2>&1 &
    else
        # 其他服務
        $command > "$log_file" 2>&1 &
    fi
    
    local pid=$!
    echo $pid > "$pid_file"
    
    # 等待服務啟動
    sleep 2
    
    # 檢查是否成功啟動
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $name 啟動成功 (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}✗ $name 啟動失敗${NC}"
        rm -f "$pid_file"
        return 1
    fi
}

# 主程式開始
echo -e "${GREEN}🚀 啟動 RAG System${NC}"
echo "================================"

# 1. 檢查 Python 環境
echo -e "\n${BLUE}1. 檢查 Python 環境${NC}"
if [ -d "$VENV_DIR" ]; then
    echo "啟用虛擬環境..."
    source "$VENV_DIR/bin/activate"
else
    echo "使用系統 Python..."
fi

# 檢查 Python 版本
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python 版本: $PYTHON_VERSION"

if [[ ! "$PYTHON_VERSION" =~ ^3\.(10|11|12) ]]; then
    echo -e "${YELLOW}警告：建議使用 Python 3.10-3.12${NC}"
fi

# 2. 檢查必要的命令
echo -e "\n${BLUE}2. 檢查系統依賴${NC}"
REQUIRED_COMMANDS=("python3" "pip3")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if check_command "$cmd"; then
        echo -e "${GREEN}✓ $cmd${NC}"
    else
        exit 1
    fi
done

# 3. 檢查端口
echo -e "\n${BLUE}3. 檢查端口可用性${NC}"
check_port 7777 "FastAPI"
check_port 11434 "Ollama"

# 4. 啟動 Ollama（如果配置使用）
if [ "$LLM_PROVIDER" == "ollama" ]; then
    echo -e "\n${BLUE}4. 啟動 Ollama 服務${NC}"
    
    if command -v ollama &> /dev/null; then
        # 檢查 Ollama 是否已在運行
        if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            start_service "ollama" "ollama serve"
            
            # 等待 Ollama 啟動
            echo "等待 Ollama 服務就緒..."
            for i in {1..30}; do
                if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
                    echo -e "${GREEN}✓ Ollama 服務已就緒${NC}"
                    break
                fi
                sleep 1
            done
            
            # 檢查模型
            if ! ollama list | grep -q "$OLLAMA_MODEL"; then
                echo -e "${YELLOW}下載 $OLLAMA_MODEL 模型...${NC}"
                ollama pull "$OLLAMA_MODEL"
            fi
        else
            echo -e "${GREEN}✓ Ollama 已在運行${NC}"
        fi
    else
        echo -e "${YELLOW}警告：未安裝 Ollama，請先安裝${NC}"
        echo "安裝命令：curl -fsSL https://ollama.com/install.sh | sh"
    fi
fi

# 5. 啟動 Redis（如果配置使用）
if [ "$VECTOR_DB" == "redis" ]; then
    echo -e "\n${BLUE}5. 啟動 Redis 服務${NC}"
    
    if command -v redis-server &> /dev/null; then
        if ! redis-cli ping >/dev/null 2>&1; then
            start_service "redis" "redis-server"
        else
            echo -e "${GREEN}✓ Redis 已在運行${NC}"
        fi
    else
        echo -e "${YELLOW}警告：未安裝 Redis${NC}"
    fi
fi

# 6. 檢查 PostgreSQL（如果配置使用）
if [ "$DB_TYPE" == "postgresql" ]; then
    echo -e "\n${BLUE}6. 檢查 PostgreSQL${NC}"
    
    if command -v psql &> /dev/null; then
        if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ PostgreSQL 連接正常${NC}"
        else
            echo -e "${YELLOW}警告：無法連接到 PostgreSQL${NC}"
            echo "請確保 PostgreSQL 服務正在運行"
        fi
    fi
fi

# 7. 安裝/檢查 Python 依賴
echo -e "\n${BLUE}7. 檢查 Python 依賴${NC}"
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    # 檢查關鍵套件
    if ! python3 -c "import fastapi" 2>/dev/null; then
        echo -e "${YELLOW}安裝 Python 依賴...${NC}"
        pip3 install -r "$PROJECT_ROOT/requirements.txt"
    else
        echo -e "${GREEN}✓ Python 依賴已安裝${NC}"
    fi
fi

# 8. 啟動 API 服務
echo -e "\n${BLUE}8. 啟動 FastAPI 應用${NC}"
cd "$PROJECT_ROOT"
start_service "api_server" "python3 api_server.py"

# 9. 顯示狀態
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✅ RAG System 啟動完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo
echo -e "📊 服務狀態："
echo -e "  ${BLUE}Web UI${NC}: http://localhost:7777"
echo -e "  ${BLUE}API Docs${NC}: http://localhost:7777/docs"

if [ "$LLM_PROVIDER" == "ollama" ]; then
    echo -e "  ${BLUE}Ollama API${NC}: http://localhost:11434"
fi

if [ "$VECTOR_DB" == "redis" ]; then
    echo -e "  ${BLUE}Redis${NC}: localhost:6379"
fi

echo
echo -e "📁 日誌位置："
echo -e "  API Server: $LOG_DIR/api_server.log"
if [ -f "$PID_DIR/ollama.pid" ]; then
    echo -e "  Ollama: $LOG_DIR/ollama.log"
fi

echo
echo -e "💡 提示："
echo -e "  - 查看日誌: tail -f $LOG_DIR/*.log"
echo -e "  - 停止服務: ./stop-app.sh"
echo -e "  - 查看狀態: ps aux | grep -E 'api_server|ollama'"

# 10. 健康檢查（可選）
echo -e "\n${BLUE}執行健康檢查...${NC}"
sleep 3

if curl -s http://localhost:7777 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ API Server 回應正常${NC}"
else
    echo -e "${RED}✗ API Server 無回應，請查看日誌${NC}"
fi

echo -e "\n${GREEN}🎉 系統已就緒！${NC}"