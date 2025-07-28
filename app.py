# -*- coding: utf-8 -*-
import os
from pathlib import Path
import streamlit as st
from rag_chain import run_rag
import tempfile
import sys
import json
from datetime import datetime
import redis
import uuid
from typing import List, Dict, Any, Optional

# 配置系統會自動載入 .env
from config import get_config, validate_config

# 驗證配置
try:
    validate_config()
except ValueError as e:
    st.error(f"配置錯誤: {e}")
    st.stop()

print("🔍 正在執行的 Python 版本:", sys.executable)

# 配置頁面
st.set_page_config(
    page_title="RAG 智能助手",
    # page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定義 CSS - Claude.ai 風格
st.markdown("""
<style>
    /* 主容器樣式 */
    .main {
        padding-top: 2rem;
    }
    
    /* 聊天輸入框樣式 */
    .stTextArea textarea {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 15px;
        font-size: 16px;
        resize: none;
    }
    
    .stTextArea textarea:focus {
        border-color: #4a90e2;
        box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
    }
    
    /* 按鈕樣式 */
    .stButton > button {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* 訊息容器樣式 */
    .message-container {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        background-color: #f8f9fa;
    }
    
    /* 來源標籤樣式 */
    .source-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
        margin-right: 5px;
    }
    
    .source-docs { background-color: #e3f2fd; color: #1976d2; }
    .source-web { background-color: #fff3cd; color: #856404; }
    .source-db { background-color: #e8f5e9; color: #2e7d32; }
    .source-jira { background-color: #f3e5f5; color: #7b1fa2; }
    
    /* 檔案上傳區域 */
    .upload-area {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s;
    }
    
    .upload-area:hover {
        border-color: #4a90e2;
        background-color: #f0f7ff;
    }
    
    /* 側邊欄樣式 */
    .css-1d391kg {
        padding-top: 3rem;
    }
    
    /* 對話歷史樣式 */
    .chat-history {
        max-height: 600px;
        overflow-y: auto;
        padding-right: 10px;
    }
    
    /* 工具選擇器 */
    .tool-selector {
        display: flex;
        gap: 10px;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }
    
    .tool-chip {
        padding: 6px 12px;
        border-radius: 20px;
        border: 1px solid #ddd;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .tool-chip:hover {
        background-color: #f0f0f0;
    }
    
    .tool-chip.selected {
        background-color: #4a90e2;
        color: white;
        border-color: #4a90e2;
    }
</style>
""", unsafe_allow_html=True)

# 初始化 session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'indexed_files' not in st.session_state:
    st.session_state.indexed_files = []
if 'selected_sources' not in st.session_state:
    st.session_state.selected_sources = ['docs']
if 'uploaded_files_processed' not in st.session_state:
    st.session_state.uploaded_files_processed = set()

# Redis 連接（用於 session 管理）
@st.cache_resource
def get_redis_client():
    try:
        r = redis.Redis(
            host=get_config("REDIS_HOST", "localhost"),
            port=int(get_config("REDIS_PORT", "6379")),
            decode_responses=True
        )
        r.ping()
        return r
    except:
        return None

redis_client = get_redis_client()

# 側邊欄 - 知識庫管理
with st.sidebar:
    st.markdown("## 🧠 知識庫管理")
    
    # 標籤頁
    tab1, tab2, tab3 = st.tabs(["📚 文件管理", "🔌 資料來源", "⚙️ 設定"])
    
    with tab1:
        st.markdown("### 已索引的檔案")
        
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
            
            # 檔案列表
            for idx, file_info in enumerate(st.session_state.indexed_files):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(f"📄 {file_info['name']}")
                    st.caption(f"{file_info['date']} | {file_info['size'] / 1024 / 1024:.1f} MB")
                with col2:
                    if st.button("🗑️", key=f"del_{idx}"):
                        # TODO: 實作刪除功能
                        st.warning("刪除功能開發中")
        else:
            st.info("知識庫為空")
        
        # 上傳新檔案
        st.markdown("### 新增到知識庫")
        kb_files = st.file_uploader(
            "拖放或選擇檔案",
            type=["pdf", "docx", "doc", "txt", "md", "html", "htm", "xlsx", "xls", "json", "log", "csv"],
            accept_multiple_files=True,
            key="kb_uploader"
        )
        
        if kb_files and st.button("📥 加入知識庫", type="primary", use_container_width=True):
            with st.spinner("正在處理並索引檔案..."):
                temp_files = []
                temp_dir = tempfile.mkdtemp()
                
                for uploaded_file in kb_files:
                    temp_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    temp_files.append(temp_path)
                
                try:
                    from loader.doc_parser import load_and_split_documents
                    from vectorstore.index_manager import get_vectorstore
                    
                    docs = load_and_split_documents(temp_files)
                    if docs:
                        vs = get_vectorstore()
                        vs.add_documents(docs)
                        
                        # 更新索引記錄
                        for uploaded_file in kb_files:
                            file_info = {
                                'name': uploaded_file.name,
                                'size': uploaded_file.size,
                                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            st.session_state.indexed_files.append(file_info)
                        
                        os.makedirs("vector_db", exist_ok=True)
                        with open(index_file, 'w', encoding='utf-8') as f:
                            json.dump({'files': st.session_state.indexed_files}, f, ensure_ascii=False, indent=2)
                        
                        st.success(f"✅ 成功索引 {len(kb_files)} 個檔案")
                        st.rerun()
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
        
        # 清理向量資料庫
        if st.button("🗑️ 清空知識庫", use_container_width=True):
            if st.checkbox("確認清空所有知識庫資料"):
                import shutil
                chroma_path = get_config("CHROMA_PERSIST_DIR", "vector_db/chroma")
                if os.path.exists(chroma_path):
                    shutil.rmtree(chroma_path)
                    os.makedirs(chroma_path, exist_ok=True)
                if os.path.exists(index_file):
                    os.remove(index_file)
                st.session_state.indexed_files = []
                st.rerun()
    
    with tab2:
        st.markdown("### 資料來源設定")
        st.info("🚧 開發中：支援連接 Jira、Wiki、Outlook 等")
        
        # 預留擴充介面
        st.markdown("#### 可用的資料來源")
        
        sources = {
            "docs": {"name": "📄 文件庫", "enabled": True},
            "db": {"name": "🗄️ 資料庫", "enabled": True},
            "web": {"name": "🌐 網路搜尋", "enabled": False, "badge": "即將推出"},
            "jira": {"name": "📋 Jira", "enabled": False, "badge": "即將推出"},
            "wiki": {"name": "📖 Wiki", "enabled": False, "badge": "即將推出"},
            "outlook": {"name": "📧 Outlook", "enabled": False, "badge": "即將推出"}
        }
        
        for source_id, source_info in sources.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"{source_info['name']}")
                if 'badge' in source_info:
                    st.caption(source_info['badge'])
            with col2:
                if source_info['enabled']:
                    st.toggle("啟用", value=True, key=f"source_{source_id}")
                else:
                    st.toggle("啟用", value=False, disabled=True, key=f"source_{source_id}")
    
    with tab3:
        st.markdown("### 系統設定")
        
        # LLM 設定
        llm_provider = st.selectbox(
            "LLM 提供者",
            ["openai", "claude", "ollama"],
            index=["openai", "claude", "ollama"].index(get_config("LLM_PROVIDER", "ollama"))
        )
        
        # 向量資料庫設定
        vector_db = st.selectbox(
            "向量資料庫",
            ["chroma", "redis", "qdrant"],
            index=["chroma", "redis", "qdrant"].index(get_config("VECTOR_DB", "chroma"))
        )
        
        # 搜尋設定
        search_k = st.number_input(
            "搜尋結果數量",
            min_value=1,
            max_value=20,
            value=int(get_config("SEARCH_K", "5"))
        )
        
        # 對話記憶設定
        st.markdown("#### 對話設定")
        enable_memory = st.toggle("啟用對話記憶", value=True)
        if enable_memory:
            memory_window = st.slider(
                "記憶視窗大小",
                min_value=1,
                max_value=20,
                value=10,
                help="保留最近幾輪對話作為上下文"
            )

# 主要內容區域
st.markdown("# 🤖 RAG 智能助手")

# 來源選擇器（類似 Claude.ai）
st.markdown("### 🔍 搜尋來源")
cols = st.columns(6)
source_options = [
    ("docs", "📄 文件", True),
    ("db", "🗄️ 資料庫", True),
    ("web", "🌐 網路", False),
    ("jira", "📋 Jira", False),
    ("wiki", "📖 Wiki", False),
    ("outlook", "📧 Outlook", False)
]

selected_sources = []
for idx, (source_id, source_name, enabled) in enumerate(source_options):
    with cols[idx]:
        if enabled:
            if st.checkbox(source_name, value=source_id in st.session_state.selected_sources, key=f"src_{source_id}"):
                selected_sources.append(source_id)
        else:
            st.checkbox(source_name, value=False, disabled=True, key=f"src_{source_id}_disabled")
            st.caption("即將推出")

st.session_state.selected_sources = selected_sources if selected_sources else ["docs"]

# 對話歷史區域
chat_container = st.container()
with chat_container:
    # 顯示對話歷史
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message.get("avatar")):
            st.markdown(message["content"])
            
            # 如果有來源資訊，顯示來源標籤
            if "sources" in message:
                source_html = ""
                for source in message["sources"]:
                    source_html += f'<span class="source-tag source-{source}">{source.upper()}</span>'
                st.markdown(source_html, unsafe_allow_html=True)

