#!/bin/bash

# Docker 代碼更新腳本
# 用於快速更新 Docker 容器中的代碼，無需重建映像

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔄 Docker RAG 系統代碼更新${NC}"
echo "============================"

# 檢查 Docker 服務
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}錯誤：Docker 服務未運行！${NC}"
    exit 1
fi

# 檢查容器是否運行
if ! docker ps | grep -q "rag-app"; then
    echo -e "${RED}錯誤：RAG 應用容器未運行！${NC}"
    echo "請先執行：docker-compose up -d"
    exit 1
fi

# 顯示選項
echo -e "\n${YELLOW}選擇更新類型：${NC}"
echo "1) 🔥 熱更新 Python 代碼（最快）"
echo "2) 📦 更新 Python 套件"
echo "3) 🐳 重建並更新（完整更新）"
echo "4) 🔄 重啟應用容器"
echo "0) 取消"
echo

read -p "請選擇 [0-4]: " choice

case $choice in
    1)
        echo -e "\n${BLUE}執行熱更新...${NC}"
        
        # 檢查哪些檔案有變更
        echo "檢查變更的檔案..."
        
        # 列出主要 Python 檔案
        FILES=(
            "app.py"
            "rag_chain.py"
            "config/__init__.py"
            "llm/provider_selector.py"
            "loader/doc_parser.py"
            "vectorstore/index_manager.py"
            "db/sql_executor.py"
        )
        
        CHANGED_FILES=()
        for file in "${FILES[@]}"; do
            if [ -f "$file" ]; then
                # 比較檔案（簡單方式）
                if ! docker exec rag-app test -f "/app/$file" || \
                   [ "$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)" -gt "$(docker exec rag-app stat -c %Y "/app/$file" 2>/dev/null || echo 0)" ]; then
                    CHANGED_FILES+=("$file")
                fi
            fi
        done
        
        if [ ${#CHANGED_FILES[@]} -eq 0 ]; then
            echo -e "${GREEN}沒有檢測到檔案變更${NC}"
        else
            echo -e "\n${YELLOW}檢測到以下檔案有變更：${NC}"
            for file in "${CHANGED_FILES[@]}"; do
                echo "  • $file"
            done
            
            echo -e "\n${BLUE}正在更新檔案...${NC}"
            
            # 複製變更的檔案到容器
            for file in "${CHANGED_FILES[@]}"; do
                docker cp "$file" "rag-app:/app/$file"
                echo -e "${GREEN}✓${NC} 更新 $file"
            done
            
            # 觸發 Streamlit 重載
            echo -e "\n${BLUE}觸發應用重載...${NC}"
            docker exec rag-app touch /app/app.py
            
            echo -e "\n${GREEN}✅ 熱更新完成！${NC}"
            echo "應用將在幾秒內自動重載"
        fi
        ;;
        
    2)
        echo -e "\n${BLUE}更新 Python 套件...${NC}"
        
        # 檢查 requirements.txt 是否有變更
        if [ -f "requirements.txt" ]; then
            echo "複製 requirements.txt 到容器..."
            docker cp requirements.txt rag-app:/app/requirements.txt
            
            echo "安裝/更新套件..."
            docker exec -it rag-app pip install -r requirements.txt
            
            echo -e "\n${GREEN}✅ 套件更新完成！${NC}"
            echo -e "${YELLOW}建議重啟應用容器以確保所有變更生效${NC}"
        else
            echo -e "${RED}找不到 requirements.txt${NC}"
        fi
        ;;
        
    3)
        echo -e "\n${YELLOW}完整重建將需要較長時間...${NC}"
        read -p "確定要繼續嗎？[y/N]: " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "\n${BLUE}停止現有容器...${NC}"
            docker-compose stop app
            
            echo -e "\n${BLUE}重建映像...${NC}"
            docker-compose build --no-cache app
            
            echo -e "\n${BLUE}啟動新容器...${NC}"
            docker-compose up -d app
            
            echo -e "\n${GREEN}✅ 完整重建完成！${NC}"
        fi
        ;;
        
    4)
        echo -e "\n${BLUE}重啟應用容器...${NC}"
        docker-compose restart app
        
        echo -e "\n${GREEN}✅ 應用容器已重啟${NC}"
        ;;
        
    0)
        echo "取消操作"
        exit 0
        ;;
        
    *)
        echo -e "${RED}無效的選項${NC}"
        exit 1
        ;;
esac

echo -e "\n${BLUE}檢查應用狀態...${NC}"
sleep 3

# 檢查健康狀態
if curl -s http://localhost:8501/_stcore/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ 應用運行正常${NC}"
    echo -e "\n訪問: ${BLUE}http://localhost:8501${NC}"
else
    echo -e "${YELLOW}⚠️  應用可能還在啟動中，請稍後再試${NC}"
fi

echo -e "\n${GRAY}提示：你可以使用 'docker-compose logs -f app' 查看日誌${NC}"