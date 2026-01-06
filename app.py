"""
微信公众号文章发布助手 - Web 应用
Flask 后端服务

项目结构:
├── app.py              # 主应用入口
├── backend/            # 后端代码
│   ├── config.py       # 配置文件
│   ├── api/            # API 路由
│   └── services/       # 业务服务
├── frontend/           # 前端代码
│   ├── templates/      # HTML 模板
│   └── static/         # 静态资源
├── data/               # 数据文件
│   ├── temp/           # 临时文件
│   └── uploads/        # 上传文件
└── docs/               # 文档
"""

import os
import sys
import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory, render_template, session
from flask_cors import CORS
import openai
import requests

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入后端服务
from backend.services.converter import convert_markdown_to_wechat_html, extract_metadata, generate_custom_style_html
from backend.services.cover_generator import generate_cover_image, generate_fallback_cover
from backend.services.image_uploader import process_markdown_images, upload_image
from backend.services.wechat_publisher import WeChatPublisher, get_access_token
from backend.config import THEMES

# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='frontend/templates',
            static_folder='frontend/static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'wechat-publisher-secret-key-2024')
CORS(app, supports_credentials=True)


# ==================== 全局错误处理 ====================
# 确保所有错误都返回 JSON 格式，而不是 HTML 页面

@app.errorhandler(404)
def not_found_error(error):
    """处理 404 错误"""
    return jsonify({"success": False, "error": "接口不存在"}), 404


@app.errorhandler(500)
def internal_server_error(error):
    """处理 500 错误"""
    import traceback
    print(f"500 Error: {str(error)}")
    print(traceback.format_exc())
    return jsonify({"success": False, "error": "服务器内部错误，请稍后重试"}), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """处理所有未捕获的异常"""
    import traceback
    print(f"Unhandled exception: {str(error)}")
    print(traceback.format_exc())
    # 返回 JSON 格式的错误信息
    return jsonify({"success": False, "error": f"服务器错误: {str(error)}"}), 500

# Google OAuth 配置
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')

# 配置路径
DATA_DIR = Path("data")
CONFIG_FILE = DATA_DIR / "user_config.json"
USERS_DIR = DATA_DIR / "users"  # 用户配置目录
TEMP_DIR = DATA_DIR / "temp"
UPLOADS_DIR = DATA_DIR / "uploads"

# 确保目录存在
TEMP_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
USERS_DIR.mkdir(parents=True, exist_ok=True)


# ==================== 用户管理 ====================

# 尝试导入数据库模块
try:
    from backend.db import (
        init_db, 
        load_user_config_from_db, 
        save_user_config_to_db, 
        is_db_available
    )
    # 初始化数据库表（非阻塞）
    try:
        init_db()
    except Exception as db_err:
        print(f"Database init failed (non-fatal): {db_err}")
except Exception as e:
    print(f"Database module not available: {e}")
    is_db_available = lambda: False
    load_user_config_from_db = lambda x: None
    save_user_config_to_db = lambda x, y: False


def get_user_config_path(user_id: str) -> Path:
    """获取用户配置文件路径"""
    # 使用 hash 确保文件名安全
    safe_id = hashlib.md5(user_id.encode()).hexdigest()
    return USERS_DIR / f"{safe_id}.json"


def load_user_config(user_id: str = None):
    """加载用户配置（优先从数据库加载，fallback 到本地文件）"""
    default_config = {
        "wechat_app_id": "",
        "wechat_app_secret": "",
        "imgbb_api_key": "",
        "poe_api_key": "",
        "deepseek_api_key": "",
        "groq_api_key": ""
    }
    
    if user_id:
        # 优先从数据库加载（带错误保护）
        try:
            db_config = load_user_config_from_db(user_id)
            if db_config:
                return {**default_config, **db_config}
        except Exception as e:
            print(f"Database load error (falling back to file): {e}")
        
        # fallback 到本地文件
        try:
            user_config_path = get_user_config_path(user_id)
            if user_config_path.exists():
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    return {**default_config, **json.load(f)}
        except Exception as e:
            print(f"File load error: {e}")
    
    # 未登录或用户配置不存在，使用本地配置
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return {**default_config, **json.load(f)}
    except Exception as e:
        print(f"Config file load error: {e}")
    
    return default_config


