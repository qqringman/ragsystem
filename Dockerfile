FROM python:3.12

# 使用完整版 Python 映像，已包含大部分構建工具

# 安裝額外依賴
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    tesseract-ocr-chi-sim \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 複製並清理 requirements
COPY requirements.txt .

# 安裝 Python 套件
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製應用
COPY . .

# 創建目錄
RUN mkdir -p /app/vector_db /app/uploads /app/logs

ENV PYTHONUNBUFFERED=1

EXPOSE 8501

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.serverAddress=0.0.0.0"]