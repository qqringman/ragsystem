import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any
import logging
from config import get_config
from llm.provider_selector import get_llm

# 設定日誌
logger = logging.getLogger(__name__)

def query_database(nl_query: str) -> List[Dict[str, Any]]:
    """
    將自然語言查詢轉換為 SQL 並執行
    
    Args:
        nl_query: 自然語言查詢
        
    Returns:
        查詢結果列表
    """
    try:
        # 獲取 SQL 查詢語句
        sql = nl_to_sql(nl_query)
        logger.info(f"Generated SQL: {sql}")
        
        # 執行查詢
        results = execute_sql(sql)
        return results
        
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}")
        return [{"error": f"查詢失敗: {str(e)}"}]

def nl_to_sql(nl_query: str) -> str:
    """將自然語言轉換為 SQL"""
    # 獲取資料庫結構資訊
    db_schema = get_database_schema()
    db_type = get_config("DB_TYPE", "postgresql")
    
    system_prompt = f"""你是一個資料庫查詢助手。根據以下資料庫結構，將自然語言問題轉換為 SQL 查詢語句。

資料庫結構：
{db_schema}

規則：
1. 只使用上述提到的資料表和欄位
2. 生成的 SQL 必須是有效的 {db_type} 語法
3. 只返回 SQL 語句，不要包含任何解釋
4. 對於聚合查詢，記得使用 GROUP BY
5. 使用適當的 JOIN 來連接相關資料表
"""

    # 使用 LangChain 的 LLM
    llm = get_llm()
    
    # 建構提示
    prompt = f"{system_prompt}\n\n問題：{nl_query}\n\nSQL："
    
    # 獲取 SQL
    sql = llm.predict(prompt).strip()
    
    # 清理 SQL（移除可能的 markdown 標記）
    sql = sql.replace("```sql", "").replace("```", "").strip()
    
    # 基本的 SQL 注入防護
    if any(keyword in sql.upper() for keyword in ["DROP", "DELETE", "TRUNCATE", "ALTER"]):
        raise ValueError("不允許執行危險的 SQL 操作")
    
    return sql

def execute_sql(sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """執行 SQL 查詢"""
    # 獲取資料庫連接參數
    db_config = get_db_config()
    
    # 建立引擎
    engine = create_engine(db_config)
    
    try:
        with engine.connect() as conn:
            # 使用參數化查詢以防止 SQL 注入
            if params:
                result = conn.execute(sqlalchemy.text(sql), params)
            else:
                result = conn.execute(sqlalchemy.text(sql))
            
            # 轉換結果為字典列表
            rows = result.fetchall()
            columns = result.keys()
            
            return [dict(zip(columns, row)) for row in rows]
            
    except SQLAlchemyError as e:
        logger.error(f"SQL execution failed: {str(e)}")
        raise
    finally:
        engine.dispose()

def get_db_config() -> str:
    """獲取資料庫連接字串"""
    db_type = get_config("DB_TYPE", "postgresql")
    user = get_config("DB_USER", "raguser")
    password = get_config("DB_PASSWORD", "ragpass")
    host = get_config("DB_HOST", "localhost")
    port = get_config("DB_PORT", "5432" if db_type == "postgresql" else "3306")
    db_name = get_config("DB_NAME", "ragdb")
    
    # 建構連接字串
    if db_type == "postgresql":
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
    elif db_type == "mysql":
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def create_engine(connection_string: str):
    """創建資料庫引擎"""
    return sqlalchemy.create_engine(
        connection_string,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # 檢查連接是否有效
        echo=False  # 生產環境設為 False
    )

def get_database_schema() -> str:
    """獲取資料庫結構（示例）"""
    # 實際應用中，這應該從資料庫動態讀取
    return """
資料表：
1. products (產品表)
   - id: INTEGER (主鍵)
   - name: VARCHAR(255)
   - price: DECIMAL(10,2)
   - category: VARCHAR(100)
   - stock: INTEGER
   - created_at: TIMESTAMP

2. orders (訂單表)
   - id: INTEGER (主鍵)
   - customer_name: VARCHAR(255)
   - order_date: DATE
   - total_amount: DECIMAL(10,2)
   - status: VARCHAR(50)

3. order_items (訂單明細)
   - id: INTEGER (主鍵)
   - order_id: INTEGER (外鍵 -> orders.id)
   - product_id: INTEGER (外鍵 -> products.id)
   - quantity: INTEGER
   - unit_price: DECIMAL(10,2)
"""

def test_connection() -> bool:
    """測試資料庫連接"""
    try:
        engine = create_engine(get_db_config())
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False