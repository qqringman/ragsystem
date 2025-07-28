# -*- coding: utf-8 -*-
import os
import shutil
from loader.doc_parser import load_and_split_documents
from vectorstore.index_manager import get_vectorstore
from llm.provider_selector import get_llm
from utils.highlighter import highlight_chunks
from db.sql_executor import query_database
from config import get_config
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage


class RAGChain:
    """增強的 RAG 鏈，支援對話記憶和多資料來源"""
    
    def __init__(self, memory_window: int = 10):
        """
        初始化 RAG 鏈
        
        Args:
            memory_window: 對話記憶視窗大小
        """
        self.memory = ConversationBufferWindowMemory(
            k=memory_window,
            return_messages=True
        )
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        """初始化 LLM"""
        llm_provider = get_config("LLM_PROVIDER")
        self.llm = get_llm(provider=llm_provider)
    
    def add_to_memory(self, human_input: str, ai_output: str):
        """添加對話到記憶"""
        self.memory.chat_memory.add_user_message(human_input)
        self.memory.chat_memory.add_ai_message(ai_output)
    
    def get_conversation_context(self) -> str:
        """獲取對話上下文"""
        messages = self.memory.chat_memory.messages
        if not messages:
            return ""
        
        context = "之前的對話記錄：\n"
        for msg in messages:
            if isinstance(msg, HumanMessage):
                context += f"用戶：{msg.content}\n"
            elif isinstance(msg, AIMessage):
                context += f"助手：{msg.content}\n"
        
        return context
    
    def run_query(self, query: str, sources: List[str], files: Optional[List[str]] = None) -> List[Tuple[str, str, Any]]:
        """
        執行查詢
        
        Args:
            query: 使用者查詢
            sources: 資料來源列表
            files: 檔案列表（可選）
            
        Returns:
            結果列表，每個結果是 (來源類型, 答案, 額外資訊) 的元組
        """
        results = []
        
        # 獲取對話上下文
        context = self.get_conversation_context()
        
        # 增強查詢（加入對話上下文）
        if context:
            enhanced_query = f"{context}\n\n當前問題：{query}"
        else:
            enhanced_query = query
        
        if "docs" in sources:
            doc_results = self._query_documents(enhanced_query, files)
            if doc_results:
                results.extend(doc_results)
        
        if "db" in sources:
            db_results = self._query_database(query)  # 資料庫查詢使用原始查詢
            if db_results:
                results.extend(db_results)
        
        # 未來可以擴充其他資料來源
        # if "web" in sources:
        #     web_results = self._query_web(query)
        #     if web_results:
        #         results.extend(web_results)
        
        return results
    
    def _query_documents(self, query: str, files: Optional[List[str]] = None) -> List[Tuple[str, str, Any]]:
        """查詢文件"""
        try:
            # 判斷是臨時分析還是知識庫查詢
            if files:
                # 臨時檔案分析模式
                print(f"📊 臨時分析模式：處理 {len(files)} 個檔案")
                
                # 創建臨時向量資料庫
                temp_dir = tempfile.mkdtemp()
                temp_vectorstore_path = os.path.join(temp_dir, "temp_chroma")
                
                try:
                    # 載入文檔
                    docs = load_and_split_documents(files)
                    if not docs:
                        return [("docs", "無法載入檔案內容", None)]
                    
                    # 創建臨時向量資料庫
                    from langchain_community.vectorstores import Chroma
                    from vectorstore.index_manager import get_embeddings
                    
                    embeddings = get_embeddings()
                    temp_vs = Chroma(
                        embedding_function=embeddings,
                        persist_directory=temp_vectorstore_path
                    )
                    
                    # 添加文檔到臨時資料庫
                    temp_vs.add_documents(docs)
                    print(f"✅ 已將 {len(docs)} 個文檔片段加入臨時資料庫")
                    
                    # 使用臨時資料庫進行查詢
                    search_k = int(get_config("SEARCH_K", "5"))
                    rel_docs = temp_vs.similarity_search(query, k=search_k)
                    
                finally:
                    # 清理臨時向量資料庫
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                        print("🧹 已清理臨時向量資料庫")
                        
            else:
                # 知識庫查詢模式
                print("📚 知識庫查詢模式")
                
                # 獲取持久化向量資料庫
                vs = get_vectorstore()
                
                # 從向量資料庫搜尋
                search_k = int(get_config("SEARCH_K", "5"))
                
                try:
                    rel_docs = vs.similarity_search(query, k=search_k)
                except Exception as e:
                    if "collection" in str(e).lower() and "does not exist" in str(e).lower():
                        return [("docs", "知識庫為空，請先建立知識庫", None)]
                    else:
                        raise e
            
            # 處理查詢結果
            if not rel_docs:
                if files:
                    return [("docs", "在上傳的檔案中找不到相關內容", None)]
                else:
                    return [("docs", "在知識庫中找不到相關內容", None)]
            
            print(f"🔍 找到 {len(rel_docs)} 個相關文檔片段")
            
            # 構建上下文
            context = "\n\n---\n\n".join([
                f"文檔 {i+1}:\n{doc.page_content}" 
                for i, doc in enumerate(rel_docs)
            ])
            
            # 檢查是否需要特殊處理
            is_log_analysis = any(
                doc.metadata.get('file_type') == 'log' or 
                doc.metadata.get('log_type') is not None 
                for doc in rel_docs
            )
            
            # 構建提示
            if is_log_analysis:
                prompt = self._build_log_analysis_prompt(query, context, rel_docs)
            else:
                prompt = self._build_general_prompt(query, context)
            
                # 生成答案
                try:
                    raw_answer = self.llm.predict(prompt)
                    
                    # 確保答案是字串
                    if isinstance(raw_answer, str):
                        answer = raw_answer
                    elif hasattr(raw_answer, '__iter__') and not isinstance(raw_answer, str):
                        # 如果是 generator 或其他可迭代物件
                        answer = ''.join(str(chunk) for chunk in raw_answer)
                    else:
                        # 其他情況，轉換為字串
                        answer = str(raw_answer)
                    
                    # 準備相關文檔的元數據
                    highlighted = self._prepare_highlights(rel_docs, is_log_analysis)
                    
                    return [("docs", answer, highlighted)]
                    
                except Exception as e:
                    print(f"❌ LLM 生成答案錯誤：{str(e)}")
                    return [("docs", f"生成答案時發生錯誤：{str(e)}", None)]
            
            # 準備相關文檔的元數據
            highlighted = self._prepare_highlights(rel_docs, is_log_analysis)
            
            return [("docs", answer, highlighted)]
            
        except Exception as e:
            print(f"❌ 文檔查詢錯誤：{str(e)}")
            return [("docs", f"查詢失敗：{str(e)}", None)]
    
    def _query_database(self, query: str) -> List[Tuple[str, str, Any]]:
        """查詢資料庫"""
        try:
            sql_result = query_database(query)
            return [("db", f"查詢結果：{sql_result}", sql_result)]
        except Exception as e:
            return [("db", f"資料庫查詢失敗：{str(e)}", None)]
    
    def _build_general_prompt(self, query: str, context: str) -> str:
        """構建一般查詢提示"""
        return f"""你是一個智能助手，請根據提供的文檔內容回答問題。

相關文檔內容：
{context}

問題：{query}

請提供準確、相關的答案。如果內容中包含具體的數據或事實，請引用它們。
如果文檔中沒有相關資訊，請明確說明。"""
    
    def _build_log_analysis_prompt(self, query: str, context: str, docs: List) -> str:
        """構建 Log 分析提示"""
        log_types = set(doc.metadata.get('log_type', 'general') for doc in docs if doc.metadata.get('log_type'))
        
        if 'android_anr' in log_types:
            return f"""你是 Android ANR 分析專家。請根據以下 ANR trace 內容回答問題：

問題：{query}

ANR Trace 內容：
{context}

請提供：
1. ANR 的直接原因
2. 受影響的線程（特別是主線程）
3. 可能的優化建議
4. 如果有死鎖風險，請特別指出"""
        
        elif 'android_tombstone' in log_types:
            return f"""你是 Android 崩潰分析專家。請根據以下 tombstone 內容回答問題：

問題：{query}

Tombstone 內容：
{context}

請提供：
1. 崩潰的根本原因
2. 崩潰類型（如空指針、記憶體錯誤等）
3. 關鍵的 backtrace 解釋
4. 修復建議"""
        
        else:
            return f"""你是 Log 分析專家。請根據以下 log 內容回答問題：

問題：{query}

Log 內容：
{context}

請提供詳細的分析，包括：
1. 問題的直接答案
2. 相關的錯誤或異常
3. 可能的原因分析
4. 建議的解決方案"""
    
    def _prepare_highlights(self, docs: List, is_log_analysis: bool) -> List[Dict[str, Any]]:
        """準備高亮顯示的文檔"""
        highlighted = []
        
        for doc in docs:
            doc_info = {
                'content': doc.page_content,
                'source': doc.metadata.get('source', ''),
                'score': doc.metadata.get('score', 0)
            }
            
            # 添加特殊的 log 元數據
            if is_log_analysis:
                if doc.metadata.get('chunk_type'):
                    doc_info['chunk_type'] = doc.metadata['chunk_type']
                if doc.metadata.get('severity'):
                    doc_info['severity'] = doc.metadata['severity']
                if doc.metadata.get('error_count'):
                    doc_info['error_count'] = doc.metadata['error_count']
                if doc.metadata.get('crash_type'):
                    doc_info['crash_type'] = doc.metadata['crash_type']
            
            highlighted.append(doc_info)
        
        return highlighted


