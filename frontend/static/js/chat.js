/**
 * 聊天逻辑
 */

function quickSend(text) {
    const input = document.getElementById('free-chat-text');
    if (input) {
        input.value = text;
        sendFreeChat();
    }
}

async function sendFreeChat() {
    if (state.isGenerating) return;

    const input = document.getElementById('free-chat-text');
    const message = input?.value?.trim();

    if (!message) return;
    
    // 检查登录状态
    if (!checkAuth()) return;
    
    // 先检查 API Key，不要显示 typing
    let configData;
    try {
        configData = await getConfigKeys();
        if (!configData.iflow_api_key) {
            addMessage(message, 'user');
            addMessage('❌ 请先在设置中配置心流 API Key（点击右上角齿轮）');
            return;
        }
    } catch (e) {
        addMessage(message, 'user');
        addMessage('❌ 无法连接服务器，请检查网络');
        return;
    }
    
    input.value = '';
    addMessage(message, 'user');
    addToHistory('user', message);

    setGeneratingState(true);
    
    // API Key 验证通过后才显示 typing
    const typingMsg = addTypingIndicator();

    try {
        const recentHistory = state.chatHistory.slice(-10).map(h => ({
            role: h.role,
            content: h.content
        }));

        const response = await chatWithAgent(recentHistory, state.getContext());
        const data = await response.json();
        
        // 移除 typing
        typingMsg.remove();
        
        if (!response.ok) {
            throw new Error(data.error || '请求失败');
        }

        console.log('🤖 Agent 响应:', data);

        if (data.react) {
            // 有最终回复（闲聊）- 流式显示
            if (data.final_answer) {
                await typeMessage(data.final_answer);
                addToHistory('assistant', data.final_answer);
            }
            
            // 需要执行工具
            if (data.action && data.needs_tool_execution) {
                await executeReActTool(data.action, data.action_input || {});
            }
        } else if (data.reply) {
            await typeMessage(data.reply);
            addToHistory('assistant', data.reply);
        }

    } catch (e) {
        typingMsg?.remove?.();
        addMessage('❌ ' + (e.message || '请重试'));
    } finally {
        setGeneratingState(false);
    }
}

