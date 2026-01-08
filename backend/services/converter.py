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


def preprocess_markdown_tables(md_content: str) -> str:
    """
    预处理 Markdown 内容，修复表格格式问题
    主要解决：表格行之间有空行导致无法正确解析的问题
    """
    lines = md_content.split('\n')
    result = []
    in_table = False
    table_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # 检测表格行（以 | 开头或结尾）
        is_table_line = stripped.startswith('|') or stripped.endswith('|') or re.match(r'^\|?[\s\-:|]+\|?$', stripped)
        
        if is_table_line and stripped:
            if not in_table:
                in_table = True
            table_lines.append(line)
        elif in_table:
            if not stripped:
                # 空行，可能是表格内的空行，先跳过
                continue
            else:
                # 非表格行，输出之前积累的表格
                if table_lines:
                    result.extend(table_lines)
                    result.append('')  # 表格后加空行
                    table_lines = []
                in_table = False
                result.append(line)
        else:
            result.append(line)
    
    # 处理末尾的表格
    if table_lines:
        result.extend(table_lines)
    
    return '\n'.join(result)


def convert_markdown_to_wechat_html(md_content: str, theme_name: str = "professional", custom_style: str = None) -> str:
    """
    将 Markdown 转换为适配微信公众号的精美 HTML
    
    排版标准参考：
    - 正文字号: 15-16px，行高 1.75-2.0
    - 段落间距: 1.2-1.5em
    - 侧边距: 内置 padding 保证手机端阅读
    - 字间距: 0.5-1px 提升阅读体验
    """
    # 预处理：修复表格格式
    md_content = preprocess_markdown_tables(md_content)
    
    if isinstance(theme_name, dict):
        theme = theme_name
    else:
        theme = THEMES.get(theme_name, THEMES["professional"])
    
    # 使用 markdown 库转换基础 HTML
    md = markdown.Markdown(extensions=[
        'extra',
        'tables',  # 显式启用表格支持
        'codehilite',
        'toc',
        'sane_lists',
        # 注意：移除 nl2br，因为它会干扰表格解析
    ])
    
    html_content = md.convert(md_content)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 主题配置
    primary = theme['primary_color']
    secondary = theme['secondary_color']
    text_color = theme['text_color']
    heading_color = theme['heading_color']
    accent = theme.get('accent_color', primary)
    line_height = theme.get('line_height', 1.85)
    paragraph_indent = theme.get('paragraph_indent', False)
    blockquote_bg = theme.get('blockquote_bg', '#f8f9fa')
    blockquote_border = theme.get('blockquote_border', primary)
    code_bg = theme.get('code_bg', '#f6f8fa')
    font_family = theme.get('font_family', "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif")
    heading_style = theme.get('heading_style', 'border-left')
    
    # ==================== 段落样式（核心阅读体验） ====================
    letter_spacing = theme.get('letter_spacing', 0.8)
    font_size = 16 if heading_style == 'editorial' else 15  # 社论风格用稍大字号
    
    for p in soup.find_all('p'):
        indent = 'text-indent: 2em;' if paragraph_indent else ''
        p['style'] = f'''
            margin: 0 0 1.4em 0;
            padding: 0;
            font-size: {font_size}px;
            line-height: {line_height};
            color: {text_color};
            letter-spacing: {letter_spacing}px;
            word-break: break-word;
            {indent}
        '''.strip().replace('\n', ' ').replace('  ', ' ')
    
    # ==================== 标题样式（视觉层次感） ====================
    heading_configs = {
        1: {'size': 22, 'margin_top': 32, 'margin_bottom': 20, 'weight': 700},
        2: {'size': 19, 'margin_top': 28, 'margin_bottom': 16, 'weight': 700},
        3: {'size': 17, 'margin_top': 24, 'margin_bottom': 12, 'weight': 600},
        4: {'size': 16, 'margin_top': 20, 'margin_bottom': 10, 'weight': 600},
        5: {'size': 15, 'margin_top': 16, 'margin_bottom': 8, 'weight': 600},
        6: {'size': 14, 'margin_top': 12, 'margin_bottom': 6, 'weight': 600},
    }
    
    for level in range(1, 7):
        cfg = heading_configs[level]
        for h in soup.find_all(f'h{level}'):
            base_style = f'''
                margin: {cfg['margin_top']}px 0 {cfg['margin_bottom']}px 0;
                font-size: {cfg['size']}px;
                font-weight: {cfg['weight']};
                color: {heading_color};
                line-height: 1.35;
                letter-spacing: 0.5px;
            '''
            
            if level == 1 and heading_style == 'minimal':
                # 极简风格大标题 - 无装饰，靠字重和留白
                h['style'] = f'''
                    margin: 32px 0 28px 0;
                    font-size: 24px;
                    font-weight: 600;
                    color: {heading_color};
                    line-height: 1.4;
                    letter-spacing: 1px;
                '''.strip().replace('\n', ' ')
            elif level == 2 and heading_style == 'minimal':
                # 极简风格二级标题 - 只靠字重区分
                h['style'] = f'''
                    margin: 28px 0 16px 0;
                    font-size: 17px;
                    font-weight: 600;
                    color: {heading_color};
                    line-height: 1.4;
                '''.strip().replace('\n', ' ')
            elif level == 1 and heading_style == 'editorial':
                # 社论风格大标题 - 居中、大气、衬线
                h['style'] = f'''
                    margin: 40px 0 32px 0;
                    font-size: 26px;
                    font-weight: 700;
                    color: {heading_color};
                    line-height: 1.4;
                    letter-spacing: 2px;
                    text-align: center;
                    font-family: 'Noto Serif SC', Georgia, serif;
                '''.strip().replace('\n', ' ')
            elif level == 2 and heading_style == 'editorial':
                # 社论风格二级标题 - 上方分隔线，克制有力
                h['style'] = f'''
                    margin: 36px 0 20px 0;
                    padding-top: 24px;
                    font-size: 18px;
                    font-weight: 600;
                    color: {heading_color};
                    line-height: 1.4;
                    letter-spacing: 1px;
                    border-top: 1px solid #e0e0e0;
                '''.strip().replace('\n', ' ')
            elif level <= 2 and heading_style == 'border-left':
                # 左边框风格 - 经典公众号样式
                h['style'] = (base_style + f'''
                    padding: 10px 0 10px 14px;
                    border-left: 3px solid {primary};
                    background: linear-gradient(90deg, {primary}06 0%, transparent 60%);
                ''').strip().replace('\n', ' ')
            elif level <= 2 and heading_style == 'underline':
                # 下划线风格
                h['style'] = (base_style + f'''
                    padding-bottom: 10px;
                    border-bottom: 2px solid {primary};
                ''').strip().replace('\n', ' ')
            elif level <= 2 and heading_style == 'background':
                # 背景高亮风格
                h['style'] = (base_style + f'''
                    padding: 12px 16px;
                    background: {primary}0d;
                    border-radius: 6px;
                ''').strip().replace('\n', ' ')
            else:
                # 简洁风格
                h['style'] = base_style.strip().replace('\n', ' ')
    
    # ==================== 链接样式 ====================
    for a in soup.find_all('a'):
        a['style'] = f'''
            color: {primary};
            text-decoration: none;
            border-bottom: 1px solid {primary}50;
            transition: all 0.2s;
        '''.strip().replace('\n', ' ')
    
    # ==================== 图片样式 ====================
    for img in soup.find_all('img'):
        img['style'] = '''
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border-radius: 6px;
        '''.strip().replace('\n', ' ')
        
        # 图片容器，增加上下间距
        wrapper = soup.new_tag('section')
        wrapper['style'] = 'text-align: center; margin: 20px 0; padding: 0;'
        img.wrap(wrapper)
    
    # ==================== 代码块样式 ====================
    for pre in soup.find_all('pre'):
        pre['style'] = f'''
            background: {code_bg};
            padding: 14px 18px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 18px 0;
            font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 13px;
            line-height: 1.55;
            border: 1px solid {primary}12;
        '''.strip().replace('\n', ' ')
        
        for code in pre.find_all('code'):
            code['style'] = f'color: {text_color}; font-family: inherit; background: none;'
    
    # 行内代码
    for code in soup.find_all('code'):
        if code.parent.name != 'pre':
            code['style'] = f'''
                background: {code_bg};
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'SF Mono', 'Monaco', monospace;
                font-size: 13px;
                color: #d63384;
            '''.strip().replace('\n', ' ')
    
    # ==================== 引用块样式（公众号特色，重要内容高亮） ====================
    for blockquote in soup.find_all('blockquote'):
        if heading_style == 'editorial':
            # 社论风格引用 - 居中、斜体、有分隔线，像书籍中的金句
            blockquote['style'] = f'''
                margin: 32px 24px;
                padding: 20px 0;
                background: transparent;
                border-top: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
                border-left: none;
                text-align: center;
            '''.strip().replace('\n', ' ')
            
            for p in blockquote.find_all('p'):
                p['style'] = f'''
                    margin: 0;
                    font-size: 15px;
                    line-height: 1.9;
                    color: #4a4a4a;
                    font-style: italic;
                    font-family: 'Noto Serif SC', Georgia, serif;
                '''.strip().replace('\n', ' ')
        else:
            # 默认引用样式
            blockquote['style'] = f'''
                margin: 20px 0;
                padding: 16px 18px;
                background: {blockquote_bg};
                border-left: 3px solid {blockquote_border};
                border-radius: 0 6px 6px 0;
            '''.strip().replace('\n', ' ')
            
            for p in blockquote.find_all('p'):
                p['style'] = f'''
                    margin: 0 0 8px 0;
                    font-size: 14px;
                    line-height: 1.75;
                    color: #5c6370;
                '''.strip().replace('\n', ' ')
            # 最后一个段落去掉底部 margin
            last_p = blockquote.find_all('p')
            if last_p:
                style = last_p[-1].get('style', '')
                last_p[-1]['style'] = style.replace('margin: 0 0 8px 0', 'margin: 0')
    
    # ==================== 列表样式（清晰的层次结构） ====================
    for ul in soup.find_all('ul'):
        ul['style'] = f'''
            margin: 16px 0;
            padding-left: 0;
            list-style: none;
        '''.strip().replace('\n', ' ')
    
    for ol in soup.find_all('ol'):
        ol['style'] = f'''
            margin: 16px 0;
            padding-left: 24px;
            color: {text_color};
        '''.strip().replace('\n', ' ')
    
    # 列表项
    for li in soup.find_all('li'):
        if li.parent.name == 'ul':
            li['style'] = f'''
                margin: 8px 0;
                line-height: 1.75;
                font-size: 15px;
                color: {text_color};
                padding-left: 20px;
                position: relative;
                letter-spacing: 0.5px;
            '''.strip().replace('\n', ' ')
            
            # 自定义圆点 - 使用主题色
            bullet = soup.new_tag('span')
            bullet['style'] = f'''
                position: absolute;
                left: 0;
                top: 8px;
                width: 6px;
                height: 6px;
                background: {primary};
                border-radius: 50%;
            '''.strip().replace('\n', ' ')
            bullet.string = ''
            li.insert(0, bullet)
        else:
            li['style'] = f'''
                margin: 8px 0;
                line-height: 1.75;
                font-size: 15px;
                color: {text_color};
                letter-spacing: 0.5px;
            '''.strip().replace('\n', ' ')
    
    # ==================== 表格样式（清晰的数据展示） ====================
    for table in soup.find_all('table'):
        table['style'] = '''
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
            border-radius: 6px;
            overflow: hidden;
            border: 1px solid #e5e7eb;
        '''.strip().replace('\n', ' ')
    
    for th in soup.find_all('th'):
        th['style'] = f'''
            padding: 10px 14px;
            background: {primary};
            color: white;
            text-align: left;
            font-weight: 600;
            font-size: 13px;
            border: none;
        '''.strip().replace('\n', ' ')
    
    # 表格行斑马纹
    for i, tr in enumerate(soup.find_all('tr')):
        if tr.find('th'):  # 跳过表头行
            continue
        bg = '#f9fafb' if i % 2 == 1 else 'white'
        tr['style'] = f'background: {bg};'
    
    for td in soup.find_all('td'):
        td['style'] = f'''
            padding: 10px 14px;
            border-bottom: 1px solid #e5e7eb;
            color: {text_color};
            font-size: 14px;
            line-height: 1.5;
        '''.strip().replace('\n', ' ')
    
    # ==================== 分割线（装饰性元素） ====================
    for hr in soup.find_all('hr'):
        hr['style'] = f'''
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, {primary}25 50%, transparent 100%);
            margin: 28px 0;
        '''.strip().replace('\n', ' ')
    
    # ==================== 加粗/斜体（重点强调） ====================
    for strong in soup.find_all(['strong', 'b']):
        strong['style'] = f'font-weight: 600; color: {heading_color};'
    
    for em in soup.find_all(['em', 'i']):
        em['style'] = f'font-style: italic; color: {text_color};'
    
    # ==================== 最终包装（根容器） ====================
    # 微信公众号最佳实践：适当内边距，保证移动端阅读体验
    final_html = f'''<section style="
        max-width: 100%;
        padding: 8px 0;
        background: {secondary};
        font-family: {font_family};
        color: {text_color};
        line-height: {line_height};
        font-size: 15px;
        letter-spacing: 0.5px;
        word-break: break-word;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
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
