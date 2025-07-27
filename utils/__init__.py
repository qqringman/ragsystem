"""
工具函數模組

提供各種輔助功能：
- 文字高亮
- 日誌記錄
- 檔案處理
- 錯誤處理
"""

from .highlighter import highlight_chunks
from .logger import logger

import os
import hashlib
from typing import List, Optional
from pathlib import Path


def calculate_file_hash(filepath: str) -> str:
    """
    計算檔案的 MD5 雜湊值
    
    Args:
        filepath: 檔案路徑
        
    Returns:
        MD5 雜湊值
    """
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def ensure_directory(path: str) -> Path:
    """
    確保目錄存在，如果不存在則創建
    
    Args:
        path: 目錄路徑
        
    Returns:
        Path 物件
    """
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def clean_temp_files(temp_dir: str, pattern: str = "*") -> int:
    """
    清理臨時檔案
    
    Args:
        temp_dir: 臨時目錄
        pattern: 檔案模式（預設為所有檔案）
        
    Returns:
        刪除的檔案數量
    """
    temp_path = Path(temp_dir)
    if not temp_path.exists():
        return 0
    
    count = 0
    for file in temp_path.glob(pattern):
        if file.is_file():
            try:
                file.unlink()
                count += 1
            except Exception as e:
                logger.error(f"無法刪除檔案 {file}: {e}")
    
    return count


def format_file_size(size_bytes: int) -> str:
    """
    格式化檔案大小為人類可讀格式
    
    Args:
        size_bytes: 檔案大小（位元組）
        
    Returns:
        格式化的大小字串
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def sanitize_filename(filename: str) -> str:
    """
    清理檔案名稱，移除不安全字元
    
    Args:
        filename: 原始檔案名稱
        
    Returns:
        安全的檔案名稱
    """
    # 移除路徑分隔符號和其他不安全字元
    unsafe_chars = ['/', '\\', '..', '~', '|', ':', '*', '?', '"', '<', '>', '|']
    safe_filename = filename
    for char in unsafe_chars:
        safe_filename = safe_filename.replace(char, '_')
    
    # 確保不是空字串
    return safe_filename or "unnamed_file"


# 匯出的公開 API
__all__ = [
    "highlight_chunks",
    "logger",
    "calculate_file_hash",
    "ensure_directory",
    "clean_temp_files",
    "format_file_size",
    "sanitize_filename",
]