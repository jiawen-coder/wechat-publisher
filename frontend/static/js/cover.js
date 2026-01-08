/**
 * 封面生成（仅保留独立调用入口）
 */

async function generateCover() {
    if (!state.title) {
        addMessage('请先创作文章内容');
        return;
    }
    await doGenerateCover();
}
