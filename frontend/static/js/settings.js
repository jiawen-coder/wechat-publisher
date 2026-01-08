/**
 * 设置弹窗
 */

function openSettings() {
    const modal = document.getElementById('settings-modal');
    if (modal) {
        modal.style.display = 'flex';
        loadSettings();
    }
}

function closeSettings() {
    const modal = document.getElementById('settings-modal');
    if (modal) modal.style.display = 'none';
}

async function loadSettings() {
    try {
        const config = await getConfig();
        
        const mapping = {
            'iflow_api_key': 'setting-iflow-api-key',
            'poe_api_key': 'setting-poe-api-key',
            'groq_api_key': 'setting-groq-api-key',
            'imgbb_api_key': 'setting-imgbb-api-key',
            'wechat_appid': 'setting-wechat-appid',
            'wechat_secret': 'setting-wechat-secret'
        };
        
        Object.entries(mapping).forEach(([key, id]) => {
            const input = document.getElementById(id);
            if (input && config[key]) {
                input.value = config[key];
            }
        });
    } catch (e) {
        console.error('加载设置失败:', e);
    }
}

async function saveSettings() {
    const mapping = {
        'iflow_api_key': 'setting-iflow-api-key',
        'poe_api_key': 'setting-poe-api-key',
        'groq_api_key': 'setting-groq-api-key',
        'imgbb_api_key': 'setting-imgbb-api-key',
        'wechat_appid': 'setting-wechat-appid',
        'wechat_secret': 'setting-wechat-secret'
    };
    
    const config = {};
    
    Object.entries(mapping).forEach(([key, id]) => {
        const input = document.getElementById(id);
        if (input && input.value.trim()) {
            config[key] = input.value.trim();
        }
    });
    
    try {
        await saveConfig(config);
        addMessage('✅ 设置已保存');
        closeSettings();
    } catch (e) {
        addMessage('❌ 保存失败: ' + e.message);
    }
}
