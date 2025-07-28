# -*- coding: utf-8 -*-
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime
import tempfile
import os
import asyncio
from pathlib import Path

# 導入現有的 RAG 功能
from rag_chain import run_rag
from loader.doc_parser import load_and_split_documents
from vectorstore.index_manager import get_vectorstore
from config import get_config, validate_config
import redis

# 驗證配置
try:
    validate_config()
except ValueError as e:
    print(f"配置錯誤: {e}")
    exit(1)

# 創建 FastAPI 應用
app = FastAPI(title="RAG 智能助手 API", version="1.0.0")

# CORS 設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境請設置具體域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis 連接
redis_client = None
try:
    redis_client = redis.Redis(
        host=get_config("REDIS_HOST", "localhost"),
        port=int(get_config("REDIS_PORT", "6379")),
        decode_responses=True
    )
    redis_client.ping()
except:
    print("警告：Redis 連接失敗，將無法保存對話歷史")

# 資料模型
class ChatMessage(BaseModel):
    role: str
    content: str
    sources: Optional[List[str]] = None
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    query: str
    sources: List[str] = ["docs"]
    session_id: Optional[str] = None
    context_messages: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str

class IndexedFile(BaseModel):
    name: str
    size: int
    date: str
    id: str

# 全局變量
connected_clients: Dict[str, WebSocket] = {}
sessions: Dict[str, List[ChatMessage]] = {}

# API 端點