def save_user_config(config, user_id: str = None):
    """保存用户配置（优先保存到数据库，同时保存本地文件作为备份）"""
    if user_id:
        # 优先保存到数据库
        if is_db_available():
            save_user_config_to_db(user_id, config)
        
        # 同时保存到本地文件作为备份
        user_config_path = get_user_config_path(user_id)
        with open(user_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    else:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)


# ==================== 配置管理（兼容旧接口） ====================

def load_config():
    """加载配置（从请求上下文获取用户ID）"""
    try:
        from flask import has_request_context
        if has_request_context():
            user_id = request.headers.get('X-User-Id')
            return load_user_config(user_id)
    except:
        pass
    return load_user_config(None)


def save_config(config):
    """保存配置"""
    try:
        from flask import has_request_context
        if has_request_context():
            user_id = request.headers.get('X-User-Id')
            save_user_config(config, user_id)
            return
    except:
        pass
    save_user_config(config, None)


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """返回前端页面"""
    return render_template('index.html')


# ==================== Google 登录 API ====================

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Google 登录验证"""
    data = request.json
    credential = data.get('credential')
    
    if not credential:
        return jsonify({"success": False, "error": "缺少凭证"}), 400
    
    try:
        # 验证 Google ID Token
        # 使用 Google 的 tokeninfo 端点验证
        verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        response = requests.get(verify_url, timeout=10)
        
        if response.status_code != 200:
            return jsonify({"success": False, "error": "Token 验证失败"}), 401
        
        token_info = response.json()
        
        # 验证 audience（客户端ID）
        # if token_info.get('aud') != GOOGLE_CLIENT_ID:
        #     return jsonify({"success": False, "error": "无效的客户端"}), 401
        
        # 提取用户信息
        user_id = token_info.get('sub')  # Google 用户唯一ID
        email = token_info.get('email')
        name = token_info.get('name', email.split('@')[0] if email else 'User')
        picture = token_info.get('picture', '')
        
        # 保存到 session
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = name
        session['user_picture'] = picture
        
        # 检查是否有已保存的配置
        user_config = load_user_config(user_id)
        has_config = bool(user_config.get('deepseek_api_key') or user_config.get('wechat_app_id'))
        
        return jsonify({
            "success": True,
            "user": {
                "id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "has_config": has_config
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """退出登录"""
    session.clear()
    return jsonify({"success": True})


@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """获取登录状态"""
    if 'user_id' in session:
        return jsonify({
            "logged_in": True,
            "user": {
                "id": session.get('user_id'),
                "email": session.get('user_email'),
                "name": session.get('user_name'),
                "picture": session.get('user_picture')
            }
        })
    return jsonify({"logged_in": False})


# ==================== API 路由 ====================

@app.route('/api/config', methods=['GET', 'POST'])
def config_api():
    """获取或保存配置（支持按用户ID保存）"""
    # 从请求头获取用户ID（前端传递）
    user_id = request.headers.get('X-User-Id')
    
    if request.method == 'GET':
        cfg = load_user_config(user_id)
        return jsonify({
            "wechat_app_id": cfg.get("wechat_app_id", "")[:10] + "***" if cfg.get("wechat_app_id") else "",
            "wechat_app_secret": "***" if cfg.get("wechat_app_secret") else "",
            "imgbb_api_key": cfg.get("imgbb_api_key", "")[:10] + "***" if cfg.get("imgbb_api_key") else "",
            "deepseek_api_key": cfg.get("deepseek_api_key", "")[:10] + "***" if cfg.get("deepseek_api_key") else "",
            "groq_api_key": cfg.get("groq_api_key", "")[:10] + "***" if cfg.get("groq_api_key") else "",
            "configured": bool(cfg.get("deepseek_api_key")),  # 主要检查DeepSeek API
            "user_id": user_id or ""
        })
    else:
        data = request.json
        cfg = load_user_config(user_id)
        for key in ["wechat_app_id", "wechat_app_secret", "imgbb_api_key", "poe_api_key", "deepseek_api_key", "groq_api_key"]:
            if data.get(key):
                cfg[key] = data[key]
        save_user_config(cfg, user_id)
        return jsonify({"success": True, "message": "配置已保存", "user_id": user_id or ""})


@app.route('/api/config/keys', methods=['GET'])
def config_keys_api():
    """获取完整 API Keys（用于前端直接调用 AI API）"""
    user_id = request.headers.get('X-User-Id')
    
    if not user_id:
        return jsonify({"error": "请先登录"}), 401
    
    cfg = load_user_config(user_id)
    
    # 返回完整的 API keys（仅限已登录用户）
    return jsonify({
        "deepseek_api_key": cfg.get("deepseek_api_key", ""),
        "groq_api_key": cfg.get("groq_api_key", ""),
        "poe_api_key": cfg.get("poe_api_key", "")
    })


@app.route('/api/config/prompts', methods=['GET'])
def config_prompts_api():
    """获取 AI 提示词配置（从环境变量读取，简化为三大核心 Prompt）"""
    import os
    
    # --- 1. 文章改写 Prompt (李继刚风格 1.0) ---
    # 占位符: {content} (原文), {style} (用户选的风格)
    default_article_prompt = """## Role: 资深微信公众号爆款写手 (李继刚风格 1.0)

