import os
from pathlib import Path
import streamlit as st
from rag_chain import run_rag
import tempfile
from dotenv import load_dotenv
import sys

load_dotenv()

print("🔍 正在執行的 Python 版本:", sys.executable)

st.set_page_config(page_title="RAG 全功能系統", layout="wide")
st.title("🧠 RAG 問答引擎")

# 輸入查詢
query = st.text_input("請輸入你的問題：")

# 上傳檔案
uploaded_files = st.file_uploader(
    "上傳文件（支援 .pdf, .docx, .xlsx 等）", 
    type=["pdf", "docx", "doc", "txt", "md", "html", "htm", "xlsx", "xls", "json"], 
    accept_multiple_files=True
)

# 選擇資料來源
data_source = st.multiselect("請選擇資料來源", ["docs", "db"], default=["docs"])

# 處理上傳的檔案
temp_files = []
if uploaded_files:
    # 創建臨時目錄
    temp_dir = tempfile.mkdtemp()
    
    for uploaded_file in uploaded_files:
        # 將上傳的檔案保存到臨時目錄
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        temp_files.append(temp_path)
        
    # 顯示已上傳的檔案
    st.success(f"已上傳 {len(uploaded_files)} 個檔案")

# 查詢按鈕
if st.button("查詢"):
    if not query:
        st.warning("請輸入查詢問題")
    else:
        with st.spinner("正在查詢..."):
            try:
                # 執行查詢
                results = run_rag(query, sources=data_source, files=temp_files)
                
                # 調試資訊（生產環境可移除）
                print(f"DEBUG - results type: {type(results)}")
                print(f"DEBUG - results content: {results}")
                
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
                                        st.markdown("**重點摘要：**")
                                        st.markdown(extra_info)
                                        
                                        # 顯示檔案來源
                                        if uploaded_files:
                                            st.markdown("**來源文件：**")
                                            for f in uploaded_files:
                                                st.write(f"- {f.name}")
                                                
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
                            # 處理意外格式
                            st.warning(f"收到未預期的回應格式: {type(result)}")
                            st.write(result)
                else:
                    st.info("沒有找到相關資訊")
                    
            except Exception as e:
                st.error(f"處理查詢時發生錯誤：{str(e)}")
                st.exception(e)
            finally:
                # 清理臨時檔案
                if temp_files:
                    for temp_file in temp_files:
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    try:
                        os.rmdir(temp_dir)
                    except:
                        pass

# 側邊欄資訊
with st.sidebar:
    st.markdown("### 📋 使用說明")
    st.markdown("""
    1. 輸入您的問題
    2. （可選）上傳相關文件
    3. 選擇資料來源：
       - **docs**: 搜尋文件
       - **db**: 查詢資料庫
    4. 點擊「查詢」按鈕
    """)
    
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