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
    return run_query(query, sources, files)
    
def run_query(query, sources, files=None):
    results = []

    if "docs" in sources and files:
        try:
            # 載入文件
            docs = load_and_split_documents(files)
            
            # 獲取向量資料庫
            vs = get_vectorstore()
            vs.add_documents(docs)
            
            # 搜尋相關文件
            search_k = int(get_config("SEARCH_K", "5"))
            rel_docs = vs.similarity_search(query, k=search_k)
            
            # 使用 LLM 生成答案
            llm_provider = get_config("LLM_PROVIDER")
            llm = get_llm(provider=llm_provider)
            
            # 構建提示
            context = "\n\n".join([d.page_content for d in rel_docs])
            prompt = f"根據以下內容回答問題：{query}\n\n內容：\n{context}"
            
            answer = llm.predict(prompt)
            highlighted = highlight_chunks(answer, rel_docs)
            results.append(("docs", answer, highlighted))
            
        except Exception as e:
            if "object of type 'int' has no len()" in str(e):
                print("⚠️  檢測到 ChromaDB 資料庫損壞，正在重建...")
                
                # 清理損壞的資料庫
                chroma_path = get_config("CHROMA_PERSIST_DIR", "vector_db/chroma")
                if os.path.exists(chroma_path):
                    shutil.rmtree(chroma_path)
                    os.makedirs(chroma_path, exist_ok=True)
                
                # 重試
                try:
                    vs = get_vectorstore()
                    vs.add_documents(docs)
                    
                    rel_docs = vs.similarity_search(query, k=search_k)
                    context = "\n\n".join([d.page_content for d in rel_docs])
                    prompt = f"根據以下內容回答問題：{query}\n\n內容：\n{context}"
                    
                    answer = llm.predict(prompt)
                    highlighted = highlight_chunks(answer, rel_docs)
                    results.append(("docs", answer, highlighted))
                    print("✅ 資料庫已重建並成功查詢")
                except Exception as retry_error:
                    results.append(("docs", f"查詢失敗：{str(retry_error)}", None))
            else:
                raise e

    if "db" in sources:
        sql_result = query_database(query)
        results.append(("db", f"查詢結果：{sql_result}", sql_result))

    return results