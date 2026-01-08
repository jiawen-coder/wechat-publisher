/**
 * 发布功能
 */

async function publishArticle() {
    if (!state.htmlContent) {
        addMessage('请先完成排版');
        return;
    }
    
    if (state.isGenerating) return;
    setGeneratingState(true);
    
    const loading = addProgress('正在发布到草稿箱...');
    
    try {
        const data = await publishToDraft(
            state.title || '未命名文章',
            state.htmlContent,
            state.coverUrl
        );
        
        if (data.success) {
            loading.complete('发布成功');
            addMessage('✅ 文章已保存到公众号草稿箱，请登录公众号后台查看');
        } else {
            throw new Error(data.error || '发布失败');
        }
    } catch (e) {
        loading.complete('发布失败');
        addMessage(`❌ ${e.message}`);
    } finally {
        setGeneratingState(false);
    }
}

