# -*- coding: utf-8 -*-
from rag_chain import run_rag
from dotenv import load_dotenv
import sys

load_dotenv()

print("🔍 正在執行的 Python 版本:", sys.executable)

if __name__ == "__main__":
    query = input("請輸入問題: ")
    sources = ["docs"]  # ✅ 或 ["db"] 或 ["docs", "db"]，根據你要的資料來源
    result = run_rag(query, sources)
    for src, answer, highlighted in result:
        print(f"\n🧠 來源：{src}")
        print("📌 回答：", answer)
