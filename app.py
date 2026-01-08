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

# 加载 .env 文件
def load_env_file():
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        print(f"Loading .env from {env_path}")
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")):
                        value = value[1:-1]
                    value = value.replace('\\n', '\n')
                    if key not in os.environ:
                        os.environ[key] = value

load_env_file()

# ==================== AI 提示词配置 ====================
# 所有提示词都从环境变量读取，方便在 Render 后台修改
# 环境变量格式: PROMPT_{NAME}

PROMPT_DEFAULTS = {
    # 文章改写/创作提示词 - PROMPT_WRITER
    "writer": """你是一位资深的微信公众号爆款文章写手，擅长将素材改写成引人入胜、传播力强的优质长文。

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
- 字数要充实，宁多勿少""",

    # 文章改写(v2 李继刚风格) - PROMPT_ARTICLE
    "article": """## Role: 资深微信公众号爆款写手 (李继刚风格 1.0)

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
---""",

    # HTML 排版样式生成 - PROMPT_LAYOUT
    "layout": """你是一位克制的视觉设计师。根据用户描述，生成公众号排版配置。

## 设计原则（张小龙式）：
- 克制：颜色不超过3种，装饰能省则省
- 让内容说话：排版服务于阅读，不喧宾夺主
- 舒适留白：行距宽松，段落呼吸

## 用户描述：{style_description}

## 返回 JSON（只返回JSON，不要其他内容）：
{{
    "primary_color": "#主色（标题、强调，只用一个色）",
    "secondary_color": "#背景色（白或接近白）",
    "text_color": "#正文色（深灰或黑）",
    "heading_color": "#标题色（可与primary一致）",
    "link_color": "#链接色（与primary一致即可）",
    "code_bg": "#代码背景（浅灰）",
    "blockquote_border": "#引用边框（与primary一致或灰色）",
    "blockquote_bg": "#引用背景（极浅色）",
    "font_family": "字体（优先系统字体，衬线用于深度阅读）",
    "heading_style": "minimal/editorial/border-left/normal",
    "paragraph_indent": false,
    "line_height": 2.0,
    "letter_spacing": 0.5
}}

注意：
- heading_style 推荐 minimal（极简）或 editorial（社论风）
- 背景色保持白或接近白，不要彩色背景
- 配色要克制，宁可单调也不要花哨""",

    # 封面图描述生成 - PROMPT_COVER
    "cover": """你是一位顶尖的视觉设计师。请根据文章信息，设计一个极具视觉张力的公众号封面图描述词（中英双语）。

文章标题：{title}
文章摘要：{summary}
视觉风格要求：{style}

要求：
1. 描述必须具体、视觉化、充满电影感或设计感。
2. 不要出现文字。
3. 直接输出描述词，不超过 60 字。""",

    # 聊天模式创作 - PROMPT_CHAT
    "chat": """你是专业的微信公众号写手。

【任务】{instruction}

【素材/参考】
{context}

【要求】
- 直接输出文章内容，使用 Markdown 格式
- 不要输出任何解释
- 标题用 # 开头
- 结构清晰，段落分明
- 1500-2000字""",
}

def get_prompt(name: str) -> str:
    """获取 AI 提示词（优先环境变量，否则默认值）"""
    env_key = f"PROMPT_{name.upper()}"
    return os.environ.get(env_key, PROMPT_DEFAULTS.get(name, ""))

