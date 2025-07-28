#!/bin/bash

# ==============================================
# RAG 系統 Docker 停止腳本
# ==============================================

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 檢查 Docker 是否安裝
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker 服務未運行"
        exit 1
    fi
}

# 顯示選項
show_options() {
    echo "======================================"
    echo "🛑 RAG 系統 Docker 停止腳本"
    echo "======================================"
    echo ""
    echo "請選擇停止方式："
    echo "1) 停止服務（保留容器和資料）"
    echo "2) 移除容器（保留資料卷）"
    echo "3) 完全清理（移除容器和資料）⚠️"
    echo "4) 取消"
    echo ""
}

# 停止服務
stop_services() {
    log_info "停止所有服務..."
    
    # 檢查 docker-compose 命令
    if command -v docker-compose &> /dev/null; then
        docker-compose stop
    else
        docker compose stop
    fi
    
    log_success "服務已停止"
}

# 移除容器
remove_containers() {
    log_info "停止並移除容器..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
    
    log_success "容器已移除（資料卷保留）"
}

# 完全清理
clean_all() {
    log_warning "即將移除所有容器和資料！"
    echo -n "請輸入 'yes' 確認: "
    read confirm
    
    if [ "$confirm" = "yes" ]; then
        log_info "移除所有容器和資料卷..."
        
        if command -v docker-compose &> /dev/null; then
            docker-compose down -v
        else
            docker compose down -v
        fi
        
        # 清理本地資料目錄
        if [ -d "vector_db" ]; then
            rm -rf vector_db/*
            log_info "已清理 vector_db 目錄"
        fi
        
        if [ -d "uploads" ]; then
            rm -rf uploads/*
            log_info "已清理 uploads 目錄"
        fi
        
        log_success "完全清理完成"
    else
        log_info "操作已取消"
    fi
}

# 主流程
main() {
    # 檢查 Docker
    check_docker
    
    show_options
    
    echo -n "請輸入選項 (1-4): "
    read choice
    
    case $choice in
        1)
            stop_services
            ;;
        2)
            remove_containers
            ;;
        3)
            clean_all
            ;;
        4)
            log_info "操作已取消"
            ;;
        *)
            log_error "無效的選項"
            exit 1
            ;;
    esac
    
    echo ""
    log_info "目前 Docker 容器狀態："
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
}

# 執行主流程
main