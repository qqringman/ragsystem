# 使用多階段構建優化映像大小
FROM python:3.12-slim as builder

# 安裝構建依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt
COPY requirements.txt .

# 安裝 Python 套件到特定目錄
RUN pip install --no-cache-dir --target=/app/deps -r requirements.txt

# 最終階段
FROM python:3.12-slim

# 安裝運行時依賴
RUN apt-get update && apt-get install -y \
    # PDF 處理
    poppler-utils \
    # OCR 支援
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    tesseract-ocr-chi-sim \
    # 文件類型檢測
    libmagic1 \
    # 健康檢查
    curl \
    # 清理
    && rm -rf /var/lib/apt/lists/*

# 創建非 root 用戶
RUN useradd -m -u 1000 raguser

# 設定工作目錄
WORKDIR /app

# 複製 Python 依賴
COPY --from=builder /app/deps /usr/local/lib/python3.12/site-packages

# 複製應用程式碼
COPY --chown=raguser:raguser . .

# 創建必要的目錄
RUN mkdir -p /app/vector_db /app/uploads /app/logs && \
    chown -R raguser:raguser /app

# 切換到非 root 用戶
USER raguser

# 設定環境變數
ENV PYTHONPATH=/app:/usr/local/lib/python3.12/site-packages
ENV PYTHONUNBUFFERED=1

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 暴露端口
EXPOSE 8501

# 啟動命令
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.serverAddress=0.0.0.0"]