# 全局 RAG 實例
_rag_chain = None


def get_rag_chain() -> RAGChain:
    """獲取 RAG 鏈實例（單例模式）"""
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = RAGChain()
    return _rag_chain


def run_rag(query: str, sources: List[str], files: Optional[List[str]] = None) -> List[Tuple[str, str, Any]]:
    """
    執行 RAG 查詢
    
    Args:
        query: 查詢問題
        sources: 資料來源列表 ['docs', 'db', 'web', ...]
        files: 新檔案列表（可選）
        
    Returns:
        結果列表，每個結果是 (來源類型, 答案, 額外資訊) 的元組
    """
    rag_chain = get_rag_chain()
    results = rag_chain.run_query(query, sources, files)
    
    # 如果有成功的結果，更新對話記憶
    if results:
        combined_answer = ""
        for result in results:
            if isinstance(result, tuple) and len(result) >= 2:
                source_type = result[0]
                answer = result[1]
                if answer and not answer.startswith("查詢失敗"):
                    if combined_answer:
                        combined_answer += f"\n\n[來源: {source_type.upper()}]\n"
                    combined_answer += answer
        
        if combined_answer:
            rag_chain.add_to_memory(query, combined_answer)
    
    return results


def run_query(query: str, sources: List[str], files: Optional[List[str]] = None) -> List[Tuple[str, str, Any]]:
    """向後兼容的別名"""
    return run_rag(query, sources, files)