"""
基礎 Log 解析器

提供所有 log 解析器的基礎功能和介面
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
from datetime import datetime
import os


class BaseLogParser(ABC):
    """所有 log 解析器的基類"""
    
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200):
        """
        初始化基礎解析器
        
        Args:
            chunk_size: 分塊大小
            chunk_overlap: 重疊大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.get_separators(),
            length_function=len,
        )
    
    @abstractmethod
    def get_log_type(self) -> str:
        """返回 log 類型標識"""
        pass
    
    @abstractmethod
    def can_parse(self, file_path: str, content_sample: str) -> bool:
        """
        檢查是否能解析此檔案
        
        Args:
            file_path: 檔案路徑
            content_sample: 內容樣本（前 1000 字符）
            
        Returns:
            是否能解析
        """
        pass
    
    @abstractmethod
    def get_patterns(self) -> Dict[str, str]:
        """返回此類型 log 的正則表達式模式"""
        pass
    
    def get_separators(self) -> List[str]:
        """返回用於分割的分隔符（可覆寫）"""
        return ["\n\n", "\n", " ", ""]
    
    def parse_log_file(self, file_path: str) -> List[Document]:
        """
        解析 log 檔案的主要方法
        
        Args:
            file_path: log 檔案路徑
            
        Returns:
            Document 列表
        """
        try:
            content = self.read_file(file_path)
        except Exception as e:
            print(f"❌ 讀取檔案失敗: {e}")
            return []
        
        # 分析 log 結構
        log_info = self.analyze_log_structure(content)
        log_info['log_type'] = self.get_log_type()
        log_info['parser_class'] = self.__class__.__name__
        
        # 執行特定的解析策略
        documents = self.parse_content(content, file_path, log_info)
        
        # 後處理
        documents = self.post_process_documents(documents, log_info)
        
        print(f"✅ {self.get_log_type()} 解析完成: {len(documents)} 個片段")
        
        return documents
    
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """讀取檔案內容"""
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            return f.read()
    
    @abstractmethod
    def analyze_log_structure(self, content: str) -> Dict[str, Any]:
        """
        分析 log 結構，返回統計資訊
        
        Args:
            content: log 內容
            
        Returns:
            結構分析結果
        """
        pass
    
    @abstractmethod
    def parse_content(self, content: str, file_path: str, log_info: Dict[str, Any]) -> List[Document]:
        """
        執行具體的內容解析
        
        Args:
            content: log 內容
            file_path: 檔案路徑
            log_info: 結構分析結果
            
        Returns:
            Document 列表
        """
        pass
    
    def post_process_documents(self, documents: List[Document], log_info: Dict[str, Any]) -> List[Document]:
        """
        後處理文檔（添加元數據等）
        
        Args:
            documents: 原始文檔列表
            log_info: log 分析資訊
            
        Returns:
            處理後的文檔列表
        """
        for doc in documents:
            # 添加通用元數據
            doc.metadata.update({
                'log_type': self.get_log_type(),
                'parser_class': self.__class__.__name__,
                'file_type': 'log'
            })
            
            # 添加 log 分析資訊
            for key, value in log_info.items():
                if key not in doc.metadata:
                    doc.metadata[key] = value
        
        return documents
    
    def extract_time_range(self, content: str) -> Optional[Tuple[datetime, datetime]]:
        """提取時間範圍（如果有時間戳）"""
        patterns = self.get_patterns()
        if 'timestamp' not in patterns:
            return None
        
        timestamps = []
        for match in re.finditer(patterns['timestamp'], content):
            try:
                ts = self.parse_timestamp(match.group())
                if ts:
                    timestamps.append(ts)
            except:
                continue
        
        if timestamps:
            return min(timestamps), max(timestamps)
        return None
    
    def parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """解析時間戳字串（子類可覆寫）"""
        # 嘗試常見格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S,%f',  # Log4j format
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str.strip(), fmt)
            except:
                continue
        return None
    
    def create_document(self, content: str, file_path: str, metadata: Dict[str, Any]) -> Document:
        """創建文檔的輔助方法"""
        return Document(
            page_content=content,
            metadata={
                'source': file_path,
                'chunk_size': len(content),
                **metadata
            }
        )
    
    def smart_split(self, content: str, split_pattern: Optional[str] = None) -> List[str]:
        """
        智能分割內容
        
        Args:
            content: 要分割的內容
            split_pattern: 分割模式（正則表達式）
            
        Returns:
            分割後的片段列表
        """
        if split_pattern:
            # 使用指定的模式分割，但保留分隔符
            parts = re.split(f'({split_pattern})', content)
            
            # 重組片段，將分隔符附加到前一個片段
            chunks = []
            current_chunk = ""
            
            for i, part in enumerate(parts):
                if i % 2 == 0:  # 內容部分
                    current_chunk = part
                else:  # 分隔符部分
                    if current_chunk or part:
                        chunks.append(current_chunk + part)
                    current_chunk = ""
            
            if current_chunk:  # 最後一個片段
                chunks.append(current_chunk)
            
            return [chunk for chunk in chunks if chunk.strip()]
        else:
            # 使用標準文字分割器
            doc = Document(page_content=content, metadata={})
            return [d.page_content for d in self.text_splitter.split_documents([doc])]