def log_ai_call(endpoint, messages, response, model=None):
    """统一的 AI 调用日志记录"""
    print("\n" + "="*50)
    print(f"🤖 [AI 调用] 接口: {endpoint}")
    print(f"🤖 [AI 调用] 模型: {model or 'unknown'}")
    print(f"🤖 [AI 调用] Base URL: https://apis.iflow.cn/v1")
    print("-" * 20 + " [上下文/提示词] " + "-" * 20)
    for m in messages:
        role = m.get('role', 'unknown')
        content = m.get('content', '')
        # 如果内容太长，截断显示
        display_content = content if len(content) < 500 else content[:500] + "...(省略)"
        print(f"[{role}]: {display_content}")
    print("-" * 20 + " [AI 返回内容] " + "-" * 20)
    print(response)
    print("="*50 + "\n")

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
        "iflow_api_key": os.environ.get("IFLOW_API_KEY", ""),
        "groq_api_key": ""
    }
    
    if user_id == "guest":
        config = default_config.copy()
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                print(f"Guest config load error: {e}")
        
        # 核心修复：环境变量必须覆盖文件中的旧值
        if os.environ.get("IFLOW_API_KEY"):
            config["iflow_api_key"] = os.environ.get("IFLOW_API_KEY")
        if os.environ.get("GROQ_API_KEY"):
            config["groq_api_key"] = os.environ.get("GROQ_API_KEY")
            
        return config

    if user_id:
        # 优先从数据库加载（带错误保护）
        try:
            db_config = load_user_config_from_db(user_id)
            if db_config:
                # 检查关键字段是否存在
                poe_key = db_config.get('poe_api_key', '')
                print(f"📂 从数据库加载配置: user={user_id}, poe_key={'已配置' if poe_key else '未配置'}")
                return {**default_config, **db_config}
        except Exception as e:
            print(f"Database load error (falling back to file): {e}")
        
        # fallback 到本地文件
        try:
            user_config_path = get_user_config_path(user_id)
            if user_config_path.exists():
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    poe_key = file_config.get('poe_api_key', '')
                    print(f"📂 从本地文件加载配置: user={user_id}, poe_key={'已配置' if poe_key else '未配置'}")
                    return {**default_config, **file_config}
        except Exception as e:
            print(f"File load error: {e}")
    
    # 未登录或用户配置不存在，使用本地配置
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return {**default_config, **json.load(f)}
    except Exception as e:
        print(f"Config file load error: {e}")
    
    print(f"⚠ 使用默认配置: user={user_id}")
    return default_config


def save_user_config(config, user_id: str = None):
    """保存用户配置（优先保存到数据库，同时保存本地文件作为备份）"""
    print(f"💾 保存用户配置: user_id={user_id}, keys={list(config.keys())}")
    
    if user_id == "guest":
        # 访客配置保存到主配置文件 user_config.json
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print(f"✓ Guest 配置已保存到文件")
            return True
        except Exception as e:
            print(f"✗ Guest config save error: {e}")
            return False

    if user_id:
        # 优先保存到数据库
        db_saved = False
        if is_db_available():
            db_saved = save_user_config_to_db(user_id, config)
            if db_saved:
                print(f"✓ 配置已保存到数据库: {user_id}")
            else:
                print(f"✗ 数据库保存失败，将使用本地文件: {user_id}")
        else:
            print(f"⚠ 数据库不可用，使用本地文件: {user_id}")
        
        # 同时保存到本地文件作为备份
        try:
            user_config_path = get_user_config_path(user_id)
            with open(user_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"✓ 配置已保存到本地文件: {user_config_path}")
        except Exception as e:
            print(f"✗ 本地文件保存失败: {e}")
    else:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✓ 配置已保存到默认文件")


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
    """渲染主页"""
    # 注入配置给前端
    prompts = {
        "chat_system": get_prompt('chat'),
    }
    api_config = {
        "endpoint": "https://apis.iflow.cn/v1" + "/chat/completions",
        "model": "deepseek-v3"
    }
    return render_template('index.html', prompts=prompts, api_config=api_config)


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
        has_config = bool(user_config.get('iflow_api_key') or user_config.get('wechat_app_id'))
        
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
    user = None
    if 'user' in session:
        user = session['user']
    
    # 生产环境禁用访客模式，必须登录
    # 本地开发时可设置 ALLOW_GUEST=true 启用访客
    allow_guest = os.environ.get('ALLOW_GUEST', 'false').lower() == 'true'
    
    if not user:
        if allow_guest:
            # 本地开发：允许访客
            user = {
                "id": "guest",
                "name": "Guest 访客",
                "email": "guest@local.dev",
                "picture": "",
                "has_config": CONFIG_FILE.exists()
            }
            return jsonify({
                "logged_in": True,
                "user": user
            })
        else:
            # 生产环境：必须登录
            return jsonify({
                "logged_in": False,
                "user": None
            })
        
    return jsonify({
        "logged_in": True,
        "user": user
    })


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
            "iflow_api_key": cfg.get("iflow_api_key", "")[:10] + "***" if cfg.get("iflow_api_key") else "",
            "groq_api_key": cfg.get("groq_api_key", "")[:10] + "***" if cfg.get("groq_api_key") else "",
            "poe_api_key": cfg.get("poe_api_key", "")[:10] + "***" if cfg.get("poe_api_key") else "",
            "configured": bool(cfg.get("iflow_api_key")),  # 主要检查 iFlow API
            "user_id": user_id or ""
        })
    else:
        data = request.json
        cfg = load_user_config(user_id)
        for key in ["wechat_app_id", "wechat_app_secret", "imgbb_api_key", "poe_api_key", "iflow_api_key", "groq_api_key"]:
            if data.get(key):
                cfg[key] = data[key]
        save_user_config(cfg, user_id)
        return jsonify({"success": True, "message": "配置已保存", "user_id": user_id or ""})


