# -*- coding: utf-8 -*-
import os
from pathlib import Path
import streamlit as st
from rag_chain import run_rag
import tempfile
import sys
import json
from datetime import datetime

# 配置系統會自動載入 .env
from config import get_config, validate_config

# 驗證配置
try:
    validate_config()
except ValueError as e:
    st.error(f"配置錯誤: {e}")
    st.stop()

print("🔍 正在執行的 Python 版本:", sys.executable)

st.set_page_config(page_title="RAG 全功能系統", layout="wide")
st.title("🧠 RAG 問答引擎")

# 初始化 session state
if 'indexed_files' not in st.session_state:
    st.session_state.indexed_files = []
if 'vector_db_initialized' not in st.session_state:
    st.session_state.vector_db_initialized = False

# 側邊欄 - 向量資料庫管理
with st.sidebar:
    st.markdown("### 📚 向量資料庫狀態")
    
    # 檢查已索引的檔案
    index_file = "vector_db/indexed_files.json"
    if os.path.exists(index_file):
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                indexed_data = json.load(f)
                st.session_state.indexed_files = indexed_data.get('files', [])
        except:
            st.session_state.indexed_files = []
    
    if st.session_state.indexed_files:
        st.success(f"已索引 {len(st.session_state.indexed_files)} 個檔案")
        with st.expander("查看已索引檔案"):
            for file_info in st.session_state.indexed_files:
                st.write(f"📄 {file_info['name']} ({file_info['date']})")
    else:
        st.info("向量資料庫為空")
    
    # 清理向量資料庫按鈕
    if st.button("🗑️ 清空向量資料庫"):
        import shutil
        chroma_path = get_config("CHROMA_PERSIST_DIR", "vector_db/chroma")
        if os.path.exists(chroma_path):
            shutil.rmtree(chroma_path)
            os.makedirs(chroma_path, exist_ok=True)
        if os.path.exists(index_file):
            os.remove(index_file)
        st.session_state.indexed_files = []
        st.rerun()
    
    st.markdown("---")
    
    # 系統資訊
    st.markdown("### 🔧 系統資訊")
    st.markdown(f"Python 版本: {sys.version.split()[0]}")
    
    # 顯示環境變數狀態
    st.markdown("### 🔑 API 設定狀態")
    llm_provider = os.getenv("LLM_PROVIDER", "未設定")
    st.markdown(f"LLM Provider: `{llm_provider}`")
    
    # 檢查 API 金鑰
    if llm_provider == "openai":
        api_key_set = bool(os.getenv("OPENAI_API_KEY"))
        st.markdown(f"OpenAI API Key: {'✅ 已設定' if api_key_set else '❌ 未設定'}")
    elif llm_provider in ["claude", "anthropic"]:
        api_key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
        st.markdown(f"Anthropic API Key: {'✅ 已設定' if api_key_set else '❌ 未設定'}")

# 主要內容區域
col1, col2 = st.columns([2, 1])

with col1:
    # 輸入查詢
    query = st.text_input("請輸入你的問題：", placeholder="例如：分析最近的錯誤日誌")

with col2:
    # 選擇資料來源
    data_source = st.multiselect("請選擇資料來源", ["docs", "db"], default=["docs"])

# 檔案上傳區域
st.markdown("### 📤 上傳新檔案（可選）")
uploaded_files = st.file_uploader(
    "上傳文件到向量資料庫（支援 .pdf, .docx, .xlsx, .log, .txt 等）", 
    type=["pdf", "docx", "doc", "txt", "md", "html", "htm", "xlsx", "xls", "json", "log", "csv"], 
    accept_multiple_files=True,
    help="上傳的檔案會被永久加入向量資料庫，之後查詢時不需要重新上傳"
)

