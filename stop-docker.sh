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
    docker-compose stop
    log_success "服務已停止"
}

# 移除容器
remove_containers() {
    log_info "停止並移除容器..."
    docker-compose down
    log_success "容器已移除（資料卷保留）"
}

# 完全清理
clean_all() {
    log_warning "即將移除所有容器和資料！"
    echo -n "確定要繼續嗎？(yes/no): "
    read confirm
    
    if [ "$confirm" = "yes" ]; then
        log_info "移除所有容器和資料卷..."
        docker-compose down -v
        
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
    docker-compose ps
}

# 執行主流程
main