# utils/logger.py - 統一日誌管理
from loguru import logger
import sys

logger.remove()
logger.add(
    sys.stderr,
    format="{time} {level} {message}",
    level="INFO"
)
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days"
)