## Profile:
你是一位擅长深刻洞察、逻辑严密、表达富有节奏感的顶尖自媒体人。你的文章不仅有深度，更能引发情绪共鸣，排版精美。

## Rules:
1. **核心逻辑**：保留原文核心观点，不遗漏任何重要细节。
2. **深度扩展**：对每个观点进行多维度的论证，加入金句、案例或数据支撑。
3. **语言风格**：{style}
4. **结构规范**：
    - 使用 # 一级标题作为文章标题
    - 开篇必须引人入胜（金句开场或深刻提问）
    - 章节间使用 ## 二级标题，逻辑层层递进
    - 结尾必须有力，提供行动指南或深刻总结
5. **格式**：直接输出 Markdown 格式，不要任何解释说明。

## Content:
请基于以下内容进行创作：
---
{content}
---"""

    # --- 2. HTML 样式生成 Prompt (JSON 格式) ---
    # 占位符: {style_description} (用户描述的风格)
    default_layout_prompt = """根据以下风格描述，生成一组公众号专属的 CSS 配置（JSON格式）：

风格描述：{style_description}

请返回以下格式的 JSON（只返回 JSON，不要其他内容）：
{{
    "primary_color": "#主题色",
    "secondary_color": "#背景色",
    "text_color": "#正文颜色",
    "heading_color": "#标题颜色",
    "link_color": "#链接颜色",
    "code_bg": "#代码背景",
    "blockquote_border": "#引用边框",
    "blockquote_bg": "#引用背景色",
    "font_family": "字体集",
    "heading_style": "normal/underline/background/border-left",
    "paragraph_indent": true/false,
    "line_height": 1.8
}}"""

    # --- 3. 封面图描述生成 Prompt ---
    # 占位符: {title} (标题), {summary} (摘要), {style} (封面愿景)
    default_cover_prompt = """你是一位顶尖的视觉设计师。请根据文章信息，设计一个极具视觉张力的公众号封面图描述词（中英双语）。

文章标题：{title}
文章摘要：{summary}
视觉风格要求：{style}

