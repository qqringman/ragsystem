"""
Log 解析器管理器

自動識別和分配適當的 log 解析器
"""

from typing import List, Optional, Type
from pathlib import Path
from .base_log_parser import BaseLogParser
from .general_log_parser import GeneralLogParser
from .android_anr_parser import AndroidANRParser
from .android_tombstone_parser import AndroidTombstoneParser


class LogParserManager:
    """Log 解析器管理器"""
    
    def __init__(self):
        """初始化管理器"""
        # 註冊所有可用的解析器（優先順序由高到低）
        self.parsers: List[Type[BaseLogParser]] = [
            AndroidANRParser,        # Android ANR
            AndroidTombstoneParser,  # Android Tombstone
            GeneralLogParser,        # 通用 log（放最後作為 fallback）
        ]
    
    def parse_log_file(self, file_path: str) -> List:
        """
        自動識別並解析 log 檔案
        
        Args:
            file_path: log 檔案路徑
            
        Returns:
            Document 列表
        """
        # 讀取檔案樣本用於識別
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 讀取前 5000 字符作為樣本
                content_sample = f.read(5000)
        except Exception as e:
            print(f"❌ 無法讀取檔案 {file_path}: {e}")
            return []
        
        # 嘗試每個解析器
        for parser_class in self.parsers:
            parser = parser_class()
            
            # 檢查是否能解析
            if parser.can_parse(file_path, content_sample):
                print(f"🔍 使用 {parser.get_log_type()} 解析器處理: {Path(file_path).name}")
                
                # 執行解析
                try:
                    documents = parser.parse_log_file(file_path)
                    if documents:
                        print(f"✅ 成功解析為 {len(documents)} 個片段")
                        return documents
                except Exception as e:
                    print(f"⚠️ {parser.get_log_type()} 解析失敗: {e}")
                    # 繼續嘗試下一個解析器
                    continue
        
        # 如果沒有解析器能處理，使用通用解析器作為最後手段
        print(f"⚠️ 無特定解析器匹配，使用通用解析器")
        general_parser = GeneralLogParser()
        return general_parser.parse_log_file(file_path)
    
    def get_available_parsers(self) -> List[str]:
        """獲取所有可用的解析器類型"""
        return [parser().get_log_type() for parser in self.parsers]
    
    def add_parser(self, parser_class: Type[BaseLogParser], priority: int = -1):
        """
        添加新的解析器
        
        Args:
            parser_class: 解析器類
            priority: 優先級位置（-1 表示最後）
        """
        if priority == -1:
            # 插入到通用解析器之前
            self.parsers.insert(-1, parser_class)
        else:
            self.parsers.insert(priority, parser_class)


# 全局實例
log_parser_manager = LogParserManager()