#!/bin/bash

# ==============================================
# RAG 系統 Docker 一鍵啟動腳本
# ==============================================

set -e  # 遇到錯誤即停止

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函數：印出彩色訊息
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函數：檢查 Docker 是否安裝
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝！請先安裝 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安裝！請先安裝 Docker Compose"
        exit 1
    fi
    
    log_success "Docker 和 Docker Compose 已安裝"
}

# 函數：檢查環境變數檔案
check_env() {
    if [ ! -f .env ]; then
        log_warning ".env 檔案不存在，從範例創建..."
        if [ -f .env.docker ]; then
            cp .env.docker .env
            log_success "已從 .env.docker 創建 .env"
        elif [ -f .env.example ]; then
            cp .env.example .env
            log_success "已從 .env.example 創建 .env"
        else
            log_error "找不到環境變數範例檔案！"
            exit 1
        fi
    else
        log_success ".env 檔案已存在"
    fi
}

# 函數：檢查端口是否被占用
check_ports() {
    local ports=("8501" "11434" "5432" "6379")
    local port_names=("Streamlit" "Ollama" "PostgreSQL" "Redis")
    local has_conflict=false
    
    log_info "檢查端口可用性..."
    
    for i in "${!ports[@]}"; do
        if lsof -Pi :${ports[$i]} -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_error "端口 ${ports[$i]} (${port_names[$i]}) 已被占用！"
            has_conflict=true
        fi
    done
    
    if [ "$has_conflict" = true ]; then
        log_error "請先釋放被占用的端口或修改 docker-compose.yml"
        exit 1
    fi
    
    log_success "所有端口都可用"
}

# 函數：啟動服務
start_services() {
    log_info "啟動 Docker 服務..."
    
    # 如果是首次運行，構建映像
    if [[ "$(docker images -q rag-app:latest 2> /dev/null)" == "" ]]; then
        log_info "首次運行，構建 Docker 映像（這可能需要幾分鐘）..."
        docker-compose build --no-cache
    fi
    
    # 啟動所有服務
    docker-compose up -d
    
    log_info "等待服務啟動..."
    sleep 10
    
    # 檢查服務狀態
    local services=("rag-app" "rag-ollama" "rag-postgres" "rag-redis")
    local all_healthy=true
    
    for service in "${services[@]}"; do
        if docker ps --filter "name=$service" --filter "status=running" | grep -q $service; then
            log_success "$service 運行中"
        else
            log_error "$service 啟動失敗"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = false ]; then
        log_error "部分服務啟動失敗，請檢查日誌："
        echo "docker-compose logs"
        exit 1
    fi
}

# 函數：下載 Ollama 模型
setup_ollama() {
    log_info "檢查 Ollama 模型..."
    
    # 檢查是否已有模型
    if docker-compose exec -T ollama ollama list 2>/dev/null | grep -q "llama3"; then
        log_success "llama3 模型已存在"
    else
        log_info "下載 llama3 模型（約 4.7GB，請耐心等待）..."
        docker-compose exec -T ollama ollama pull llama3
        log_success "模型下載完成"
    fi
}

# 函數：顯示服務資訊
show_info() {
    echo ""
    echo "======================================"
    echo -e "${GREEN}✅ RAG 系統已成功啟動！${NC}"
    echo "======================================"
    echo ""
    echo "🌐 服務訪問地址："
    echo "   - Web UI: http://localhost:8501"
    echo "   - Ollama API: http://localhost:11434"
    echo ""
    echo "📊 服務狀態："
    docker-compose ps
    echo ""
    echo "🔧 常用命令："
    echo "   - 查看日誌: docker-compose logs -f [service]"
    echo "   - 停止服務: docker-compose stop"
    echo "   - 重啟服務: docker-compose restart"
    echo "   - 進入容器: docker-compose exec app bash"
    echo ""
}

# 主流程
main() {
    echo "======================================"
    echo "🚀 RAG 系統 Docker 啟動腳本"
    echo "======================================"
    echo ""
    
    # 執行檢查
    check_docker
    check_env
    check_ports
    
    # 啟動服務
    start_services
    
    # 設置 Ollama
    setup_ollama
    
    # 顯示資訊
    show_info
}

# 執行主流程
main