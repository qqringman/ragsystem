#!/bin/bash

# RAG System 互動式管理控制台
# 統一管理本地執行和 Docker 執行模式

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# 特殊字符
CHECK_MARK="✓"
CROSS_MARK="✗"
ARROW="➜"
DOT="•"

# 設定變數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
PID_DIR="$PROJECT_ROOT/.pids"
LOG_DIR="$PROJECT_ROOT/logs"
STATE_FILE="$PROJECT_ROOT/.rag-system-state"

# 創建必要目錄
mkdir -p "$PID_DIR" "$LOG_DIR"

# 檢查作業系統
OS_TYPE="$(uname -s)"
case "$OS_TYPE" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS_TYPE}"
esac

# 清除螢幕並顯示標題
show_header() {
    clear
    echo
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}            RAG System 管理控制台 v1.0                  ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo
}

# 顯示系統狀態
show_system_status() {
    local native_running=false
    local docker_running=false
    local current_mode="none"
    
    # 檢查本地服務
    if pgrep -f "streamlit run" >/dev/null 2>&1 || [ -f "$PID_DIR/streamlit.pid" ]; then
        native_running=true
        current_mode="native"
    fi
    
    # 檢查 Docker 服務
    if docker ps 2>/dev/null | grep -q "rag-app"; then
        docker_running=true
        current_mode="docker"
    fi
    
    # 如果兩者都在運行
    if $native_running && $docker_running; then
        current_mode="both"
    fi
    
    # 顯示狀態卡片
    echo -e "${BLUE}┌─ 系統狀態 ─────────────────────────────────────────┐${NC}"
    
    case $current_mode in
        "native")
            echo -e "${BLUE}│${NC} ${GREEN}● 運行模式：本地執行${NC}                              ${BLUE}│${NC}"
            ;;
        "docker")
            echo -e "${BLUE}│${NC} ${BLUE}● 運行模式：Docker 容器${NC}                           ${BLUE}│${NC}"
            ;;
        "both")
            echo -e "${BLUE}│${NC} ${YELLOW}● 警告：本地和 Docker 同時運行！${NC}                   ${BLUE}│${NC}"
            ;;
        "none")
            echo -e "${BLUE}│${NC} ${GRAY}○ 系統未運行${NC}                                      ${BLUE}│${NC}"
            ;;
    esac
    
    echo -e "${BLUE}└────────────────────────────────────────────────────┘${NC}"
    
    # 顯示服務狀態
    echo
    echo -e "${WHITE}服務狀態：${NC}"
    
    # 本地服務
    echo -e "  ${GRAY}本地服務：${NC}"
    check_service "streamlit" "Streamlit" "  "
    check_service "ollama" "Ollama" "  "
    check_service "redis-server" "Redis" "  "
    
    # Docker 服務
    if command -v docker &>/dev/null; then
        echo -e "  ${GRAY}Docker 服務：${NC}"
        check_docker_service "rag-app" "RAG App" "  "
        check_docker_service "rag-ollama" "Ollama" "  "
        check_docker_service "rag-postgres" "PostgreSQL" "  "
        check_docker_service "rag-redis" "Redis" "  "
    fi
    
    # 端口狀態
    echo
    echo -e "${WHITE}端口使用情況：${NC}"
    check_port 8501 "Streamlit"
    check_port 11434 "Ollama"
    check_port 5432 "PostgreSQL"
    check_port 6379 "Redis"
    
    return $([ "$current_mode" == "none" ] && echo 1 || echo 0)
}

# 檢查服務
check_service() {
    local service=$1
    local name=$2
    local indent=$3
    
    if pgrep -f "$service" >/dev/null 2>&1; then
        echo -e "$indent  ${GREEN}$CHECK_MARK${NC} $name"
    else
        echo -e "$indent  ${GRAY}$CROSS_MARK${NC} $name"
    fi
}

# 檢查 Docker 服務
check_docker_service() {
    local container=$1
    local name=$2
    local indent=$3
    
    if docker ps 2>/dev/null | grep -q "$container"; then
        echo -e "$indent  ${GREEN}$CHECK_MARK${NC} $name"
    else
        echo -e "$indent  ${GRAY}$CROSS_MARK${NC} $name"
    fi
}