// 添加 typing 指示器
function addTypingIndicator() {
    const chatArea = document.getElementById('chat-area');
    if (!chatArea) return { remove: () => {} };
    
    const msg = document.createElement('div');
    msg.className = 'message assistant';
    msg.innerHTML = `
        <div class="avatar">✨</div>
        <div class="bubble typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;
    chatArea.appendChild(msg);
    chatArea.scrollTop = chatArea.scrollHeight;
    return msg;
}

// 打字机效果显示消息
async function typeMessage(content) {
    const chatArea = document.getElementById('chat-area');
    if (!chatArea) return;
    
    const msg = document.createElement('div');
    msg.className = 'message assistant';
    msg.innerHTML = `
        <div class="avatar">✨</div>
        <div class="bubble"></div>
    `;
    chatArea.appendChild(msg);
    
    const bubble = msg.querySelector('.bubble');
    let displayed = '';
    
    // 逐字显示（每 20ms 一个字符，比较快）
    for (let i = 0; i < content.length; i++) {
        displayed += content[i];
        bubble.innerHTML = renderChatMarkdown(displayed);
        chatArea.scrollTop = chatArea.scrollHeight;
        
        // 每 3 个字符暂停一下，模拟流式
        if (i % 3 === 0) {
            await new Promise(r => setTimeout(r, 15));
        }
    }
    
    return msg;
}

async function processWithAI(context, instruction, showInPreview = true) {
    const systemPrompt = `你是专业的微信公众号写手。

【任务】${instruction}

【素材/参考】
${context || '（无素材，请根据指令创作）'}

【要求】
- 直接输出文章内容，使用 Markdown 格式
- 不要输出任何解释
- 标题用 # 开头
- 结构清晰，段落分明
- 1500-2000字`;

    const response = await chatStream([{ role: 'user', content: systemPrompt }], 'write');

    if (!response.ok) {
        throw new Error('AI 调用失败');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullContent = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        for (const line of chunk.split('\n')) {
            if (line.startsWith('data: ') && line !== 'data: [DONE]') {
                try {
                    const data = JSON.parse(line.substring(6));
                    const delta = data.choices?.[0]?.delta?.content || '';
                    if (delta) {
                        fullContent += delta;
                        if (showInPreview) {
                            updatePreview(fullContent);
                        }
                    }
                } catch (e) {}
            }
        }
    }

    if (fullContent) {
        state.processedContent = fullContent;
        state.rawContent = fullContent;
        
        // 解析标题
        try {
            const parseData = await parseContent(fullContent);
            if (parseData.title) state.title = parseData.title;
            if (parseData.summary) state.summary = parseData.summary;
        } catch (e) {}
        // 注意：showNextStepOptions 由调用方处理，避免重复
    }

    return fullContent;
}

// 显示下一步操作按钮
function showNextStepOptions(currentStep) {
    const chatArea = document.getElementById('chat-area');
    if (!chatArea) return;
    
    // 进度条
    const progress = currentStep === 'write' ? 1 : currentStep === 'theme' ? 2 : 3;
    const progressBar = `
        <div class="step-progress">
            <div class="step ${progress >= 1 ? 'done' : ''}">① 文章</div>
            <div class="step-line ${progress >= 2 ? 'done' : ''}"></div>
            <div class="step ${progress >= 2 ? 'done' : ''}">② 排版</div>
            <div class="step-line ${progress >= 3 ? 'done' : ''}"></div>
            <div class="step ${progress >= 3 ? 'done' : ''}">③ 封面</div>
        </div>
    `;
    
    let html = '';
    
    if (currentStep === 'write') {
        html = `
            <div class="message assistant">
                <div class="avatar">✨</div>
                <div class="bubble">
                    ${progressBar}
                    <div style="margin:16px 0 12px;">✅ <strong>文章已生成</strong></div>
                    <div class="action-buttons">
                        <button class="action-btn primary" onclick="autoApplyTheme()">🎨 一键排版</button>
                        <button class="action-btn" onclick="showThemeSelector()">🎯 选择风格</button>
                        <button class="action-btn" onclick="quickSend('帮我改一下，更口语化')">✏️ 修改</button>
                    </div>
                </div>
            </div>
        `;
    } else if (currentStep === 'theme') {
        html = `
            <div class="message assistant">
                <div class="avatar">✨</div>
                <div class="bubble">
                    ${progressBar}
                    <div style="margin:16px 0 12px;">✅ <strong>排版已完成</strong></div>
                    <div class="action-buttons">
                        <button class="action-btn primary" onclick="showCoverSelector()">🖼️ 生成封面</button>
                        <button class="action-btn" onclick="showThemeSelector()">🔄 换排版</button>
                        <button class="action-btn" onclick="skipCoverAndPublish()">⏭️ 跳过封面</button>
                    </div>
                </div>
            </div>
        `;
    } else if (currentStep === 'cover') {
        html = `
            <div class="message assistant">
                <div class="avatar">✨</div>
                <div class="bubble">
                    ${progressBar}
                    <div style="margin:16px 0 12px;">🎉 <strong>全部就绪，可以发布了！</strong></div>
                    <div class="action-buttons">
                        <button class="action-btn primary" onclick="publishArticle()">📤 发布到公众号</button>
                        <button class="action-btn" onclick="showCoverSelector()">🔄 换封面</button>
                        <button class="action-btn" onclick="copyHtmlContent()">📋 复制HTML</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    chatArea.insertAdjacentHTML('beforeend', html);
    chatArea.scrollTop = chatArea.scrollHeight;
}

// 显示封面风格选择器
function showCoverSelector() {
    const chatArea = document.getElementById('chat-area');
    if (!chatArea) return;
    
    const styles = [
        { id: 'simple', name: '🎯 简约', desc: '纯色背景+标题' },
        { id: 'gradient', name: '🌈 渐变', desc: '渐变背景' },
        { id: 'tech', name: '💻 科技', desc: '科技感设计' },
        { id: 'warm', name: '☀️ 温暖', desc: '暖色调' }
    ];
    
    const html = `
        <div class="message assistant">
            <div class="avatar">✨</div>
            <div class="bubble">
                <div style="margin-bottom:12px;">🖼️ <strong>选择封面风格</strong></div>
                <div style="display:grid; grid-template-columns:repeat(2,1fr); gap:8px; margin-bottom:12px;">
                    ${styles.map(s => `
                        <button class="theme-chip" onclick="generateCoverWithStyle('${s.id}')">${s.name}</button>
                    `).join('')}
                </div>
                <div style="display:flex; gap:8px;">
                    <input type="text" id="cover-style-input" 
                        placeholder="或描述你想要的风格..." 
                        style="flex:1; background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.2); border-radius:8px; padding:10px 12px; color:white; outline:none; font-size:13px;"
                        onkeypress="if(event.key==='Enter')generateCoverWithCustomStyle()">
                    <button onclick="generateCoverWithCustomStyle()" 
                        style="background:var(--primary); color:white; border:none; border-radius:8px; padding:10px 14px; cursor:pointer; font-size:13px;">
                        生成
                    </button>
                </div>
            </div>
        </div>
    `;
    
    chatArea.insertAdjacentHTML('beforeend', html);
    chatArea.scrollTop = chatArea.scrollHeight;
}

