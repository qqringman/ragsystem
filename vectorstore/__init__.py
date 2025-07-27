"""
向量資料庫管理模組

支援多種向量資料庫：
- Chroma (預設)
- Redis
- Qdrant

支援的嵌入模型：
- OpenAI Embeddings
- HuggingFace Embeddings
"""

from .index_manager import get_vectorstore, get_embeddings

# 支援的向量資料庫
SUPPORTED_VECTOR_DBS = ["chroma", "redis", "qdrant"]

# 支援的嵌入提供者
SUPPORTED_EMBED_PROVIDERS = ["openai", "huggingface"]

# 預設配置
DEFAULT_VECTOR_DB = "chroma"
DEFAULT_EMBED_PROVIDER = "openai"

# 向量資料庫連接配置
VECTOR_DB_CONFIGS = {
    "chroma": {
        "persist_directory": "vector_db/chroma",
    },
    "redis": {
        "index_name": "rag_index",
        "redis_url": "redis://localhost:6379",
    },
    "qdrant": {
        "collection_name": "rag_data",
        "location": "http://localhost:6333",
    },
}

# 嵌入模型配置
EMBEDDING_CONFIGS = {
    "openai": {
        "model": "text-embedding-ada-002",
    },
    "huggingface": {
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    },
}

# 匯出的公開 API
__all__ = [
    "get_vectorstore",
    "get_embeddings",
    "SUPPORTED_VECTOR_DBS",
    "SUPPORTED_EMBED_PROVIDERS",
    "DEFAULT_VECTOR_DB",
    "DEFAULT_EMBED_PROVIDER",
    "VECTOR_DB_CONFIGS",
    "EMBEDDING_CONFIGS",
]