@app.route('/api/config/keys', methods=['GET'])
def config_keys_api():
    """获取完整 API Keys（用于前端直接调用 AI API）"""
    user_id = request.headers.get('X-User-Id')
    
    if not user_id:
        # 如果没有 header 且 session 中也没有，则报错
        if 'user_id' not in session:
            return jsonify({"error": "请先登录"}), 401
        user_id = session['user_id']
    
    cfg = load_user_config(user_id)
    
    # 优先返回环境变量中的 Key（如果存在），确保 UI 设置项与环境一致
    iflow_key = os.environ.get("IFLOW_API_KEY") or cfg.get("iflow_api_key", "")
    groq_key = os.environ.get("GROQ_API_KEY") or cfg.get("groq_api_key", "")
    poe_key = os.environ.get("POE_API_KEY") or cfg.get("poe_api_key", "")

    # 返回完整的 API keys（仅限已登录用户）
    return jsonify({
        "iflow_api_key": iflow_key,
        "groq_api_key": groq_key,
        "poe_api_key": poe_key
    })


@app.route('/api/config/prompts', methods=['GET'])
def config_prompts_api():
    """获取 AI 提示词配置（从环境变量读取）"""
    return jsonify({
        "article_prompt": get_prompt('article'),
        "layout_prompt": get_prompt('layout'),
        "cover_prompt": get_prompt('cover'),
        "writer_prompt": get_prompt('writer'),
        "chat_prompt": get_prompt('chat'),
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
    api_key = cfg.get("iflow_api_key")
    
    # 调试日志
    print(f"[DEBUG convert_custom] user_id: {user_id}")
    print(f"[DEBUG convert_custom] style_description: {style_description}")
    print(f"[DEBUG convert_custom] iflow_api_key exists: {bool(api_key)}")
    if api_key:
        print(f"[DEBUG convert_custom] iflow_api_key prefix: {api_key[:10]}...")
    
    html = generate_custom_style_html(content, style_description, api_key)
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
    style = data.get('style', '')  # 用户输入的封面描述/主题关键词
    
    user_id = request.headers.get('X-User-Id')
    cfg = load_user_config(user_id)
    
    # 判断逻辑：
    # 1. 如果用户明确输入了封面描述（style），以用户输入为主
    # 2. 如果没有输入，则用 AI 根据文章内容自动生成
    
    cover_prompt = ""
    
    # 用户明确输入了封面描述
    if style and len(style.strip()) > 0:
        user_input = style.strip()
        # 如果用户输入的是具体主题（如"猫咪"），则结合文章主题生成描述
        if cfg.get("iflow_api_key"):
            try:
                client = openai.OpenAI(
                    api_key=cfg["iflow_api_key"],
                    base_url="https://apis.iflow.cn/v1"
                )
                
                # 新的 prompt：以用户输入为核心主题
                messages = [{
                    "role": "user",
                    "content": f"""你是一位顶尖视觉设计师。请根据用户指定的封面主题，设计一张公众号封面图的描述词。

用户指定的封面主题：{user_input}
文章标题（供参考）：{title}

要求：
1. 以用户指定的主题为核心进行设计
2. 描述必须具体、视觉化、有设计感
3. 不要出现文字
4. 适合作为文章封面，专业美观
5. 直接输出描述词，不超过 80 字"""
                }]
                
                response = client.chat.completions.create(
                    model="deepseek-v3",
                    messages=messages,
                    max_tokens=200
                )
                cover_prompt = response.choices[0].message.content.strip()
                log_ai_call("/api/cover [用户主题]", messages, cover_prompt, model="deepseek-v3")
            except Exception as e:
                print(f"AI 优化描述失败: {e}")
                cover_prompt = f"{user_input}，专业美观，适合作为文章封面"
        else:
            # 没有 AI，直接用用户输入
            cover_prompt = f"{user_input}，专业美观，适合作为文章封面"
    
    # 用户没有输入，根据文章内容自动生成
    elif cfg.get("iflow_api_key") and (summary or title):
        try:
            client = openai.OpenAI(
                api_key=cfg["iflow_api_key"],
                base_url="https://apis.iflow.cn/v1"
            )
            
            prompt = get_prompt('cover')
            messages = [{
                "role": "user",
                "content": prompt.format(
                    title=title, 
                    summary=summary, 
                    style='专业简约'
                )
            }]
            
            response = client.chat.completions.create(
                model="deepseek-v3",
                messages=messages,
                max_tokens=200
            )
            response_content = response.choices[0].message.content.strip()
            log_ai_call("/api/cover [自动生成]", messages, response_content, model="deepseek-v3")
            
            # 检查是否是 URL
            import re
            image_url = None
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]\)]+'
            markdown_pattern = r'!\[.*?\]\((https?://.*?)\)'
            mk_match = re.search(markdown_pattern, response_content)
            
            if mk_match:
                image_url = mk_match.group(1)
            else:
                urls = re.findall(url_pattern, response_content)
                for url in urls:
                    if any(ext in url.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', 'image', 'img']):
                        image_url = url
                        break
            
            cover_prompt = image_url if image_url else response_content
        except Exception as e:
            print(f"AI 生成提示词失败: {e}")
            cover_prompt = f"{title}，专业简约风格"
    else:
        cover_prompt = f"{title}，专业简约风格"
    
    # 2. 调用绘图服务
    output_dir = str(TEMP_DIR)
    
    # 检查并打印 POE API Key 状态
    poe_key = cfg.get("poe_api_key", "")
    if poe_key:
        print(f"✓ 已配置 POE API Key: {poe_key[:10]}...")
    else:
        print("✗ 未配置 POE API Key，将使用 fallback 封面")
    
    print(f"正在生成封面图，提示词: {cover_prompt[:50]}...")
    result = generate_cover_image(title=cover_prompt, theme_name=theme, output_dir=output_dir, poe_api_key=poe_key)
    
    if result["success"]:
        print(f"✓ POE 生成封面成功: {result['file_path']}")
        filename = os.path.basename(result["file_path"])
        return jsonify({"success": True, "image_url": f"/api/cover/{filename}", "prompt": cover_prompt})
    else:
        print(f"✗ POE 生成封面失败: {result.get('error', '未知错误')}")
        print("使用 fallback 封面...")
        result = generate_fallback_cover(title, theme, output_dir)
        if result["success"]:
            filename = os.path.basename(result["file_path"])
            return jsonify({"success": True, "image_url": f"/api/cover/{filename}", "prompt": cover_prompt, "fallback": True})
        return jsonify({"success": False, "error": result["error"]}), 500


def generate_custom_style_html(md_content: str, style_description: str, iflow_api_key: str = None) -> str:
    """根据用户自定义风格描述生成 HTML (使用简化 Prompt)"""
    import openai
    import json as json_lib
    
    print(f"[DEBUG generate_custom_style_html] 开始处理, style: {style_description}")
    print(f"[DEBUG generate_custom_style_html] API Key exists: {bool(iflow_api_key)}")
    
    if not iflow_api_key:
        print("[DEBUG generate_custom_style_html] ❌ 无 API Key，使用默认主题")
        return convert_markdown_to_wechat_html(md_content, "professional")
    
    try:
        # 获取样式 Prompt
        prompt = get_prompt('layout')

        print(f"[DEBUG generate_custom_style_html] 🚀 正在调用 AI (iFlow)...")
        api_base = "https://apis.iflow.cn/v1"
        model_name = "deepseek-v3"
        
        client = openai.OpenAI(api_key=iflow_api_key, base_url=api_base)
        messages = [{"role": "user", "content": prompt.format(style_description=style_description)}]
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=800
        )
        style_json = response.choices[0].message.content.strip()
        
        # 记录详细日志
        log_ai_call("/api/convert-custom [Function]", messages, style_json, model=model_name)
        print(f"[DEBUG generate_custom_style_html] ✅ AI 返回: {style_json[:200]}...")
        
        # 尝试提取 JSON（更健壮的处理）
        import re
        
        # 方法1：从代码块中提取
        if '```' in style_json:
            # 匹配 ```json ... ``` 或 ``` ... ```
            code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', style_json)
            if code_block_match:
                style_json = code_block_match.group(1).strip()
        
        # 方法2：如果还不是有效 JSON，尝试找到 { } 之间的内容
        if not style_json.startswith('{'):
            json_match = re.search(r'\{[\s\S]*\}', style_json)
            if json_match:
                style_json = json_match.group(0)
        
        print(f"[DEBUG generate_custom_style_html] 📝 清理后 JSON: {style_json[:100]}...")
        custom_theme = json_lib.loads(style_json)
        print(f"[DEBUG generate_custom_style_html] ✅ 解析成功: {list(custom_theme.keys())}")
        
        # 补充缺失的字段
        default_theme = THEMES["professional"]
        for key in default_theme:
            if key not in custom_theme:
                custom_theme[key] = default_theme[key]
        
        # 临时添加到主题中
        THEMES["_custom_"] = custom_theme
        return convert_markdown_to_wechat_html(md_content, "_custom_")
        
    except Exception as e:
        print(f"[DEBUG generate_custom_style_html] ❌ 自定义风格生成失败: {e}")
        import traceback
        traceback.print_exc()
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
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        ip_data = response.json()
        return jsonify({
            "success": True,
            "ip": ip_data.get("ip"),
            "note": "请将此IP添加到微信公众号后台的IP白名单中"
        })
    except Exception as e:
        # 本地环境可能无法获取公网 IP，返回友好提示而不是 500 错误
        return jsonify({
            "success": False,
            "ip": "本地开发环境",
            "error": "本地环境无需配置 IP 白名单"
        })



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
        # 清除 token 缓存，确保用最新的配置获取
        from backend.services.wechat_publisher import _token_cache
        _token_cache["access_token"] = None
        _token_cache["expires_at"] = 0
        
        # 获取 access_token，传入用户配置的 AppID 和 AppSecret
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
    """AI二次创作完整文章 - 使用 iFlow API"""
    data = request.json
    content = data.get('content', '')
    
    if not content:
        return jsonify({"success": False, "error": "内容为空"}), 400
    
    user_id = request.headers.get('X-User-Id')
    cfg = load_user_config(user_id)
    
    print(f"Rewrite API - User ID: {user_id}, Has iflow_key: {bool(cfg.get('iflow_api_key'))}")
    
    if not cfg.get("iflow_api_key"):
        return jsonify({"success": False, "error": "请先配置心流 API Key"}), 400
    
    try:
        api_base = "https://apis.iflow.cn/v1"
        model_name = "deepseek-v3"

        client = openai.OpenAI(
            api_key=cfg["iflow_api_key"],
            base_url=api_base
        )
        
        # 根据输入内容长度动态调整输出要求
        input_length = len(content)
        if input_length < 200:
            length_hint = "请将内容扩展成一篇 1500-2500 字的深度文章"
        elif input_length < 500:
            length_hint = "请将内容扩展成一篇 2000-3000 字的完整文章"
        else:
            length_hint = "请将内容改写成一篇不少于 2500 字的完整文章，保留所有要点并适当扩展"
        
        system_prompt = get_prompt('writer').format(length_hint=length_hint)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请将以下内容改写成一篇完整的公众号文章：\n\n---\n{content}\n---\n\n请直接输出完整文章："}
        ]
        
        response = client.chat.completions.create(
            model=model_name,  # DeepSeek V3.2
            messages=messages,
            max_tokens=4000,  # 降低到4000减少内存消耗（Render免费版限制）
            temperature=0.75,
            timeout=60  # 60秒超时
        )
        
        article = response.choices[0].message.content.strip()
        log_ai_call("/api/rewrite", messages, article, model=model_name)
        
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
    """与 AI 对话（ReAct Agent 架构）"""
    data = request.json
    messages = data.get('messages', [])
    stream = data.get('stream', False)
    context = data.get('context', {})  # 前端传入的文章上下文
    use_react = data.get('use_react', True)  # 是否使用 ReAct 模式
    
    user_id = request.headers.get('X-User-Id')
    cfg = load_user_config(user_id)
    
    if not cfg.get("iflow_api_key"):
        return jsonify({"error": "请先配置心流 API Key"}), 400
    
    api_base = "https://apis.iflow.cn/v1"
    
    # ReAct 模式：使用 Agent 进行推理
    if use_react and messages:
        try:
            from backend.services.react_agent import ReActAgent, MODELS
            
            print(f"🤖 [ReAct Agent] 启动，推理模型: {MODELS['agent']}")
            
            agent = ReActAgent(api_key=cfg["iflow_api_key"], api_base=api_base)
            
            # 获取最后一条用户消息
            user_input = messages[-1].get('content', '') if messages else ''
            history = messages[:-1] if len(messages) > 1 else []
            
            print(f"🤖 [ReAct Agent] 用户输入: {user_input[:100]}...")
            result = agent.run(user_input, context, history)
            print(f"🤖 [ReAct Agent] 结果: {result}")
        except Exception as e:
            import traceback
            print(f"🤖 [ReAct Agent] 错误: {str(e)}")
            print(traceback.format_exc())
            return jsonify({"error": f"Agent 错误: {str(e)}", "success": False}), 500
        
        if result.get("success"):
            # 构建响应
            response_data = {
                "react": True,
                "thought": result.get("thought", ""),
                "iterations": result.get("iterations", 1)
            }
            
            if result.get("final_answer"):
                response_data["final_answer"] = result["final_answer"]
            
            if result.get("action"):
                response_data["action"] = result["action"]
                response_data["action_input"] = result.get("action_input", {})
                response_data["needs_tool_execution"] = result.get("needs_tool_execution", False)
            
            return jsonify(response_data)
        else:
            return jsonify({"error": result.get("error", "Agent 执行失败")}), 500
    
    # 非 ReAct 模式：直接调用模型（兼容旧逻辑）
    model_name = "deepseek-v3"
    
    # 构建上下文感知的状态描述
    context_desc = ""
    if context.get('hasArticle'):
        context_desc = f"\n\n【当前文章状态】\n- 标题: {context.get('title', '未命名')}\n- 字数: {context.get('articleLength', 0)}\n- 排版: {context.get('theme', 'professional')}\n- 封面: {'已生成' if context.get('hasCover') else '未生成'}"
    
    print(f"🚀 [Chat Direct] Model: {model_name}, Stream: {stream}, Context: {bool(context)}")

    try:
        client = openai.OpenAI(
            api_key=cfg["iflow_api_key"],
            base_url=api_base
        )
        
        # Agent System Prompt（上下文感知）
        base_system = """你是一个专业的微信公众号创作 Agent，通过 Tools 帮助用户完成文章创作全流程。

【你的能力（Tools）】
1. **创作文章** → STREAM_REWRITE - 从零写文章、改写、加案例、润色
2. **排版美化** → UPDATE_STYLE - 切换预设主题 | GENERATE_STYLE - AI 生成自定义风格  
3. **生成封面** → UPDATE_COVER - 根据文章生成封面图
4. **搜索资料** → SEARCH_WEB - 搜索实时信息（开发中）

【工作模式】
- 用户说话/语音/上传文件 → 你理解意图 → 调用合适的 Tool → 右侧实时展示结果
- 对话框只做简短回复（确认、解释、询问），实际工作交给 Tool 完成
- 任何涉及内容变动的请求，必须调用 Tool！

【Tool 调用格式】
[OPERATION]{"action":"动作名","参数":"值"}[/OPERATION]

【可用动作】
- STREAM_REWRITE: {"action":"STREAM_REWRITE","instruction":"具体创作要求"}
- UPDATE_STYLE: {"action":"UPDATE_STYLE","theme":"主题ID"}
  主题可选: professional, magazine, minimalist_notion, futurism, elegant, fresh, xiaohongshu, zhihu
- GENERATE_STYLE: {"action":"GENERATE_STYLE","description":"风格描述"}
- UPDATE_COVER: {"action":"UPDATE_COVER","style":"封面风格描述"}

【对话示例】
用户: 帮我写一篇关于时间管理的文章
你: 好的！我来帮你创作一篇关于时间管理的干货文章 📝
[OPERATION]{"action":"STREAM_REWRITE","instruction":"写一篇关于时间管理的文章，干货实用风格，包含具体方法论"}[/OPERATION]

用户: 太长了，精简一下
你: 收到，正在精简内容，保留核心要点 ✂️
[OPERATION]{"action":"STREAM_REWRITE","instruction":"精简文章，删除冗余内容，保留核心干货"}[/OPERATION]

用户: 换个好看的排版
你: 给你换一个杂志风格的排版 🎨
[OPERATION]{"action":"UPDATE_STYLE","theme":"magazine"}[/OPERATION]

用户: 你好
你: 你好！👋 我是你的公众号创作助手。你可以直接告诉我想写什么，或者发语音/上传文件，我来帮你搞定！"""

        # 注入当前文章上下文
        default_chat_system = base_system + context_desc
        
        if not any(m.get('role') == 'system' for m in messages):
            messages = [{"role": "system", "content": default_chat_system}] + messages

        if stream:
            def generate():
                full_content = ""
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        stream=True,
                        timeout=120  # 2分钟超时
                    )
                    for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_content += content
                            yield f"data: {json.dumps({'choices': [{'delta': {'content': content}}]})}\n\n"
                    
                    # 记录完整回复日志
                    log_ai_call("/api/chat [STREAM]", messages, full_content, model=model_name)
                except Exception as e:
                    print(f"Stream error: {str(e)}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                finally:
                    yield "data: [DONE]\n\n"
                
            return app.response_class(
                generate(), 
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no'  # 禁用 Nginx 缓冲
                }
            )
        else:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=False
            )
            reply = response.choices[0].message.content
            log_ai_call("/api/chat [POST]", messages, reply, model=model_name)
            return jsonify({"reply": reply})
            
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/vision', methods=['POST'])
def vision_analyze():
    """图片识别 API（使用 qwen3-vl-plus 模型）"""
    data = request.json
    image_url = data.get('image_url')  # 图片 URL
    image_base64 = data.get('image_base64')  # 或 base64 编码
    prompt = data.get('prompt', '请描述这张图片的内容，如果是文档/笔记，请提取其中的文字内容')
    
    user_id = request.headers.get('X-User-Id')
    cfg = load_user_config(user_id)
    
    if not cfg.get("iflow_api_key"):
        return jsonify({"error": "请先配置心流 API Key"}), 400
    
    if not image_url and not image_base64:
        return jsonify({"error": "请提供图片 URL 或 base64 数据"}), 400
    
    api_base = "https://apis.iflow.cn/v1"
    vision_model = "qwen3-vl-plus"  # iFlow 的视觉模型
    
    print(f"🖼️ [Vision] 使用模型: {vision_model}")
    
    try:
        client = openai.OpenAI(
            api_key=cfg["iflow_api_key"],
            base_url=api_base
        )
        
        # 构建图片内容
        if image_url:
            image_content = {"type": "image_url", "image_url": {"url": image_url}}
        else:
            image_content = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                image_content
            ]
        }]
        
        response = client.chat.completions.create(
            model=vision_model,
            messages=messages,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        print(f"🖼️ [Vision] 识别结果: {result[:200]}...")
        
        return jsonify({
            "success": True,
            "content": result,
            "model": vision_model
        })
        
    except Exception as e:
        print(f"Vision error: {str(e)}")
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
