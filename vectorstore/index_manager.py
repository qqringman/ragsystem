
import os
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores import Qdrant, Redis
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

def get_vectorstore():
    vec_type = os.getenv("VECTOR_DB", "chroma").lower()
    embedding = get_embeddings()

    if vec_type == "chroma":
        return Chroma(embedding_function=embedding, persist_directory="vector_db/chroma")
    elif vec_type == "redis":
        return Redis(embedding_function=embedding, index_name="rag_index", redis_url="redis://localhost:6379")
    elif vec_type == "qdrant":
        return Qdrant(collection_name="rag_data", embeddings=embedding, location="http://localhost:6333")
    else:
        raise ValueError("Unsupported VECTOR_DB")

def get_embeddings():
    provider = os.getenv("EMBED_PROVIDER", "openai")
    if provider == "openai":
        return OpenAIEmbeddings()
    else:
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
