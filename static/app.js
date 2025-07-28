// RAG 智能助手前端 JavaScript

// 全局變量
let sessionId = localStorage.getItem('sessionId') || generateUUID();
let messages = [];
let uploadedFiles = [];
let kbFiles = [];

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    loadIndexedFiles();
    loadConfig();
});

// 生成 UUID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// 初始化應用
function initializeApp() {
    localStorage.setItem('sessionId', sessionId);
    
    // 設置拖放功能
    setupDragAndDrop('kb-upload-area', 'kb-file-input', (files) => {
        kbFiles = files;
        updateKBFilesList();
    });
    
    setupDragAndDrop('temp-upload-area', 'temp-file-input', (files) => {
        uploadedFiles = files;
        updateTempFilesList();
    });
}

// 設置事件監聽器
function setupEventListeners() {
    // 輸入框事件
    const messageInput = document.getElementById('message-input');
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 自動調整輸入框高度
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    });
    
    // 快捷鍵
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'k':
                    e.preventDefault();
                    newChat();
                    break;
                case 's':
                    e.preventDefault();
                    exportChat();
                    break;
            }
        }
    });
}

// 設置拖放功能
function setupDragAndDrop(areaId, inputId, callback) {
    const area = document.getElementById(areaId);
    const input = document.getElementById(inputId);
    
    area.addEventListener('click', () => input.click());
    
    area.addEventListener('dragover', (e) => {
        e.preventDefault();
        area.classList.add('dragover');
    });
    
    area.addEventListener('dragleave', () => {
        area.classList.remove('dragover');
    });
    
    area.addEventListener('drop', (e) => {
        e.preventDefault();
        area.classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files);
        callback(files);
    });
    
    input.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        callback(files);
    });
}

// 發送訊息
async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const query = messageInput.value.trim();
    
    if (!query) return;
    
    // 清空輸入框
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // 隱藏歡迎訊息
    const welcomeMessage = document.getElementById('welcome-message');
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
    
    // 添加用戶訊息
    addMessage('user', query);
    
    // 獲取選中的資料來源
    const sources = [];
    if (document.getElementById('source-docs').checked) sources.push('docs');
    if (document.getElementById('source-db').checked) sources.push('db');
    
    // 顯示載入動畫
    showLoading();
    
    try {
        let response;
        
        if (uploadedFiles.length > 0) {
            // 有檔案的請求
            const formData = new FormData();
            formData.append('query', query);
            formData.append('sources', JSON.stringify(sources));
            formData.append('session_id', sessionId);
            
            uploadedFiles.forEach(file => {
                formData.append('files', file);
            });
            
            response = await fetch('/api/chat/upload', {
                method: 'POST',
                body: formData
            });
        } else {
            // 無檔案的請求
            response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    sources: sources,
                    session_id: sessionId,
                    context_messages: messages.slice(-10) // 最近10條訊息
                })
            });
        }
        
        if (!response.ok) {
            throw new Error('請求失敗');
        }
        
        const data = await response.json();
        
        // 添加助手回應
        addMessage('assistant', data.answer, data.sources);
        
        // 清空臨時檔案
        uploadedFiles = [];
        updateTempFilesList();
        
    } catch (error) {
        console.error('Error:', error);
        addMessage('assistant', '抱歉，處理您的請求時發生錯誤。請稍後再試。');
    } finally {
        hideLoading();
    }
}

// 發送建議問題
function sendSuggestion(text) {
    document.getElementById('message-input').value = text;
    sendMessage();
}

