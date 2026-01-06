"""
Markdown 转 HTML 转换器
专门适配微信公众号的格式要求
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
        # 如果没有找到一级标题，使用第一行非空内容作为标题
        for i, line in enumerate(lines):
            if line.strip():
                title = line.strip().lstrip('#').strip()
                content_start = i + 1
                break
    
    remaining_content = '\n'.join(lines[content_start:]).strip()
    return title, remaining_content


def extract_summary(md_content: str, max_length: int = 120) -> str:
    """
    从 Markdown 内容中提取摘要
    """
    # 移除 Markdown 语法
    text = re.sub(r'!\[.*?\]\(.*?\)', '', md_content)  # 移除图片
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # 保留链接文字
    text = re.sub(r'[#*`_~>\-]', '', text)  # 移除 Markdown 符号
    text = re.sub(r'\n+', ' ', text)  # 换行转空格
    text = re.sub(r'\s+', ' ', text).strip()  # 合并空格
    
    if len(text) > max_length:
        text = text[:max_length] + '...'
    
    return text


def get_heading_style(level: int, theme: dict) -> str:
    """根据主题生成标题样式"""
    style_type = theme.get('heading_style', 'normal')
    font_sizes = {1: 26, 2: 22, 3: 19, 4: 17, 5: 15, 6: 14}
    margins = {1: '36px 0 20px', 2: '30px 0 16px', 3: '24px 0 14px', 
               4: '20px 0 12px', 5: '16px 0 10px', 6: '14px 0 8px'}
    
    base_style = f"""
        margin: {margins[level]};
        padding: 0;
        font-size: {font_sizes[level]}px;
        font-weight: 700;
        color: {theme['heading_color']};
        line-height: 1.4;
        font-family: {theme['font_family']};
    """
    
    if style_type == 'underline':
        base_style += f"""
            padding-bottom: 10px;
            border-bottom: 2px solid {theme['primary_color']};
        """
    elif style_type == 'background':
        base_style += f"""
            background: linear-gradient(to right, {theme['primary_color']}15, transparent);
            padding: 12px 16px;
            border-radius: 6px;
            margin-left: -16px;
            margin-right: -16px;
        """
    elif style_type == 'border-left':
        base_style += f"""
            padding-left: 16px;
            border-left: 4px solid {theme['primary_color']};
        """
    
    return base_style.strip().replace('\n', ' ')


def convert_markdown_to_wechat_html(md_content: str, theme_name: str = "professional", custom_style: str = None) -> str:
    """
    将 Markdown 转换为适配微信公众号的 HTML
    
    Args:
        md_content: Markdown 内容
        theme_name: 主题名称
        custom_style: 用户自定义风格描述（如果提供，会影响生成的样式）
    
    Returns:
        适配公众号的 HTML 字符串
    """
    theme = THEMES.get(theme_name, THEMES["professional"])
    
    # 使用 markdown 库转换基础 HTML
    md = markdown.Markdown(extensions=[
        'extra',           # 表格、代码块等
        'codehilite',      # 代码高亮
        'toc',             # 目录
        'nl2br',           # 换行转 <br>
        'sane_lists',      # 更好的列表处理
    ])
    
    html_content = md.convert(md_content)
    
    # 使用 BeautifulSoup 处理 HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 获取主题配置
    line_height = theme.get('line_height', 1.8)
    paragraph_indent = theme.get('paragraph_indent', False)
    blockquote_bg = theme.get('blockquote_bg', theme['secondary_color'])
    
    # 处理段落
    for p in soup.find_all('p'):
        indent_style = 'text-indent: 2em;' if paragraph_indent else ''
        p['style'] = f"""
            margin: 0 0 20px 0;
            padding: 0;
            font-size: 16px;
            line-height: {line_height};
            color: {theme['text_color']};
            text-align: justify;
            font-family: {theme['font_family']};
            letter-spacing: 0.5px;
            {indent_style}
        """.strip().replace('\n', ' ')
    
    # 处理标题
    for level in range(1, 7):
        for h in soup.find_all(f'h{level}'):
            h['style'] = get_heading_style(level, theme)
    
    # 处理链接
    for a in soup.find_all('a'):
        a['style'] = f"""
            color: {theme['link_color']};
            text-decoration: none;
            border-bottom: 1px solid {theme['link_color']}50;
            word-break: break-all;
            transition: all 0.2s;
        """.strip().replace('\n', ' ')
    
    # 处理图片
    for img in soup.find_all('img'):
        img['style'] = """
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        """.strip().replace('\n', ' ')
        # 包裹在 section 中以便更好控制
        wrapper = soup.new_tag('section')
        wrapper['style'] = 'text-align: center; margin: 24px 0;'
        img.wrap(wrapper)
    
    # 处理代码块
    for pre in soup.find_all('pre'):
        pre['style'] = f"""
            background-color: {theme['code_bg']};
            padding: 20px;
            border-radius: 10px;
            overflow-x: auto;
            margin: 20px 0;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
            font-size: 13px;
            line-height: 1.6;
            border: 1px solid {theme['primary_color']}20;
        """.strip().replace('\n', ' ')
        
        # 处理代码块内的 code
        for code in pre.find_all('code'):
            code['style'] = f"""
                color: {theme['text_color']};
                font-family: inherit;
            """.strip().replace('\n', ' ')
    
    # 处理行内代码
    for code in soup.find_all('code'):
        if code.parent.name != 'pre':
            code['style'] = f"""
                background-color: {theme['code_bg']};
                padding: 3px 8px;
                border-radius: 4px;
                font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
                font-size: 14px;
                color: {theme['primary_color']};
                border: 1px solid {theme['primary_color']}30;
            """.strip().replace('\n', ' ')
    
    # 处理引用块
    for blockquote in soup.find_all('blockquote'):
        blockquote['style'] = f"""
            margin: 24px 0;
            padding: 16px 20px;
            border-left: 4px solid {theme['blockquote_border']};
            background-color: {blockquote_bg};
            border-radius: 0 8px 8px 0;
            color: {theme['text_color']};
        """.strip().replace('\n', ' ')
        # 处理引用块内的段落
        for p in blockquote.find_all('p'):
            p['style'] = f"""
                margin: 0;
                padding: 0;
                font-size: 15px;
                line-height: 1.7;
                color: {theme['text_color']};
                font-style: italic;
                text-indent: 0;
            """.strip().replace('\n', ' ')
    
    # 处理无序列表
    for ul in soup.find_all('ul'):
        ul['style'] = f"""
            margin: 20px 0;
            padding-left: 0;
            list-style: none;
            color: {theme['text_color']};
        """.strip().replace('\n', ' ')
    
    # 处理有序列表
    for ol in soup.find_all('ol'):
        ol['style'] = f"""
            margin: 20px 0;
            padding-left: 24px;
            color: {theme['text_color']};
        """.strip().replace('\n', ' ')
    
    # 处理列表项
    for i, li in enumerate(soup.find_all('li')):
        # 检查是否在无序列表中
        if li.parent.name == 'ul':
            li['style'] = f"""
                margin: 12px 0;
                line-height: {line_height};
                font-size: 16px;
                color: {theme['text_color']};
                padding-left: 24px;
                position: relative;
            """.strip().replace('\n', ' ')
            # 添加自定义圆点
            bullet = soup.new_tag('span')
            bullet['style'] = f"""
                position: absolute;
                left: 0;
                top: 0;
                color: {theme['primary_color']};
                font-weight: bold;
            """.strip().replace('\n', ' ')
            bullet.string = '●'
            li.insert(0, bullet)
        else:
            li['style'] = f"""
                margin: 12px 0;
                line-height: {line_height};
                font-size: 16px;
                color: {theme['text_color']};
            """.strip().replace('\n', ' ')
    
    # 处理表格
    for table in soup.find_all('table'):
        table['style'] = f"""
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
            font-size: 14px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        """.strip().replace('\n', ' ')
    
    for th in soup.find_all('th'):
        th['style'] = f"""
            border: 1px solid {theme['primary_color']}30;
            padding: 14px 16px;
            background-color: {theme['primary_color']};
            color: white;
            text-align: left;
            font-weight: 600;
        """.strip().replace('\n', ' ')
    
    for i, td in enumerate(soup.find_all('td')):
        row_bg = theme['secondary_color'] if i % 2 == 0 else 'transparent'
        td['style'] = f"""
            border: 1px solid {theme['primary_color']}20;
            padding: 12px 16px;
            color: {theme['text_color']};
            background-color: {row_bg};
        """.strip().replace('\n', ' ')
    
    # 处理分割线
    for hr in soup.find_all('hr'):
        hr['style'] = f"""
            border: none;
            height: 1px;
            background: linear-gradient(to right, transparent, {theme['primary_color']}50, transparent);
            margin: 32px 0;
        """.strip().replace('\n', ' ')
    
    # 处理加粗
    for strong in soup.find_all(['strong', 'b']):
        strong['style'] = f"""
            font-weight: 700;
            color: {theme['heading_color']};
        """.strip().replace('\n', ' ')
    
    # 处理斜体
    for em in soup.find_all(['em', 'i']):
        em['style'] = """
            font-style: italic;
        """.strip().replace('\n', ' ')
    
    # 生成最终 HTML
    final_html = f"""