# 檢查端口（修正版）
check_port() {
    local port=$1
    local name=$2
    
    # 使用不同方式檢查端口，根據作業系統
    if [ "$MACHINE" = "Mac" ]; then
        if lsof -i:$port >/dev/null 2>&1; then
            local pid=$(lsof -t -i:$port | head -1)
            local process=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
            echo -e "  ${YELLOW}●${NC} $port ($name) - $process"
        else
            echo -e "  ${GREEN}○${NC} $port ($name) - 可用"
        fi
    else
        # Linux
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            echo -e "  ${YELLOW}●${NC} $port ($name) - 使用中"
        else
            echo -e "  ${GREEN}○${NC} $port ($name) - 可用"
        fi
    fi
}

# 顯示主選單
show_main_menu() {
    echo
    echo -e "${CYAN}┌─ 主選單 ───────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC}                                                    ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}1)${NC} 🚀 啟動系統                                    ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}2)${NC} 🛑 停止系統                                    ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}3)${NC} 🔄 重啟系統                                    ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}4)${NC} 📊 詳細狀態                                    ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}5)${NC} 📜 查看日誌                                    ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}6)${NC} ⚙️  系統設定                                    ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}7)${NC} 🔥 熱更新程式碼                                ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}0)${NC} 🚪 退出                                        ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}                                                    ${CYAN}│${NC}"
    echo -e "${CYAN}└────────────────────────────────────────────────────┘${NC}"
    echo
}

# 啟動系統選單
start_system_menu() {
    echo
    echo -e "${GREEN}請選擇啟動模式：${NC}"
    echo
    echo -e "  ${WHITE}1)${NC} 💻 本地執行模式"
    echo -e "     ${GRAY}直接在本機運行，適合開發測試${NC}"
    echo
    echo -e "  ${WHITE}2)${NC} 🐳 Docker 模式"
    echo -e "     ${GRAY}容器化運行，環境隔離，適合生產部署${NC}"
    echo
    echo -e "  ${WHITE}0)${NC} ↩️  返回主選單"
    echo
    
    read -p "$(echo -e ${WHITE}請選擇 [0-2]: ${NC})" choice
    
    case $choice in
        1)
            start_native_mode
            ;;
        2)
            start_docker_mode
            ;;
        0)
            return
            ;;
        *)
            echo -e "\n${RED}無效選項！${NC}"
            sleep 1
            ;;
    esac
}

# 啟動本地模式
start_native_mode() {
    echo
    echo -e "${GREEN}準備啟動本地執行模式...${NC}"
    
    # 檢查是否有衝突
    if check_conflicts "native"; then
        return
    fi
    
    # 確認啟動
    echo
    echo -e "${YELLOW}即將啟動以下服務：${NC}"
    echo -e "  $DOT Streamlit (端口 8501)"
    echo -e "  $DOT Ollama (端口 11434) - 如果配置使用"
    echo -e "  $DOT Redis (端口 6379) - 如果配置使用"
    echo
    read -p "$(echo -e ${WHITE}確定啟動嗎？[Y/n]: ${NC})" -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo
        echo -e "${BLUE}正在啟動本地服務...${NC}"
        if [ -x "$PROJECT_ROOT/start-app.sh" ]; then
            "$PROJECT_ROOT/start-app.sh"
            echo "native" > "$STATE_FILE"
            echo
            echo -e "${GREEN}✅ 本地模式啟動完成！${NC}"
            echo -e "${WHITE}訪問地址：${CYAN}http://localhost:8501${NC}"
        else
            echo -e "${RED}錯誤：找不到 start-app.sh${NC}"
        fi
    fi
    
    echo
    read -p "按 Enter 鍵返回..."
}

