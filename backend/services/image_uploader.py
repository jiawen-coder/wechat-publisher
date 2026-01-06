"""
图片上传器
将本地图片上传到图床，获取在线链接
支持 ImgBB 等免费图床服务
"""

import os
import re
import base64
import requests
from pathlib import Path
from typing import Optional

from backend.config import IMGBB_API_KEY


def upload_to_imgbb(image_path: str, api_key: str = None) -> dict:
    """
    上传图片到 ImgBB 图床
    
    Args:
        image_path: 本地图片路径
        api_key: ImgBB API Key（如果不提供则使用配置文件中的）
    
    Returns:
        {"success": bool, "url": str, "display_url": str, "thumb_url": str, "error": str}
    """
    api_key = api_key or IMGBB_API_KEY
    
    if not api_key:
        return {
            "success": False,
            "url": None,
            "display_url": None,
            "thumb_url": None,
            "error": "未配置 ImgBB API Key，请在 config.py 中设置 IMGBB_API_KEY"
        }
    
    try:
        # 读取图片并转换为 base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # 上传到 ImgBB
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={
                "key": api_key,
                "image": image_data,
            },
            timeout=60
        )
        
        result = response.json()
        
        if result.get("success"):
            data = result["data"]
            return {
                "success": True,
                "url": data["url"],
                "display_url": data["display_url"],
                "thumb_url": data["thumb"]["url"],
                "delete_url": data.get("delete_url"),
                "error": None
            }
        else:
            return {
                "success": False,
                "url": None,
                "display_url": None,
                "thumb_url": None,
                "error": result.get("error", {}).get("message", "上传失败")
            }
            
    except Exception as e:
        return {
            "success": False,
            "url": None,
            "display_url": None,
            "thumb_url": None,
            "error": str(e)
        }


def upload_image(image_path: str, service: str = "imgbb") -> dict:
    """
    上传图片到指定图床服务
    
    Args:
        image_path: 本地图片路径
        service: 图床服务名称，目前支持 "imgbb"
    
    Returns:
        上传结果字典
    """
    if not os.path.exists(image_path):
        return {
            "success": False,
            "url": None,
            "error": f"文件不存在: {image_path}"
        }
    
    if service == "imgbb":
        return upload_to_imgbb(image_path)
    else:
        return {
            "success": False,
            "url": None,
            "error": f"不支持的图床服务: {service}"
        }


def process_markdown_images(md_content: str, base_dir: str = ".") -> tuple[str, list]:
    """
    处理 Markdown 中的本地图片，上传到图床并替换链接
    
    Args:
        md_content: Markdown 内容
        base_dir: 基础目录（用于解析相对路径）
    
    Returns:
        (处理后的 Markdown 内容, 上传结果列表)
    """
    # 匹配 Markdown 图片语法 ![alt](path)
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    results = []
    processed_content = md_content
    
    for match in re.finditer(image_pattern, md_content):
        alt_text = match.group(1)
        image_path = match.group(2)
        original_syntax = match.group(0)
        
        # 跳过已经是 URL 的图片
        if image_path.startswith(('http://', 'https://', 'data:')):
            results.append({
                "original": image_path,
                "uploaded": image_path,
                "success": True,
                "skipped": True
            })
            continue
        
        # 解析相对路径
        full_path = os.path.join(base_dir, image_path)
        
        if not os.path.exists(full_path):
            results.append({
                "original": image_path,
                "uploaded": None,
                "success": False,
                "error": f"文件不存在: {full_path}"
            })
            continue
        
        # 上传图片
        print(f"正在上传图片: {image_path}")
        upload_result = upload_image(full_path)
        
        if upload_result["success"]:
            # 替换为在线链接
            new_syntax = f'![{alt_text}]({upload_result["url"]})'
            processed_content = processed_content.replace(original_syntax, new_syntax, 1)
            
            results.append({
                "original": image_path,
                "uploaded": upload_result["url"],
                "success": True,
                "skipped": False
            })
            print(f"  ✓ 上传成功: {upload_result['url']}")
        else:
            results.append({
                "original": image_path,
                "uploaded": None,
                "success": False,
                "error": upload_result["error"]
            })
            print(f"  ✗ 上传失败: {upload_result['error']}")
    
    return processed_content, results


if __name__ == "__main__":
    # 测试代码
    test_md = """
# 测试文章

这是一张本地图片：
![测试图片](./images/test.png)

这是一张在线图片：
![在线图片](https://example.com/image.jpg)
"""
    
    processed, results = process_markdown_images(test_md, ".")
    print("处理结果：")
    for r in results:
        print(r)
    print("\n处理后的内容：")
    print(processed)

