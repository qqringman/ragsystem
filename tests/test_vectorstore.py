"""
向量資料庫測試

測試支援的向量資料庫：
- Chroma
- Redis
- Qdrant
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from vectorstore.index_manager import get_vectorstore, get_embeddings
from langchain.schema import Document
import numpy as np


class TestEmbeddings:
    """嵌入模型測試"""
    
    def setup_method(self):
        """設置測試環境"""
        self.original_env = os.environ.copy()
    
    def teardown_method(self):
        """清理測試環境"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    @patch('vectorstore.index_manager.OpenAIEmbeddings')
    def test_get_openai_embeddings(self, mock_openai_embeddings):
        """測試獲取 OpenAI 嵌入模型"""
        os.environ["EMBED_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = "test-key"
        
        embeddings = get_embeddings()
        
        mock_openai_embeddings.assert_called_once()
    
    @patch('vectorstore.index_manager.HuggingFaceEmbeddings')
    def test_get_huggingface_embeddings(self, mock_hf_embeddings):
        """測試獲取 HuggingFace 嵌入模型"""
        os.environ["EMBED_PROVIDER"] = "huggingface"
        
        embeddings = get_embeddings()
        
        mock_hf_embeddings.assert_called_once_with(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )


class TestVectorStores:
    """向量資料庫測試"""
    
    def setup_method(self):
        """設置測試環境"""
        self.original_env = os.environ.copy()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """清理測試環境"""
        os.environ.clear()
        os.environ.update(self.original_env)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('vectorstore.index_manager.Chroma')
    @patch('vectorstore.index_manager.get_embeddings')
    def test_get_chroma_vectorstore(self, mock_get_embeddings, mock_chroma):
        """測試獲取 Chroma 向量資料庫"""
        # 設置環境變數
        os.environ["VECTOR_DB"] = "chroma"
        
        # 設置 mock
        mock_embeddings = Mock()
        mock_get_embeddings.return_value = mock_embeddings
        
        # 獲取向量資料庫
        vectorstore = get_vectorstore()
        
        # 驗證
        mock_get_embeddings.assert_called_once()
        mock_chroma.assert_called_once_with(
            embedding_function=mock_embeddings,
            persist_directory="vector_db/chroma"
        )
    
    @patch('vectorstore.index_manager.Redis')
    @patch('vectorstore.index_manager.get_embeddings')
    def test_get_redis_vectorstore(self, mock_get_embeddings, mock_redis):
        """測試獲取 Redis 向量資料庫"""
        # 設置環境變數
        os.environ["VECTOR_DB"] = "redis"
        
        # 設置 mock
        mock_embeddings = Mock()
        mock_get_embeddings.return_value = mock_embeddings
        
        # 獲取向量資料庫
        vectorstore = get_vectorstore()
        
        # 驗證
        mock_get_embeddings.assert_called_once()
        mock_redis.assert_called_once_with(
            embedding_function=mock_embeddings,
            index_name="rag_index",
            redis_url="redis://localhost:6379"
        )
    
    @patch('vectorstore.index_manager.Qdrant')
    @patch('vectorstore.index_manager.get_embeddings')
    def test_get_qdrant_vectorstore(self, mock_get_embeddings, mock_qdrant):
        """測試獲取 Qdrant 向量資料庫"""
        # 設置環境變數
        os.environ["VECTOR_DB"] = "qdrant"
        
        # 設置 mock
        mock_embeddings = Mock()
        mock_get_embeddings.return_value = mock_embeddings
        
        # 獲取向量資料庫
        vectorstore = get_vectorstore()
        
        # 驗證
        mock_get_embeddings.assert_called_once()
        mock_qdrant.assert_called_once_with(
            collection_name="rag_data",
            embeddings=mock_embeddings,
            location="http://localhost:6333"
        )
    
    def test_unsupported_vectorstore(self):
        """測試不支援的向量資料庫"""
        os.environ["VECTOR_DB"] = "unsupported"
        
        with pytest.raises(ValueError, match="Unsupported VECTOR_DB"):
            get_vectorstore()


class TestVectorStoreOperations:
    """向量資料庫操作測試"""
    
    @patch('vectorstore.index_manager.Chroma')
    @patch('vectorstore.index_manager.get_embeddings')
    def test_add_documents(self, mock_get_embeddings, mock_chroma):
        """測試添加文件到向量資料庫"""
        # 設置 mock
        mock_embeddings = Mock()
        mock_get_embeddings.return_value = mock_embeddings
        
        mock_vectorstore = Mock()
        mock_chroma.return_value = mock_vectorstore
        
        # 準備測試文件
        test_docs = [
            Document(page_content="測試文件1", metadata={"source": "test1.txt"}),
            Document(page_content="測試文件2", metadata={"source": "test2.txt"})
        ]
        
        # 獲取向量資料庫並添加文件
        os.environ["VECTOR_DB"] = "chroma"
        vectorstore = get_vectorstore()
        vectorstore.add_documents(test_docs)
        
        # 驗證
        mock_vectorstore.add_documents.assert_called_once_with(test_docs)
    
    @patch('vectorstore.index_manager.Chroma')
    @patch('vectorstore.index_manager.get_embeddings')
    def test_similarity_search(self, mock_get_embeddings, mock_chroma):
        """測試相似度搜尋"""
        # 設置 mock
        mock_embeddings = Mock()
        mock_get_embeddings.return_value = mock_embeddings
        
        mock_vectorstore = Mock()
        mock_results = [
            Document(page_content="相關文件1", metadata={"source": "doc1.txt", "score": 0.9}),
            Document(page_content="相關文件2", metadata={"source": "doc2.txt", "score": 0.8})
        ]
        mock_vectorstore.similarity_search.return_value = mock_results
        mock_chroma.return_value = mock_vectorstore
        
        # 執行搜尋
        os.environ["VECTOR_DB"] = "chroma"
        vectorstore = get_vectorstore()
        results = vectorstore.similarity_search("測試查詢", k=2)
        
        # 驗證
        assert len(results) == 2
        assert results[0].page_content == "相關文件1"
        assert results[1].page_content == "相關文件2"
        mock_vectorstore.similarity_search.assert_called_once_with("測試查詢", k=2)
    
    @patch('vectorstore.index_manager.Chroma')
    @patch('vectorstore.index_manager.get_embeddings')
    def test_similarity_search_with_score(self, mock_get_embeddings, mock_chroma):
        """測試帶分數的相似度搜尋"""
        # 設置 mock
        mock_embeddings = Mock()
        mock_get_embeddings.return_value = mock_embeddings
        
        mock_vectorstore = Mock()
        mock_results = [
            (Document(page_content="相關文件1", metadata={"source": "doc1.txt"}), 0.95),
            (Document(page_content="相關文件2", metadata={"source": "doc2.txt"}), 0.85)
        ]
        mock_vectorstore.similarity_search_with_score.return_value = mock_results
        mock_chroma.return_value = mock_vectorstore
        
        # 執行搜尋
        os.environ["VECTOR_DB"] = "chroma"
        vectorstore = get_vectorstore()
        results = vectorstore.similarity_search_with_score("測試查詢", k=2)
        
        # 驗證
        assert len(results) == 2
        assert results[0][0].page_content == "相關文件1"
        assert results[0][1] == 0.95
        assert results[1][0].page_content == "相關文件2"
        assert results[1][1] == 0.85


class TestVectorStoreIntegration:
    """向量資料庫整合測試"""
    
    def setup_method(self):
        """設置測試環境"""
        self.temp_dir = tempfile.mkdtemp()
        os.environ["CHROMA_PERSIST_DIR"] = self.temp_dir
    
    def teardown_method(self):
        """清理測試環境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.path.exists("/usr/local/lib/python3.12/site-packages/chromadb"),
        reason="需要安裝 chromadb"
    )
    def test_real_chroma_operations(self):
        """測試真實的 Chroma 操作"""
        # 使用本地嵌入模型以避免 API 調用
        os.environ["VECTOR_DB"] = "chroma"
        os.environ["EMBED_PROVIDER"] = "huggingface"
        
        # 獲取向量資料庫
        vectorstore = get_vectorstore()
        
        # 添加測試文件
        test_docs = [
            Document(page_content="Python 是一種程式語言", metadata={"source": "test1.txt"}),
            Document(page_content="JavaScript 是網頁開發語言", metadata={"source": "test2.txt"}),
            Document(page_content="Python 適合資料科學", metadata={"source": "test3.txt"})
        ]
        
        vectorstore.add_documents(test_docs)
        
        # 執行搜尋
        results = vectorstore.similarity_search("Python 程式設計", k=2)
        
        # 驗證結果
        assert len(results) <= 2
        # 結果應該包含 Python 相關的文件
        python_related = any("Python" in doc.page_content for doc in results)
        assert python_related


# 測試 fixtures
@pytest.fixture
def mock_embedding_function():
    """模擬嵌入函數"""
    def embed_documents(texts):
        # 返回隨機向量作為嵌入
        return [np.random.rand(384).tolist() for _ in texts]
    
    def embed_query(text):
        # 返回隨機向量作為嵌入
        return np.random.rand(384).tolist()
    
    mock = Mock()
    mock.embed_documents = embed_documents
    mock.embed_query = embed_query
    return mock


@pytest.fixture
def sample_vector_documents():
    """提供測試用的向量文件"""
    return [
        Document(
            page_content="機器學習是人工智慧的分支",
            metadata={"source": "ml.txt", "topic": "AI"}
        ),
        Document(
            page_content="深度學習使用神經網路",
            metadata={"source": "dl.txt", "topic": "AI"}
        ),
        Document(
            page_content="自然語言處理處理文字資料",
            metadata={"source": "nlp.txt", "topic": "AI"}
        ),
    ]