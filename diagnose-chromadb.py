#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChromaDB 診斷工具
診斷並修復 ChromaDB 權限和連接問題
"""

import os
import sys
import stat
import json
import subprocess
from pathlib import Path

# 顏色輸出
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_color(msg, color=Colors.BLUE):
    print(f"{color}{msg}{Colors.END}")

def check_directory_permissions():
    """檢查目錄權限"""
    print_color("\n1. 檢查目錄權限", Colors.YELLOW)
    
    dirs_to_check = [
        "vector_db",
        "vector_db/chroma",
        "uploads",
        "logs"
    ]
    
    for dir_path in dirs_to_check:
        if os.path.exists(dir_path):
            # 獲取權限
            st = os.stat(dir_path)
            mode = stat.filemode(st.st_mode)
            
            # 檢查是否可寫
            if os.access(dir_path, os.W_OK):
                print_color(f"✓ {dir_path}: {mode} (可寫入)", Colors.GREEN)
            else:
                print_color(f"✗ {dir_path}: {mode} (不可寫入)", Colors.RED)
                
                # 嘗試修復
                try:
                    os.chmod(dir_path, 0o777)
                    print_color(f"  → 已嘗試修復權限", Colors.YELLOW)
                except:
                    print_color(f"  → 無法修復，需要 sudo 權限", Colors.RED)
        else:
            print_color(f"✗ {dir_path}: 不存在", Colors.RED)
            try:
                os.makedirs(dir_path, exist_ok=True)
                os.chmod(dir_path, 0o777)
                print_color(f"  → 已創建目錄", Colors.GREEN)
            except Exception as e:
                print_color(f"  → 創建失敗: {e}", Colors.RED)

def check_chromadb_files():
    """檢查 ChromaDB 檔案"""
    print_color("\n2. 檢查 ChromaDB 檔案", Colors.YELLOW)
    
    chroma_dir = "vector_db/chroma"
    if os.path.exists(chroma_dir):
        files = list(Path(chroma_dir).rglob("*"))
        
        if not files:
            print_color("ChromaDB 目錄是空的（正常）", Colors.BLUE)
        else:
            for file_path in files:
                if file_path.is_file():
                    st = os.stat(file_path)
                    mode = stat.filemode(st.st_mode)
                    
                    if os.access(file_path, os.W_OK):
                        print_color(f"✓ {file_path}: {mode} (可寫入)", Colors.GREEN)
                    else:
                        print_color(f"✗ {file_path}: {mode} (不可寫入)", Colors.RED)
                        
                        # 如果是 SQLite 檔案，檢查是否損壞
                        if str(file_path).endswith('.sqlite3'):
                            print_color(f"  → 這是 SQLite 資料庫檔案", Colors.YELLOW)
                            
                            # 嘗試修復權限
                            try:
                                os.chmod(file_path, 0o666)
                                print_color(f"  → 已嘗試修復權限", Colors.YELLOW)
                            except:
                                print_color(f"  → 無法修復，需要 sudo 權限", Colors.RED)

def test_chromadb_connection():
    """測試 ChromaDB 連接"""
    print_color("\n3. 測試 ChromaDB 連接", Colors.YELLOW)
    
    try:
        # 設置環境變數
        os.environ["CHROMA_TELEMETRY"] = "false"
        os.environ["ANONYMIZED_TELEMETRY"] = "false"
        
        # 嘗試導入並創建 ChromaDB
        import chromadb
        from chromadb.config import Settings
        
        settings = Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="vector_db/chroma",
            anonymized_telemetry=False
        )
        
        client = chromadb.Client(settings)
        
        # 嘗試創建或獲取集合
        collection = client.get_or_create_collection("test_collection")
        
        # 嘗試添加一個測試文檔
        collection.add(
            documents=["This is a test document"],
            metadatas=[{"source": "test"}],
            ids=["test_id"]
        )
        
        # 嘗試查詢
        results = collection.query(
            query_texts=["test"],
            n_results=1
        )
        
        print_color("✓ ChromaDB 連接成功！", Colors.GREEN)
        
        # 清理測試數據
        collection.delete(ids=["test_id"])
        
    except Exception as e:
        print_color(f"✗ ChromaDB 連接失敗: {str(e)}", Colors.RED)
        
        # 提供具體的解決建議
        if "readonly database" in str(e):
            print_color("\n問題：資料庫是唯讀的", Colors.RED)
            print_color("解決方案：", Colors.YELLOW)
            print("1. sudo chmod -R 777 vector_db")
            print("2. 或刪除並重建：rm -rf vector_db/chroma && mkdir -p vector_db/chroma")
        elif "No such file or directory" in str(e):
            print_color("\n問題：找不到必要的檔案", Colors.RED)
            print_color("解決方案：", Colors.YELLOW)
            print("mkdir -p vector_db/chroma && chmod -R 777 vector_db")

def check_docker_environment():
    """檢查 Docker 環境"""
    print_color("\n4. 檢查 Docker 環境", Colors.YELLOW)
    
    # 檢查是否在 Docker 內
    if os.path.exists("/.dockerenv"):
        print_color("✓ 在 Docker 容器內運行", Colors.GREEN)
        
        # 檢查用戶資訊
        import pwd
        user_info = pwd.getpwuid(os.getuid())
        print(f"  用戶: {user_info.pw_name} (UID: {os.getuid()}, GID: {os.getgid()})")
        
    else:
        print_color("在本地環境運行", Colors.BLUE)
        
        # 檢查 Docker 容器是否運行
        try:
            result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
            if "rag-app" in result.stdout:
                print_color("✓ Docker 容器 rag-app 正在運行", Colors.GREEN)
                
                # 檢查容器內的權限
                result = subprocess.run(
                    ["docker", "exec", "rag-app", "ls", "-la", "/app/vector_db"],
                    capture_output=True,
                    text=True
                )
                print("容器內 vector_db 權限：")
                print(result.stdout)
        except:
            print_color("Docker 未安裝或未運行", Colors.YELLOW)

def provide_solutions():
    """提供解決方案"""
    print_color("\n5. 建議的解決方案", Colors.YELLOW)
    
    print("\n方案 1：快速修復（推薦）")
    print("```bash")
    print("# 停止容器")
    print("docker-compose stop app")
    print("")
    print("# 修復權限")
    print("sudo chmod -R 777 vector_db uploads logs")
    print("")
    print("# 重啟容器")
    print("docker-compose up -d app")
    print("```")
    
    print("\n方案 2：完全重置")
    print("```bash")
    print("# 停止並刪除容器")
    print("docker-compose down")
    print("")
    print("# 刪除舊數據")
    print("rm -rf vector_db/chroma")
    print("")
    print("# 重新創建目錄")
    print("mkdir -p vector_db/chroma")
    print("chmod -R 777 vector_db")
    print("")
    print("# 重新啟動")
    print("docker-compose up -d")
    print("```")
    
    print("\n方案 3：使用 docker-compose.override.yml")
    print("創建 docker-compose.override.yml 檔案：")
    print("```yaml")
    print("version: '3.8'")
    print("services:")
    print("  app:")
    print("    user: root")
    print("```")

def main():
    print_color("🔧 ChromaDB 診斷工具", Colors.BLUE)
    print("=" * 50)
    
    # 執行檢查
    check_directory_permissions()
    check_chromadb_files()
    test_chromadb_connection()
    check_docker_environment()
    provide_solutions()
    
    print_color("\n診斷完成！", Colors.GREEN)

if __name__ == "__main__":
    main()