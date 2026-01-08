/**
 * 应用入口
 */

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 App 初始化');
    
    // 检查登录状态
    try {
        const authRes = await apiRequest('/api/auth/status');
        const authData = await authRes.json();
        
        if (authData.logged_in && authData.user) {
            state.userId = authData.user_id || authData.user.id;
            state.user = authData.user;
            localStorage.setItem('userId', state.userId);
            updateAuthUI(true);
        } else {
            // 未登录，显示登录按钮
            updateAuthUI(false);
        }
    } catch (e) {
        console.warn('Auth check failed:', e);
        // 出错时也显示登录按钮
        updateAuthUI(false);
    }
    
    // 显示欢迎消息
    showWelcome();
});

function updateAuthUI(loggedIn) {
    const loginBtn = document.getElementById('login-btn');
    const userArea = document.getElementById('user-area');
    const avatar = document.getElementById('user-avatar');
    const userName = document.getElementById('user-name');
    const userEmail = document.getElementById('user-email');
    
    if (loggedIn && state.user) {
        if (loginBtn) loginBtn.style.display = 'none';
        if (userArea) userArea.style.display = 'block';
        
        const initial = state.user.name?.[0] || 'U';
        const defaultAvatar = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="%238b5cf6"/><text x="50" y="65" text-anchor="middle" fill="white" font-size="40" font-family="Arial">${initial}</text></svg>`;
        
        if (avatar) avatar.src = state.user.picture || defaultAvatar;
        if (userName) userName.textContent = state.user.name || '用户';
        if (userEmail) userEmail.textContent = state.user.email || '';
    } else {
        if (loginBtn) loginBtn.style.display = 'flex';
        if (userArea) userArea.style.display = 'none';
    }
}

function showWelcome() {
    const chatArea = document.getElementById('chat-area');
    if (!chatArea) return;
    
    chatArea.innerHTML = `
        <div class="message assistant">
            <div class="avatar">✨</div>
            <div class="bubble agent-welcome">
                <div class="welcome-title">👋 你好，我来帮你创作公众号文章</div>
                <div class="welcome-desc">选择一种方式开始：</div>
                
                <div class="start-modes">
                    <div class="start-mode" onclick="startChatMode()">
                        <div class="mode-icon">💬</div>
                        <div class="mode-info">
                            <div class="mode-title">自由对话</div>
                            <div class="mode-desc">告诉我想写什么</div>
                        </div>
                    </div>
                    <div class="start-mode" onclick="triggerFileUpload()">
                        <div class="mode-icon">📄</div>
                        <div class="mode-info">
                            <div class="mode-title">上传文件</div>
                            <div class="mode-desc">从 PDF/TXT/图片开始</div>
                        </div>
                    </div>
                    <div class="start-mode" onclick="startVoiceInput()">
                        <div class="mode-icon">🎤</div>
                        <div class="mode-info">
                            <div class="mode-title">语音输入</div>
                            <div class="mode-desc">说出你的想法</div>
                        </div>
                    </div>
                    <div class="start-mode" onclick="showPasteInput()">
                        <div class="mode-icon">📋</div>
                        <div class="mode-info">
                            <div class="mode-title">粘贴内容</div>
                            <div class="mode-desc">已有文章直接排版</div>
                        </div>
                    </div>
                </div>
                
            </div>
        </div>
    `;
}

// 开始对话模式（聚焦输入框）
function startChatMode() {
    const input = document.getElementById('free-chat-text');
    if (input) {
        input.focus();
        input.placeholder = '告诉我你想写什么主题的文章...';
    }
    addMessage('好的，你想写什么主题的文章？比如：时间管理、职场成长、健身指南...');
}

// 开始语音输入
function startVoiceInput() {
    if (typeof toggleVoiceInput === 'function') {
        addMessage('🎤 开始录音...说完后再次点击麦克风停止');
        toggleVoiceInput();
    } else {
        addMessage('🎤 请点击输入框左侧的麦克风按钮开始录音');
    }
}

// 显示粘贴输入框
function showPasteInput() {
    const chatArea = document.getElementById('chat-area');
    chatArea.innerHTML += `
        <div class="message assistant">
            <div class="avatar">✨</div>
            <div class="bubble">
                <div style="margin-bottom:12px;">📋 <strong>粘贴你的文章内容</strong></div>
                <textarea id="paste-content" placeholder="在这里粘贴文章内容..." 
                    style="width:100%; min-height:150px; background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.2); border-radius:8px; padding:12px; color:white; font-size:14px; resize:vertical; outline:none;"></textarea>
                <div style="margin-top:12px; display:flex; gap:8px;">
                    <button onclick="processPastedContent()" class="action-btn primary">开始排版</button>
                    <button onclick="showWelcome()" class="action-btn">取消</button>
                </div>
            </div>
        </div>
    `;
    chatArea.scrollTop = chatArea.scrollHeight;
}

// 处理粘贴的内容
async function processPastedContent() {
    const textarea = document.getElementById('paste-content');
    const content = textarea?.value?.trim();
    
    if (!content) {
        addMessage('请先粘贴文章内容');
        return;
    }
    
    state.rawContent = content;
    state.processedContent = content;
    
    // 解析标题
    try {
        const parseData = await parseContent(content);
        if (parseData.title) state.title = parseData.title;
        if (parseData.summary) state.summary = parseData.summary;
    } catch (e) {}
    
    // 显示预览
    updatePreview(content);
    
    addMessage(`✅ 已读取 ${content.length} 字`, 'assistant');
    showThemeSelector();
}

function toggleUserMenu() {
    const menu = document.getElementById('user-menu');
    if (menu) {
        menu.classList.toggle('show');
    }
}

function handleLogout() {
    localStorage.removeItem('userId');
    state.userId = 'guest';
    state.user = null;
    location.reload();
}

// 点击外部关闭菜单
document.addEventListener('click', (e) => {
    const menu = document.getElementById('user-menu');
    const avatar = document.getElementById('user-avatar');
    if (menu && !menu.contains(e.target) && e.target !== avatar) {
        menu.classList.remove('show');
    }
});
