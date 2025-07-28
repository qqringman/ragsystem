import os
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader, UnstructuredWordDocumentLoader, UnstructuredExcelLoader,
    UnstructuredMarkdownLoader, UnstructuredHTMLLoader, JSONLoader, TextLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import get_config

# 導入 log 解析器管理器
try:
    from .log_parser_manager import log_parser_manager
    HAS_LOG_PARSER = True
except ImportError:
    log_parser_manager = None
    HAS_LOG_PARSER = False
    print("⚠️  Log 解析器未安裝，將使用標準文字處理")


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
        file_size_mb = os.path.getsize(path) / (1024 * 1024)
        
        print(f"📄 處理檔案: {Path(path).name} ({file_size_mb:.2f} MB)")
        
        try:
            # 特殊處理 log 檔案
            if ext == ".log" or (ext == ".txt" and "log" in Path(path).stem.lower()):
                if HAS_LOG_PARSER and log_parser_manager:
                    print(f"📊 使用專門的 Log 解析器處理...")
                    loaded_docs = log_parser_manager.parse_log_file(path)
                    
                    # 如果是大型 log 檔案，顯示分析結果
                    if file_size_mb > 1:
                        print(f"   ✅ Log 檔案分析完成：{len(loaded_docs)} 個片段")
                        
                        # 顯示分析統計
                        if loaded_docs:
                            log_types = set(doc.metadata.get('log_type', 'unknown') for doc in loaded_docs)
                            print(f"   📋 Log 類型: {', '.join(log_types)}")
                            
                            # 如果有錯誤統計
                            error_docs = [doc for doc in loaded_docs if doc.metadata.get('error_count', 0) > 0]
                            if error_docs:
                                total_errors = sum(doc.metadata.get('error_count', 0) for doc in error_docs)
                                print(f"   🔍 發現 {total_errors} 個錯誤相關條目")
                            
                            # 如果有崩潰資訊
                            crash_docs = [doc for doc in loaded_docs if doc.metadata.get('crash_type')]
                            if crash_docs:
                                crash_types = set(doc.metadata.get('crash_type', 'unknown') for doc in crash_docs)
                                print(f"   💥 崩潰類型: {', '.join(crash_types)}")
                else:
                    # 降級到文字載入器
                    loader = TextLoader(path, encoding='utf-8')
                    loaded_docs = loader.load()
                    
            elif ext == ".pdf":
                loader = PyPDFLoader(path)
                loaded_docs = loader.load()
                
            elif ext in [".doc", ".docx"]:
                loader = UnstructuredWordDocumentLoader(path)
                loaded_docs = loader.load()
                
            elif ext in [".xls", ".xlsx"]:
                loader = UnstructuredExcelLoader(path)
                loaded_docs = loader.load()
                
            elif ext == ".md":
                loader = UnstructuredMarkdownLoader(path)
                loaded_docs = loader.load()
                
            elif ext in [".html", ".htm"]:
                loader = UnstructuredHTMLLoader(path)
                loaded_docs = loader.load()
                
            elif ext == ".json":
                loader = JSONLoader(path, jq_schema=".", text_content=False)
                loaded_docs = loader.load()
                
            elif ext in [".txt", ".csv"]:
                # 一般文字檔案
                loader = TextLoader(path, encoding='utf-8')
                loaded_docs = loader.load()
                
            else:
                print(f"⚠️  不支援的檔案格式: {ext}")
                continue

            # 為所有文檔添加檔案大小元數據
            for doc in loaded_docs:
                doc.metadata['file_size_mb'] = file_size_mb
                doc.metadata['file_type'] = ext[1:]  # 移除點號
                
            docs.extend(loaded_docs)
            print(f"✅ 成功載入: {Path(path).name} ({len(loaded_docs)} 個文件)")
            
        except Exception as e:
            print(f"❌ 載入檔案 {path} 時發生錯誤: {str(e)}")
            continue

    if not docs:
        print("⚠️  沒有成功載入任何文件")
        return []

    # 檢查是否需要進一步分割
    # 對於已經由 LogParser 處理的文檔，不再分割
    already_split_docs = [doc for doc in docs if doc.metadata.get('chunk_method')]
    need_split_docs = [doc for doc in docs if not doc.metadata.get('chunk_method')]
    
    if need_split_docs:
        # 使用配置中的 chunk_size 和 chunk_overlap
        chunk_size = int(get_config("CHUNK_SIZE", "1000"))
        chunk_overlap = int(get_config("CHUNK_OVERLAP", "100"))
        
        print(f"📄 開始分割 {len(need_split_docs)} 個文件 (chunk_size={chunk_size}, overlap={chunk_overlap})...")
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )
        
        split_docs = splitter.split_documents(need_split_docs)
        print(f"✅ 文件分割完成，新增 {len(split_docs)} 個片段")
        
        # 合併已分割和新分割的文檔
        all_docs = already_split_docs + split_docs
    else:
        all_docs = already_split_docs
    
    print(f"📚 總共處理完成 {len(all_docs)} 個文檔片段")
    
    # 顯示處理統計
    if all_docs:
        # 統計不同類型的文檔
        doc_types = {}
        for doc in all_docs:
            doc_type = doc.metadata.get('file_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        if len(doc_types) > 1 or 'log' in doc_types:
            print(f"📊 文檔類型統計:")
            for doc_type, count in doc_types.items():
                print(f"   - {doc_type}: {count} 個片段")
    
    return all_docs