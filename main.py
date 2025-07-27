# -*- coding: utf-8 -*-
from rag_chain import run_rag
from config import get_config, validate_config
import sys

print("🔍 正在執行的 Python 版本:", sys.executable)

def main():
    """主程式入口"""
    try:
        # 驗證配置
        validate_config()
        print("✅ 配置驗證通過")
        
        # 顯示當前配置
        print("\n📋 當前配置:")
        print(f"  LLM Provider: {get_config('LLM_PROVIDER')}")
        print(f"  Vector DB: {get_config('VECTOR_DB')}")
        print(f"  Embed Provider: {get_config('EMBED_PROVIDER')}")
        
    except ValueError as e:
        print(f"❌ 配置錯誤: {e}")
        print("\n請檢查 .env 檔案是否正確設定")
        return
    
    # 主要邏輯
    while True:
        print("\n" + "="*50)
        query = input("請輸入問題 (輸入 'quit' 退出): ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 再見！")
            break
        
        if not query:
            print("⚠️  請輸入有效的問題")
            continue
        
        # 選擇資料來源
        print("\n選擇資料來源:")
        print("1. 只搜尋文件 (docs)")
        print("2. 只查詢資料庫 (db)")
        print("3. 兩者都使用 (docs + db)")
        
        choice = input("請選擇 (1/2/3，預設為 1): ").strip() or "1"
        
        sources = []
        if choice == "1":
            sources = ["docs"]
        elif choice == "2":
            sources = ["db"]
        elif choice == "3":
            sources = ["docs", "db"]
        else:
            print("⚠️  無效的選擇，使用預設值")
            sources = ["docs"]
        
        # 檔案上傳（可選）
        files = []
        if "docs" in sources:
            upload_choice = input("\n是否要上傳檔案？(y/N): ").strip().lower()
            if upload_choice == 'y':
                while True:
                    filepath = input("請輸入檔案路徑 (輸入空白結束): ").strip()
                    if not filepath:
                        break
                    if os.path.exists(filepath):
                        files.append(filepath)
                        print(f"✅ 已加入: {filepath}")
                    else:
                        print(f"❌ 檔案不存在: {filepath}")
        
        # 執行查詢
        print(f"\n🔍 正在查詢...")
        print(f"   資料來源: {sources}")
        if files:
            print(f"   檔案數量: {len(files)}")
        
        try:
            result = run_rag(query, sources, files)
            
            if result:
                print("\n📊 查詢結果:")
                for idx, (src, answer, highlighted) in enumerate(result):
                    print(f"\n{'='*50}")
                    print(f"🧠 來源：{src.upper()}")
                    print(f"📌 回答：{answer}")
                    
                    if highlighted and src == "docs":
                        print("\n📄 相關段落:")
                        if isinstance(highlighted, str):
                            print(f"   {highlighted[:200]}...")
                        elif isinstance(highlighted, list):
                            for i, h in enumerate(highlighted[:3]):  # 只顯示前3個
                                if isinstance(h, dict):
                                    content = h.get('content', '')
                                    print(f"   {i+1}. {content[:100]}...")
                                else:
                                    print(f"   {i+1}. {str(h)[:100]}...")
            else:
                print("\n❌ 沒有找到相關資訊")
                
        except Exception as e:
            print(f"\n❌ 查詢失敗: {str(e)}")
            import traceback
            if get_config("LOG_LEVEL") == "DEBUG":
                traceback.print_exc()


if __name__ == "__main__":
    import os
    
    # 顯示歡迎訊息
    print("🤖 RAG 問答系統")
    print("=" * 50)
    
    # 執行主程式
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程式被中斷，再見！")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        if get_config("LOG_LEVEL") == "DEBUG":
            import traceback
            traceback.print_exc()