要求：
1. 描述必须具体、视觉化、充满电影感或设计感。
2. 不要出现文字。
3. 直接输出描述词，不超过 60 字。"""

    return jsonify({
        "article_prompt": os.environ.get("PROMPT_ARTICLE", default_article_prompt),
        "layout_prompt": os.environ.get("PROMPT_LAYOUT", default_layout_prompt),
        "cover_prompt": os.environ.get("PROMPT_COVER", default_cover_prompt)
    })


@app.route('/api/convert', methods=['POST'])
def convert_content():
    """将 Markdown 转换为公众号 HTML"""
    data = request.json
    content = data.get('content', '')
    theme = data.get('theme', 'professional')
    
    if not content:
        return jsonify({"error": "内容不能为空"}), 400
    
    html = convert_markdown_to_wechat_html(content, theme)
    metadata = extract_metadata(content)
    
    return jsonify({
        "html": html,
        "title": metadata["title"],
        "summary": metadata["summary"]
    })


@app.route('/api/convert-custom', methods=['POST'])
def convert_custom():
    """使用自定义风格转换"""
    data = request.json
    content = data.get('content', '')
    style_description = data.get('style_description', '')
    
    if not content:
        return jsonify({"error": "内容不能为空"}), 400
    
    if not style_description:
        return jsonify({"error": "请提供风格描述"}), 400
    
    user_id = request.headers.get('X-User-Id')
    cfg = load_user_config(user_id)
    html = generate_custom_style_html(content, style_description, cfg.get("deepseek_api_key"))
    metadata = extract_metadata(content)
    
    return jsonify({
        "html": html,
        "title": metadata["title"],
        "summary": metadata["summary"]
    })


@app.route('/api/parse', methods=['POST'])
def parse_content():
    """解析内容，提取元数据"""
    data = request.json
    content = data.get('content', '')
    
    if not content:
        return jsonify({"error": "内容不能为空"}), 400
    
    metadata = extract_metadata(content)
    return jsonify({
        "title": metadata["title"],
        "summary": metadata["summary"],
        "images": metadata["images"],
        "word_count": len(content)
    })


@app.route('/api/generate-cover', methods=['POST'])
def generate_cover():
    """生成封面图"""
    data = request.json
    title = data.get('title', '')
    summary = data.get('summary', '')
    theme = data.get('theme', 'professional')
    style = data.get('style', '')  # 这里的 style 是封面愿景/自定义描述
    
    user_id = request.headers.get('X-User-Id')
    cfg = load_user_config(user_id)
    
    # 1. 获取封面描述 Prompt
    default_cover_prompt = """你是一位顶尖的视觉设计师。请根据文章信息，设计一个极具视觉张力的公众号封面图描述词（中英双语）。\n\n文章标题：{title}\n文章摘要：{summary}\n视觉风格要求：{style}\n\n要求：\n1. 描述必须具体、视觉化、充满电影感或设计感。\n2. 不要出现文字。\n3. 直接输出描述词，不超过 60 字。"""
    prompt = os.environ.get("PROMPT_COVER", default_cover_prompt)
    
    cover_prompt = title
    if cfg.get("deepseek_api_key") and (summary or title):
        try:
            client = openai.OpenAI(
                api_key=cfg["deepseek_api_key"],
                base_url="https://api.deepseek.com"
            )
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": prompt.format(
                        title=title, 
                        summary=summary, 
                        style=(style if style else '专业简约')
                    )
                }],
                max_tokens=100
            )
            cover_prompt = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI 生成提示词失败: {e}")
            cover_prompt = f"{title}，{style if style else '专业简约风格'}"
    
    # 2. 调用绘图服务
    output_dir = str(TEMP_DIR)
    if cfg.get("poe_api_key"):
        import backend.config as app_config
        app_config.POE_API_KEY = cfg["poe_api_key"]
    
    result = generate_cover_image(title=cover_prompt, theme_name=theme, output_dir=output_dir)
    # ... 后续逻辑保持一致 (正常返回或 fallback)
    if result["success"]:
        filename = os.path.basename(result["file_path"])
        return jsonify({"success": True, "image_url": f"/api/cover/{filename}", "prompt": cover_prompt})
    else:
        result = generate_fallback_cover(title, theme, output_dir)
        if result["success"]:
            filename = os.path.basename(result["file_path"])
            return jsonify({"success": True, "image_url": f"/api/cover/{filename}", "prompt": cover_prompt, "fallback": True})
        return jsonify({"success": False, "error": result["error"]}), 500


def generate_custom_style_html(md_content: str, style_description: str, deepseek_api_key: str = None) -> str:
    """根据用户自定义风格描述生成 HTML (使用简化 Prompt)"""
    import openai
    import json as json_lib
    if not deepseek_api_key:
        return convert_markdown_to_wechat_html(md_content, "professional")
    
    try:
        # 获取样式 Prompt
        default_layout_prompt = """根据以下风格描述，生成一组公众号专属的 CSS 配置（JSON格式）：

风格描述：{style_description}

