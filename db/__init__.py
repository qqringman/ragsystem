"""
資料庫查詢模組

提供自然語言轉 SQL 查詢功能，支援：
- PostgreSQL
- MySQL

主要功能：
- 自然語言查詢轉換
- SQL 執行
- 結果格式化
"""

from .sql_executor import (
    query_database,
    nl_to_sql,
    execute_sql,
    get_db_config,
    create_engine,
    get_database_schema,
    test_connection,
)

# 支援的資料庫類型
SUPPORTED_DB_TYPES = ["postgresql", "mysql"]

# 預設資料庫配置
DEFAULT_DB_CONFIG = {
    "DB_TYPE": "postgresql",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_USER": "raguser",
    "DB_PASSWORD": "ragpass",
    "DB_NAME": "ragdb",
}

# 危險的 SQL 關鍵字（用於安全檢查）
DANGEROUS_SQL_KEYWORDS = [
    "DROP",
    "DELETE",
    "TRUNCATE",
    "ALTER",
    "CREATE",
    "REPLACE",
    "INSERT",
    "UPDATE",
]


def is_safe_sql(sql: str) -> bool:
    """
    檢查 SQL 是否安全（不包含危險操作）
    
    Args:
        sql: SQL 語句
        
    Returns:
        是否安全
    """
    sql_upper = sql.upper()
    return not any(keyword in sql_upper for keyword in DANGEROUS_SQL_KEYWORDS)


# 匯出的公開 API
__all__ = [
    "query_database",
    "nl_to_sql",
    "execute_sql",
    "get_db_config",
    "create_engine",
    "get_database_schema",
    "test_connection",
    "SUPPORTED_DB_TYPES",
    "DEFAULT_DB_CONFIG",
    "DANGEROUS_SQL_KEYWORDS",
    "is_safe_sql",
]