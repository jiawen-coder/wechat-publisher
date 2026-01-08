/**
 * 全局状态管理
 */
const state = {
    userId: localStorage.getItem('userId') || 'guest',
    isGenerating: false,
    rawContent: '',
    processedContent: '',
    htmlContent: '',
    title: '',
    summary: '',
    theme: 'professional',
    coverUrl: '',
    coverStyle: '',
    chatHistory: [],
    currentStage: 'idle',
    
    // 获取上下文
    getContext() {
        return {
            hasArticle: !!(this.processedContent || this.rawContent),
            articleLength: (this.processedContent || '').length,
            title: this.title || '',
            theme: this.theme,
            hasCover: !!this.coverUrl
        };
    },
    
    // 重置状态
    reset() {
        this.rawContent = '';
        this.processedContent = '';
        this.htmlContent = '';
        this.title = '';
        this.summary = '';
        this.coverUrl = '';
        this.currentStage = 'idle';
    }
};

// 添加到历史记录
function addToHistory(role, content) {
    state.chatHistory.push({ role, content });
    if (state.chatHistory.length > 20) {
        state.chatHistory = state.chatHistory.slice(-20);
    }
}