// 添加訊息到對話
function addMessage(role, content, sources = []) {
    const message = {
        role: role,
        content: content,
        sources: sources,
        timestamp: new Date().toISOString()
    };
    
    messages.push(message);
    
    const chatContainer = document.getElementById('chat-container');
    const messageDiv = createMessageElement(message);
    chatContainer.appendChild(messageDiv);
    
    // 滾動到底部
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 創建訊息元素
function createMessageElement(message) {
    const div = document.createElement('div');
    div.className = `message ${message.role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = message.role === 'user' ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    const text = document.createElement('div');
    text.className = 'message-text';
    text.textContent = message.content;
    
    bubble.appendChild(text);
    
    // 添加來源標籤
    if (message.sources && message.sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';
        
        message.sources.forEach(source => {
            const tag = document.createElement('span');
            tag.className = `source-tag source-${source}`;
            tag.textContent = source.toUpperCase();
            sourcesDiv.appendChild(tag);
        });
        
        bubble.appendChild(sourcesDiv);
    }
    
    content.appendChild(bubble);
    div.appendChild(avatar);
    div.appendChild(content);
    
    return div;
}

// 新對話
function newChat() {
    if (messages.length > 0) {
        if (confirm('確定要開始新對話嗎？當前對話將被清空。')) {
            messages = [];
            document.getElementById('chat-container').innerHTML = `
                <div class="welcome-message" id="welcome-message">
                    <h2>👋 歡迎使用 RAG 智能助手</h2>
                    <p>我可以幫您搜尋文件、查詢資料庫，回答各種問題。</p>
                    <div class="suggestions">
                        <p><strong>您可以試著問我：</strong></p>
                        <button class="suggestion-chip" onclick="sendSuggestion('幫我搜尋相關文件')">搜尋特定文件內容</button>
                        <button class="suggestion-chip" onclick="sendSuggestion('分析這個檔案的內容')">分析上傳的檔案</button>
                        <button class="suggestion-chip" onclick="sendSuggestion('查詢資料庫中的資訊')">查詢資料庫資訊</button>
                        <button class="suggestion-chip" onclick="sendSuggestion('解釋一下這個技術概念')">解答技術問題</button>
                    </div>
                </div>
            `;
            sessionId = generateUUID();
            localStorage.setItem('sessionId', sessionId);
        }
    }
}

// 匯出對話
async function exportChat() {
    if (messages.length === 0) {
        alert('沒有對話可以匯出');
        return;
    }
    
    try {
        const response = await fetch('/api/export-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(messages)
        });
        
        const data = await response.json();
        
        // 下載 JSON 檔案
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('Error:', error);
        alert('匯出失敗');
    }
}

// 載入已索引的檔案
async function loadIndexedFiles() {
    try {
        const response = await fetch('/api/knowledge-base/files');
        const data = await response.json();
        
        const filesList = document.getElementById('indexed-files-list');
        filesList.innerHTML = '';
        
        if (data.files && data.files.length > 0) {
            data.files.forEach(file => {
                const fileDiv = createFileElement(file);
                filesList.appendChild(fileDiv);
            });
        } else {
            filesList.innerHTML = '<p style="text-align: center; color: #6B7280;">知識庫為空</p>';
        }
        
    } catch (error) {
        console.error('Error:', error);
    }
}

// 創建檔案元素
function createFileElement(file) {
    const div = document.createElement('div');
    div.className = 'file-item';
    
    div.innerHTML = `
        <div class="file-info">
            <div class="file-name">📄 ${file.name}</div>
            <div class="file-meta">${file.date} | ${(file.size / 1024 / 1024).toFixed(1)} MB</div>
        </div>
        <div class="file-actions">
            <button onclick="deleteFile('${file.id}')">🗑️</button>
        </div>
    `;
    
    return div;
}

// 添加到知識庫
async function addToKnowledgeBase() {
    if (kbFiles.length === 0) {
        alert('請先選擇要添加的檔案');
        return;
    }
    
    const formData = new FormData();
    kbFiles.forEach(file => {
        formData.append('files', file);
    });
    
    showLoading();
    
    try {
        const response = await fetch('/api/knowledge-base/add', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            kbFiles = [];
            updateKBFilesList();
            loadIndexedFiles();
        } else {
            alert(data.message || '添加失敗');
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('添加失敗');
    } finally {
        hideLoading();
    }
}

// 清空知識庫
async function clearKnowledgeBase() {
    if (!confirm('確定要清空整個知識庫嗎？此操作無法撤銷。')) {
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/knowledge-base/clear', {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            loadIndexedFiles();
        } else {
            alert('清空失敗');
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('清空失敗');
    } finally {
        hideLoading();
    }
}

// 更新知識庫檔案列表
function updateKBFilesList() {
    const area = document.getElementById('kb-upload-area');
    
    if (kbFiles.length > 0) {
        area.innerHTML = `<p>已選擇 ${kbFiles.length} 個檔案</p>`;
    } else {
        area.innerHTML = '<p>📁 拖放檔案到這裡，或點擊選擇</p>';
    }
}

// 更新臨時檔案列表
function updateTempFilesList() {
    const list = document.getElementById('temp-files-list');
    list.innerHTML = '';
    
    uploadedFiles.forEach((file, index) => {
        const div = document.createElement('div');
        div.className = 'temp-file-item';
        div.innerHTML = `
            <span>${file.name}</span>
            <button onclick="removeTempFile(${index})">×</button>
        `;
        list.appendChild(div);
    });
}

// 移除臨時檔案
function removeTempFile(index) {
    uploadedFiles.splice(index, 1);
    updateTempFilesList();
}

// 載入配置
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        // 設置 LLM 提供者
        document.getElementById('llm-provider').value = config.llm_provider;
        
        // 設置搜尋數量
        document.getElementById('search-k').value = config.search_k;
        
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

// 切換側邊欄
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}

// 顯示標籤頁
function showTab(tabName) {
    // 隱藏所有標籤內容
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // 移除所有活動狀態
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 顯示選中的標籤
    document.getElementById(`${tabName}-tab`).style.display = 'block';
    
    // 設置活動按鈕
    event.target.classList.add('active');
}

// 顯示載入動畫
function showLoading() {
    document.getElementById('loading-overlay').classList.add('active');
}

// 隱藏載入動畫
function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

// 顯示說明
function showHelp() {
    document.getElementById('help-modal').classList.add('active');
}

// 關閉說明
function closeHelp() {
    document.getElementById('help-modal').classList.remove('active');
}

// 點擊模態框外部關閉
document.getElementById('help-modal').addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        closeHelp();
    }
});