# 處理上傳的檔案
if uploaded_files:
    with st.spinner("正在處理並索引檔案..."):
        temp_files = []
        temp_dir = tempfile.mkdtemp()
        
        for uploaded_file in uploaded_files:
            # 將上傳的檔案保存到臨時目錄
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            temp_files.append(temp_path)
        
        # 索引檔案到向量資料庫
        try:
            from loader.doc_parser import load_and_split_documents
            from vectorstore.index_manager import get_vectorstore
            
            # 載入和分割文件
            docs = load_and_split_documents(temp_files)
            
            if docs:
                # 加入到向量資料庫
                vs = get_vectorstore()
                vs.add_documents(docs)
                
                # 更新已索引檔案列表
                new_files = []
                for uploaded_file in uploaded_files:
                    file_info = {
                        'name': uploaded_file.name,
                        'size': uploaded_file.size,
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    new_files.append(file_info)
                    st.session_state.indexed_files.append(file_info)
                
                # 保存索引記錄
                os.makedirs("vector_db", exist_ok=True)
                with open(index_file, 'w', encoding='utf-8') as f:
                    json.dump({'files': st.session_state.indexed_files}, f, ensure_ascii=False, indent=2)
                
                st.success(f"✅ 成功索引 {len(uploaded_files)} 個檔案到向量資料庫")
                st.info("這些檔案已永久保存，之後的查詢會自動包含這些內容")
            else:
                st.warning("無法載入檔案內容")
                
        except Exception as e:
            st.error(f"索引檔案時發生錯誤：{str(e)}")
        finally:
            # 清理臨時檔案
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass

# 查詢按鈕
if st.button("🔍 查詢", type="primary", use_container_width=True):
    if not query:
        st.warning("請輸入查詢問題")
    else:
        # 檢查是否有已索引的檔案或新上傳的檔案
        if not st.session_state.indexed_files and "docs" in data_source:
            st.warning("向量資料庫為空，請先上傳檔案或選擇其他資料來源")
        else:
            with st.spinner("正在查詢..."):
                try:
                    # 執行查詢（不需要傳遞檔案，因為已經在向量資料庫中）
                    results = run_rag(query, sources=data_source, files=None)
                    
                    if results and isinstance(results, list):
                        # 處理每個結果
                        for idx, result in enumerate(results):
                            if isinstance(result, tuple) and len(result) >= 2:
                                source_type = result[0]
                                answer = result[1]
                                extra_info = result[2] if len(result) > 2 else None
                                
                                # 顯示主要答案
                                if idx == 0:  # 只在第一個結果顯示標題
                                    st.markdown("### 💬 回答")
                                
                                # 根據來源類型顯示不同的圖標
                                icon = "📄" if source_type == "docs" else "🗄️"
                                st.markdown(f"{icon} **{source_type.upper()}**: {answer}")
                                
                                # 顯示額外資訊
                                if extra_info:
                                    with st.expander(f"查看詳細資訊 - {source_type}"):
                                        if source_type == "docs":
                                            st.markdown("**相關內容：**")
                                            if isinstance(extra_info, list):
                                                for item in extra_info[:3]:
                                                    st.markdown(f"- {item.get('content', str(item))[:200]}...")
                                            else:
                                                st.markdown(extra_info)
                                                
                                        elif source_type == "db":
                                            st.markdown("**資料庫查詢結果：**")
                                            if isinstance(extra_info, str):
                                                st.code(extra_info)
                                            else:
                                                st.json(extra_info)
                                
                                # 在結果之間加入分隔線
                                if idx < len(results) - 1:
                                    st.divider()
                    else:
                        st.info("沒有找到相關資訊")
                        
                except Exception as e:
                    st.error(f"處理查詢時發生錯誤：{str(e)}")
                    st.exception(e)

# 使用說明
with st.expander("📋 使用說明", expanded=False):
    st.markdown("""
    ### 向量資料庫持久化功能
    
    1. **首次使用**：上傳您的文件（PDF、Word、Excel、Log 等）
    2. **檔案會被永久索引**：上傳的檔案會被處理並存入向量資料庫
    3. **之後查詢**：不需要重新上傳，直接輸入問題即可
    4. **新增檔案**：隨時可以上傳新檔案來擴充知識庫
    5. **清空資料**：使用側邊欄的「清空向量資料庫」按鈕重新開始
    
    ### 支援的檔案類型
    - 文檔：PDF, Word (.docx, .doc), Markdown (.md)
    - 資料：Excel (.xlsx, .xls), CSV, JSON
    - 日誌：.log, .txt
    - 網頁：HTML
    
    ### 查詢技巧
    - 可以直接詢問關於已索引檔案的任何問題
    - 支援中文查詢
    - 可以要求分析、總結或比較檔案內容
    """)