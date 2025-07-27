from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores import Qdrant, Redis
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from config import get_config

def get_vectorstore():
    vec_type = get_config("VECTOR_DB", "chroma").lower()
    embedding = get_embeddings()

    if vec_type == "chroma":
        persist_dir = get_config("CHROMA_PERSIST_DIR", "vector_db/chroma")
        return Chroma(embedding_function=embedding, persist_directory=persist_dir)
    elif vec_type == "redis":
        redis_url = get_config("REDIS_URL", "redis://localhost:6379")
        index_name = get_config("REDIS_INDEX_NAME", "rag_index")
        return Redis(embedding_function=embedding, index_name=index_name, redis_url=redis_url)
    elif vec_type == "qdrant":
        qdrant_url = get_config("QDRANT_URL", "http://localhost:6333")
        collection_name = get_config("QDRANT_COLLECTION", "rag_data")
        return Qdrant(collection_name=collection_name, embeddings=embedding, location=qdrant_url)
    else:
        raise ValueError(f"Unsupported VECTOR_DB: {vec_type}")

def get_embeddings():
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
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )