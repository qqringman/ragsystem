import os
import warnings

# 禁用 ChromaDB 遙測
os.environ["CHROMA_TELEMETRY"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "false"

# 嘗試使用新版本的 Chroma
try:
    from langchain_chroma import Chroma
    print("✅ 使用 langchain-chroma 包")
except ImportError:
    # 如果新包不存在，使用舊版本但禁用警告
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain_community.vectorstores")
    from langchain_community.vectorstores import Chroma
    print("⚠️  使用舊版 Chroma (langchain_community)")

from langchain_community.vectorstores import Qdrant, Redis
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from config import get_config

# 禁用其他警告
warnings.filterwarnings("ignore", message=".*torch.classes.*")
warnings.filterwarnings("ignore", message=".*telemetry.*")

def get_vectorstore():
    """
    獲取向量資料庫實例
    
    Returns:
        向量資料庫實例 (Chroma, Redis 或 Qdrant)
    """
    vec_type = get_config("VECTOR_DB", "chroma").lower()
    embedding = get_embeddings()

    if vec_type == "chroma":
        persist_dir = get_config("CHROMA_PERSIST_DIR", "vector_db/chroma")
        
        # 確保目錄存在
        os.makedirs(persist_dir, exist_ok=True)
        
        try:
            # 嘗試使用客戶端設定來避免遙測問題
            import chromadb
            from chromadb.config import Settings
            
            # 創建客戶端設定
            client_settings = Settings(
                anonymized_telemetry=False,
                telemetry=False,
                persist_directory=persist_dir
            )
            
            # 創建 Chroma 實例
            return Chroma(
                embedding_function=embedding,
                persist_directory=persist_dir,
                client_settings=client_settings,
                collection_metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"⚠️  使用預設 Chroma 設定: {e}")
            # 如果失敗，使用簡單配置
            return Chroma(
                embedding_function=embedding,
                persist_directory=persist_dir
            )
            
    elif vec_type == "redis":
        redis_url = get_config("REDIS_URL", "redis://localhost:6379")
        index_name = get_config("REDIS_INDEX_NAME", "rag_index")
        return Redis(
            embedding_function=embedding, 
            index_name=index_name, 
            redis_url=redis_url
        )
        
    elif vec_type == "qdrant":
        qdrant_url = get_config("QDRANT_URL", "http://localhost:6333")
        collection_name = get_config("QDRANT_COLLECTION", "rag_data")
        return Qdrant(
            collection_name=collection_name, 
            embeddings=embedding, 
            location=qdrant_url
        )
    else:
        raise ValueError(f"Unsupported VECTOR_DB: {vec_type}")

def get_embeddings():
    """
    獲取嵌入模型
    
    Returns:
        嵌入模型實例
    """
    provider = get_config("EMBED_PROVIDER", "huggingface")  # 預設使用 huggingface
    
    if provider == "openai":
        api_key = get_config("OPENAI_API_KEY")
        if not api_key or api_key.startswith("sk-your"):
            print("⚠️  無效的 OpenAI API key，自動切換到 HuggingFace 嵌入模型")
            provider = "huggingface"
        else:
            return OpenAIEmbeddings(openai_api_key=api_key)
    
    # 預設使用 HuggingFace（免費且不需要 API key）
    print("🤗 使用 HuggingFace 嵌入模型（免費）")
    model_name = get_config("HUGGINGFACE_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # 設定來避免警告
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )