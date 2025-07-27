
# 🧠 RAG Ultimate All-in-One

此專案為多格式、多來源、多模型支援的 RAG (Retrieval-Augmented Generation) 系統。

## ✅ 功能
- 文件支援：PDF, Word (.docx), Excel (.xlsx), Markdown, JSON, HTML
- 資料庫支援：PostgreSQL / MySQL，支援自然語言查詢
- 多模型支援：OpenAI / Qwen / Anthropic / Ollama
- 多向量庫支援：Chroma / Redis / Qdrant
- 前端介面：Streamlit Web UI
- Docker 部署支援
- 自然語言轉 SQL 查詢
- 段落來源顯示與高亮

## 🚀 快速開始

1. 安裝相依套件
```bash
pip install -r requirements.txt
cp .env.example .env
```

2. 執行查詢（CLI）
```bash
python main.py
```

3. 執行 Web UI
```bash
streamlit run app.py
```

## 🐳 使用 Docker
```bash
docker build -t rag-ui .
docker run -p 8501:8501 --env-file .env rag-ui
```

## 📁 .env 設定說明
請參考 `.env.example` 設定 LLM 與資料庫與向量庫類型

## 🤝 協助與貢獻
如需協助或客製整合，歡迎聯繫作者。
