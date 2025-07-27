#!/bin/bash

echo "🚀 RAG 系統 - Ollama 啟動腳本"
echo "================================"

# 檢查 Ollama 是否已安裝
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama 未安裝！"
    echo ""
    echo "請先安裝 Ollama："
    echo "  - macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh"
    echo "  - Windows: 從 https://ollama.com/download 下載"
    exit 1
fi

echo "✅ 檢測到 Ollama 已安裝"

# 檢查 Ollama 服務是否在運行
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "🔄 啟動 Ollama 服務..."
    ollama serve &
    sleep 5
fi

echo "✅ Ollama 服務正在運行"

# 檢查是否有 llama3 模型
if ! ollama list | grep -q "llama3"; then
    echo "📥 下載 llama3 模型（約 4.7GB）..."
    echo "這可能需要一些時間，請耐心等待..."
    ollama pull llama3
fi

echo "✅ llama3 模型已就緒"

# 顯示可用的模型
echo ""
echo "📋 可用的模型："
ollama list

echo ""
echo "🎉 Ollama 準備完成！"
echo ""
echo "現在你可以運行 RAG 系統了："
echo "  1. 使用 Docker: docker-compose up -d"
echo "  2. 或本地運行: python app.py"
echo ""
echo "💡 提示："
echo "  - 如果要使用其他模型，運行: ollama pull <model-name>"
echo "  - 支援的模型: llama3, llama2, mistral, mixtral, neural-chat, starling-lm, codellama, llama2-uncensored, llama2:13b, llama2:70b, orca-mini, vicuna, llava, gemma:2b, gemma:7b, solar"
echo "  - 修改 .env 中的 OLLAMA_MODEL 來切換模型"