// 使用指定风格生成封面
async function generateCoverWithStyle(styleId) {
    const styleMap = {
        'simple': '简约风格，纯色背景',
        'gradient': '渐变背景，现代感',
        'tech': '科技感，深色背景，几何图形',
        'warm': '温暖色调，橙色黄色'
    };
    state.coverStyle = styleMap[styleId] || styleId;
    await doGenerateCover();
}

// 使用自定义描述生成封面
async function generateCoverWithCustomStyle() {
    const input = document.getElementById('cover-style-input');
    const style = input?.value?.trim();
    if (style) {
        state.coverStyle = style;
    }
    await doGenerateCover();
}

// 跳过封面直接发布
function skipCoverAndPublish() {
    addMessage('好的，跳过封面。你可以直接发布或复制HTML。');
    const chatArea = document.getElementById('chat-area');
    chatArea.insertAdjacentHTML('beforeend', `
        <div class="message assistant">
            <div class="avatar">✨</div>
            <div class="bubble">
                <div class="action-buttons">
                    <button class="action-btn primary" onclick="publishArticle()">📤 发布到公众号</button>
                    <button class="action-btn" onclick="copyHtmlContent()">📋 复制HTML</button>
                </div>
            </div>
        </div>
    `);
    chatArea.scrollTop = chatArea.scrollHeight;
}

// 自动应用排版
async function autoApplyTheme() {
    state.theme = 'professional';
    await doApplyTheme();
}

// 显示主题选择器（横向网格 + 自定义输入）
function showThemeSelector() {
    const themes = [
        { id: 'professional', name: '💼 商务蓝' },
        { id: 'magazine', name: '📰 杂志风' },
        { id: 'fresh', name: '🌿 清新绿' },
        { id: 'elegant', name: '🎀 优雅粉' },
        { id: 'xiaohongshu', name: '📕 小红书' },
        { id: 'minimalist_notion', name: '📝 极简风' }
    ];
    
    let html = `
        <div class="message assistant">
            <div class="avatar">✨</div>
            <div class="bubble">
                <div style="margin-bottom:12px;">🎨 <strong>选择排版风格</strong></div>
                <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:16px;">
                    ${themes.map(t => `
                        <button class="theme-chip" onclick="selectAndApplyTheme('${t.id}')">${t.name}</button>
                    `).join('')}
                </div>
                <div style="display:flex; gap:8px;" id="custom-style-row">
                    <input type="text" class="custom-style-input" 
                        placeholder="或输入自定义风格..." 
                        style="flex:1; background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.2); border-radius:8px; padding:10px 12px; color:white; outline:none; font-size:13px;"
                        onkeypress="if(event.key==='Enter')applyCustomStyle(this)">
                    <button onclick="applyCustomStyle(this.previousElementSibling)" 
                        style="background:var(--primary); color:white; border:none; border-radius:8px; padding:10px 14px; cursor:pointer; font-size:13px;">
                        应用
                    </button>
                </div>
            </div>
        </div>
    `;
    
    const chatArea = document.getElementById('chat-area');
    chatArea.insertAdjacentHTML('beforeend', html);
    chatArea.scrollTop = chatArea.scrollHeight;
}

// 应用自定义风格
async function applyCustomStyle(inputEl) {
    // 优先使用传入的 input，否则查找最后一个
    let input = inputEl;
    if (!input) {
        const inputs = document.querySelectorAll('.custom-style-input');
        input = inputs.length > 0 ? inputs[inputs.length - 1] : null;
    }
    const styleDesc = input?.value?.trim();
    if (!styleDesc) {
        addMessage('请输入风格描述');
        return;
    }
    
    addMessage(`自定义风格: ${styleDesc}`, 'user');
    
    const loading = addProgress('AI 正在生成自定义风格...');
    
    try {
        const content = state.processedContent || state.rawContent;
        if (!content) {
            throw new Error('没有文章内容');
        }
        
        const res = await apiRequest('/api/convert-custom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, style_description: styleDesc })
        });
        const data = await res.json();
        
        if (data.html) {
            loading.complete('自定义风格应用完成');
            state.htmlContent = data.html;
            
            const previewArea = document.getElementById('preview-area');
            if (previewArea) {
                previewArea.innerHTML = data.html;
            }
            
            showNextStepOptions('theme');
        } else {
            throw new Error(data.error || '风格生成失败');
        }
    } catch (e) {
        loading.complete('生成失败');
        addMessage(`❌ ${e.message}`);
    }
}

async function selectAndApplyTheme(themeId) {
    state.theme = themeId;
    addMessage(`选择「${themeId}」风格`, 'user');
    await doApplyTheme();
}

// 自动生成封面
async function autoGenerateCover() {
    await doGenerateCover();
}