# 啟動 Docker 模式
start_docker_mode() {
    echo
    echo -e "${BLUE}準備啟動 Docker 模式...${NC}"
    
    # 檢查 Docker
    if ! command -v docker &>/dev/null; then
        echo -e "${RED}錯誤：未安裝 Docker！${NC}"
        echo "請先安裝 Docker Desktop"
        read -p "按 Enter 鍵返回..."
        return
    fi
    
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}錯誤：Docker 服務未運行！${NC}"
        echo "請先啟動 Docker Desktop"
        read -p "按 Enter 鍵返回..."
        return
    fi
    
    # 檢查是否有衝突
    if check_conflicts "docker"; then
        return
    fi
    
    # 確認啟動
    echo
    echo -e "${YELLOW}即將啟動以下容器：${NC}"
    echo -e "  $DOT rag-app (Streamlit 應用)"
    echo -e "  $DOT rag-ollama (LLM 服務)"
    echo -e "  $DOT rag-postgres (資料庫)"
    echo -e "  $DOT rag-redis (快取)"
    echo
    read -p "$(echo -e ${WHITE}確定啟動嗎？[Y/n]: ${NC})" -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo
        echo -e "${BLUE}正在啟動 Docker 容器...${NC}"
        if [ -x "$PROJECT_ROOT/start-docker.sh" ]; then
            "$PROJECT_ROOT/start-docker.sh"
            echo "docker" > "$STATE_FILE"
            echo
            echo -e "${GREEN}✅ Docker 模式啟動完成！${NC}"
            echo -e "${WHITE}訪問地址：${CYAN}http://localhost:8501${NC}"
        else
            echo -e "${YELLOW}使用 docker-compose 啟動...${NC}"
            docker-compose up -d
            echo "docker" > "$STATE_FILE"
        fi
    fi
    
    echo
    read -p "按 Enter 鍵返回..."
}

# 檢查衝突
check_conflicts() {
    local mode=$1
    local has_conflict=false
    
    # 檢查端口占用
    local ports=(8501 11434 5432 6379)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -i:$port >/dev/null 2>&1; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        echo
        echo -e "${YELLOW}⚠️  發現端口被占用：${NC}"
        for port in "${occupied_ports[@]}"; do
            local pid=$(lsof -t -i:$port | head -1)
            local process=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
            echo -e "  ${RED}$CROSS_MARK${NC} 端口 $port - $process (PID: $pid)"
        done
        
        echo
        echo -e "${WHITE}請選擇：${NC}"
        echo -e "  ${WHITE}1)${NC} 停止占用的服務並繼續"
        echo -e "  ${WHITE}2)${NC} 取消啟動"
        echo
        read -p "$(echo -e ${WHITE}請選擇 [1-2]: ${NC})" choice
        
        case $choice in
            1)
                stop_all_services
                sleep 2
                ;;
            2)
                return 0
                ;;
        esac
    fi
    
    return 1
}

# 停止所有服務
stop_all_services() {
    echo
    echo -e "${RED}正在停止所有服務...${NC}"
    
    # 停止本地服務
    if [ -x "$PROJECT_ROOT/stop-app.sh" ]; then
        "$PROJECT_ROOT/stop-app.sh" >/dev/null 2>&1
    fi
    
    # 停止 Docker 服務
    if [ -x "$PROJECT_ROOT/stop-docker.sh" ]; then
        "$PROJECT_ROOT/stop-docker.sh" >/dev/null 2>&1
    else
        docker-compose down >/dev/null 2>&1
    fi
    
    # 強制清理端口
    for port in 8501 11434 5432 6379; do
        local pid=$(lsof -t -i:$port 2>/dev/null)
        if [ -n "$pid" ]; then
            kill -9 $pid 2>/dev/null
        fi
    done
    
    echo -e "${GREEN}✅ 所有服務已停止${NC}"
}

