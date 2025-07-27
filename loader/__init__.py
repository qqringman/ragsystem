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
]

# 檔案大小限制 (MB)
MAX_FILE_SIZE_MB = 200

# 分割參數預設值
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100


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


# 匯出的公開 API
__all__ = [
    "load_and_split_documents",
    "SUPPORTED_EXTENSIONS",
    "is_supported_file",
    "MAX_FILE_SIZE_MB",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_CHUNK_OVERLAP",
]