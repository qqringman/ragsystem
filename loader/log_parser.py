"""
Log 檔案專用處理器

針對 log 檔案的特殊處理，包括：
- 智能分割（按時間、錯誤級別等）
- 結構化解析
- 錯誤模式識別
"""

import re
from datetime import datetime
from typing import List, Dict, Any
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

class LogParser:
    """Log 檔案解析器"""
    
    # 常見的日誌格式模式
    LOG_PATTERNS = {
        'timestamp': r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',
        'iso_timestamp': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
        'level': r'\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b',
        'ip': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        'error_keywords': r'(error|exception|failed|failure|critical|fatal)',
    }
    
    def __init__(self, chunk_size=2000, chunk_overlap=200):
        """
        初始化 Log 解析器
        
        Args:
            chunk_size: 分塊大小（log 檔案可以用較大的 chunk）
            chunk_overlap: 重疊大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
            length_function=len,
        )
    
    def parse_log_file(self, file_path: str) -> List[Document]:
        """
        解析 log 檔案
        
        Args:
            file_path: log 檔案路徑
            
        Returns:
            Document 列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"讀取 log 檔案失敗: {e}")
            return []
        
        # 分析 log 結構
        log_info = self.analyze_log_structure(content)
        
        # 智能分割
        if log_info['has_timestamps']:
            # 按時間段分割
            documents = self.split_by_time_blocks(content, file_path)
        else:
            # 使用標準分割
            documents = self.standard_split(content, file_path)
        
        # 為每個文檔添加元數據
        for doc in documents:
            doc.metadata.update(log_info)
            doc.metadata['file_type'] = 'log'
            
            # 分析該片段的錯誤級別
            error_count = len(re.findall(self.LOG_PATTERNS['error_keywords'], 
                                       doc.page_content, re.IGNORECASE))
            doc.metadata['error_count'] = error_count
            
            # 提取該片段的日誌級別
            levels = re.findall(self.LOG_PATTERNS['level'], doc.page_content)
            if levels:
                doc.metadata['log_levels'] = list(set(levels))
        
        return documents
    
    def analyze_log_structure(self, content: str) -> Dict[str, Any]:
        """分析 log 檔案的結構"""
        lines = content.split('\n')
        total_lines = len(lines)
        
        # 檢測時間戳
        timestamp_count = len(re.findall(self.LOG_PATTERNS['timestamp'], content))
        iso_timestamp_count = len(re.findall(self.LOG_PATTERNS['iso_timestamp'], content))
        has_timestamps = (timestamp_count + iso_timestamp_count) > total_lines * 0.5
        
        # 統計錯誤級別
        error_levels = re.findall(self.LOG_PATTERNS['level'], content)
        level_counts = {}
        for level in error_levels:
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # 統計錯誤關鍵字
        error_keywords = re.findall(self.LOG_PATTERNS['error_keywords'], content, re.IGNORECASE)
        
        return {
            'total_lines': total_lines,
            'has_timestamps': has_timestamps,
            'timestamp_format': 'iso' if iso_timestamp_count > timestamp_count else 'standard',
            'level_counts': level_counts,
            'error_count': len(error_keywords),
            'file_size_mb': len(content) / (1024 * 1024),
        }
    
    def split_by_time_blocks(self, content: str, file_path: str) -> List[Document]:
        """按時間塊分割 log（適用於有時間戳的 log）"""
        lines = content.split('\n')
        documents = []
        current_block = []
        current_size = 0
        
        for line in lines:
            current_block.append(line)
            current_size += len(line) + 1  # +1 for newline
            
            # 檢查是否需要創建新塊
            if current_size >= self.chunk_size:
                # 找到下一個時間戳開始的位置
                if current_block:
                    block_content = '\n'.join(current_block)
                    doc = Document(
                        page_content=block_content,
                        metadata={
                            'source': file_path,
                            'chunk_method': 'time_block',
                            'chunk_size': len(block_content)
                        }
                    )
                    documents.append(doc)
                    
                    # 保留最後幾行作為重疊
                    overlap_lines = int(self.chunk_overlap / 50)  # 假設平均每行50字符
                    current_block = current_block[-overlap_lines:]
                    current_size = sum(len(line) + 1 for line in current_block)
        
        # 處理最後一個塊
        if current_block:
            block_content = '\n'.join(current_block)
            doc = Document(
                page_content=block_content,
                metadata={
                    'source': file_path,
                    'chunk_method': 'time_block',
                    'chunk_size': len(block_content)
                }
            )
            documents.append(doc)
        
        return documents
    
    def split_by_error_blocks(self, content: str, file_path: str) -> List[Document]:
        """按錯誤塊分割（將錯誤及其上下文保持在一起）"""
        # 找出所有錯誤位置
        error_positions = []
        for match in re.finditer(self.LOG_PATTERNS['error_keywords'], content, re.IGNORECASE):
            error_positions.append(match.start())
        
        if not error_positions:
            # 沒有錯誤，使用標準分割
            return self.standard_split(content, file_path)
        
        documents = []
        last_pos = 0
        
        for i, error_pos in enumerate(error_positions):
            # 提取錯誤前後的上下文
            start = max(0, error_pos - 500)  # 錯誤前500字符
            end = min(len(content), error_pos + 1500)  # 錯誤後1500字符
            
            # 確保不重複
            if start < last_pos:
                start = last_pos
            
            if start < end:
                error_context = content[start:end]
                doc = Document(
                    page_content=error_context,
                    metadata={
                        'source': file_path,
                        'chunk_method': 'error_block',
                        'error_index': i,
                        'chunk_size': len(error_context)
                    }
                )
                documents.append(doc)
                last_pos = end
        
        # 處理剩餘內容
        if last_pos < len(content):
            remaining = content[last_pos:]
            if len(remaining) > 100:  # 只保留有意義的內容
                doc = Document(
                    page_content=remaining,
                    metadata={
                        'source': file_path,
                        'chunk_method': 'error_block_remainder',
                        'chunk_size': len(remaining)
                    }
                )
                documents.append(doc)
        
        return documents
    
    def standard_split(self, content: str, file_path: str) -> List[Document]:
        """標準文字分割"""
        # 創建基礎文檔
        base_doc = Document(
            page_content=content,
            metadata={'source': file_path}
        )
        
        # 使用文字分割器
        return self.text_splitter.split_documents([base_doc])
    
    def extract_error_summary(self, content: str) -> Dict[str, Any]:
        """提取錯誤摘要"""
        errors = []
        
        # 查找所有錯誤行
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if re.search(self.LOG_PATTERNS['error_keywords'], line, re.IGNORECASE):
                # 獲取錯誤上下文（前後各2行）
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = '\n'.join(lines[start:end])
                
                errors.append({
                    'line_number': i + 1,
                    'error_line': line,
                    'context': context
                })
        
        return {
            'total_errors': len(errors),
            'error_samples': errors[:5],  # 只返回前5個錯誤作為樣本
        }