请返回以下格式的 JSON（只返回 JSON，不要其他内容）：
{{
    "primary_color": "#主题色",
    "secondary_color": "#背景色",
    "text_color": "#正文颜色",
    "heading_color": "#标题颜色",
    "link_color": "#链接颜色",
    "code_bg": "#代码背景",
    "blockquote_border": "#引用边框",
    "blockquote_bg": "#引用背景色",
    "font_family": "字体集",
    "heading_style": "normal",
    "paragraph_indent": false,
    "line_height": 1.8
}}"""
        prompt = os.environ.get("PROMPT_LAYOUT", default_layout_prompt)

        client = openai.OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt.format(style_description=style_description)}],
            max_tokens=500
        )
        style_json = response.choices[0].message.content.strip()
        
        # 尝试提取 JSON
        if '```' in style_json:
            style_json = style_json.split('```')[1]
            if style_json.startswith('json'):
                style_json = style_json[4:]
        
        custom_theme = json_lib.loads(style_json)
        
        # 补充缺失的字段
        default_theme = THEMES["professional"]
        for key in default_theme:
            if key not in custom_theme:
                custom_theme[key] = default_theme[key]
        
        # 临时添加到主题中
        THEMES["_custom_"] = custom_theme
        return convert_markdown_to_wechat_html(md_content, "_custom_")
        
    except Exception as e:
        print(f"自定义风格生成失败: {e}")
        return convert_markdown_to_wechat_html(md_content, "professional")


@app.route('/api/themes')
def get_themes():
    """获取可用的主题列表"""
    return jsonify(THEMES)


@app.route('/api/server-ip')
def get_server_ip():
    """获取服务器出站IP地址（用于配置微信公众号白名单）"""
    import requests
    try:
        # 通过外部服务获取出站IP
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        ip_data = response.json()
        return jsonify({
            "success": True,
            "ip": ip_data.get("ip"),
            "note": "请将此IP添加到微信公众号后台的IP白名单中"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500



@app.route('/api/cover/<filename>')
def get_cover(filename):
    """获取封面图"""
    return send_from_directory(str(TEMP_DIR), filename)


@app.route('/api/publish', methods=['POST'])
def publish():
    """发布到公众号草稿箱"""
    data = request.json
    title = data.get('title', '')
    content = data.get('content', '')
    summary = data.get('summary', '')
    cover_path = data.get('cover_path', '')
    author = data.get('author', '')
    
    user_id = request.headers.get('X-User-Id')
    cfg = load_user_config(user_id)
    
    if not cfg.get("wechat_app_id") or not cfg.get("wechat_app_secret"):
        return jsonify({"error": "请先配置微信公众号 AppID 和 AppSecret"}), 400
    
    # 更新配置
    import backend.config as app_config
    app_config.WECHAT_APP_ID = cfg["wechat_app_id"]
    app_config.WECHAT_APP_SECRET = cfg["wechat_app_secret"]
    
    try:
        # 先直接调用 get_access_token 获取详细错误信息
        token_result = get_access_token(cfg["wechat_app_id"], cfg["wechat_app_secret"])
        if not token_result["success"]:
            error_msg = token_result.get("error", "未知错误")
            print(f"获取 access_token 失败: {error_msg}")
            return jsonify({"error": f"获取 access_token 失败: {error_msg}"}), 500
        
        publisher = WeChatPublisher(auto_token=False)
        publisher.access_token = token_result["access_token"]
        
        if not publisher.access_token:
            return jsonify({"error": "获取 access_token 失败: token 为空"}), 500
        
        local_cover_path = None
        if cover_path:
            filename = cover_path.split('/')[-1]
            local_cover_path = str(TEMP_DIR / filename)
        
        result = publisher.publish_article(
            title=title,
            content=content,
            author=author,
            digest=summary,
            cover_image_path=local_cover_path
        )
        
        if result["success"]:
            return jsonify({
                "success": True,
                "media_id": result["media_id"],
                "message": "发布成功！文章已保存到草稿箱"
            })
        else:
            return jsonify({"success": False, "error": result["error"]}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/rewrite', methods=['POST'])
def rewrite_article():
    """AI二次创作完整文章 - 使用 deepseek-v3"""
    data = request.json
    content = data.get('content', '')
    
    if not content:
        return jsonify({"success": False, "error": "内容为空"}), 400
    
    user_id = request.headers.get('X-User-Id')
    cfg = load_user_config(user_id)
    
    print(f"Rewrite API - User ID: {user_id}, Has deepseek_key: {bool(cfg.get('deepseek_api_key'))}")
    
    if not cfg.get("deepseek_api_key"):
        return jsonify({"success": False, "error": "请先配置 DeepSeek API Key"}), 400
    
    try:
        client = openai.OpenAI(
            api_key=cfg["deepseek_api_key"],
            base_url="https://api.deepseek.com"
        )
        
        # 根据输入内容长度动态调整输出要求
        input_length = len(content)
        if input_length < 200:
            length_hint = "请将内容扩展成一篇 1500-2500 字的深度文章"
        elif input_length < 500:
            length_hint = "请将内容扩展成一篇 2000-3000 字的完整文章"
        else:
            length_hint = "请将内容改写成一篇不少于 2500 字的完整文章，保留所有要点并适当扩展"
        
        system_prompt = f"""你是一位资深的微信公众号爆款文章写手，擅长将素材改写成引人入胜、传播力强的优质长文。

