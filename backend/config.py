"""
配置文件 - 存储 API 密钥和配置项
注意：所有 API Key 都应该从用户配置或环境变量加载，不要硬编码！
"""

# =============================================
# Poe API 配置（用于 AI 生成封面图）
# 从用户配置动态加载
# =============================================
POE_API_KEY = ""  # 由用户在设置中配置
POE_BASE_URL = "https://api.poe.com/v1"

# =============================================
# ImgBB 图床 API（可选，暂未使用）
# =============================================
IMGBB_API_KEY = ""  # 如需使用请让用户自行配置

# =============================================
# 微信公众号 API 配置（从用户配置加载）
# =============================================
WECHAT_APP_ID = ""  # 从用户配置动态加载
WECHAT_APP_SECRET = ""  # 从用户配置动态加载

# 第三方服务配置（可选）
WECHAT_API_URL = ""  # 例如：https://wx.limyai.com/api/openapi/wechat-accounts
WECHAT_API_KEY = ""  # 你的微信 API Key

# =============================================
# 主题风格配置 - 差异化设计
# =============================================
THEMES = {
    # ========== 深度洞察（首推） ==========
    "insight": {
        "name": "📰 深度洞察",
        "description": "经济学人/财新风格，大留白、克制配色，适合商业深度长文",
        "primary_color": "#1a1a1a",
        "secondary_color": "#ffffff",
        "accent_color": "#c41e3a",  # 点睛红，克制使用
        "text_color": "#2d2d2d",
        "heading_color": "#0d0d0d",
        "link_color": "#c41e3a",
        "code_bg": "#f7f7f7",
        "blockquote_border": "#c41e3a",
        "blockquote_bg": "#fafafa",
        "font_family": "'Noto Serif SC', 'Source Han Serif CN', Georgia, 'Times New Roman', serif",
        "heading_style": "editorial",  # 新样式：社论风格
        "paragraph_indent": True,  # 首行缩进，书籍感
        "line_height": 2.0,  # 大行距，阅读舒适
        "letter_spacing": 1,  # 字间距
    },
    
    # ========== 商务/专业类 ==========
    "professional": {
        "name": "💼 商务蓝",
        "description": "现代商务风，适合技术文章、深度分析",
        "primary_color": "#2563eb",
        "secondary_color": "#ffffff",
        "accent_color": "#3b82f6",
        "text_color": "#374151",
        "heading_color": "#1e3a5f",
        "link_color": "#2563eb",
        "code_bg": "#f1f5f9",
        "blockquote_border": "#3b82f6",
        "blockquote_bg": "#eff6ff",
        "font_family": "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif",
        "heading_style": "border-left",  # 左边框更有设计感
        "paragraph_indent": False,
        "line_height": 1.9,
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
    
    # ========== 2.0 高级设计风格 ==========
    "futurism": {
        "name": "🌌 赛博 2.0",
        "description": "高度视觉化，荧光描边与科技装饰",
        "primary_color": "#00f2ff",
        "secondary_color": "#0a0a0c",
        "accent_color": "#ff00e5",
        "text_color": "#e0e0e0",
        "heading_color": "#00f2ff",
        "link_color": "#00f2ff",
        "code_bg": "#16161a",
        "blockquote_border": "#ff00e5",
        "blockquote_bg": "#16161a",
        "font_family": "'Space Grotesk', 'JetBrains Mono', monospace",
        "heading_style": "futuristic",  # 新增
        "paragraph_indent": False,
        "line_height": 1.7,
        "decorative": True
    },
    
    "magazine": {
        "name": "📖 艺术杂志",
        "description": "优雅衬线体，大留白排版",
        "primary_color": "#1a1a1a",
        "secondary_color": "#ffffff",
        "accent_color": "#c19a6b",
        "text_color": "#333333",
        "heading_color": "#000000",
        "link_color": "#c19a6b",
        "code_bg": "#f9f9f9",
        "blockquote_border": "#c19a6b",
        "blockquote_bg": "#fcfaf4",
        "font_family": "'Noto Serif SC', 'Source Han Serif', Georgia, serif",
        "heading_style": "magazine",  # 新增
        "paragraph_indent": True,
        "line_height": 2.2,
        "decorative": True
    },
    
    "minimalist_notion": {
        "name": "📝 精致 Notion",
        "description": "极致呼吸感，单色精致美学",
        "primary_color": "#2f2e2b",
        "secondary_color": "#ffffff",
        "accent_color": "#ebeced",
        "text_color": "#37352f",
        "heading_color": "#1a1a1a",
        "link_color": "#2563eb",
        "code_bg": "#f7f6f3",
        "blockquote_border": "#ebeced",
        "blockquote_bg": "#f7f6f3",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "heading_style": "notion",  # 新增
        "paragraph_indent": False,
        "line_height": 1.8,
        "decorative": True
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
