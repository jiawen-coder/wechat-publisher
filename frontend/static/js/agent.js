/**
 * ReAct Agent 逻辑
 */

async function executeReActTool(action, actionInput) {
    console.log('🔧 [Tool]', action, actionInput);
    
    try {
        switch (action) {
            case 'write_article':
                const instruction = actionInput.instruction || '创作文章';
                // 写作使用流式，会自动更新预览
                const loading = addProgress('正在创作文章...');
                try {
                    await processWithAI(state.rawContent || '', instruction, true);
                    loading.complete('文章创作完成');
                    // 写完后显示下一步
                    showNextStepOptions('write');
                } catch (e) {
                    loading.complete('创作失败');
                    throw e;
                }
                break;
                
            case 'apply_theme':
                if (!state.processedContent && !state.rawContent) {
                    addMessage('还没有文章内容，先告诉我你想写什么？');
                    return;
                }
                state.theme = actionInput.theme || 'professional';
                await doApplyTheme();
                break;
                
            case 'generate_cover':
                if (!state.title) {
                    addMessage('还没有文章，先写完文章再生成封面吧。');
                    return;
                }
                state.coverStyle = actionInput.style || '';
                await doGenerateCover();
                break;
                
            default:
                addMessage(`暂不支持: ${action}`);
        }
    } catch (e) {
        addMessage(`❌ ${e.message}`);
    }
}

// 执行排版（统一入口）
async function doApplyTheme() {
    const content = state.processedContent || state.rawContent;
    if (!content) throw new Error('没有文章内容');
    
    const loading = addProgress(`排版中 (${state.theme})...`);
    
    try {
        const data = await convertToHtml(content, state.theme);
        
        if (data.html) {
            loading.complete('排版完成');
            state.htmlContent = data.html;
            if (data.title) state.title = data.title;
            if (data.summary) state.summary = data.summary;
            
            const previewArea = document.getElementById('preview-area');
            if (previewArea) {
                previewArea.innerHTML = data.html;
            }
            
            // 显示下一步
            showNextStepOptions('theme');
        } else {
            throw new Error(data.error || '排版失败');
        }
    } catch (e) {
        loading.complete('排版失败');
        throw e;
    }
}

// 执行封面生成（统一入口）
async function doGenerateCover() {
    if (!state.title) throw new Error('没有标题');
    
    const loading = addProgress('生成封面中...');
    
    try {
        const data = await generateCoverApi(
            state.title,
            state.summary,
            state.theme,
            state.coverStyle || ''
        );
        
        if (data.success && data.image_url) {
            loading.complete('封面生成完成');
            state.coverUrl = data.image_url;
            
            // 显示封面预览
            addMessage(`
                <div style="margin-bottom: 8px;">🖼️ 封面已生成</div>
                <img src="${data.image_url}" style="width: 100%; max-width: 280px; border-radius: 8px;">
            `);
            
            // 显示下一步
            showNextStepOptions('cover');
        } else {
            throw new Error(data.error || '封面生成失败');
        }
    } catch (e) {
        loading.complete('生成失败');
        throw e;
    }
}

function getToolDisplayName(action) {
    const names = {
        'write_article': '写作引擎',
        'apply_theme': '排版引擎',
        'generate_style': '风格生成器',
        'generate_cover': '封面生成器'
    };
    return names[action] || action;
}