## 你的任务
{length_hint}，确保内容完整、有深度、有价值。

## 写作要求

### 1. 文章结构（必须完整）
- **标题**：一个吸引眼球的标题（使用 # 一级标题）
- **引言**：用一个引人入胜的开头抓住读者（可以是故事、问题、数据或金句）
- **正文**：分成 3-5 个清晰的章节，每个章节用 ## 二级标题
- **每个章节**：包含论点、论据、案例或数据支撑，段落丰富
- **结尾**：有力的总结，给读者留下深刻印象或行动指引

### 2. 内容质量
- 保留原文的所有核心观点，一个都不能丢
- 每个观点都要展开论述，不能一笔带过
- 适当补充相关的案例、数据、引用来增强说服力
- 逻辑清晰，层层递进，让读者有收获感

### 3. 语言风格
- 专业但不晦涩，通俗易懂
- 有节奏感，长短句结合
- 适当使用金句、比喻、排比增强可读性
- 段落不要太长，方便手机阅读

### 4. 格式规范
- 使用 Markdown 格式
- 一级标题 # 只用于文章主标题
- 二级标题 ## 用于章节
- 三级标题 ### 用于小节（如需要）
- 重点内容可用 **加粗** 强调
- 列表用 - 或数字

## 重要提醒
- 文章必须完整，从头写到尾，不能中途截断
- 不要输出任何解释说明，直接输出完整的 Markdown 文章
- 字数要充实，宁多勿少"""

        response = client.chat.completions.create(
            model="deepseek-chat",  # DeepSeek V3.2
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请将以下内容改写成一篇完整的公众号文章：\n\n---\n{content}\n---\n\n请直接输出完整文章："}
            ],
            max_tokens=4000,  # 降低到4000减少内存消耗（Render免费版限制）
            temperature=0.75,
            timeout=60  # 60秒超时
        )
        
        article = response.choices[0].message.content.strip()
        
        # 检查是否被截断（简单判断）
        if not article.endswith(('。', '！', '？', '"', '）', '…', '\n')):
            # 可能被截断，记录日志但仍返回
            print(f"Warning: Article may be truncated, length: {len(article)}")
        
        word_count = len(article.replace(' ', '').replace('\n', ''))
        
        return jsonify({
            "success": True,
            "article": article,
            "word_count": word_count
        })
        
    except Exception as e:
        import traceback
        print(f"Rewrite error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": f"AI处理失败: {str(e)}"}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """与 AI 对话"""
    data = request.json
    messages = data.get('messages', [])
    
    user_id = request.headers.get('X-User-Id')
    cfg = load_user_config(user_id)
    
    if not cfg.get("deepseek_api_key"):
        return jsonify({"error": "请先配置 DeepSeek API Key"}), 400
    
    try:
        client = openai.OpenAI(
            api_key=cfg["deepseek_api_key"],
            base_url="https://api.deepseek.com"
        )
        
        system_message = {
            "role": "system",
            "content": "你是一个微信公众号文章发布助手，帮助用户分析文章、推荐排版风格、建议封面图风格。请用友好专业的语气交流。"
        }
        
        response = client.chat.completions.create(
            model="deepseek-chat",  # DeepSeek V3.2
            messages=[system_message] + messages,
            max_tokens=500
        )
        
        return jsonify({"reply": response.choices[0].message.content})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传文件（支持 txt, md, docx, pdf）"""
    if 'file' not in request.files:
        return jsonify({"error": "没有上传文件"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "文件名为空"}), 400
    
    filename = file.filename.lower()
    content = ""
    
    try:
        if filename.endswith('.txt') or filename.endswith('.md'):
            content = file.read().decode('utf-8')
        elif filename.endswith('.docx'):
            from docx import Document
            import io
            doc = Document(io.BytesIO(file.read()))
            content = '\n\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
        elif filename.endswith('.pdf'):
            try:
                import fitz
                import io
                pdf_bytes = file.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                text_parts = [page.get_text() for page in doc]
                content = '\n\n'.join(text_parts)
                doc.close()
            except ImportError:
                return jsonify({"error": "需要安装 PyMuPDF 库。运行: pip install PyMuPDF"}), 500
        else:
            return jsonify({"error": "不支持的文件格式，请上传 .txt, .md, .docx 或 .pdf 文件"}), 400
        
        return jsonify({
            "success": True,
            "content": content,
            "filename": file.filename
        })
        
    except Exception as e:
        return jsonify({"error": f"文件读取失败: {str(e)}"}), 500


