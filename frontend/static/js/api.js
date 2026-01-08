/**
 * API 请求封装
 */

async function apiRequest(url, options = {}) {
    const headers = {
        'X-User-Id': state.userId || 'guest',
        ...options.headers
    };
    return fetch(url, { ...options, headers });
}

async function getConfig() {
    const res = await apiRequest('/api/config');
    return res.json();
}

async function saveConfig(config) {
    return apiRequest('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });
}

async function getConfigKeys() {
    const res = await apiRequest('/api/config/keys');
    return res.json();
}

async function chatWithAgent(messages, context) {
    return apiRequest('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            messages,
            stream: false,
            use_react: true,
            context
        })
    });
}

async function chatStream(messages, task = 'chat') {
    return apiRequest('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            messages,
            stream: true,
            use_react: false,
            task
        })
    });
}

async function parseContent(content) {
    const res = await apiRequest('/api/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
    });
    return res.json();
}

async function convertToHtml(content, theme, customStyle = '') {
    const res = await apiRequest('/api/convert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, theme, custom_style: customStyle })
    });
    return res.json();
}

async function generateCoverApi(title, summary, theme, style) {
    const res = await apiRequest('/api/generate-cover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, summary, theme, style })
    });
    return res.json();
}

async function uploadFile(formData) {
    return apiRequest('/api/upload', {
        method: 'POST',
        body: formData
    });
}

async function transcribeVoice(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    const res = await apiRequest('/api/transcribe', {
        method: 'POST',
        body: formData
    });
    return res.json();
}

async function publishToDraft(title, content, coverUrl, summary = '') {
    const res = await apiRequest('/api/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            title,
            content,
            summary,
            cover_path: coverUrl  // 后端需要的是 cover_path
        })
    });
    return res.json();
}

