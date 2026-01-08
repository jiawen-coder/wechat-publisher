/**
 * 语音输入
 */

let mediaRecorder = null;
let audioChunks = [];

async function toggleVoiceInput() {
    const btn = document.getElementById('voice-input-btn');
    
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        stopVoiceInput();
    } else {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                await processVoiceInput(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };
            
            mediaRecorder.start();
            if (btn) btn.classList.add('recording');
            
            const status = document.getElementById('voice-recording-status');
            if (status) status.style.display = 'flex';
            
        } catch (e) {
            addMessage('❌ 无法访问麦克风');
        }
    }
}

function stopVoiceInput() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
    
    const btn = document.getElementById('voice-input-btn');
    if (btn) btn.classList.remove('recording');
    
    const status = document.getElementById('voice-recording-status');
    if (status) status.style.display = 'none';
}

async function processVoiceInput(audioBlob) {
    const loading = addProgress('语音识别中...');
    
    try {
        const data = await transcribeVoice(audioBlob);
        
        if (data.success && data.text) {
            loading.complete('识别完成');
            const input = document.getElementById('free-chat-text');
            if (input) {
                input.value = data.text;
                sendFreeChat();
            }
        } else {
            throw new Error(data.error || '识别失败');
        }
    } catch (e) {
        loading.complete('识别失败');
        addMessage(`❌ ${e.message}`);
    }
}

