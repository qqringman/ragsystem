
import streamlit as st

st.set_page_config(page_title="RAG 全功能系統", layout="wide")

st.title("📚 RAG 多來源問答系統")

with st.sidebar:
    st.header("選擇資料來源")
    use_docs = st.checkbox("📄 文件", value=True)
    use_db = st.checkbox("🗃️ 資料庫", value=False)

    st.markdown("---")
    uploaded_files = st.file_uploader("上傳文件", accept_multiple_files=True, type=["pdf", "docx", "md", "html", "json", "xlsx"])

    st.markdown("---")
    st.text_input("🔑 查詢關鍵字", key="query")

if st.session_state.query:
    st.write(f"開始查詢：`{st.session_state.query}` ...")
    st.success("（此處省略）回傳查詢結果與來源段落")

