/**
 * 文件上传
 */

async function handleFileUpload(file) {
    const loading = addProgress(`读取 ${file.name}...`);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await uploadFile(formData);
        const data = await response.json();
        
        if (data.success) {
            loading.complete('读取完成');
            state.rawContent = data.content || '';
            state.processedContent = data.content || '';
            
            if (data.content) {
                updatePreview(data.content);
                
                // 解析标题
                try {
                    const parseData = await parseContent(data.content);
                    if (parseData.title) state.title = parseData.title;
                    if (parseData.summary) state.summary = parseData.summary;
                } catch (e) {}
                
                // 恢复输入状态
                setGeneratingState(false);
                
                // 显示下一步操作
                showFileUploadOptions(data.content.length);
            } else if (data.image_url) {
                state.uploadedImageUrl = data.image_url;
                setGeneratingState(false);
                addMessage(`🖼️ 图片已上传，你想让我识别图片内容吗？`);
            } else {
                setGeneratingState(false);
            }
        } else {
            throw new Error(data.error || '上传失败');
        }
    } catch (e) {
        loading.complete('上传失败');
        addMessage(`❌ ${e.message}`);
        setGeneratingState(false);
    }
}

// 显示文件上传后的操作选项
function showFileUploadOptions(charCount) {
    const chatArea = document.getElementById('chat-area');
    if (!chatArea) return;
    
    const html = `
        <div class="message assistant">
            <div class="avatar">✨</div>
            <div class="bubble">
                <div style="margin-bottom:12px;">📄 已读取 <strong>${charCount}</strong> 字</div>
                <div style="color:var(--text-secondary);margin-bottom:12px;">你想要：</div>
                <div class="action-buttons">
                    <button class="action-btn primary" onclick="showThemeSelector()">🎨 直接排版</button>
                    <button class="action-btn" onclick="rewriteUploadedContent()">✏️ 改写优化</button>
                    <button class="action-btn" onclick="expandUploadedContent()">📝 扩写成文章</button>
                </div>
            </div>
        </div>
    `;
    
    chatArea.insertAdjacentHTML('beforeend', html);
    chatArea.scrollTop = chatArea.scrollHeight;
}

// 改写上传的内容
function rewriteUploadedContent() {
    quickSend('帮我改写这篇文章，语言更流畅，结构更清晰');
}

// 扩写成完整文章
function expandUploadedContent() {
    quickSend('基于这个素材，帮我扩写成一篇完整的公众号文章');
}

function triggerFileUpload() {
    if (!checkAuth()) return;
    
    const input = document.getElementById('file-input');
    if (input) input.click();
}

function onFileSelected(event) {
    if (!checkAuth()) {
        event.target.value = '';
        return;
    }
    
    const file = event.target.files[0];
    if (file) {
        addMessage(`📎 上传：${file.name}`, 'user');
        setGeneratingState(true);
        handleFileUpload(file);
    }
    event.target.value = '';
}

