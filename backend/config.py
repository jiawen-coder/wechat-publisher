"""
配置文件 - 存储 API 密钥和配置项
请根据实际情况修改以下配置
"""

# =============================================
# Poe API 配置（用于 nano-banana-pro 生成封面图）
# =============================================
POE_API_KEY = "GcHgGlj3hH7SFrjaFnEO_-1NevMKSnbVU9CM-KWngR0"
POE_BASE_URL = "https://api.poe.com/v1"

# =============================================
# ImgBB 图床 API（免费图床服务）
# 获取地址：https://api.imgbb.com/
# =============================================
IMGBB_API_KEY = "9c68b63f2c97417f3431e7d448dbd409"

# =============================================
# 微信公众号 API 配置（官方 API）
# =============================================
WECHAT_APP_ID = "wx052d812236258509"
WECHAT_APP_SECRET = "57596b477b9cdec1853807a7bde7c772"

# 第三方服务配置（可选）
WECHAT_API_URL = ""  # 例如：https://wx.limyai.com/api/openapi/wechat-accounts
WECHAT_API_KEY = ""  # 你的微信 API Key

# =============================================
# 主题风格配置 - 差异化设计
# =============================================
THEMES = {
    # ========== 商务/专业类 ==========
    "professional": {
        "name": "💼 商务蓝",
        "description": "蓝色主色调，适合技术文章、深度分析",
        "primary_color": "#1a73e8",
        "secondary_color": "#f8f9fa",
        "text_color": "#202124",
        "heading_color": "#1a73e8",
        "link_color": "#1a73e8",
        "code_bg": "#f1f3f4",
        "blockquote_border": "#1a73e8",
        "blockquote_bg": "#e8f0fe",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "heading_style": "normal",  # normal, underline, background, border-left
        "paragraph_indent": False,
        "line_height": 1.8,
    },
    
    "corporate": {
        "name": "🏢 企业灰",
        "description": "沉稳灰色，适合企业公告、正式通知",
        "primary_color": "#424242",
        "secondary_color": "#fafafa",
        "text_color": "#212121",
        "heading_color": "#212121",
        "link_color": "#1565c0",
        "code_bg": "#eeeeee",
        "blockquote_border": "#9e9e9e",
        "blockquote_bg": "#f5f5f5",
        "font_family": "'PingFang SC', 'Microsoft YaHei', sans-serif",
        "heading_style": "underline",
        "paragraph_indent": False,
        "line_height": 1.75,
    },
    
    # ========== 科技/极客类 ==========
    "tech": {
        "name": "🚀 科技紫",
        "description": "渐变紫色，适合科技、AI、产品类",
        "primary_color": "#7c3aed",
        "secondary_color": "#faf5ff",
        "text_color": "#1f2937",
        "heading_color": "#7c3aed",
        "link_color": "#8b5cf6",
        "code_bg": "#f3e8ff",
        "blockquote_border": "#a78bfa",
        "blockquote_bg": "#ede9fe",
        "font_family": "'Inter', -apple-system, sans-serif",
        "heading_style": "background",
        "paragraph_indent": False,
        "line_height": 1.8,
    },
    
    "dark": {
        "name": "🌙 极客暗黑",
        "description": "深色背景，霓虹绿色，程序员最爱",
        "primary_color": "#10b981",
        "secondary_color": "#111827",
        "text_color": "#e5e7eb",
        "heading_color": "#34d399",
        "link_color": "#6ee7b7",
        "code_bg": "#1f2937",
        "blockquote_border": "#10b981",
        "blockquote_bg": "#1f2937",
        "font_family": "'JetBrains Mono', 'Fira Code', monospace",
        "heading_style": "border-left",
        "paragraph_indent": False,
        "line_height": 1.75,
    },
    
    "cyber": {
        "name": "⚡ 赛博朋克",
        "description": "霓虹粉蓝，未来科技感",
        "primary_color": "#ec4899",
        "secondary_color": "#0f172a",
        "text_color": "#cbd5e1",
        "heading_color": "#f472b6",
        "link_color": "#22d3ee",
        "code_bg": "#1e293b",
        "blockquote_border": "#06b6d4",
        "blockquote_bg": "#1e293b",
        "font_family": "'Space Grotesk', 'Noto Sans SC', sans-serif",
        "heading_style": "background",
        "paragraph_indent": False,
        "line_height": 1.7,
    },
    
    # ========== 文艺/生活类 ==========
    "elegant": {
        "name": "🎨 优雅紫",
        "description": "淡紫色调，适合散文、随笔、生活类",
        "primary_color": "#6b5b95",
        "secondary_color": "#fef7ff",
        "text_color": "#4a4a4a",
        "heading_color": "#6b5b95",
        "link_color": "#9b8bb8",
        "code_bg": "#f9f4ff",
        "blockquote_border": "#d8b4fe",
        "blockquote_bg": "#faf5ff",
        "font_family": "'Noto Serif SC', 'Source Han Serif', Georgia, serif",
        "heading_style": "normal",
        "paragraph_indent": True,
        "line_height": 2.0,
    },
    
    "warm": {
        "name": "☀️ 暖阳橙",
        "description": "温暖橙色，适合美食、旅行、生活分享",
        "primary_color": "#ea580c",
        "secondary_color": "#fffbeb",
        "text_color": "#431407",
        "heading_color": "#c2410c",
        "link_color": "#ea580c",
        "code_bg": "#fef3c7",
        "blockquote_border": "#fb923c",
        "blockquote_bg": "#ffedd5",
        "font_family": "'ZCOOL XiaoWei', 'Noto Sans SC', sans-serif",
        "heading_style": "normal",
        "paragraph_indent": False,
        "line_height": 1.9,
    },
    
    "fresh": {
        "name": "🌿 清新绿",
        "description": "自然绿色，适合健康、环保、户外类",
        "primary_color": "#059669",
        "secondary_color": "#f0fdf4",
        "text_color": "#166534",
        "heading_color": "#047857",
        "link_color": "#10b981",
        "code_bg": "#dcfce7",
        "blockquote_border": "#34d399",
        "blockquote_bg": "#ecfdf5",
        "font_family": "'Noto Sans SC', -apple-system, sans-serif",
        "heading_style": "border-left",
        "paragraph_indent": False,
        "line_height": 1.85,
    },
    
    "romantic": {
        "name": "🌸 浪漫粉",
        "description": "柔和粉色，适合情感、女性话题",
        "primary_color": "#db2777",
        "secondary_color": "#fdf2f8",
        "text_color": "#831843",
        "heading_color": "#be185d",
        "link_color": "#ec4899",
        "code_bg": "#fce7f3",
        "blockquote_border": "#f472b6",
        "blockquote_bg": "#fbcfe8",
        "font_family": "'LXGW WenKai', 'Noto Serif SC', serif",
        "heading_style": "normal",
        "paragraph_indent": True,
        "line_height": 2.0,
    },
    
    # ========== 极简/高级类 ==========
    "minimalist": {
        "name": "⬜ 极简白",
        "description": "纯净黑白，大量留白，高级感",
        "primary_color": "#18181b",
        "secondary_color": "#ffffff",
        "text_color": "#3f3f46",
        "heading_color": "#18181b",
        "link_color": "#18181b",
        "code_bg": "#f4f4f5",
        "blockquote_border": "#d4d4d8",
        "blockquote_bg": "#fafafa",
        "font_family": "'Inter', 'Noto Sans SC', sans-serif",
        "heading_style": "normal",
        "paragraph_indent": False,
        "line_height": 2.0,
    },
    
    "newspaper": {
        "name": "📰 报纸风",
        "description": "复古报纸排版，适合新闻、评论",
        "primary_color": "#1c1917",
        "secondary_color": "#fafaf9",
        "text_color": "#292524",
        "heading_color": "#0c0a09",
        "link_color": "#78716c",
        "code_bg": "#f5f5f4",
        "blockquote_border": "#a8a29e",
        "blockquote_bg": "#f5f5f4",
        "font_family": "'Noto Serif SC', 'Source Han Serif', Georgia, serif",
        "heading_style": "underline",
        "paragraph_indent": True,
        "line_height": 1.9,
    },
    
    "notion": {
        "name": "📝 Notion 风",
        "description": "清爽简洁，适合笔记、教程类",
        "primary_color": "#2563eb",
        "secondary_color": "#ffffff",
        "text_color": "#37352f",
        "heading_color": "#37352f",
        "link_color": "#2563eb",
        "code_bg": "#f7f6f3",
        "blockquote_border": "#e5e5e5",
        "blockquote_bg": "#f7f6f3",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "heading_style": "normal",
        "paragraph_indent": False,
        "line_height": 1.7,
    },
    
    # ========== 特色风格 ==========
    "wechat_official": {
        "name": "📱 微信官方",
        "description": "模仿微信官方文章风格",
        "primary_color": "#07c160",
        "secondary_color": "#ffffff",
        "text_color": "#3d3d3d",
        "heading_color": "#000000",
        "link_color": "#576b95",
        "code_bg": "#f2f2f2",
        "blockquote_border": "#07c160",
        "blockquote_bg": "#f2f2f2",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif",
        "heading_style": "normal",
        "paragraph_indent": False,
        "line_height": 1.75,
    },
    
    "zhihu": {
        "name": "🔵 知乎风",
        "description": "知乎蓝，适合知识分享、问答",
        "primary_color": "#0066ff",
        "secondary_color": "#ffffff",
        "text_color": "#1a1a1a",
        "heading_color": "#1a1a1a",
        "link_color": "#0066ff",
        "code_bg": "#f6f6f6",
        "blockquote_border": "#0066ff",
        "blockquote_bg": "#f6f6f6",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif",
        "heading_style": "normal",
        "paragraph_indent": False,
        "line_height": 1.8,
    },
    
    "xiaohongshu": {
        "name": "📕 小红书风",
        "description": "小红书红，适合种草、分享",
        "primary_color": "#ff2442",
        "secondary_color": "#fffaf0",
        "text_color": "#333333",
        "heading_color": "#ff2442",
        "link_color": "#ff2442",
        "code_bg": "#fff5f5",
        "blockquote_border": "#ff6b81",
        "blockquote_bg": "#fff0f3",
        "font_family": "'PingFang SC', 'Noto Sans SC', sans-serif",
        "heading_style": "background",
        "paragraph_indent": False,
        "line_height": 1.9,
    },
}

# =============================================
# 文章类型配置
# =============================================
ARTICLE_TYPES = {
    "normal": {
        "name": "普通文章",
        "description": "标准图文消息"
    },
    "original": {
        "name": "原创文章",
        "description": "声明原创，获得原创保护"
    }
}
