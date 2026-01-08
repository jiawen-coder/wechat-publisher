/**
 * 消息显示
 */

function addMessage(content, role = 'assistant') {
    const chatArea = document.getElementById('chat-area');
    if (!chatArea) return null;

    const msg = document.createElement('div');
    msg.className = `message ${role}`;
    
    // 用户消息不显示头像，助手消息显示
    if (role === 'user') {
        msg.innerHTML = `<div class="bubble">${escapeHtml(content)}</div>`;
    } else {
        msg.innerHTML = `
            <div class="avatar">✨</div>
            <div class="bubble">${renderChatMarkdown(content)}</div>
        `;
    }

    chatArea.appendChild(msg);
    chatArea.scrollTop = chatArea.scrollHeight;
    return msg;
}

function addProgress(title) {
    const chatArea = document.getElementById('chat-area');
    if (!chatArea) return { complete: () => {}, remove: () => {} };
    
    const id = 'loading-' + Date.now();
    const msg = document.createElement('div');
    msg.className = 'message assistant';
    msg.innerHTML = `
        <div class="avatar">✨</div>
        <div class="bubble" style="padding: 12px 16px;">
            <div class="loading-status" id="${id}">
                <span class="loading-spinner"></span>
                <span>${escapeHtml(title)}</span>
            </div>
        </div>
    `;
    chatArea.appendChild(msg);
    chatArea.scrollTop = chatArea.scrollHeight;
    return {
        id,
        element: msg,
        complete: (text) => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = `<span style="color:#22c55e">✓</span> ${escapeHtml(text || '完成')}`;
        },
        remove: () => msg.remove()
    };
}

function updatePreview(content) {
    const previewArea = document.getElementById('preview-area');
    if (!previewArea) return;
    
    // 清理各种标记
    content = (content || '')
        .replace(/\[OPERATION\][\s\S]*?\[\/OPERATION\]/g, '')
        .replace(/```markdown\s*/gi, '')
        .replace(/```\s*$/gm, '')
        .replace(/^```\s*/gm, '')
        .trim();
    
    if (!content) {
        previewArea.innerHTML = `
            <div class="preview-placeholder">
                <div class="preview-placeholder-icon">📄</div>
                <div class="preview-placeholder-text">文章内容将在这里展示</div>
            </div>
        `;
        return;
    }
    
    // 更好的 Markdown 渲染
    const lines = content.split('\n');
    let html = '';
    let inList = false;
    let listType = '';
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        
        // 标题
        if (line.startsWith('# ')) {
            if (inList) { html += `</${listType}>`; inList = false; }
            html += `<h1 class="article-title">${line.slice(2)}</h1>`;
            continue;
        }
        if (line.startsWith('## ')) {
            if (inList) { html += `</${listType}>`; inList = false; }
            html += `<h2 class="article-h2">${line.slice(3)}</h2>`;
            continue;
        }
        if (line.startsWith('### ')) {
            if (inList) { html += `</${listType}>`; inList = false; }
            html += `<h3 class="article-h3">${line.slice(4)}</h3>`;
            continue;
        }
        
        // 无序列表
        if (line.match(/^[-*] /)) {
            if (!inList || listType !== 'ul') {
                if (inList) html += `</${listType}>`;
                html += '<ul class="article-list">';
                inList = true;
                listType = 'ul';
            }
            html += `<li>${formatInline(line.slice(2))}</li>`;
            continue;
        }
        
        // 有序列表
        if (line.match(/^\d+\. /)) {
            if (!inList || listType !== 'ol') {
                if (inList) html += `</${listType}>`;
                html += '<ol class="article-list">';
                inList = true;
                listType = 'ol';
            }
            html += `<li>${formatInline(line.replace(/^\d+\. /, ''))}</li>`;
            continue;
        }
        
        // 引用
        if (line.startsWith('> ')) {
            if (inList) { html += `</${listType}>`; inList = false; }
            html += `<blockquote class="article-quote">${formatInline(line.slice(2))}</blockquote>`;
            continue;
        }
        
        // 空行
        if (!line.trim()) {
            if (inList) { html += `</${listType}>`; inList = false; }
            continue;
        }
        
        // 普通段落
        if (inList) { html += `</${listType}>`; inList = false; }
        html += `<p class="article-p">${formatInline(line)}</p>`;
    }
    
    if (inList) html += `</${listType}>`;
    
    previewArea.innerHTML = `<div class="article-preview">${html}</div>`;
}

// 行内格式化
function formatInline(text) {
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>');
}

function clearChat() {
    const chatArea = document.getElementById('chat-area');
    if (chatArea) chatArea.innerHTML = '';
    state.chatHistory = [];
}
