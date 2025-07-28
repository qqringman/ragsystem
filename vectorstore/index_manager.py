# vectorstore/index_manager.py
# 改進版本 - 更好的權限處理

import os
import stat
import warnings
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from config import get_config

def ensure_directory_permissions(directory_path: str):
    """確保目錄有正確的權限"""
    try:
        # 創建目錄
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        
        # 嘗試設置權限
        try:
            # 設置目錄權限為 755
            os.chmod(directory_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            
            # 對目錄下的所有文件設置權限
            for root, dirs, files in os.walk(directory_path):
                for d in dirs:
                    try:
                        os.chmod(os.path.join(root, d), 
                                stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                    except:
                        pass
                
                for f in files:
                    try:
                        # SQLite 文件需要寫入權限
                        if f.endswith('.sqlite3'):
                            os.chmod(os.path.join(root, f), stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP)
                        else:
                            os.chmod(os.path.join(root, f), stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                    except:
                        pass
                        
        except PermissionError:
            # 如果無法修改權限，只發出警告而不是失敗
            warnings.warn(
                f"⚠️  無法修改 {directory_path} 的權限。\n"
                f"   如果遇到權限問題，請手動執行: sudo chmod -R 755 {directory_path}\n"
                f"   或使用 Docker 環境避免權限問題。"
            )
        
        # 測試是否可以寫入
        test_file = os.path.join(directory_path, '.write_test')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            warnings.warn(
                f"⚠️  無法寫入 {directory_path}。\n"
                f"   錯誤: {str(e)}\n"
                f"   請確保有寫入權限。"
            )
            
    except Exception as e:
        print(f"❌ 創建目錄失敗: {str(e)}")
        raise

def get_embeddings():
    """根據配置獲取嵌入模型"""
    provider = get_config("EMBEDDING_PROVIDER", "huggingface")
    
    if provider == "openai":
        print("🔑 使用 OpenAI 嵌入模型")
        return OpenAIEmbeddings(
            openai_api_key=get_config("OPENAI_API_KEY")
        )
    else:
        print("🤗 使用 HuggingFace 嵌入模型（免費）")
        # 使用更輕量的模型，支援中文
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

def get_vectorstore(collection_name: str = "rag_docs"):
    """獲取或創建向量存儲"""
    vector_db = get_config("VECTOR_DB", "chroma")
    
    if vector_db == "chroma":
        persist_dir = get_config("CHROMA_PERSIST_DIR", "vector_db/chroma")
        
        # 確保目錄權限正確
        ensure_directory_permissions(persist_dir)
        
        try:
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=get_embeddings(),
                persist_directory=persist_dir
            )
            return vectorstore
            
        except Exception as e:
            if "does not exist" in str(e):
                print(f"📦 創建新的向量資料庫集合: {collection_name}")
                # 創建新的集合
                vectorstore = Chroma(
                    collection_name=collection_name,
                    embedding_function=get_embeddings(),
                    persist_directory=persist_dir
                )
                return vectorstore
            else:
                # 如果是權限問題，提供更清晰的錯誤信息
                if "permission" in str(e).lower() or "errno 1" in str(e).lower():
                    print(f"\n❌ 權限錯誤: {str(e)}")
                    print("\n🔧 解決方案：")
                    print("1. 使用 sudo 修改權限:")
                    print(f"   sudo chmod -R 755 {persist_dir}")
                    print(f"   sudo chown -R $USER:$USER {persist_dir}")
                    print("\n2. 或刪除並重建:")
                    print(f"   rm -rf {persist_dir}")
                    print("   然後重新運行程序")
                    print("\n3. 或使用 Docker 環境避免權限問題")
                raise
    
    # 其他向量資料庫實現...
    else:
        raise NotImplementedError(f"向量資料庫 {vector_db} 尚未實現")

def clear_vectorstore(collection_name: str = "rag_docs"):
    """清空向量存儲"""
    vector_db = get_config("VECTOR_DB", "chroma")
    
    if vector_db == "chroma":
        persist_dir = get_config("CHROMA_PERSIST_DIR", "vector_db/chroma")
        
        try:
            # 嘗試刪除整個目錄
            import shutil
            if os.path.exists(persist_dir):
                shutil.rmtree(persist_dir)
                print(f"✅ 已清空向量資料庫: {persist_dir}")
            
            # 重新創建目錄
            ensure_directory_permissions(persist_dir)
            
        except PermissionError:
            print(f"❌ 無法刪除 {persist_dir}，權限不足")
            print("請手動執行:")
            print(f"  sudo rm -rf {persist_dir}")
            raise
        except Exception as e:
            print(f"❌ 清空向量資料庫失敗: {str(e)}")
            raise

# 添加一個測試函數
def test_vectorstore_access():
    """測試向量資料庫訪問權限"""
    try:
        print("🧪 測試向量資料庫訪問...")
        vs = get_vectorstore()
        
        # 嘗試添加測試文檔
        from langchain.schema import Document
        test_doc = Document(
            page_content="這是一個測試文檔",
            metadata={"source": "test", "type": "test"}
        )
        
        vs.add_documents([test_doc])
        print("✅ 向量資料庫訪問正常")
        
        # 清理測試文檔
        # 注意：Chroma 不支援直接刪除，這裡只是測試
        
        return True
        
    except Exception as e:
        print(f"❌ 向量資料庫訪問失敗: {str(e)}")
        return False

if __name__ == "__main__":
    # 測試向量資料庫
    test_vectorstore_access()