@app.get("/")
async def read_root():
    """返回前端頁面"""
    return FileResponse('static/index.html')

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """處理聊天請求"""
    try:
        # 生成或使用 session_id
        session_id = request.session_id or str(uuid.uuid4())
        
        # 構建對話上下文
        enhanced_query = request.query
        if request.context_messages:
            # 過濾有效的訊息
            valid_messages = []
            for msg in request.context_messages[-10:]:  # 最多10輪
                if hasattr(msg, 'role') and hasattr(msg, 'content'):
                    valid_messages.append(f"{msg.role}: {msg.content}")
                elif isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    valid_messages.append(f"{msg['role']}: {msg['content']}")
            
            if valid_messages:
                context = "\n".join(valid_messages)
                enhanced_query = f"根據以下對話歷史：\n{context}\n\n當前問題：{request.query}"
        
        # 記錄請求信息
        print(f"📨 收到查詢請求:")
        print(f"   Session ID: {session_id}")
        print(f"   Query: {request.query}")
        print(f"   Sources: {request.sources}")
        
        # 執行 RAG 查詢
        try:
            results = run_rag(
                enhanced_query,
                sources=request.sources,
                files=None
            )
        except Exception as rag_error:
            print(f"❌ RAG 執行錯誤: {str(rag_error)}")
            import traceback
            traceback.print_exc()
            
            # 返回友好的錯誤訊息
            return ChatResponse(
                answer=f"抱歉，處理您的請求時發生錯誤：{str(rag_error)}",
                sources=[],
                session_id=session_id
            )
        
        # 檢查結果類型
        if not results:
            print("⚠️ RAG 返回空結果")
            return ChatResponse(
                answer="抱歉，沒有找到相關資訊。",
                sources=[],
                session_id=session_id
            )
        
        if not isinstance(results, list):
            print(f"❌ RAG 返回了非預期的結果類型: {type(results)}")
            results = []  # 設為空列表以避免後續錯誤
        
        # 整合結果
        combined_answer = ""
        used_sources = []
        error_messages = []
        
        for result in results:
            try:
                # 檢查結果格式
                if isinstance(result, tuple) and len(result) >= 2:
                    source_type = str(result[0])
                    
                    # 確保 answer 是字串
                    raw_answer = result[1]
                    if isinstance(raw_answer, str):
                        answer = raw_answer
                    elif hasattr(raw_answer, '__iter__') and not isinstance(raw_answer, str):
                        # 如果是 generator 或其他可迭代物件
                        answer = ''.join(str(chunk) for chunk in raw_answer)
                    else:
                        answer = str(raw_answer)
                    
                    # 檢查是否為錯誤訊息
                    if answer and not answer.startswith("沒有找到") and not answer.startswith("無法") and not answer.startswith("查詢失敗"):
                        if combined_answer:
                            combined_answer += "\n\n"
                        combined_answer += answer
                        used_sources.append(source_type)
                    else:
                        # 收集錯誤訊息
                        error_messages.append(f"{source_type}: {answer}")
                        print(f"⚠️ {source_type} 查詢失敗: {answer}")
                else:
                    print(f"⚠️ 無效的結果格式: {result}")
            except Exception as result_error:
                print(f"❌ 處理結果時發生錯誤: {str(result_error)}")
                continue
        
        # 如果沒有成功的結果，但有錯誤訊息
        if not combined_answer and error_messages:
            combined_answer = "查詢過程中遇到以下問題：\n" + "\n".join(error_messages)
        elif not combined_answer:
            combined_answer = "抱歉，在選定的資料來源中沒有找到相關資訊。"
        
        # 保存到 Redis（如果可用）
        if redis_client:
            try:
                session_key = f"rag_session:{session_id}"
                
                # 準備要保存的訊息
                messages_to_save = []
                if request.context_messages:
                    for msg in request.context_messages:
                        if hasattr(msg, 'dict'):
                            messages_to_save.append(msg.dict())
                        elif isinstance(msg, dict):
                            messages_to_save.append(msg)
                        else:
                            # 嘗試轉換為字典
                            try:
                                messages_to_save.append({
                                    'role': getattr(msg, 'role', 'unknown'),
                                    'content': getattr(msg, 'content', str(msg))
                                })
                            except:
                                pass
                
                # 添加當前的問答
                messages_to_save.append({
                    'role': 'user',
                    'content': request.query,
                    'timestamp': datetime.now().isoformat()
                })
                messages_to_save.append({
                    'role': 'assistant',
                    'content': combined_answer,
                    'sources': list(set(used_sources)),
                    'timestamp': datetime.now().isoformat()
                })
                
                session_data = {
                    "messages": messages_to_save,
                    "last_update": datetime.now().isoformat()
                }
                
                redis_client.setex(
                    session_key,
                    86400,  # 24小時過期
                    json.dumps(session_data, ensure_ascii=False)
                )
                print(f"✅ 已保存對話到 Redis: {session_key}")
            except Exception as redis_error:
                print(f"⚠️ 保存到 Redis 失敗: {str(redis_error)}")
                # Redis 錯誤不應該影響主要功能
                pass
        
        # 返回結果
        response = ChatResponse(
            answer=combined_answer,
            sources=list(set(used_sources)),
            session_id=session_id
        )
        
        print(f"✅ 成功返回回應:")
        print(f"   Sources: {response.sources}")
        print(f"   Answer length: {len(response.answer)} chars")
        
        return response
        
    except ValueError as ve:
        # 處理值錯誤（如配置問題）
        print(f"❌ 值錯誤: {str(ve)}")
        raise HTTPException(
            status_code=400, 
            detail=f"請求參數錯誤：{str(ve)}"
        )
    except Exception as e:
        # 處理其他未預期的錯誤
        print(f"❌ 未預期的錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 返回通用錯誤訊息給用戶
        raise HTTPException(
            status_code=500, 
            detail=f"服務器內部錯誤：{str(e)}"
        )

@app.post("/api/chat/upload")
async def chat_with_files(
    query: str,
    sources: List[str] = ["docs"],
    files: List[UploadFile] = File(None),
    session_id: Optional[str] = None
):
    """處理帶檔案的聊天請求"""
    try:
        temp_files = []
        temp_dir = None
        
        # 處理上傳的檔案
        if files:
            temp_dir = tempfile.mkdtemp()
            for file in files:
                if file.filename:  # 確保有檔案
                    temp_path = os.path.join(temp_dir, file.filename)
                    content = await file.read()
                    with open(temp_path, "wb") as f:
                        f.write(content)
                    temp_files.append(temp_path)
        
        # 執行 RAG 查詢
        results = run_rag(
            query,
            sources=sources,
            files=temp_files if temp_files else None
        )
        
        # 整合結果（同上）
        combined_answer = ""
        used_sources = []
        
        if results and isinstance(results, list):
            for result in results:
                if isinstance(result, tuple) and len(result) >= 2:
                    source_type = result[0]
                    answer = result[1]
                    
                    if answer and not answer.startswith("沒有找到") and not answer.startswith("無法"):
                        if combined_answer:
                            combined_answer += "\n\n"
                        combined_answer += answer
                        used_sources.append(source_type)
        
        if not combined_answer:
            combined_answer = "抱歉，在選定的資料來源中沒有找到相關資訊。"
        
        return ChatResponse(
            answer=combined_answer,
            sources=list(set(used_sources)),
            session_id=session_id or str(uuid.uuid4())
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理臨時檔案
        if temp_files:
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
        if temp_dir:
            try:
                os.rmdir(temp_dir)
            except:
                pass

@app.get("/api/knowledge-base/files")
async def get_indexed_files():
    """獲取已索引的檔案列表"""
    index_file = "vector_db/indexed_files.json"
    if os.path.exists(index_file):
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                indexed_data = json.load(f)
                files = indexed_data.get('files', [])
                # 添加 ID
                for idx, file in enumerate(files):
                    file['id'] = f"file_{idx}"
                return {"files": files}
        except:
            pass
    return {"files": []}

@app.post("/api/knowledge-base/add")
async def add_to_knowledge_base(files: List[UploadFile] = File(...)):
    """添加檔案到知識庫"""
    try:
        temp_files = []
        temp_dir = tempfile.mkdtemp()
        file_infos = []
        
        # 保存上傳的檔案
        for file in files:
            temp_path = os.path.join(temp_dir, file.filename)
            content = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content)
            temp_files.append(temp_path)
            
            file_infos.append({
                'name': file.filename,
                'size': len(content),
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # 載入並索引文檔
        docs = load_and_split_documents(temp_files)
        if docs:
            vs = get_vectorstore()
            vs.add_documents(docs)
            
            # 更新索引記錄
            index_file = "vector_db/indexed_files.json"
            existing_files = []
            
            if os.path.exists(index_file):
                try:
                    with open(index_file, 'r', encoding='utf-8') as f:
                        indexed_data = json.load(f)
                        existing_files = indexed_data.get('files', [])
                except:
                    pass
            
            existing_files.extend(file_infos)
            
            os.makedirs("vector_db", exist_ok=True)
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump({'files': existing_files}, f, ensure_ascii=False, indent=2)
            
            return {"success": True, "message": f"成功索引 {len(files)} 個檔案"}
        else:
            return {"success": False, "message": "無法載入檔案內容"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
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

@app.delete("/api/knowledge-base/clear")
async def clear_knowledge_base():
    """清空知識庫"""
    try:
        import shutil
        
        # 清空向量資料庫
        chroma_path = get_config("CHROMA_PERSIST_DIR", "vector_db/chroma")
        if os.path.exists(chroma_path):
            shutil.rmtree(chroma_path)
            os.makedirs(chroma_path, exist_ok=True)
        
        # 清空索引記錄
        index_file = "vector_db/indexed_files.json"
        if os.path.exists(index_file):
            os.remove(index_file)
        
        return {"success": True, "message": "知識庫已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 連接（用於即時聊天）"""
    await websocket.accept()
    connected_clients[session_id] = websocket
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            
            # 處理聊天請求
            request = ChatRequest(**data)
            response = await chat(request)
            
            # 發送回應
            await websocket.send_json({
                "type": "response",
                "data": response.dict()
            })
            
    except WebSocketDisconnect:
        del connected_clients[session_id]
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

@app.get("/api/config")
async def get_config_info():
    """獲取系統配置資訊"""
    return {
        "llm_provider": get_config("LLM_PROVIDER", "ollama"),
        "vector_db": get_config("VECTOR_DB", "chroma"),
        "search_k": int(get_config("SEARCH_K", "5")),
        "available_sources": {
            "docs": {"name": "文件庫", "enabled": True},
            "db": {"name": "資料庫", "enabled": True},
            "web": {"name": "網路搜尋", "enabled": False},
            "jira": {"name": "Jira", "enabled": False},
            "wiki": {"name": "Wiki", "enabled": False},
            "outlook": {"name": "Outlook", "enabled": False}
        }
    }

@app.post("/api/export-chat")
async def export_chat(messages: List[ChatMessage]):
    """匯出對話記錄"""
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "messages": [msg.dict() for msg in messages],
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return export_data

# 掛載靜態檔案目錄
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    
    # 創建靜態檔案目錄
    os.makedirs("static", exist_ok=True)
    
    print("🚀 RAG 智能助手 API 啟動中...")
    print("📄 API 文檔：http://localhost:8000/docs")
    print("🌐 前端頁面：http://localhost:8000")
    
    # 直接運行時不使用 reload，避免警告
    uvicorn.run(app, host="0.0.0.0", port=7777)