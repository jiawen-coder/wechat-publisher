/**
 * UI 交互
 */

function setGeneratingState(generating) {
    state.isGenerating = generating;
    
    const sendBtn = document.querySelector('.free-chat-send');
    if (sendBtn) {
        sendBtn.disabled = generating;
        sendBtn.style.opacity = generating ? '0.5' : '1';
    }
    
    const input = document.getElementById('free-chat-text');
    if (input) {
        input.disabled = generating;
    }
}

function toggleEditMode() {
    const previewArea = document.getElementById('preview-area');
    const btn = document.getElementById('edit-toggle-btn');
    
    if (!previewArea) return;
    
    const isEditable = previewArea.contentEditable === 'true';
    previewArea.contentEditable = !isEditable;
    
    if (btn) {
        btn.textContent = isEditable ? '✏️ 编辑' : '💾 保存';
    }
    
    if (isEditable) {
        // 保存编辑内容
        state.htmlContent = previewArea.innerHTML;
        addMessage('✅ 内容已保存');
    }
}

function closePreview() {
    const rightPanel = document.getElementById('right-panel');
    if (rightPanel) {
        rightPanel.style.display = 'none';
    }
}

function showPreview() {
    const rightPanel = document.getElementById('right-panel');
    if (rightPanel) {
        rightPanel.style.display = 'flex';
    }
}

function copyHtmlContent() {
    if (state.htmlContent) {
        copyToClipboard(state.htmlContent);
        addMessage('✅ HTML 已复制到剪贴板');
    } else {
        addMessage('还没有排版内容');
    }
}

// 点击外部关闭弹窗
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
});

// Enter 发送消息
document.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && e.target.id === 'free-chat-text') {
        sendFreeChat();
    }
});