# 輸入區域
input_container = st.container()
with input_container:
    # 檔案上傳區（可選）
    with st.expander("📎 附加檔案（可選）", expanded=False):
        uploaded_files = st.file_uploader(
            "拖放檔案到這裡，或點擊瀏覽",
            type=["pdf", "docx", "doc", "txt", "md", "html", "htm", "xlsx", "xls", "json", "log", "csv"],
            accept_multiple_files=True,
            key="temp_uploader",
            help="這些檔案只會用於本次對話，不會保存到知識庫"
        )
        
        if uploaded_files:
            st.info(f"已附加 {len(uploaded_files)} 個檔案")
    
    # 聊天輸入
    query = st.chat_input(
        "輸入你的問題...",
        key="chat_input"
    )

# 處理使用者輸入
if query:
    # 添加使用者訊息
    st.session_state.messages.append({
        "role": "user",
        "content": query,
        "avatar": "🧑‍💻"
    })
    
    # 重新顯示使用者訊息
    with chat_container:
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(query)
    
    # 處理查詢
    with chat_container:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("思考中..."):
                # 準備檔案
                temp_files = []
                if uploaded_files:
                    temp_dir = tempfile.mkdtemp()
                    for uploaded_file in uploaded_files:
                        # 只處理新上傳的檔案
                        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                        if file_id not in st.session_state.uploaded_files_processed:
                            temp_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            temp_files.append(temp_path)
                            st.session_state.uploaded_files_processed.add(file_id)
                
                # 構建對話上下文
                context_messages = []
                if len(st.session_state.messages) > 1:
                    # 取最近的對話作為上下文
                    recent_messages = st.session_state.messages[-10:]  # 最多10輪
                    for msg in recent_messages[:-1]:  # 不包括當前訊息
                        context_messages.append(f"{msg['role']}: {msg['content']}")
                
                # 構建增強的查詢
                enhanced_query = query
                if context_messages:
                    context = "\n".join(context_messages)
                    enhanced_query = f"根據以下對話歷史：\n{context}\n\n當前問題：{query}"
                
                try:
                    # 執行查詢
                    results = run_rag(
                        enhanced_query,
                        sources=st.session_state.selected_sources,
                        files=temp_files if temp_files else None
                    )
                    
                    if results and isinstance(results, list):
                        # 整合所有來源的答案
                        combined_answer = ""
                        used_sources = []
                        
                        for result in results:
                            if isinstance(result, tuple) and len(result) >= 2:
                                source_type = result[0]
                                answer = result[1]
                                
                                if answer and not answer.startswith("沒有找到") and not answer.startswith("無法"):
                                    if combined_answer:
                                        combined_answer += "\n\n"
                                    combined_answer += answer
                                    used_sources.append(source_type)
                        
                        if combined_answer:
                            st.markdown(combined_answer)
                            
                            # 顯示來源標籤
                            if used_sources:
                                source_html = "資料來源："
                                for source in set(used_sources):
                                    source_html += f'<span class="source-tag source-{source}">{source.upper()}</span>'
                                st.markdown(source_html, unsafe_allow_html=True)
                            
                            # 保存助手回應
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": combined_answer,
                                "avatar": "🤖",
                                "sources": list(set(used_sources))
                            })
                        else:
                            no_result_msg = "抱歉，在選定的資料來源中沒有找到相關資訊。"
                            st.info(no_result_msg)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": no_result_msg,
                                "avatar": "🤖"
                            })
                    else:
                        error_msg = "查詢過程中發生錯誤，請稍後再試。"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg,
                            "avatar": "🤖"
                        })
                        
                except Exception as e:
                    error_msg = f"處理查詢時發生錯誤：{str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "avatar": "🤖"
                    })
                    
                    if get_config("LOG_LEVEL") == "DEBUG":
                        import traceback
                        st.code(traceback.format_exc())
                
                finally:
                    # 清理臨時檔案
                    for temp_file in temp_files:
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    if temp_files:
                        try:
                            os.rmdir(temp_dir)
                        except:
                            pass
    
    # 保存對話到 Redis（如果可用）
    if redis_client:
        try:
            session_key = f"rag_session:{st.session_state.session_id}"
            redis_client.setex(
                session_key,
                86400,  # 24小時過期
                json.dumps(st.session_state.messages, ensure_ascii=False)
            )
        except:
            pass

# 底部資訊
with st.expander("ℹ️ 使用說明", expanded=False):
    st.markdown("""
    ### 🎯 功能特點
    
    - **多資料來源**：可同時從文件庫、資料庫等多個來源查詢
    - **對話記憶**：系統會記住對話上下文，支援連續對話
    - **即時分析**：可上傳檔案進行即時分析，無需加入知識庫
    - **智能搜尋**：自動選擇最相關的資訊來源回答問題
    
    ### 💡 使用技巧
    
    1. **選擇資料來源**：勾選你想要搜尋的資料來源
    2. **上傳檔案**：可選擇性上傳檔案進行分析
    3. **自然對話**：像聊天一樣提問，系統會理解上下文
    4. **知識庫管理**：在側邊欄管理永久知識庫
    
    ### ⌨️ 快捷鍵
    
    - `Enter`：發送訊息
    - `Shift + Enter`：換行
    - `Ctrl/Cmd + K`：清空對話（開發中）
    """)

# 側邊欄摺疊按鈕
if st.button("☰", key="sidebar_toggle", help="切換側邊欄"):
    st.write('<script>document.querySelector(".css-1d391kg").classList.toggle("collapsed")</script>', unsafe_allow_html=True)