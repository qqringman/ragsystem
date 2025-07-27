import os
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader, UnstructuredWordDocumentLoader, UnstructuredExcelLoader,
    UnstructuredMarkdownLoader, UnstructuredHTMLLoader, JSONLoader, TextLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import get_config


def load_and_split_documents(file_paths):
    """
    載入並分割文件
    
    Args:
        file_paths: 檔案路徑列表
        
    Returns:
        分割後的文件列表
    """
    docs = []
    
    for path in file_paths:
        if not os.path.exists(path):
            print(f"⚠️  檔案不存在: {path}")
            continue
            
        ext = Path(path).suffix.lower()
        
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(path)
            elif ext in [".doc", ".docx"]:
                loader = UnstructuredWordDocumentLoader(path)
            elif ext in [".xls", ".xlsx"]:
                loader = UnstructuredExcelLoader(path)
            elif ext == ".md":
                loader = UnstructuredMarkdownLoader(path)
            elif ext in [".html", ".htm"]:
                loader = UnstructuredHTMLLoader(path)
            elif ext == ".json":
                loader = JSONLoader(path, jq_schema=".", text_content=False)
            elif ext == ".txt":
                # 支援純文字檔案
                loader = TextLoader(path, encoding='utf-8')
            else:
                print(f"⚠️  不支援的檔案格式: {ext}")
                continue

            # 載入文件
            loaded_docs = loader.load()
            docs.extend(loaded_docs)
            print(f"✅ 成功載入: {Path(path).name} ({len(loaded_docs)} 個文件)")
            
        except Exception as e:
            print(f"❌ 載入檔案 {path} 時發生錯誤: {str(e)}")
            continue

    if not docs:
        print("⚠️  沒有成功載入任何文件")
        return []

    # 使用配置中的 chunk_size 和 chunk_overlap
    chunk_size = int(get_config("CHUNK_SIZE", "1000"))
    chunk_overlap = int(get_config("CHUNK_OVERLAP", "100"))
    
    print(f"📄 開始分割文件 (chunk_size={chunk_size}, overlap={chunk_overlap})...")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
    )
    
    split_docs = splitter.split_documents(docs)
    print(f"✅ 文件分割完成，共 {len(split_docs)} 個片段")
    
    return split_docs