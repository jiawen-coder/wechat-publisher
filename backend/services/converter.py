"""
Markdown 转 HTML 转换器
专门适配微信公众号的格式要求 - 精美排版版
"""

import re
import markdown
from bs4 import BeautifulSoup
from backend.config import THEMES


def extract_title_from_markdown(md_content: str) -> tuple[str, str]:
    """
    从 Markdown 内容中提取标题
    返回 (标题, 去除标题后的内容)
    """
    lines = md_content.strip().split('\n')
    title = ""
    content_start = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('# ') and not stripped.startswith('## '):
            title = stripped[2:].strip()
            content_start = i + 1
            break
    
    if not title:
        for i, line in enumerate(lines):
            if line.strip():
                title = line.strip().lstrip('#').strip()
                content_start = i + 1
                break
    
    remaining_content = '\n'.join(lines[content_start:]).strip()
    return title, remaining_content


def extract_summary(md_content: str, max_length: int = 120) -> str:
    """从 Markdown 内容中提取摘要"""
    text = re.sub(r'!\[.*?\]\(.*?\)', '', md_content)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'[#*`_~>\-]', '', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    if len(text) > max_length:
        text = text[:max_length] + '...'
    
    return text


def convert_markdown_to_wechat_html(md_content: str, theme_name: str = "professional", custom_style: str = None) -> str:
    """
    将 Markdown 转换为适配微信公众号的精美 HTML
    """
    if isinstance(theme_name, dict):
        theme = theme_name
    else:
        theme = THEMES.get(theme_name, THEMES["professional"])
    
    # 使用 markdown 库转换基础 HTML
    md = markdown.Markdown(extensions=[
        'extra',
        'codehilite',
        'toc',
        'nl2br',
        'sane_lists',
    ])
    
    html_content = md.convert(md_content)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 主题配置
    primary = theme['primary_color']
    secondary = theme['secondary_color']
    text_color = theme['text_color']
    heading_color = theme['heading_color']
    accent = theme.get('accent_color', primary)
    line_height = theme.get('line_height', 1.9)
    paragraph_indent = theme.get('paragraph_indent', False)
    blockquote_bg = theme.get('blockquote_bg', '#f8fafc')
    blockquote_border = theme.get('blockquote_border', primary)
    code_bg = theme.get('code_bg', '#f1f5f9')
    font_family = theme.get('font_family', "-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif")
    
    # ==================== 段落样式 ====================
    for p in soup.find_all('p'):
        indent = 'text-indent: 2em;' if paragraph_indent else ''
        p['style'] = f'''
            margin: 0 0 1.5em 0;
            font-size: 16px;
            line-height: {line_height};
            color: {text_color};
            letter-spacing: 0.5px;
            word-spacing: 2px;
            {indent}
        '''.strip().replace('\n', ' ').replace('  ', ' ')
    
    # ==================== 标题样式 ====================
    heading_configs = {
        1: {'size': 24, 'margin': '2em 0 1em', 'weight': 700},
        2: {'size': 20, 'margin': '2em 0 0.8em', 'weight': 700},
        3: {'size': 18, 'margin': '1.5em 0 0.6em', 'weight': 600},
        4: {'size': 16, 'margin': '1.2em 0 0.5em', 'weight': 600},
        5: {'size': 15, 'margin': '1em 0 0.4em', 'weight': 600},
        6: {'size': 14, 'margin': '0.8em 0 0.3em', 'weight': 600},
    }
    
    for level in range(1, 7):
        cfg = heading_configs[level]
        for h in soup.find_all(f'h{level}'):
            if level <= 2:
                # 一级二级标题：左边框 + 底部装饰线
                h['style'] = f'''
                    margin: {cfg['margin']};
                    font-size: {cfg['size']}px;
                    font-weight: {cfg['weight']};
                    color: {heading_color};
                    line-height: 1.4;
                    padding: 8px 0 12px 16px;
                    border-left: 4px solid {primary};
                    background: linear-gradient(90deg, {primary}08 0%, transparent 100%);
                    position: relative;
                '''.strip().replace('\n', ' ')
            else:
                # 三级及以下：简洁风格
                h['style'] = f'''
                    margin: {cfg['margin']};
                    font-size: {cfg['size']}px;
                    font-weight: {cfg['weight']};
                    color: {heading_color};
                    line-height: 1.4;
                '''.strip().replace('\n', ' ')
    
    # ==================== 链接样式 ====================
    for a in soup.find_all('a'):
        a['style'] = f'''
            color: {primary};
            text-decoration: none;
            border-bottom: 1px solid {primary}40;
            padding-bottom: 1px;
        '''.strip().replace('\n', ' ')
    
    # ==================== 图片样式 ====================
    for img in soup.find_all('img'):
        img['style'] = '''
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1.5em auto;
            border-radius: 8px;
        '''.strip().replace('\n', ' ')
        
        wrapper = soup.new_tag('section')
        wrapper['style'] = 'text-align: center; margin: 1.5em 0;'
        img.wrap(wrapper)
    
    # ==================== 代码块样式 ====================
    for pre in soup.find_all('pre'):
        pre['style'] = f'''
            background: {code_bg};
            padding: 16px 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1.5em 0;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
            border: 1px solid {primary}15;
        '''.strip().replace('\n', ' ')
        
        for code in pre.find_all('code'):
            code['style'] = f'color: {text_color}; font-family: inherit;'
    
    # 行内代码
    for code in soup.find_all('code'):
        if code.parent.name != 'pre':
            code['style'] = f'''
                background: {code_bg};
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 14px;
                color: {primary};
            '''.strip().replace('\n', ' ')
    
    # ==================== 引用块样式（公众号特色） ====================
    for blockquote in soup.find_all('blockquote'):
        blockquote['style'] = f'''
            margin: 1.5em 0;
            padding: 16px 20px 16px 20px;
            background: linear-gradient(135deg, {blockquote_bg} 0%, {secondary} 100%);
            border-left: 4px solid {blockquote_border};
            border-radius: 0 8px 8px 0;
            position: relative;
        '''.strip().replace('\n', ' ')
        
        # 引用块内段落
        for p in blockquote.find_all('p'):
            p['style'] = f'''
                margin: 0;
                font-size: 15px;
                line-height: 1.8;
                color: #64748b;
                font-style: italic;
            '''.strip().replace('\n', ' ')
    
    # ==================== 列表样式 ====================
    for ul in soup.find_all('ul'):
        ul['style'] = f'''
            margin: 1.2em 0;
            padding-left: 0;
            list-style: none;
        '''.strip().replace('\n', ' ')
    
    for ol in soup.find_all('ol'):
        ol['style'] = f'''
            margin: 1.2em 0;
            padding-left: 1.5em;
            color: {text_color};
        '''.strip().replace('\n', ' ')
    
    # 列表项
    for i, li in enumerate(soup.find_all('li')):
        if li.parent.name == 'ul':
            li['style'] = f'''
                margin: 0.6em 0;
                line-height: {line_height};
                font-size: 16px;
                color: {text_color};
                padding-left: 1.5em;
                position: relative;
            '''.strip().replace('\n', ' ')
            
            # 自定义圆点
            bullet = soup.new_tag('span')
            bullet['style'] = f'''
                position: absolute;
                left: 0;
                top: 0;
                color: {primary};
                font-size: 8px;
                line-height: {line_height};
            '''.strip().replace('\n', ' ')
            bullet.string = '●'
            li.insert(0, bullet)
        else:
            li['style'] = f'''
                margin: 0.6em 0;
                line-height: {line_height};
                font-size: 16px;
                color: {text_color};
            '''.strip().replace('\n', ' ')
    
    # ==================== 表格样式 ====================
    for table in soup.find_all('table'):
        table['style'] = '''
            width: 100%;
            border-collapse: collapse;
            margin: 1.5em 0;
            font-size: 14px;
            border-radius: 8px;
            overflow: hidden;
        '''.strip().replace('\n', ' ')
    
    for th in soup.find_all('th'):
        th['style'] = f'''
            padding: 12px 16px;
            background: {primary};
            color: white;
            text-align: left;
            font-weight: 600;
            border: none;
        '''.strip().replace('\n', ' ')
    
    for i, td in enumerate(soup.find_all('td')):
        bg = '#f8fafc' if i % 2 == 0 else 'white'
        td['style'] = f'''
            padding: 12px 16px;
            border-bottom: 1px solid #e2e8f0;
            color: {text_color};
            background: {bg};
        '''.strip().replace('\n', ' ')
    
    # ==================== 分割线 ====================
    for hr in soup.find_all('hr'):
        hr['style'] = f'''
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, {primary}30, transparent);
            margin: 2em 0;
        '''.strip().replace('\n', ' ')
    
    # ==================== 加粗/斜体 ====================
    for strong in soup.find_all(['strong', 'b']):
        strong['style'] = f'font-weight: 700; color: {heading_color};'
    
    for em in soup.find_all(['em', 'i']):
        em['style'] = 'font-style: italic;'
    
    # ==================== 最终包装 ====================
    final_html = f'''<section style="
    max-width: 100%;
    padding: 20px;
    background: {secondary};
    font-family: {font_family};
    color: {text_color};
    line-height: {line_height};
    -webkit-font-smoothing: antialiased;
">
{str(soup)}
</section>'''.strip()
    
    return final_html


