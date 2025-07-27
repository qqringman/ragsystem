"""
文件載入器測試

測試各種文件格式的載入和處理：
- PDF
- Word (DOC/DOCX)
- Excel (XLS/XLSX)
- Markdown
- HTML
- JSON
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from loader.doc_parser import load_and_split_documents
from langchain.schema import Document


class TestDocumentLoader:
    """文件載入器測試"""
    
    def setup_method(self):
        """設置測試環境"""
        # 創建臨時目錄
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """清理測試環境"""
        # 刪除臨時檔案
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename, content="測試內容"):
        """創建測試檔案"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath
    
    @patch('loader.doc_parser.PyPDFLoader')
    def test_load_pdf(self, mock_pdf_loader):
        """測試載入 PDF 檔案"""
        # 設置 mock
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [
            Document(page_content="PDF 內容第一頁", metadata={"page": 0}),
            Document(page_content="PDF 內容第二頁", metadata={"page": 1})
        ]
        mock_pdf_loader.return_value = mock_loader_instance
        
        # 創建測試檔案
        pdf_path = self.create_test_file("test.pdf")
        
        # 載入並分割文件
        docs = load_and_split_documents([pdf_path])
        
        # 驗證
        assert len(docs) > 0
        mock_pdf_loader.assert_called_once_with(pdf_path)
        mock_loader_instance.load.assert_called_once()
    
    @patch('loader.doc_parser.UnstructuredWordDocumentLoader')
    def test_load_docx(self, mock_word_loader):
        """測試載入 Word 檔案"""
        # 設置 mock
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [
            Document(page_content="Word 文件內容", metadata={"source": "test.docx"})
        ]
        mock_word_loader.return_value = mock_loader_instance
        
        # 創建測試檔案
        docx_path = self.create_test_file("test.docx")
        
        # 載入並分割文件
        docs = load_and_split_documents([docx_path])
        
        # 驗證
        assert len(docs) > 0
        mock_word_loader.assert_called_once_with(docx_path)
    
    @patch('loader.doc_parser.UnstructuredExcelLoader')
    def test_load_excel(self, mock_excel_loader):
        """測試載入 Excel 檔案"""
        # 設置 mock
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [
            Document(page_content="A1,B1,C1\nA2,B2,C2", metadata={"source": "test.xlsx"})
        ]
        mock_excel_loader.return_value = mock_loader_instance
        
        # 創建測試檔案
        xlsx_path = self.create_test_file("test.xlsx")
        
        # 載入並分割文件
        docs = load_and_split_documents([xlsx_path])
        
        # 驗證
        assert len(docs) > 0
        mock_excel_loader.assert_called_once_with(xlsx_path)
    
    @patch('loader.doc_parser.UnstructuredMarkdownLoader')
    def test_load_markdown(self, mock_md_loader):
        """測試載入 Markdown 檔案"""
        # 設置 mock
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [
            Document(page_content="# 標題\n\n這是內容", metadata={"source": "test.md"})
        ]
        mock_md_loader.return_value = mock_loader_instance
        
        # 創建測試檔案
        md_path = self.create_test_file("test.md", "# 測試標題\n\n測試內容")
        
        # 載入並分割文件
        docs = load_and_split_documents([md_path])
        
        # 驗證
        assert len(docs) > 0
        mock_md_loader.assert_called_once_with(md_path)
    
    @patch('loader.doc_parser.UnstructuredHTMLLoader')
    def test_load_html(self, mock_html_loader):
        """測試載入 HTML 檔案"""
        # 設置 mock
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [
            Document(page_content="HTML 內容", metadata={"source": "test.html"})
        ]
        mock_html_loader.return_value = mock_loader_instance
        
        # 創建測試檔案
        html_content = "<html><body><h1>標題</h1><p>內容</p></body></html>"
        html_path = self.create_test_file("test.html", html_content)
        
        # 載入並分割文件
        docs = load_and_split_documents([html_path])
        
        # 驗證
        assert len(docs) > 0
        mock_html_loader.assert_called_once_with(html_path)
    
    @patch('loader.doc_parser.JSONLoader')
    def test_load_json(self, mock_json_loader):
        """測試載入 JSON 檔案"""
        # 設置 mock
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [
            Document(page_content='{"key": "value"}', metadata={"source": "test.json"})
        ]
        mock_json_loader.return_value = mock_loader_instance
        
        # 創建測試檔案
        json_content = '{"test": "data", "array": [1, 2, 3]}'
        json_path = self.create_test_file("test.json", json_content)
        
        # 載入並分割文件
        docs = load_and_split_documents([json_path])
        
        # 驗證
        assert len(docs) > 0
        mock_json_loader.assert_called_once()
    
    def test_load_unsupported_format(self):
        """測試載入不支援的檔案格式"""
        # 創建不支援格式的檔案
        unsupported_path = self.create_test_file("test.xyz")
        
        # 載入應該返回空列表
        docs = load_and_split_documents([unsupported_path])
        
        assert len(docs) == 0
    
    def test_load_multiple_files(self):
        """測試載入多個檔案"""
        with patch('loader.doc_parser.UnstructuredMarkdownLoader') as mock_md, \
             patch('loader.doc_parser.UnstructuredHTMLLoader') as mock_html:
            
            # 設置 mocks
            mock_md_instance = Mock()
            mock_md_instance.load.return_value = [
                Document(page_content="Markdown 內容", metadata={})
            ]
            mock_md.return_value = mock_md_instance
            
            mock_html_instance = Mock()
            mock_html_instance.load.return_value = [
                Document(page_content="HTML 內容", metadata={})
            ]
            mock_html.return_value = mock_html_instance
            
            # 創建多個測試檔案
            md_path = self.create_test_file("test1.md")
            html_path = self.create_test_file("test2.html")
            
            # 載入並分割文件
            docs = load_and_split_documents([md_path, html_path])
            
            # 驗證
            assert len(docs) > 0
            mock_md.assert_called_once()
            mock_html.assert_called_once()


