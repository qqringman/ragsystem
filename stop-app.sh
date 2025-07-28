#!/bin/bash

# RAG System 停止腳本
# 用於停止所有相關服務

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

# 檢查作業系統
OS_TYPE="$(uname -s)"
case "$OS_TYPE" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS_TYPE}"
esac

# 載入環境變數
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# 函數：停止服務
stop_service() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${BLUE}停止 $name (PID: $pid)...${NC}"
            
            # 先嘗試優雅停止
            kill -TERM $pid 2>/dev/null
            
            # 等待進程結束
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
            done
            
            # 如果還在運行，強制停止
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}強制停止 $name...${NC}"
                kill -KILL $pid 2>/dev/null
                sleep 1
            fi
            
            # 檢查是否成功停止
            if ! ps -p $pid > /dev/null 2>&1; then
                echo -e "${GREEN}✓ $name 已停止${NC}"
                rm -f "$pid_file"
                return 0
            else
                echo -e "${RED}✗ 無法停止 $name${NC}"
                return 1
            fi
        else
            echo -e "${YELLOW}$name 未在運行（PID 檔案存在但進程不存在）${NC}"
            rm -f "$pid_file"
        fi
    else
        echo -e "${YELLOW}$name 未在運行（無 PID 檔案）${NC}"
    fi
}

# 函數：透過進程名稱停止服務
stop_by_name() {
    local process_name=$1
    local service_name=$2
    
    # 使用跨平台的方式查找進程
    local pids=""
    if [ "$MACHINE" = "Mac" ]; then
        pids=$(pgrep -f "$process_name" 2>/dev/null || ps aux | grep "$process_name" | grep -v grep | awk '{print $2}')
    else
        pids=$(pgrep -f "$process_name" 2>/dev/null)
    fi
    
    if [ -n "$pids" ]; then
        echo -e "${BLUE}發現 $service_name 進程，停止中...${NC}"
        for pid in $pids; do
            kill -TERM $pid 2>/dev/null
        done
        sleep 2
        
        # 檢查是否還有進程
        if [ "$MACHINE" = "Mac" ]; then
            remaining=$(pgrep -f "$process_name" 2>/dev/null || ps aux | grep "$process_name" | grep -v grep | awk '{print $2}')
        else
            remaining=$(pgrep -f "$process_name" 2>/dev/null)
        fi
        
        if [ -n "$remaining" ]; then
            echo -e "${YELLOW}強制停止剩餘的 $service_name 進程...${NC}"
            for pid in $remaining; do
                kill -KILL $pid 2>/dev/null
            done
        fi
        echo -e "${GREEN}✓ $service_name 進程已清理${NC}"
    fi
}

