"""
使用者介面模組

提供 Streamlit 網頁介面元件和功能
"""

import streamlit as st
from typing import List, Dict, Any, Optional


def display_chat_message(role: str, content: str, avatar: Optional[str] = None):
    """
    顯示聊天訊息
    
    Args:
        role: 角色（user 或 assistant）
        content: 訊息內容
        avatar: 頭像圖標
    """
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)


def create_file_uploader(accept_types: List[str]) -> List:
    """
    創建檔案上傳元件
    
    Args:
        accept_types: 接受的檔案類型列表
        
    Returns:
        上傳的檔案列表
    """
    return st.file_uploader(
        "上傳文件",
        type=accept_types,
        accept_multiple_files=True,
        help="支援多個檔案同時上傳"
    )


def create_sidebar_config() -> Dict[str, Any]:
    """
    創建側邊欄配置介面
    
    Returns:
        配置字典
    """
    with st.sidebar:
        st.header("⚙️ 系統設定")
        
        config = {}
        
        # LLM 設定
        st.subheader("🤖 LLM 設定")
        config["llm_provider"] = st.selectbox(
            "選擇 LLM 提供者",
            ["openai", "claude", "ollama"],
            help="選擇要使用的語言模型"
        )
        
        config["temperature"] = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="控制回答的創造性"
        )
        
        # 向量資料庫設定
        st.subheader("🗄️ 向量資料庫")
        config["vector_db"] = st.selectbox(
            "選擇向量資料庫",
            ["chroma", "redis", "qdrant"],
            help="選擇要使用的向量資料庫"
        )
        
        # 搜尋設定
        st.subheader("🔍 搜尋設定")
        config["search_k"] = st.number_input(
            "搜尋結果數量",
            min_value=1,
            max_value=20,
            value=5,
            help="返回的相關文件數量"
        )
        
        return config


def display_results(results: List[tuple]):
    """
    顯示查詢結果
    
    Args:
        results: 查詢結果列表
    """
    if not results:
        st.info("沒有找到相關資訊")
        return
    
    for idx, result in enumerate(results):
        if isinstance(result, tuple) and len(result) >= 2:
            source_type = result[0]
            answer = result[1]
            extra_info = result[2] if len(result) > 2 else None
            
            # 使用不同的容器顯示不同來源的結果
            with st.container():
                col1, col2 = st.columns([1, 9])
                
                with col1:
                    # 顯示來源圖標
                    if source_type == "docs":
                        st.markdown("📄")
                    elif source_type == "db":
                        st.markdown("🗄️")
                    else:
                        st.markdown("❓")
                
                with col2:
                    st.markdown(f"**{source_type.upper()}**")
                    st.markdown(answer)
                    
                    if extra_info:
                        with st.expander("查看詳細資訊"):
                            if isinstance(extra_info, str):
                                st.text(extra_info)
                            elif isinstance(extra_info, dict):
                                st.json(extra_info)
                            elif isinstance(extra_info, list):
                                for item in extra_info:
                                    st.write(item)
            
            # 分隔線
            if idx < len(results) - 1:
                st.divider()


def show_loading_animation(text: str = "處理中..."):
    """
    顯示載入動畫
    
    Args:
        text: 載入提示文字
    """
    return st.spinner(text)


def create_metrics_dashboard(metrics: Dict[str, Any]):
    """
    創建指標儀表板
    
    Args:
        metrics: 指標字典
    """
    cols = st.columns(len(metrics))
    
    for idx, (label, value) in enumerate(metrics.items()):
        with cols[idx]:
            st.metric(label, value)


# Streamlit 頁面配置預設值
DEFAULT_PAGE_CONFIG = {
    "page_title": "RAG 全功能系統",
    "page_icon": "🧠",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# 主題色彩
THEME_COLORS = {
    "primary": "#0066CC",
    "success": "#00AA00",
    "warning": "#FF9900",
    "error": "#CC0000",
    "info": "#0099CC",
}

# 匯出的公開 API
__all__ = [
    "display_chat_message",
    "create_file_uploader",
    "create_sidebar_config",
    "display_results",
    "show_loading_animation",
    "create_metrics_dashboard",
    "DEFAULT_PAGE_CONFIG",
    "THEME_COLORS",
]