# 查看日誌選單
view_logs_menu() {
    while true; do
        show_header
        echo -e "${CYAN}┌─ 日誌查看 ─────────────────────────────────────────┐${NC}"
        echo -e "${CYAN}│${NC}                                                     ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}  ${WHITE}1)${NC} 📄 Streamlit 日誌                              ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}  ${WHITE}2)${NC} 🤖 Ollama 日誌                                 ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}  ${WHITE}3)${NC} 🐳 Docker 容器日誌                             ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}  ${WHITE}4)${NC} 📋 所有日誌（即時）                            ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}  ${WHITE}0)${NC} ↩️  返回主選單                                  ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}                                                     ${CYAN}│${NC}"
        echo -e "${CYAN}└─────────────────────────────────────────────────────┘${NC}"
        echo
        
        read -p "$(echo -e ${WHITE}請選擇 [0-4]: ${NC})" choice
        
        case $choice in
            1)
                if [ -f "$LOG_DIR/streamlit.log" ]; then
                    echo -e "\n${BLUE}Streamlit 日誌：${NC}"
                    tail -f "$LOG_DIR/streamlit.log"
                else
                    echo -e "\n${YELLOW}找不到 Streamlit 日誌${NC}"
                    sleep 2
                fi
                ;;
            2)
                if [ -f "$LOG_DIR/ollama.log" ]; then
                    echo -e "\n${BLUE}Ollama 日誌：${NC}"
                    tail -f "$LOG_DIR/ollama.log"
                else
                    echo -e "\n${YELLOW}找不到 Ollama 日誌${NC}"
                    sleep 2
                fi
                ;;
            3)
                if command -v docker &>/dev/null; then
                    echo -e "\n${BLUE}Docker 容器日誌：${NC}"
                    docker-compose logs -f --tail=100
                else
                    echo -e "\n${YELLOW}Docker 未安裝${NC}"
                    sleep 2
                fi
                ;;
            4)
                echo -e "\n${BLUE}所有日誌（按 Ctrl+C 退出）：${NC}"
                if [ -d "$LOG_DIR" ] && ls "$LOG_DIR"/*.log >/dev/null 2>&1; then
                    tail -f "$LOG_DIR"/*.log
                else
                    echo -e "${YELLOW}沒有找到日誌檔案${NC}"
                    sleep 2
                fi
                ;;
            0)
                return
                ;;
            *)
                echo -e "\n${RED}無效選項！${NC}"
                sleep 1
                ;;
        esac
    done
}

# 詳細狀態
show_detailed_status() {
    show_header
    echo -e "${WHITE}📊 系統詳細狀態${NC}"
    echo -e "${GRAY}────────────────────────────────────────────────────${NC}"
    
    # 系統資訊
    echo -e "\n${WHITE}系統環境：${NC}"
    echo -e "  ${DOT} Python: $(python3 --version 2>&1 || echo '未安裝')"
    echo -e "  ${DOT} Docker: $(docker --version 2>&1 || echo '未安裝')"
    echo -e "  ${DOT} 作業系統: $(uname -s) $(uname -r)"
    echo -e "  ${DOT} 記憶體: $(free -h 2>/dev/null | grep Mem | awk '{print $2}' || echo 'N/A')"
    
    # 配置資訊
    echo -e "\n${WHITE}當前配置：${NC}"
    if [ -f "$PROJECT_ROOT/.env" ]; then
        echo -e "  ${DOT} LLM Provider: ${GREEN}$(grep LLM_PROVIDER .env | cut -d= -f2)${NC}"
        echo -e "  ${DOT} Vector DB: ${GREEN}$(grep VECTOR_DB .env | cut -d= -f2)${NC}"
        echo -e "  ${DOT} DB Type: ${GREEN}$(grep DB_TYPE .env | cut -d= -f2)${NC}"
    else
        echo -e "  ${YELLOW}⚠️  找不到 .env 檔案${NC}"
    fi
    
    # 進程詳情
    echo -e "\n${WHITE}運行中的進程：${NC}"
    ps aux | grep -E "streamlit|ollama|redis|postgres" | grep -v grep | while read line; do
        echo -e "  ${GRAY}$line${NC}"
    done || echo -e "  ${GRAY}無相關進程${NC}"
    
    # 容器狀態
    if command -v docker &>/dev/null && docker info >/dev/null 2>&1; then
        echo -e "\n${WHITE}Docker 容器狀態：${NC}"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "rag-|NAMES" || echo -e "  ${GRAY}無運行中的容器${NC}"
    fi
    
    echo
    read -p "按 Enter 鍵返回..."
}

# 系統設定選單
system_settings_menu() {
    while true; do
        show_header
        echo -e "${CYAN}┌─ 系統設定 ─────────────────────────────────────────┐${NC}"
        echo -e "${CYAN}│${NC}                                                     ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}  ${WHITE}1)${NC} 🔧 編輯環境變數 (.env)                         ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}  ${WHITE}2)${NC} 🧹 清理日誌檔案                                ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}  ${WHITE}3)${NC} 🗑️  清理向量資料庫                              ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}  ${WHITE}4)${NC} 🔄 重建 Docker 映像                             ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}  ${WHITE}5)${NC} 📦 更新 Python 套件                             ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}  ${WHITE}0)${NC} ↩️  返回主選單                                  ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}                                                     ${CYAN}│${NC}"
        echo -e "${CYAN}└─────────────────────────────────────────────────────┘${NC}"
        echo
        
        read -p "$(echo -e ${WHITE}請選擇 [0-5]: ${NC})" choice
        
        case $choice in
            1)
                if [ -f "$PROJECT_ROOT/.env" ]; then
                    ${EDITOR:-nano} "$PROJECT_ROOT/.env"
                else
                    echo -e "\n${YELLOW}找不到 .env 檔案${NC}"
                    echo "是否從範例創建？"
                    read -p "[Y/n]: " -n 1 -r
                    echo
                    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env" 2>/dev/null
                        ${EDITOR:-nano} "$PROJECT_ROOT/.env"
                    fi
                fi
                ;;
            2)
                echo -e "\n${YELLOW}確定要清理所有日誌檔案嗎？${NC}"
                read -p "[y/N]: " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    rm -f "$LOG_DIR"/*.log
                    echo -e "${GREEN}✅ 日誌已清理${NC}"
                fi
                read -p "按 Enter 鍵返回..."
                ;;
            3)
                echo -e "\n${YELLOW}確定要清理向量資料庫嗎？這將刪除所有索引資料！${NC}"
                read -p "[y/N]: " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    rm -rf "$PROJECT_ROOT/vector_db/chroma"/*
                    echo -e "${GREEN}✅ 向量資料庫已清理${NC}"
                fi
                read -p "按 Enter 鍵返回..."
                ;;
            4)
                if command -v docker &>/dev/null; then
                    echo -e "\n${BLUE}重建 Docker 映像...${NC}"
                    docker-compose build --no-cache
                    echo -e "${GREEN}✅ Docker 映像重建完成${NC}"
                else
                    echo -e "\n${RED}Docker 未安裝${NC}"
                fi
                read -p "按 Enter 鍵返回..."
                ;;
            5)
                echo -e "\n${BLUE}更新 Python 套件...${NC}"
                pip install --upgrade -r "$PROJECT_ROOT/requirements.txt"
                echo -e "${GREEN}✅ Python 套件更新完成${NC}"
                read -p "按 Enter 鍵返回..."
                ;;
            0)
                return
                ;;
            *)
                echo -e "\n${RED}無效選項！${NC}"
                sleep 1
                ;;
        esac
    done
}

# 熱更新程式碼
hot_reload_code() {
    show_header
    echo -e "${CYAN}┌─ 熱更新程式碼 ─────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC}                                                     ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}說明：${NC}                                           ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  Docker 模式下會自動檢測檔案變更並重載            ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  本地模式下 Streamlit 會自動偵測變更              ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}                                                     ${CYAN}│${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────────────────┘${NC}"
    echo
    
    # 檢查運行模式
    local mode=$(cat "$STATE_FILE" 2>/dev/null || echo "none")
    
    if [ "$mode" == "none" ]; then
        echo -e "${YELLOW}系統未運行，無需更新${NC}"
        read -p "按 Enter 鍵返回..."
        return
    fi
    
    if [ "$mode" == "docker" ]; then
        echo -e "${BLUE}Docker 模式熱更新選項：${NC}"
        echo
        echo -e "  ${WHITE}1)${NC} 🔄 重新載入應用（保持容器運行）"
        echo -e "  ${WHITE}2)${NC} 📦 更新 Python 套件（requirements.txt）"
        echo -e "  ${WHITE}3)${NC} 🐳 重建映像（完整更新）"
        echo -e "  ${WHITE}0)${NC} ↩️  返回"
        echo
        
        read -p "$(echo -e ${WHITE}請選擇 [0-3]: ${NC})" choice
        
        case $choice in
            1)
                echo -e "\n${BLUE}重新載入應用...${NC}"
                # 觸發 Streamlit 重載
                docker-compose exec app touch /app/app.py
                echo -e "${GREEN}✅ 應用已重新載入${NC}"
                echo -e "${GRAY}提示：Streamlit 會自動偵測檔案變更${NC}"
                ;;
            2)
                echo -e "\n${BLUE}更新 Python 套件...${NC}"
                docker-compose exec app pip install -r requirements.txt
                echo -e "${GREEN}✅ 套件更新完成${NC}"
                echo -e "${YELLOW}建議重啟應用以確保生效${NC}"
                ;;
            3)
                echo -e "\n${YELLOW}這將重建整個映像，需要一些時間${NC}"
                read -p "確定要繼續嗎？[y/N]: " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    echo -e "${BLUE}重建 Docker 映像...${NC}"
                    docker-compose build --no-cache app
                    echo -e "${GREEN}✅ 映像重建完成${NC}"
                    echo -e "${YELLOW}請重啟系統以使用新映像${NC}"
                fi
                ;;
            0)
                return
                ;;
        esac
    else
        # 本地模式
        echo -e "${GREEN}本地模式說明：${NC}"
        echo
        echo "Streamlit 已啟用檔案監視功能，會自動偵測以下變更："
        echo "  • Python 檔案（.py）修改"
        echo "  • 配置檔案（.env）修改"
        echo
        echo -e "${YELLOW}如果需要更新 Python 套件：${NC}"
        echo "  1. 停止系統"
        echo "  2. pip install -r requirements.txt"
        echo "  3. 重新啟動系統"
    fi
    
    echo
    read -p "按 Enter 鍵返回..."
}

# 主循環
main_loop() {
    while true; do
        show_header
        show_system_status
        show_main_menu
        
        read -p "$(echo -e ${WHITE}請選擇操作 [0-7]: ${NC})" choice
        
        case $choice in
            1)
                start_system_menu
                ;;
            2)
                echo
                echo -e "${RED}確定要停止所有服務嗎？${NC}"
                read -p "[Y/n]: " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                    stop_all_services
                    rm -f "$STATE_FILE"
                    read -p "按 Enter 鍵返回..."
                fi
                ;;
            3)
                echo
                local mode=$(cat "$STATE_FILE" 2>/dev/null || echo "none")
                if [ "$mode" == "none" ]; then
                    echo -e "${YELLOW}系統未運行，無法重啟${NC}"
                else
                    echo -e "${BLUE}正在重啟系統...${NC}"
                    stop_all_services
                    sleep 2
                    if [ "$mode" == "docker" ]; then
                        start_docker_mode
                    else
                        start_native_mode
                    fi
                fi
                ;;
            4)
                show_detailed_status
                ;;
            5)
                view_logs_menu
                ;;
            6)
                system_settings_menu
                ;;
            7)
                hot_reload_code
                ;;
            0)
                echo
                echo -e "${GREEN}感謝使用 RAG System！${NC}"
                echo -e "${WHITE}再見！${NC}"
                echo
                exit 0
                ;;
            *)
                echo -e "\n${RED}無效選項，請重新選擇！${NC}"
                sleep 1
                ;;
        esac
    done
}

# 主程式
main() {
    # 檢查必要腳本
    local required_scripts=("start-app.sh" "stop-app.sh")
    local missing=false
    
    for script in "${required_scripts[@]}"; do
        if [ ! -f "$PROJECT_ROOT/$script" ]; then
            echo -e "${RED}錯誤：找不到必要腳本 $script${NC}"
            missing=true
        fi
    done
    
    if $missing; then
        echo -e "${YELLOW}請確保所有必要腳本都在專案目錄中${NC}"
        exit 1
    fi
    
    # 開始主循環
    main_loop
}

# 啟動程式
main