# 函數：檢查並清理端口
cleanup_port() {
    local port=$1
    local service_name=$2
    
    # 檢查是否有 lsof 命令
    if command -v lsof &> /dev/null; then
        local pid=$(lsof -t -i:$port 2>/dev/null | head -1)
        if [ -n "$pid" ]; then
            echo -e "${YELLOW}清理占用端口 $port 的進程 (PID: $pid)${NC}"
            kill -TERM $pid 2>/dev/null
            sleep 1
            # 如果還在運行，強制終止
            if lsof -t -i:$port >/dev/null 2>&1; then
                kill -KILL $pid 2>/dev/null || true
            fi
        fi
    elif command -v netstat &> /dev/null; then
        # 使用 netstat 作為備選方案（主要用於 Linux）
        if [ "$MACHINE" = "Linux" ]; then
            local pid=$(netstat -tulnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
            if [ -n "$pid" ]; then
                echo -e "${YELLOW}清理占用端口 $port 的進程 (PID: $pid)${NC}"
                kill -TERM $pid 2>/dev/null
                sleep 1
                kill -KILL $pid 2>/dev/null || true
            fi
        fi
    fi
}

# 主程式開始
echo -e "${RED}🛑 停止 RAG System${NC}"
echo "================================"

# 1. 停止 API Server
echo -e "\n${BLUE}1. 停止 API Server${NC}"
stop_service "api_server"
stop_by_name "api_server.py" "API Server"

# 2. 停止 Ollama（如果有）
if [ "$LLM_PROVIDER" == "ollama" ] || [ -f "$PID_DIR/ollama.pid" ]; then
    echo -e "\n${BLUE}2. 停止 Ollama${NC}"
    stop_service "ollama"
    
    # 嘗試使用 systemctl（如果是系統服務）
    if command -v systemctl &> /dev/null && systemctl is-active --quiet ollama 2>/dev/null; then
        echo "停止 Ollama systemd 服務..."
        sudo systemctl stop ollama
    fi
    
    # 清理可能的殘留進程
    stop_by_name "ollama serve" "Ollama"
fi

# 3. 停止 Redis（如果有）
if [ "$VECTOR_DB" == "redis" ] || [ -f "$PID_DIR/redis.pid" ]; then
    echo -e "\n${BLUE}3. 停止 Redis${NC}"
    stop_service "redis"
    
    # 也嘗試停止系統 Redis
    if command -v redis-cli &> /dev/null; then
        redis-cli shutdown 2>/dev/null || true
    fi
fi

# 4. 清理殘留進程
echo -e "\n${BLUE}4. 清理殘留進程${NC}"

# 檢查特定端口
for port in 7777 11434; do
    cleanup_port $port "Port $port"
done

# 5. 清理 PID 檔案
echo -e "\n${BLUE}5. 清理 PID 檔案${NC}"
if [ -d "$PID_DIR" ]; then
    local pid_count=$(find "$PID_DIR" -name "*.pid" 2>/dev/null | wc -l)
    if [ $pid_count -gt 0 ]; then
        echo "清理 $pid_count 個 PID 檔案..."
        rm -f "$PID_DIR"/*.pid
    fi
fi

# 6. 顯示最終狀態
echo -e "\n${BLUE}6. 檢查最終狀態${NC}"

# 檢查是否還有相關進程
PROCESSES=("api_server" "ollama" "redis-server")
FOUND_PROCESSES=false

for proc in "${PROCESSES[@]}"; do
    # 跨平台進程檢查
    if [ "$MACHINE" = "Mac" ]; then
        if pgrep -f "$proc" >/dev/null 2>&1 || ps aux | grep "$proc" | grep -v grep >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠ 發現 $proc 進程仍在運行${NC}"
            ps aux | grep "$proc" | grep -v grep
            FOUND_PROCESSES=true
        fi
    else
        if pgrep -f "$proc" >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠ 發現 $proc 進程仍在運行${NC}"
            pgrep -f "$proc" -a
            FOUND_PROCESSES=true
        fi
    fi
done

if [ "$FOUND_PROCESSES" = false ]; then
    echo -e "${GREEN}✓ 所有服務已成功停止${NC}"
fi

# 檢查端口
echo -e "\n檢查端口狀態："
for port in 7777 11434 6379; do
    port_in_use=false
    
    # 跨平台端口檢查
    if command -v lsof &> /dev/null; then
        if lsof -i:$port >/dev/null 2>&1; then
            port_in_use=true
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            port_in_use=true
        fi
    fi
    
    if [ "$port_in_use" = true ]; then
        echo -e "${YELLOW}⚠ 端口 $port 仍被占用${NC}"
    else
        echo -e "${GREEN}✓ 端口 $port 已釋放${NC}"
    fi
done

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✅ RAG System 停止完成！${NC}"
echo -e "${GREEN}================================${NC}"

# 選項：是否清理日誌
echo
read -p "是否清理日誌檔案？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "$LOG_DIR" ]; then
        echo -e "${BLUE}清理日誌檔案...${NC}"
        rm -f "$LOG_DIR"/*.log
        echo -e "${GREEN}✓ 日誌已清理${NC}"
    fi
fi

echo -e "\n${BLUE}提示：${NC}"
echo "  - 重新啟動: ./start-app.sh"
echo "  - 查看是否有殘留進程: ps aux | grep -E 'api_server|ollama|redis'"

# 刪除狀態檔案
if [ -f "$STATE_FILE" ]; then
    rm -f "$STATE_FILE"
fi