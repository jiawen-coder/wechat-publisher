/**
 * 设置弹窗
 */

function openSettings() {
    const modal = document.getElementById('settings-modal');
    if (modal) {
        modal.style.display = 'flex';
        loadSettings();
        loadServerIP();
    }
}

function closeSettings() {
    const modal = document.getElementById('settings-modal');
    if (modal) modal.style.display = 'none';
}

async function loadSettings() {
    try {
        const config = await getConfig();
        
        // 后端返回字段 -> 前端 input id
        const mapping = {
            'iflow_api_key': 'setting-iflow-api-key',
            'poe_api_key': 'setting-poe-api-key',
            'groq_api_key': 'setting-groq-api-key',
            'imgbb_api_key': 'setting-imgbb-api-key',
            'wechat_app_id': 'setting-wechat-appid',
            'wechat_app_secret': 'setting-wechat-secret'
        };
        
        Object.entries(mapping).forEach(([key, id]) => {
            const input = document.getElementById(id);
            if (input && config[key]) {
                // 如果是已配置的（带***），显示占位符
                if (config[key].includes('***')) {
                    input.placeholder = '已配置（输入新值覆盖）';
                } else {
                    input.value = config[key];
                }
            }
        });
    } catch (e) {
        console.error('加载设置失败:', e);
    }
}

async function saveSettings() {
    // 前端 input id -> 后端字段名
    const mapping = {
        'setting-iflow-api-key': 'iflow_api_key',
        'setting-poe-api-key': 'poe_api_key',
        'setting-groq-api-key': 'groq_api_key',
        'setting-imgbb-api-key': 'imgbb_api_key',
        'setting-wechat-appid': 'wechat_app_id',
        'setting-wechat-secret': 'wechat_app_secret'
    };
    
    const config = {};
    
    Object.entries(mapping).forEach(([id, key]) => {
        const input = document.getElementById(id);
        if (input && input.value.trim()) {
            config[key] = input.value.trim();
        }
    });
    
    try {
        const res = await saveConfig(config);
        const data = await res.json();
        
        if (data.success) {
            addMessage('✅ 设置已保存' + (state.user ? '（已关联到你的账号）' : ''));
            closeSettings();
        } else {
            throw new Error(data.error || '保存失败');
        }
    } catch (e) {
        addMessage('❌ 保存失败: ' + e.message);
    }
}

// 加载服务器 IP
async function loadServerIP() {
    const ipDisplay = document.getElementById('server-ip-display');
    if (!ipDisplay) return;
    
    try {
        const res = await fetch('/api/server-ip');
        const data = await res.json();
        ipDisplay.textContent = data.success ? data.ip : (data.ip || '获取失败');
    } catch (e) {
        ipDisplay.textContent = '网络错误';
    }
}

// 复制服务器 IP
async function copyServerIP() {
    const ip = document.getElementById('server-ip-display')?.textContent;
    if (ip && ip !== '加载中...' && ip !== '获取失败' && ip !== '网络错误') {
        try {
            await navigator.clipboard.writeText(ip);
            addMessage('✅ IP 已复制到剪贴板');
        } catch (e) {
            // 降级方案
            const input = document.createElement('input');
            input.value = ip;
            document.body.appendChild(input);
            input.select();
            document.execCommand('copy');
            document.body.removeChild(input);
            addMessage('✅ IP 已复制');
        }
    }
}
