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
        
        # 確保目錄存在並有正確權限
        os.makedirs(persist_dir, exist_ok=True)
        
        # 嘗試修復權限
        try:
            os.chmod(persist_dir, 0o777)
            # 如果已有 SQLite 檔案，也修復其權限
            sqlite_files = [f for f in os.listdir(persist_dir) if f.endswith('.sqlite3')]
            for sqlite_file in sqlite_files:
                os.chmod(os.path.join(persist_dir, sqlite_file), 0o666)
        except Exception as e:
            print(f"⚠️  無法修改權限: {e}")
            print("  請手動執行: sudo chmod -R 777 vector_db")
        
        try:
            # 使用新版 ChromaDB API
            import chromadb
            
            # 使用新的 PersistentClient API（ChromaDB 0.4+）
            try:
                # 嘗試新版 API
                client = chromadb.PersistentClient(
                    path=persist_dir,
                    settings=chromadb.Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                
                # 獲取或創建預設集合
                collection_name = "langchain"
                try:
                    collection = client.get_collection(collection_name)
                except:
                    collection = client.create_collection(
                        name=collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )
                
                # 使用 Chroma 包裝器
                from langchain_community.vectorstores import Chroma
                return Chroma(
                    client=client,
                    collection_name=collection_name,
                    embedding_function=embedding,
                    persist_directory=persist_dir
                )
                
            except AttributeError:
                # 如果 PersistentClient 不存在，使用舊版 API
                print("⚠️  使用舊版 ChromaDB API")
                from chromadb.config import Settings
                
                client_settings = Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=persist_dir,
                    anonymized_telemetry=False
                )
                
                return Chroma(
                    embedding_function=embedding,
                    persist_directory=persist_dir,
                    client_settings=client_settings,
                    collection_metadata={"hnsw:space": "cosine"}
                )
                
        except Exception as e:
            print(f"⚠️  ChromaDB 初始化失敗: {e}")
            print("  嘗試使用最簡單的配置...")
            
            # 最後的備案：使用最簡單的配置
            from langchain_community.vectorstores import Chroma
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