def generate_custom_style_html(md_content: str, style_description: str, iflow_api_key: str = None) -> str:
    """根据用户自定义风格描述生成 HTML"""
    import openai
    import os
    import json
    
    if not iflow_api_key:
        return convert_markdown_to_wechat_html(md_content, "professional")
    
    try:
        client = openai.OpenAI(
            api_key=iflow_api_key,
            base_url="https://apis.iflow.cn/v1"
        )
        
        messages = [{
            "role": "user",
            "content": f"""你是一个顶级排版设计师。请根据用户描述，生成一个公众号样式的 JSON 配置。
风格描述：{style_description}

请返回以下格式的 JSON（只返回 JSON，不要其他回复）：
{{
    "primary_color": "#主题主色",
    "secondary_color": "#背景色",
    "accent_color": "#强调色",
    "text_color": "#正文颜色",
    "heading_color": "#标题颜色",
    "link_color": "#链接颜色",
    "code_bg": "#代码背景",
    "blockquote_border": "#引用边框色",
    "blockquote_bg": "#引用背景色",
    "font_family": "字体栈",
    "line_height": 1.9,
    "paragraph_indent": false
}}"""
        }]
        
        response = client.chat.completions.create(
            model="deepseek-v3",
            messages=messages,
            max_tokens=800
        )
        
        style_json_raw = response.choices[0].message.content.strip()
        
        if '```' in style_json_raw:
            style_json = style_json_raw.split('```')[1]
            if style_json.startswith('json'):
                style_json = style_json[4:]
        else:
            style_json = style_json_raw
        
        custom_theme = json.loads(style_json)
        
        # 补充缺失字段
        default_theme = THEMES["professional"]
        for key in default_theme:
            if key not in custom_theme:
                custom_theme[key] = default_theme[key]
        
        return convert_markdown_to_wechat_html(md_content, custom_theme)

    except Exception as e:
        print(f"❌ 自定义风格生成失败: {str(e)}")
        return convert_markdown_to_wechat_html(md_content, "professional")


def extract_metadata(md_content: str) -> dict:
    """从 Markdown 内容中提取元数据"""
    title, remaining = extract_title_from_markdown(md_content)
    summary = extract_summary(remaining)
    images = re.findall(r'!\[.*?\]\((.*?)\)', md_content)
    
    return {
        "title": title,
        "summary": summary,
        "images": images,
        "content": remaining
    }
