"""
日誌管理模組

提供統一的日誌記錄功能
"""

import os
import sys
from loguru import logger
from pathlib import Path

# 移除預設的 logger
logger.remove()

# 獲取日誌級別
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 日誌格式
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# 簡單格式（用於生產環境）
SIMPLE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"

# 確保日誌目錄存在
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 配置控制台輸出
logger.add(
    sys.stderr,
    format=LOG_FORMAT if os.getenv("TESTING") else SIMPLE_FORMAT,
    level=LOG_LEVEL,
    colorize=True,
)

# 配置檔案輸出
logger.add(
    "logs/app.log",
    rotation="10 MB",      # 當檔案達到 10MB 時輪換
    retention="10 days",   # 保留 10 天
    compression="zip",     # 壓縮舊日誌
    level=LOG_LEVEL,
    format=SIMPLE_FORMAT,
    encoding="utf-8",
)

# 錯誤日誌單獨記錄
logger.add(
    "logs/error.log",
    rotation="5 MB",
    retention="30 days",
    compression="zip",
    level="ERROR",
    format=LOG_FORMAT,
    encoding="utf-8",
    backtrace=True,       # 記錄完整的錯誤追蹤
    diagnose=True,        # 記錄變數值
)

# 為不同模組創建 logger
def get_logger(name: str):
    """
    獲取特定模組的 logger
    
    Args:
        name: 模組名稱
        
    Returns:
        配置好的 logger
    """
    return logger.bind(name=name)


# 日誌裝飾器
def log_function_call(func):
    """
    記錄函數調用的裝飾器
    
    Usage:
        @log_function_call
        def my_function(arg1, arg2):
            pass
    """
    def wrapper(*args, **kwargs):
        logger.debug(f"調用函數 {func.__name__} | args: {args} | kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函數 {func.__name__} 執行成功")
            return result
        except Exception as e:
            logger.error(f"函數 {func.__name__} 執行失敗: {str(e)}")
            raise
    return wrapper


# 性能監控裝飾器
def log_performance(func):
    """
    記錄函數執行時間的裝飾器
    
    Usage:
        @log_performance
        def slow_function():
            pass
    """
    import time
    
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"函數 {func.__name__} 執行時間: {duration:.2f} 秒")
        
        if duration > 5:  # 超過 5 秒的警告
            logger.warning(f"函數 {func.__name__} 執行時間過長: {duration:.2f} 秒")
        
        return result
    return wrapper


# 匯出
__all__ = [
    "logger",
    "get_logger",
    "log_function_call",
    "log_performance",
]