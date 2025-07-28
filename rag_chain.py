# -*- coding: utf-8 -*-
import os
import shutil
from loader.doc_parser import load_and_split_documents
from vectorstore.index_manager import get_vectorstore
from llm.provider_selector import get_llm
from utils.highlighter import highlight_chunks
from db.sql_executor import query_database
from config import get_config

def run_rag(query, sources, files=None):
    """
    執行 RAG 查詢
    
    Args:
        query: 查詢問題
        sources: 資料來源列表 ['docs', 'db']
        files: 新檔案列表（可選）
    """
    return run_query(query, sources, files)
    
def run_query(query, sources, files=None):
    results = []

    if "docs" in sources:
        try:
            # 獲取向量資料庫
            vs = get_vectorstore()
            
            # 如果有新檔案，先加入到向量資料庫
            if files:
                print(f"📥 載入 {len(files)} 個新檔案...")
                docs = load_and_split_documents(files)
                if docs:
                    vs.add_documents(docs)
                    print(f"✅ 已將 {len(docs)} 個文檔片段加入向量資料庫")
            
            # 從向量資料庫搜尋（包含所有已索引的內容）
            search_k = int(get_config("SEARCH_K", "5"))
            
            # 嘗試搜尋
            try:
                rel_docs = vs.similarity_search(query, k=search_k)
            except Exception as e:
                if "collection" in str(e).lower() and "does not exist" in str(e).lower():
                    # 向量資料庫為空
                    results.append(("docs", "向量資料庫為空，請先上傳檔案", None))
                    return results
                else:
                    raise e
            
            if not rel_docs:
                results.append(("docs", "找不到相關文件", None))
                return results
            
            print(f"🔍 找到 {len(rel_docs)} 個相關文檔片段")
            
            # 使用 LLM 生成答案
            llm_provider = get_config("LLM_PROVIDER")
            llm = get_llm(provider=llm_provider)
            
            # 構建提示
            context = "\n\n---\n\n".join([
                f"文檔 {i+1}:\n{doc.page_content}" 
                for i, doc in enumerate(rel_docs)
            ])
            
            # 根據查詢類型調整提示
            if any(keyword in query.lower() for keyword in ['分析', '總結', '摘要', 'analyze', 'summary']):
                prompt = f"""請根據以下文檔內容，對問題進行詳細分析：

問題：{query}

相關文檔內容：
{context}

請提供：
1. 主要發現
2. 詳細分析
3. 可能的建議或結論
"""
            elif any(keyword in query.lower() for keyword in ['錯誤', 'error', 'exception', 'warning', '警告']):
                prompt = f"""請分析以下文檔中的錯誤或問題：

問題：{query}

相關文檔內容：
{context}

請識別：
1. 錯誤類型和頻率
2. 可能的原因
3. 建議的解決方案
"""
            else:
                prompt = f"""根據以下內容回答問題：

問題：{query}

相關內容：
{context}

請提供準確、相關的答案。如果內容中包含具體的數據或事實，請引用它們。
"""
            
            answer = llm.predict(prompt)
            highlighted = highlight_chunks(answer, rel_docs)
            results.append(("docs", answer, highlighted))
            
        except Exception as e:
            print(f"❌ 文檔查詢錯誤：{str(e)}")
            
            # 處理資料庫損壞的情況
            if "object of type 'int' has no len()" in str(e):
                print("⚠️  檢測到 ChromaDB 資料庫損壞，正在重建...")
                
                # 清理損壞的資料庫
                chroma_path = get_config("CHROMA_PERSIST_DIR", "vector_db/chroma")
                if os.path.exists(chroma_path):
                    shutil.rmtree(chroma_path)
                    os.makedirs(chroma_path, exist_ok=True)
                
                results.append(("docs", "向量資料庫已重置，請重新上傳檔案", None))
            else:
                results.append(("docs", f"查詢失敗：{str(e)}", None))

    if "db" in sources:
        try:
            sql_result = query_database(query)
            results.append(("db", f"查詢結果：{sql_result}", sql_result))
        except Exception as e:
            results.append(("db", f"資料庫查詢失敗：{str(e)}", None))

    return results