#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試中文嵌入模型
直接運行: python quick_test_chinese.py
"""

import sys
import time
from sentence_transformers import SentenceTransformer

def test_chinese_embedding():
    """測試中文嵌入模型"""
    print("="*50)
    print("🇨🇳 中文嵌入模型測試")
    print("="*50)
    
    # 1. 載入模型
    print("\n1️⃣ 正在載入模型 shibing624/text2vec-base-chinese...")
    print("   首次使用會自動下載（約 400MB），請耐心等待...")
    
    start_time = time.time()
    try:
        model = SentenceTransformer('shibing624/text2vec-base-chinese')
        load_time = time.time() - start_time
        print(f"   ✅ 模型載入成功！耗時: {load_time:.2f} 秒")
    except Exception as e:
        print(f"   ❌ 模型載入失敗: {str(e)}")
        print("\n   可能的解決方案:")
        print("   1. 檢查網路連接")
        print("   2. 使用代理或鏡像站")
        print("   3. 手動下載模型")
        return False
    
    # 2. 測試文本嵌入
    print("\n2️⃣ 測試中文文本嵌入...")
    test_sentences = [
        "人工智慧正在改變我們的生活方式",
        "機器學習是實現人工智慧的重要技術",
        "深度學習使用神經網路來處理複雜問題",
        "自然語言處理讓電腦能夠理解人類語言",
        "今天的天氣非常晴朗",
        "我喜歡吃中式料理"
    ]
    
    start_time = time.time()
    embeddings = model.encode(test_sentences)
    encode_time = time.time() - start_time
    
    print(f"   ✅ 成功編碼 {len(test_sentences)} 個句子")
    print(f"   ⏱️  編碼耗時: {encode_time:.2f} 秒")
    print(f"   📊 向量維度: {embeddings.shape}")
    
    # 3. 測試語義相似度
    print("\n3️⃣ 測試語義相似度搜尋...")
    query = "AI 和機器學習的關係"
    print(f"   查詢: '{query}'")
    
    query_embedding = model.encode([query])[0]
    
    # 計算相似度
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    
    # 排序並顯示結果
    print("\n   相似度排名:")
    sorted_idx = similarities.argsort()[::-1]
    for i, idx in enumerate(sorted_idx):
        print(f"   {i+1}. {test_sentences[idx]}")
        print(f"      相似度: {similarities[idx]:.4f}")
    
    # 4. 測試繁簡轉換
    print("\n4️⃣ 測試繁簡體混合處理...")
    mixed_texts = [
        "機器學習幫助我們解決問題",  # 簡體
        "機器學習幫助我們解決問題",  # 繁體
        "人工智能と機械学習",        # 混合日文
    ]
    
    try:
        mixed_embeddings = model.encode(mixed_texts)
        print("   ✅ 成功處理繁簡體混合文本")
        
        # 檢查繁簡體的語義相似度
        sim = cosine_similarity([mixed_embeddings[0]], [mixed_embeddings[1]])[0][0]
        print(f"   📊 繁簡體相似度: {sim:.4f} (應該接近 1.0)")
    except Exception as e:
        print(f"   ⚠️  混合文本處理警告: {str(e)}")
    
    # 5. 效能統計
    print("\n5️⃣ 效能統計:")
    print(f"   - 模型載入時間: {load_time:.2f} 秒")
    print(f"   - 平均編碼速度: {len(test_sentences)/encode_time:.2f} 句/秒")
    print(f"   - 向量維度: {embeddings.shape[1]}")
    
    print("\n" + "="*50)
    print("✅ 測試完成！中文嵌入模型運作正常")
    print("="*50)
    
    return True


def test_rag_integration():
    """測試與 RAG 系統的整合"""
    print("\n\n🔗 測試 RAG 系統整合...")
    
    try:
        # 設定環境變數
        import os
        os.environ['EMBED_PROVIDER'] = 'huggingface'
        os.environ['HUGGINGFACE_MODEL'] = 'shibing624/text2vec-base-chinese'
        
        # 測試載入
        from vectorstore.index_manager import get_embeddings
        embeddings = get_embeddings()
        
        # 測試嵌入功能
        test_text = "檢索增強生成技術"
        vector = embeddings.embed_query(test_text)
        
        print(f"✅ RAG 整合測試成功！")
        print(f"   - 成功載入嵌入模型")
        print(f"   - 成功生成向量 (維度: {len(vector)})")
        
    except ImportError:
        print("⚠️  無法導入 RAG 模組，請確保在專案目錄中運行")
    except Exception as e:
        print(f"❌ RAG 整合測試失敗: {str(e)}")


if __name__ == "__main__":
    # 檢查依賴
    try:
        import sentence_transformers
        import sklearn
    except ImportError as e:
        print(f"❌ 缺少必要的套件: {e}")
        print("請先安裝: pip install sentence-transformers scikit-learn")
        sys.exit(1)
    
    # 執行測試
    success = test_chinese_embedding()
    
    if success:
        test_rag_integration()
        
        print("\n💡 下一步:")
        print("1. 在 .env 中設定: HUGGINGFACE_MODEL=shibing624/text2vec-base-chinese")
        print("2. 運行 RAG 系統: streamlit run app.py")
        print("3. 上傳中文文檔進行測試")