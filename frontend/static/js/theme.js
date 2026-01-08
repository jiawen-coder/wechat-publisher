/**
 * 排版主题（仅保留选择器功能）
 */

function selectTheme(themeName) {
    state.theme = themeName;
    document.querySelectorAll('.theme-option').forEach(el => {
        el.classList.toggle('selected', el.dataset.theme === themeName);
    });
}
