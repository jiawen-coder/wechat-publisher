"""
封面图生成器
使用 Poe API 的 nano-banana-pro 模型生成封面图
支持备用方案：使用 Pillow 生成简单渐变封面图
"""

import os
import base64
import re
import requests
from datetime import datetime
from pathlib import Path

import openai
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from backend.config import POE_API_KEY, POE_BASE_URL, THEMES


def generate_cover_prompt(title: str, theme_name: str = "professional") -> str:
    """
    根据文章标题和主题生成封面图的提示词
    
    Args:
        title: 文章标题
        theme_name: 主题名称
    
    Returns:
        生成封面图的提示词
    """
    theme = THEMES.get(theme_name, THEMES["professional"])
    
    # 从环境变量读取主题风格提示词
    style_prompts = {
        "professional": os.environ.get("PROMPT_IMAGE_STYLE_PRO", "现代简约商务风格，蓝色渐变背景，科技感，专业干净"),
        "elegant": os.environ.get("PROMPT_IMAGE_STYLE_ELEGANT", "优雅文艺风格，紫色调，柔和温暖，艺术感"),
        "vibrant": os.environ.get("PROMPT_IMAGE_STYLE_VIBRANT", "活力动感风格，橙色调，明亮热情，几何图形"),
        "dark": os.environ.get("PROMPT_IMAGE_STYLE_DARK", "极客暗黑风格，深色背景，霓虹绿色点缀，赛博朋克"),
        "minimal": os.environ.get("PROMPT_IMAGE_STYLE_MINIMAL", "极简黑白风格，简洁大方，留白设计，高级感")
    }
    
    style = style_prompts.get(theme_name, style_prompts["professional"])
    
    # 简洁的提示词，让 AI 更好理解
    prompt = f"{title}，{style}，无文字，适合作为文章封面"
    
    return prompt


def generate_cover_image(title: str, theme_name: str = "professional", 
                         output_dir: str = "temp") -> dict:
    """
    使用 nano-banana-pro 生成封面图
    
    Args:
        title: 文章标题
        theme_name: 主题名称
        output_dir: 输出目录
    
    Returns:
        包含生成结果的字典 {"success": bool, "file_path": str, "error": str}
    """
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 生成提示词
    prompt = generate_cover_prompt(title, theme_name)
    
    try:
        # 检查 POE API Key
        if not POE_API_KEY:
            return {
                "success": False,
                "file_path": None,
                "url": None,
                "error": "未配置 POE API Key"
            }
        
        # 初始化 OpenAI 客户端（使用 Poe API）
        client = openai.OpenAI(
            api_key=POE_API_KEY,
            base_url=POE_BASE_URL,
        )
        
        # 调用 nano-banana 生成图片
        # 微信公众号封面图要求：2.35:1 比例
        print(f"正在生成封面图（等待 AI 响应，约需 30 秒）...")
        print(f"使用模型: nano-banana")
        print(f"提示词: {prompt}")
        
        chat = client.chat.completions.create(
            model="nano-banana",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            extra_body={
                "image_only": True
            },
            timeout=120  # 120 秒超时
        )
        
        # 获取响应内容
        response_content = chat.choices[0].message.content
        
        # nano-banana-pro 返回的是图片 URL 或 base64
        # 尝试从响应中提取图片
        image_url = None
        
        # 检查是否是 URL
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, response_content)
        
        for url in urls:
            if any(ext in url.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', 'image']):
                image_url = url
                break
        
        if image_url:
            # 下载图片
            print(f"下载图片: {image_url}")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = f"cover_{timestamp}.png"
            file_path = output_path / file_name
            
            # 保存原始图片
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # 调整图片尺寸为微信公众号要求的 900x383 (2.35:1)
            print("调整图片尺寸为 900x383...")
            img = Image.open(file_path)
            
            # 计算裁剪区域，保持中心
            target_ratio = 900 / 383  # 2.35:1
            current_ratio = img.width / img.height
            
            if current_ratio > target_ratio:
                # 图片太宽，裁剪左右
                new_width = int(img.height * target_ratio)
                left = (img.width - new_width) // 2
                img = img.crop((left, 0, left + new_width, img.height))
            else:
                # 图片太高，裁剪上下
                new_height = int(img.width / target_ratio)
                top = (img.height - new_height) // 2
                img = img.crop((0, top, img.width, top + new_height))
            
            # 缩放到精确尺寸
            img = img.resize((900, 383), Image.Resampling.LANCZOS)
            
            # 保存调整后的图片
            img.save(file_path, "PNG", quality=95)
            print(f"图片已调整为 {img.size}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "url": image_url,
                "error": None
            }
        
        # 如果没有找到 URL，可能是 base64 编码的图片
        base64_pattern = r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)'
        base64_match = re.search(base64_pattern, response_content)
        
        if base64_match:
            image_data = base64.b64decode(base64_match.group(1))
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = f"cover_{timestamp}.png"
            file_path = output_path / file_name
            
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "url": None,
                "error": None
            }
        
        # 如果都没有找到，返回原始响应
        return {
            "success": False,
            "file_path": None,
            "url": None,
            "error": f"无法从响应中提取图片。响应内容: {response_content[:500]}"
        }
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"POE API 调用异常: {error_msg}")
        return {
            "success": False,
            "file_path": None,
            "url": None,
            "error": error_msg
        }


