
import os
import sqlalchemy

def query_database(nl_query):
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    system_prompt = (
        "你是一個資料庫查詢助手，根據使用者輸入的自然語言問題，轉換為 SQL 查詢語句。"
        "只針對使用者所提供的資料表欄位做查詢，不要虛構欄位。"
    )

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": nl_query}
        ]
    )
    sql = completion["choices"][0]["message"]["content"]
    print("🔍 SQL:", sql)

    db_type = os.getenv("DB_TYPE", "postgresql")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432" if db_type == "postgresql" else "3306")
    db = os.getenv("DB_NAME")

    engine_url = f"{db_type}://{user}:{password}@{host}:{port}/{db}"
    engine = sqlalchemy.create_engine(engine_url)

    with engine.connect() as conn:
        result = conn.execute(sqlalchemy.text(sql))
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
