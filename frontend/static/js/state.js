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

    // 获取上下文（包含文章内容摘要供 AI 理解）
    getContext() {
        // 取 rawContent 前2000字作为上下文摘要（省内存）
        const contentPreview = (this.rawContent || this.processedContent || '').slice(0, 2000);
        return {
            hasArticle: !!(this.processedContent || this.rawContent),
            articleLength: (this.processedContent || this.rawContent || '').length,
            contentPreview: contentPreview,  // 传递实际内容给 AI
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

