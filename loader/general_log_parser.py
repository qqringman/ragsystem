"""
通用 Log 解析器

處理一般的應用程式 log
"""

from typing import List, Dict, Any
import re
from .base_log_parser import BaseLogParser
from langchain.schema import Document


class GeneralLogParser(BaseLogParser):
    """通用 log 解析器（原 LogParser 的實現）"""
    
    def get_log_type(self) -> str:
        return "general"
    
    def can_parse(self, file_path: str, content_sample: str) -> bool:
        """檢查是否為一般 log 格式"""
        # 如果不是特殊格式，就用通用解析器
        patterns = self.get_patterns()
        
        # 檢查是否包含常見的 log 元素
        has_timestamp = bool(re.search(patterns['timestamp'], content_sample))
        has_log_level = bool(re.search(patterns['level'], content_sample))
        
        # 如果有時間戳或日誌級別，就認為是一般 log
        return has_timestamp or has_log_level
    
    def get_patterns(self) -> Dict[str, str]:
        """返回一般 log 的模式"""
        return {
            'timestamp': r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',
            'iso_timestamp': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            'level': r'\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL|TRACE)\b',
            'ip': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'error_keywords': r'(error|exception|failed|failure|critical|fatal|panic|crash)',
            'stack_trace': r'^\s+at\s+[\w.$]+\([\w.]+:\d+\)',  # Java style
            'python_trace': r'^\s+File\s+"[^"]+",\s+line\s+\d+',  # Python style
        }
    
    def analyze_log_structure(self, content: str) -> Dict[str, Any]:
        """分析一般 log 的結構"""
        lines = content.split('\n')
        total_lines = len(lines)
        patterns = self.get_patterns()
        
        # 檢測時間戳
        timestamp_count = len(re.findall(patterns['timestamp'], content))
        iso_timestamp_count = len(re.findall(patterns['iso_timestamp'], content))
        has_timestamps = (timestamp_count + iso_timestamp_count) > total_lines * 0.3
        
        # 統計錯誤級別
        error_levels = re.findall(patterns['level'], content, re.IGNORECASE)
        level_counts = {}
        for level in error_levels:
            level = level.upper()
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # 統計錯誤關鍵字
        error_keywords = re.findall(patterns['error_keywords'], content, re.IGNORECASE)
        
        # 檢測堆疊追蹤
        stack_traces = len(re.findall(patterns['stack_trace'], content, re.MULTILINE))
        python_traces = len(re.findall(patterns['python_trace'], content, re.MULTILINE))
        
        # 提取時間範圍
        time_range = self.extract_time_range(content)
        
        return {
            'total_lines': total_lines,
            'has_timestamps': has_timestamps,
            'timestamp_format': 'iso' if iso_timestamp_count > timestamp_count else 'standard',
            'level_counts': level_counts,
            'error_count': len(error_keywords),
            'stack_trace_count': stack_traces + python_traces,
            'file_size_mb': len(content) / (1024 * 1024),
            'time_range': time_range,
            'severity_score': self._calculate_severity_score(level_counts, len(error_keywords)),
        }
    
    def _calculate_severity_score(self, level_counts: Dict[str, int], error_count: int) -> int:
        """計算嚴重程度分數（0-100）"""
        score = 0
        
        # 根據錯誤級別計分
        weights = {
            'FATAL': 20,
            'CRITICAL': 15,
            'ERROR': 10,
            'WARN': 5,
            'WARNING': 5,
        }
        
        for level, count in level_counts.items():
            score += weights.get(level, 0) * min(count, 10)  # 最多計算 10 個
        
        # 錯誤關鍵字加分
        score += min(error_count * 2, 30)
        
        return min(score, 100)
    
    def parse_content(self, content: str, file_path: str, log_info: Dict[str, Any]) -> List[Document]:
        """解析一般 log 內容"""
        documents = []
        
        # 根據嚴重程度選擇解析策略
        severity_score = log_info.get('severity_score', 0)
        
        if severity_score > 50:
            # 高嚴重度：按錯誤分組
            print(f"⚠️  檢測到高嚴重度 log (分數: {severity_score})，使用錯誤分組策略")
            documents = self._parse_by_errors(content, file_path, log_info)
        elif log_info.get('has_timestamps', False):
            # 有時間戳：按時間分組
            print("📅 使用時間分組策略")
            documents = self._parse_by_time_blocks(content, file_path, log_info)
        else:
            # 標準分割
            print("📄 使用標準分割策略")
            documents = self._standard_parse(content, file_path, log_info)
        
        return documents
    
    def _parse_by_errors(self, content: str, file_path: str, log_info: Dict[str, Any]) -> List[Document]:
        """按錯誤分組解析"""
        documents = []
        patterns = self.get_patterns()
        
        # 找出所有錯誤位置
        error_positions = []
        for match in re.finditer(patterns['error_keywords'], content, re.IGNORECASE | re.MULTILINE):
            error_positions.append({
                'pos': match.start(),
                'type': match.group(),
                'line': content[:match.start()].count('\n')
            })
        
        # 為每個錯誤創建上下文文檔
        for i, error_info in enumerate(error_positions):
            # 找到錯誤前後的邊界
            start_pos = max(0, error_info['pos'] - 1000)
            end_pos = min(len(content), error_info['pos'] + 2000)
            
            # 調整到行邊界
            if start_pos > 0:
                start_pos = content.rfind('\n', 0, start_pos) + 1
            if end_pos < len(content):
                end_pos = content.find('\n', end_pos)
                if end_pos == -1:
                    end_pos = len(content)
            
            error_context = content[start_pos:end_pos]
            
            # 檢查是否有堆疊追蹤
            has_stack_trace = bool(re.search(patterns['stack_trace'], error_context)) or \
                            bool(re.search(patterns['python_trace'], error_context))
            
            doc = self.create_document(
                error_context,
                file_path,
                {
                    'chunk_method': 'error_context',
                    'error_index': i,
                    'error_type': error_info['type'],
                    'error_line': error_info['line'],
                    'has_stack_trace': has_stack_trace,
                    'context_type': 'error'
                }
            )
            documents.append(doc)
        
        return documents
    
    def _parse_by_time_blocks(self, content: str, file_path: str, log_info: Dict[str, Any]) -> List[Document]:
        """按時間塊分割"""
        lines = content.split('\n')
        documents = []
        current_block = []
        current_size = 0
        block_start_time = None
        patterns = self.get_patterns()
        
        for line in lines:
            # 檢查時間戳
            timestamp_match = re.search(patterns['timestamp'], line) or \
                            re.search(patterns['iso_timestamp'], line)
            
            if timestamp_match and not block_start_time:
                block_start_time = timestamp_match.group()
            
            current_block.append(line)
            current_size += len(line) + 1
            
            # 檢查是否需要創建新塊
            if current_size >= self.chunk_size and timestamp_match:
                block_content = '\n'.join(current_block)
                
                # 分析此塊的內容
                block_error_count = len(re.findall(patterns['error_keywords'], 
                                                  block_content, re.IGNORECASE))
                
                doc = self.create_document(
                    block_content,
                    file_path,
                    {
                        'chunk_method': 'time_block',
                        'block_start_time': block_start_time,
                        'block_error_count': block_error_count,
                        'context_type': 'temporal'
                    }
                )
                documents.append(doc)
                
                # 保留重疊
                overlap_lines = max(1, self.chunk_overlap // 50)
                current_block = current_block[-overlap_lines:]
                current_size = sum(len(line) + 1 for line in current_block)
                block_start_time = None
        
        # 處理剩餘內容
        if current_block:
            block_content = '\n'.join(current_block)
            doc = self.create_document(
                block_content,
                file_path,
                {
                    'chunk_method': 'time_block_final',
                    'block_start_time': block_start_time,
                    'context_type': 'temporal'
                }
            )
            documents.append(doc)
        
        return documents
    
    def _standard_parse(self, content: str, file_path: str, log_info: Dict[str, Any]) -> List[Document]:
        """標準分割"""
        chunks = self.smart_split(content)
        documents = []
        
        for i, chunk in enumerate(chunks):
            doc = self.create_document(
                chunk,
                file_path,
                {
                    'chunk_method': 'standard',
                    'chunk_index': i,
                    'context_type': 'general'
                }
            )
            documents.append(doc)
        
        return documents