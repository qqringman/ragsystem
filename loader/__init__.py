"""
文件載入器模組

支援載入多種文件格式：
- PDF (.pdf)
- Word (.doc, .docx)
- Excel (.xls, .xlsx)
- Markdown (.md)
- HTML (.html, .htm)
- JSON (.json)
- 純文字 (.txt)
- Log 檔案 (.log) - 支援通用、Android ANR、Android Tombstone
"""

from .doc_parser import load_and_split_documents

# 支援的文件格式
SUPPORTED_EXTENSIONS = [
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".md",
    ".html",
    ".htm",
    ".json",
    ".txt",
    ".log",
]

# 檔案大小限制 (MB)
MAX_FILE_SIZE_MB = 200

# 分割參數預設值
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100

# Log 相關的 chunk size（通常需要更大）
LOG_CHUNK_SIZE = 2000
LOG_CHUNK_OVERLAP = 200


def is_supported_file(filename: str) -> bool:
    """
    檢查檔案是否為支援的格式
    
    Args:
        filename: 檔案名稱
        
    Returns:
        是否支援
    """
    from pathlib import Path
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def is_log_file(filename: str) -> bool:
    """
    檢查是否為 log 檔案
    
    Args:
        filename: 檔案名稱
        
    Returns:
        是否為 log 檔案
    """
    from pathlib import Path
    suffix = Path(filename).suffix.lower()
    stem = Path(filename).stem.lower()
    
    # .log 檔案或檔名包含 log 的 .txt 檔案
    return suffix == ".log" or (suffix == ".txt" and "log" in stem)


# 匯出的公開 API
__all__ = [
    "load_and_split_documents",
    "SUPPORTED_EXTENSIONS",
    "is_supported_file",
    "is_log_file",
    "MAX_FILE_SIZE_MB",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_CHUNK_OVERLAP",
    "LOG_CHUNK_SIZE",
    "LOG_CHUNK_OVERLAP",
]