
from loader.doc_parser import load_and_split_documents
from vectorstore.index_manager import get_vectorstore
from llm.provider_selector import get_llm
from utils.highlighter import highlight_chunks
from db.sql_executor import query_database

def run_rag(query, sources, files=None):
    return run_query(query, sources, files)
	
def run_query(query, sources, files=None):
    results = []

    if "docs" in sources and files:
        docs = load_and_split_documents(files)
        vs = get_vectorstore()
        vs.add_documents(docs)
        rel_docs = vs.similarity_search(query)
        llm = get_llm(provider="claude")
        answer = llm.predict(f"根據以下內容回答：{query}\n\n" + "\n\n".join([d.page_content for d in rel_docs]))
        highlighted = highlight_chunks(answer, rel_docs)
        results.append(("docs", answer, highlighted))

    if "db" in sources:
        sql_result = query_database(query)
        results.append(("db", f"查詢結果：{sql_result}", sql_result))

    return results