def generate_cover_with_text(title: str, theme_name: str = "professional",
                             output_dir: str = "temp") -> dict:
    """
    生成带有标题文字的封面图（使用 Pillow 叠加文字）
    
    Args:
        title: 文章标题
        theme_name: 主题名称
        output_dir: 输出目录
    
    Returns:
        包含生成结果的字典
    """
    from PIL import Image, ImageDraw, ImageFont
    
    # 先生成背景图
    result = generate_cover_image(title, theme_name, output_dir)
    
    if not result["success"]:
        return result
    
    try:
        # 打开生成的图片
        img = Image.open(result["file_path"])
        
        # 创建绘图对象
        draw = ImageDraw.Draw(img)
        
        # 获取图片尺寸
        width, height = img.size
        
        # 尝试加载字体（Windows 系统字体）
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",    # 黑体
            "C:/Windows/Fonts/simsun.ttc",    # 宋体
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Linux
        ]
        
        font = None
        font_size = int(height * 0.08)  # 字体大小为图片高度的 8%
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
        
        if font is None:
            font = ImageFont.load_default()
        
        # 计算文字位置（居中）
        text_bbox = draw.textbbox((0, 0), title, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # 添加文字阴影
        shadow_offset = 2
        draw.text((x + shadow_offset, y + shadow_offset), title, 
                  font=font, fill=(0, 0, 0, 128))
        
        # 添加白色文字
        draw.text((x, y), title, font=font, fill=(255, 255, 255))
        
        # 保存图片
        img.save(result["file_path"])
        
        return result
        
    except Exception as e:
        # 如果添加文字失败，返回原始图片
        result["warning"] = f"添加文字失败: {str(e)}"
        return result


def generate_fallback_cover(title: str, theme_name: str = "professional", 
                            output_dir: str = "temp") -> dict:
    """
    生成备用封面图（使用 Pillow 生成渐变背景 + 标题）
    当 AI 生成失败时使用此方法
    
    Args:
        title: 文章标题
        theme_name: 主题名称
        output_dir: 输出目录
    
    Returns:
        {"success": bool, "file_path": str, "error": str}
    """
    theme = THEMES.get(theme_name, THEMES["professional"])
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # 封面图尺寸 (微信公众号推荐尺寸)
        # 官方推荐：头条封面 900x383 (2.35:1)
        width, height = 900, 383
        
        # 解析主题颜色
        primary = theme['primary_color'].lstrip('#')
        primary_rgb = tuple(int(primary[i:i+2], 16) for i in (0, 2, 4))
        
        # 创建渐变背景
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # 生成渐变效果
        for y in range(height):
            # 从深到浅的渐变
            ratio = y / height
            r = int(primary_rgb[0] * (1 - ratio * 0.5) + 30 * ratio)
            g = int(primary_rgb[1] * (1 - ratio * 0.5) + 30 * ratio)
            b = int(primary_rgb[2] * (1 - ratio * 0.5) + 60 * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # 添加一些装饰元素（圆形）
        for i in range(5):
            x = 100 + i * 180
            y = 50 + (i % 2) * 100
            size = 30 + i * 10
            opacity_color = (
                min(255, primary_rgb[0] + 50),
                min(255, primary_rgb[1] + 50),
                min(255, primary_rgb[2] + 50)
            )
            draw.ellipse([x - size, y - size, x + size, y + size], 
                        fill=opacity_color, outline=None)
        
        # 添加标题文字
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/msyhbd.ttc",    # 微软雅黑粗体
            "C:/Windows/Fonts/simhei.ttf",    # 黑体
            "/System/Library/Fonts/PingFang.ttc",  # macOS
        ]
        
        font = None
        font_size = 42
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
        
        if font is None:
            font = ImageFont.load_default()
        
        # 截断过长的标题
        display_title = title if len(title) <= 20 else title[:18] + "..."
        
        # 计算文字位置（居中）
        text_bbox = draw.textbbox((0, 0), display_title, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # 添加文字阴影
        shadow_offset = 3
        draw.text((x + shadow_offset, y + shadow_offset), display_title, 
                  font=font, fill=(0, 0, 0))
        
        # 添加白色文字
        draw.text((x, y), display_title, font=font, fill=(255, 255, 255))
        
        # 保存图片
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"cover_{timestamp}.png"
        file_path = output_path / file_name
        
        img.save(file_path, "PNG", quality=95)
        
        return {
            "success": True,
            "file_path": str(file_path),
            "url": None,
            "error": None,
            "method": "fallback"
        }
        
    except Exception as e:
        return {
            "success": False,
            "file_path": None,
            "url": None,
            "error": str(e)
        }


def generate_cover_image_with_fallback(title: str, theme_name: str = "professional",
                                       output_dir: str = "temp", 
                                       use_ai: bool = True,
                                       timeout: int = 60) -> dict:
    """
    生成封面图，优先使用 AI，失败则使用备用方案
    
    Args:
        title: 文章标题
        theme_name: 主题名称
        output_dir: 输出目录
        use_ai: 是否尝试使用 AI 生成
        timeout: AI 生成超时时间（秒）
    
    Returns:
        生成结果字典
    """
    if use_ai and POE_API_KEY:
        print("  尝试使用 AI 生成封面图...")
        result = generate_cover_image(title, theme_name, output_dir)
        
        if result["success"]:
            result["method"] = "ai"
            return result
        else:
            print(f"  AI 生成失败: {result['error']}")
            print("  使用备用方案生成封面图...")
    
    # 使用备用方案
    return generate_fallback_cover(title, theme_name, output_dir)


if __name__ == "__main__":
    # 测试备用封面图生成
    print("测试备用封面图生成...")
    result = generate_fallback_cover(
        title="Python 编程技巧分享",
        theme_name="professional"
    )
    print(result)
    
    if result["success"]:
        print(f"\n封面图已保存: {result['file_path']}")

