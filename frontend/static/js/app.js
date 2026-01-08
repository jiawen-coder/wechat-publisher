/**
 * 应用入口 - 包含 Google 登录逻辑
 */

// Google OAuth 配置
const GOOGLE_CLIENT_ID = '918718013604-4uvqroc42ese3muoff0jkkpne6v3hkvq.apps.googleusercontent.com';
const USER_STORAGE_KEY = 'wechat_publisher_user';

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 App 初始化');
    
    // 先尝试从本地存储恢复登录状态
    const savedUser = localStorage.getItem(USER_STORAGE_KEY);
    if (savedUser) {
        try {
            state.user = JSON.parse(savedUser);
            state.userId = state.user.id;
            updateAuthUI(true);
            console.log('✅ 从本地存储恢复登录状态:', state.user.name);
        } catch (e) {
            console.warn('本地存储数据无效');
            localStorage.removeItem(USER_STORAGE_KEY);
        }
    }
    
    // 再检查服务端登录状态
    try {
        const authRes = await apiRequest('/api/auth/status');
        const authData = await authRes.json();
        
        if (authData.logged_in && authData.user) {
            state.userId = authData.user.id;
            state.user = authData.user;
            localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(authData.user));
            updateAuthUI(true);
        } else if (!savedUser) {
            // 服务端未登录且本地也没有，显示登录按钮
            updateAuthUI(false);
        }
    } catch (e) {
        console.warn('Auth check failed:', e);
        if (!savedUser) {
            updateAuthUI(false);
        }
    }
    
    // 显示欢迎消息
    showWelcome();
});

// ==================== Google 登录 ====================

let googleInitialized = false;
let loginInProgress = false;

function showGoogleLogin() {
    // 防止重复点击
    if (loginInProgress) {
        console.log('登录已在进行中...');
        return;
    }
    
    if (typeof google === 'undefined' || !google.accounts) {
        alert('Google 登录服务加载中，请稍后再试...');
        return;
    }
    
    if (!GOOGLE_CLIENT_ID) {
        alert('Google 登录未配置，请联系管理员');
        return;
    }
    
    loginInProgress = true;
    
    // 只初始化一次
    if (!googleInitialized) {
        google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: handleGoogleCredential,
            auto_select: false,
            cancel_on_tap_outside: true
        });
        googleInitialized = true;
    }
    
    // 先取消之前的请求
    google.accounts.id.cancel();
    
    // 延迟一点再发起新请求，避免 FedCM 冲突
    setTimeout(() => {
        google.accounts.id.prompt((notification) => {
            loginInProgress = false;
            if (notification.isNotDisplayed()) {
                console.log('Google 登录弹窗未显示:', notification.getNotDisplayedReason());
                // 如果弹窗被阻止，提示用户
                if (notification.getNotDisplayedReason() === 'opt_out_or_no_session') {
                    alert('请先登录您的 Google 账号，或检查浏览器是否阻止了弹窗');
                }
            }
            if (notification.isSkippedMoment()) {
                console.log('Google 登录被跳过:', notification.getSkippedReason());
            }
        });
    }, 100);
}

async function handleGoogleCredential(response) {
    try {
        const res = await fetch('/api/auth/google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ credential: response.credential })
        });
    
        const data = await res.json();

        if (data.success) {
            state.user = data.user;
            state.userId = data.user.id;
            // 保存到本地存储
            localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data.user));
            localStorage.setItem('userId', data.user.id);
            updateAuthUI(true);

            addMessage(`👋 欢迎回来，${data.user.name}！${data.user.has_config ? '已加载你的配置。' : '请在设置中配置 API Key。'}`);
        } else {
            alert('登录失败: ' + data.error);
    }
    } catch (e) {
        console.error('登录失败:', e);
        alert('登录失败，请重试');
    }
}

// ==================== UI 更新 ====================

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

// ==================== 登录保护 ====================

function checkAuth() {
    if (!state.user) {
        showLoginRequired();
        return false;
    }
    return true;
}

function showLoginRequired() {
    addMessage(`
        <div style="margin-bottom: 12px;">🔐 <strong>请先登录</strong></div>
        <div style="color: var(--text-secondary); margin-bottom: 16px;">
            登录后才能使用完整功能，你的配置将自动保存。
        </div>
        <button class="action-btn primary" onclick="showGoogleLogin()" style="width: 100%; justify-content: center;">
            <svg viewBox="0 0 24 24" width="18" height="18" style="margin-right: 8px;">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            使用 Google 登录
        </button>
    `);
}

// ==================== 欢迎消息 ====================

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

// ==================== 功能入口 ====================

// 开始对话模式（聚焦输入框）
function startChatMode() {
    if (!checkAuth()) return;
    
    const input = document.getElementById('free-chat-text');
    if (input) {
        input.focus();
        input.placeholder = '告诉我你想写什么主题的文章...';
    }
    addMessage('好的，你想写什么主题的文章？比如：时间管理、职场成长、健身指南...');
}

// 开始语音输入
function startVoiceInput() {
    if (!checkAuth()) return;
    
    if (typeof toggleVoiceInput === 'function') {
        addMessage('🎤 开始录音...说完后再次点击麦克风停止');
        toggleVoiceInput();
    } else {
        addMessage('🎤 请点击输入框左侧的麦克风按钮开始录音');
    }
}

// 显示粘贴输入框
function showPasteInput() {
    if (!checkAuth()) return;
    
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

// ==================== 用户菜单 ====================

function toggleUserMenu() {
    const menu = document.getElementById('user-menu');
    if (menu) {
        menu.classList.toggle('show');
    }
}

async function handleLogout() {
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });

        // 清除 Google 登录状态
        if (typeof google !== 'undefined' && google.accounts) {
            google.accounts.id.disableAutoSelect();
            google.accounts.id.cancel();
        }
        googleInitialized = false;
        loginInProgress = false;

        // 清除本地存储
        localStorage.removeItem(USER_STORAGE_KEY);
    localStorage.removeItem('userId');

    state.user = null;
        state.userId = null;
        updateAuthUI(false);

        // 关闭菜单
        document.getElementById('user-menu')?.classList.remove('show');

        // 刷新页面
        location.reload();
    } catch (e) {
        console.error('退出登录失败:', e);
        // 强制清除并刷新
        localStorage.removeItem(USER_STORAGE_KEY);
        localStorage.removeItem('userId');
    location.reload();
    }
}

// 点击外部关闭菜单
document.addEventListener('click', (e) => {
    const menu = document.getElementById('user-menu');
    const avatar = document.getElementById('user-avatar');
    if (menu && !menu.contains(e.target) && e.target !== avatar) {
        menu.classList.remove('show');
    }
});
