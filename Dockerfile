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

# 升級 pip 和安裝關鍵套件
RUN pip install --upgrade pip setuptools wheel

# 安裝其他 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用
COPY . .

# 創建目錄
RUN mkdir -p /app/vector_db /app/uploads /app/logs

ENV PYTHONUNBUFFERED=1

EXPOSE 7777

CMD ["python3", "api_server.py"]