def groq_speech_to_text(audio_path: str, api_key: str) -> str:
    """使用 Groq Whisper API 转换音频为文字（免费、快速、支持长语音）"""
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    with open(audio_path, "rb") as f:
        files = {
            "file": (os.path.basename(audio_path), f, "audio/webm"),
            "model": (None, "whisper-large-v3"),
            "language": (None, "zh"),  # 中文
            "response_format": (None, "text")
        }
        
        response = requests.post(url, headers=headers, files=files, timeout=120)
    
    if response.status_code == 200:
        return response.text.strip()
    else:
        error_info = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"error": response.text}
        raise Exception(f"Groq API 错误: {error_info}")


@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    """语音转文字（使用 Groq Whisper API，免费、快速、支持长语音）"""
    if 'audio' not in request.files:
        return jsonify({"success": False, "error": "没有上传音频文件"}), 400
    
    audio_file = request.files['audio']
    user_id = request.headers.get('X-User-Id')
    cfg = load_user_config(user_id)
    
    # 检查是否配置了 Groq API Key
    groq_api_key = cfg.get("groq_api_key")
    
    if not groq_api_key:
        return jsonify({
            "success": False, 
            "error": "请先在设置中配置 Groq API Key（免费获取：console.groq.com）"
        }), 400
    
    try:
        audio_dir = TEMP_DIR / "audio"
        audio_dir.mkdir(exist_ok=True)
        
        # 获取文件扩展名
        original_filename = audio_file.filename or "recording.webm"
        ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'webm'
        
        # Groq 支持的格式：mp3, mp4, mpeg, mpga, m4a, wav, webm
        supported_formats = ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']
        if ext not in supported_formats:
            ext = 'webm'  # 默认
        
        temp_path = audio_dir / f"audio_{uuid.uuid4().hex}.{ext}"
        audio_file.save(str(temp_path))
        
        # 调用 Groq Whisper API
        text = groq_speech_to_text(str(temp_path), groq_api_key)
        
        # 清理临时文件
        try:
            temp_path.unlink()
        except:
            pass
        
        return jsonify({"success": True, "text": text})
        
    except Exception as e:
        error_msg = str(e)
        # 清理临时文件
        try:
            if 'temp_path' in locals():
                temp_path.unlink()
        except:
            pass
        
        return jsonify({
            "success": False,
            "error": f"语音识别失败: {error_msg}"
        }), 500


@app.route('/api/upload-image', methods=['POST'])
def upload_image_file():
    """上传图片到图床"""
    if 'image' not in request.files:
        return jsonify({"error": "没有上传图片"}), 400
    
    image_file = request.files['image']
    user_id = request.headers.get('X-User-Id')
    cfg = load_user_config(user_id)
    
    if not cfg.get("imgbb_api_key"):
        return jsonify({"error": "请先配置 ImgBB API Key"}), 400
    
    try:
        import base64
        import requests
        
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": cfg["imgbb_api_key"], "image": image_data},
            timeout=30
        )
        
        result = response.json()
        
        if result.get("success"):
            return jsonify({
                "success": True,
                "url": result["data"]["url"],
                "display_url": result["data"]["display_url"]
            })
        else:
            return jsonify({"error": "上传失败"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== 主入口 ====================

if __name__ == '__main__':
    print("=" * 50)
    print("📝 微信公众号文章发布助手")
    print("=" * 50)
    print(f"📂 项目目录: {os.getcwd()}")
    print(f"📁 数据目录: {DATA_DIR.absolute()}")
    print(f"🌐 访问地址: http://localhost:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