class TestTextSplitter:
    """文字分割器測試"""
    
    @patch('loader.doc_parser.RecursiveCharacterTextSplitter')
    def test_text_splitter_config(self, mock_splitter_class):
        """測試文字分割器配置"""
        # 設置 mock
        mock_splitter = Mock()
        mock_splitter.split_documents.return_value = [
            Document(page_content="分割後的文字1", metadata={}),
            Document(page_content="分割後的文字2", metadata={})
        ]
        mock_splitter_class.return_value = mock_splitter
        
        # 測試預設配置
        with patch('loader.doc_parser.UnstructuredMarkdownLoader') as mock_loader:
            mock_loader_instance = Mock()
            mock_loader_instance.load.return_value = [
                Document(page_content="很長的文字" * 100, metadata={})
            ]
            mock_loader.return_value = mock_loader_instance
            
            docs = load_and_split_documents(["test.md"])
            
            # 驗證分割器配置
            mock_splitter_class.assert_called_once_with(
                chunk_size=500,
                chunk_overlap=50
            )
            mock_splitter.split_documents.assert_called_once()
    
    def test_empty_file_list(self):
        """測試空檔案列表"""
        docs = load_and_split_documents([])
        assert docs == []
    
    def test_non_existent_file(self):
        """測試不存在的檔案"""
        docs = load_and_split_documents(["/path/to/non/existent/file.pdf"])
        assert docs == []


class TestDocumentMetadata:
    """文件元資料測試"""
    
    @patch('loader.doc_parser.PyPDFLoader')
    def test_preserve_metadata(self, mock_pdf_loader):
        """測試保留文件元資料"""
        # 設置 mock
        mock_loader_instance = Mock()
        test_metadata = {
            "source": "test.pdf",
            "page": 0,
            "total_pages": 10,
            "author": "Test Author"
        }
        mock_loader_instance.load.return_value = [
            Document(page_content="測試內容", metadata=test_metadata)
        ]
        mock_pdf_loader.return_value = mock_loader_instance
        
        # 載入文件
        docs = load_and_split_documents(["test.pdf"])
        
        # 驗證元資料是否保留
        assert len(docs) > 0
        # 分割後的文件應該包含原始元資料
        for doc in docs:
            assert "source" in doc.metadata


# 測試 fixtures
@pytest.fixture
def sample_documents():
    """提供測試用的文件樣本"""
    return [
        Document(
            page_content="這是第一個文件的內容",
            metadata={"source": "doc1.txt", "page": 1}
        ),
        Document(
            page_content="這是第二個文件的內容",
            metadata={"source": "doc2.txt", "page": 1}
        ),
    ]


@pytest.fixture
def long_document():
    """提供需要分割的長文件"""
    content = "這是一段很長的文字。" * 100  # 創建超過 chunk_size 的內容
    return Document(
        page_content=content,
        metadata={"source": "long_doc.txt"}
    )