<section style="
    padding: 24px 20px;
    background-color: {theme['secondary_color']};
    font-family: {theme['font_family']};
    color: {theme['text_color']};
    line-height: {line_height};
">
{str(soup)}
</section>
""".strip()
    
    return final_html


def generate_custom_style_html(md_content: str, style_description: str, deepseek_api_key: str = None) -> str:
    """
    根据用户自定义风格描述生成 HTML
    使用 AI 来解析风格描述并生成对应的样式
    """
    import openai
    
    if not deepseek_api_key:
        # 如果没有 API key，使用默认风格
        return convert_markdown_to_wechat_html(md_content, "professional")
    
    try:
        client = openai.OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        
        # 让 AI 生成 CSS 变量
        response = client.chat.completions.create(
            model="deepseek-chat",  # DeepSeek V3.2
            messages=[{
                "role": "user",
                "content": f"""根据以下风格描述，生成一组 CSS 颜色和字体配置（JSON格式）：

风格描述：{style_description}

请返回以下格式的 JSON（只返回 JSON，不要其他内容）：
{{
    "primary_color": "#颜色值",
    "secondary_color": "#背景色",
    "text_color": "#文字颜色",
    "heading_color": "#标题颜色",
    "link_color": "#链接颜色",
    "code_bg": "#代码背景色",
    "blockquote_border": "#引用边框色",
    "blockquote_bg": "#引用背景色",
    "font_family": "字体族",
    "heading_style": "normal/underline/background/border-left",
    "paragraph_indent": true/false,
    "line_height": 1.8
}}"""
            }],
            max_tokens=500
        )
        
        import json
        style_json = response.choices[0].message.content.strip()
        # 尝试提取 JSON
        if '```' in style_json:
            style_json = style_json.split('```')[1]
            if style_json.startswith('json'):
                style_json = style_json[4:]
        
        custom_theme = json.loads(style_json)
        
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


def extract_metadata(md_content: str) -> dict:
    """
    从 Markdown 内容中提取元数据
    
    Returns:
        包含 title, summary, images 的字典
    """
    title, remaining = extract_title_from_markdown(md_content)
    summary = extract_summary(remaining)
    
    # 提取所有图片链接
    images = re.findall(r'!\[.*?\]\((.*?)\)', md_content)
    
    return {
        "title": title,
        "summary": summary,
        "images": images,
        "content": remaining
    }


if __name__ == "__main__":
    # 测试代码
    test_md = """
# 这是一篇测试文章

这是文章的第一段，介绍一些内容。

## 二级标题

这里有一些**加粗文字**和*斜体文字*。

### 代码示例

```python
def hello():
    print("Hello, World!")
```

还有行内代码 `print("test")`。

> 这是一段引用文字
> 可以有多行

- 列表项 1
- 列表项 2
- 列表项 3

1. 有序列表 1
2. 有序列表 2

| 表头1 | 表头2 |
|-------|-------|
| 内容1 | 内容2 |

---

文章结束。
"""
    
    result = convert_markdown_to_wechat_html(test_md, "professional")
    print(result)
