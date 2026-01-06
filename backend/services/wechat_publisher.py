"""
微信公众号发布器
通过微信公众号 API 将文章发布到草稿箱

官方文档：https://developers.weixin.qq.com/doc/service/api/draftbox/draftmanage/api_draft_add.html
"""

import requests
import time
from typing import Optional

from backend.config import WECHAT_API_URL, WECHAT_API_KEY, WECHAT_APP_ID, WECHAT_APP_SECRET


# 缓存 access_token
_token_cache = {
    "access_token": None,
    "expires_at": 0
}


def get_access_token(app_id: str = None, app_secret: str = None) -> dict:
    """
    获取微信 access_token
    
    Args:
        app_id: 微信 AppID
        app_secret: 微信 AppSecret
    
    Returns:
        {"success": bool, "access_token": str, "expires_in": int, "error": str}
    """
    global _token_cache
    
    app_id = app_id or WECHAT_APP_ID
    app_secret = app_secret or WECHAT_APP_SECRET
    
    if not app_id or not app_secret:
        return {
            "success": False,
            "access_token": None,
            "error": "未配置 WECHAT_APP_ID 或 WECHAT_APP_SECRET"
        }
    
    # 检查缓存是否有效（提前 5 分钟过期）
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"] - 300:
        return {
            "success": True,
            "access_token": _token_cache["access_token"],
            "expires_in": int(_token_cache["expires_at"] - time.time()),
            "error": None
        }
    
    try:
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": app_id,
            "secret": app_secret
        }
        
        response = requests.get(url, params=params, timeout=30)
        result = response.json()
        
        if "access_token" in result:
            # 缓存 token
            _token_cache["access_token"] = result["access_token"]
            _token_cache["expires_at"] = time.time() + result.get("expires_in", 7200)
            
            return {
                "success": True,
                "access_token": result["access_token"],
                "expires_in": result.get("expires_in", 7200),
                "error": None
            }
        else:
            return {
                "success": False,
                "access_token": None,
                "error": f"错误码: {result.get('errcode')}, 错误信息: {result.get('errmsg')}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "access_token": None,
            "error": str(e)
        }


def check_draft_switch(access_token: str) -> dict:
    """
    检查草稿箱开关状态
    
    Args:
        access_token: 微信 access_token
    
    Returns:
        {"success": bool, "is_open": bool, "error": str}
    """
    try:
        url = f"https://api.weixin.qq.com/cgi-bin/draft/switch?access_token={access_token}&checkonly=1"
        response = requests.post(url, timeout=30)
        result = response.json()
        
        if result.get("errcode", 0) == 0:
            return {
                "success": True,
                "is_open": result.get("is_open", 0) == 1,
                "error": None
            }
        else:
            return {
                "success": False,
                "is_open": False,
                "error": f"错误码: {result.get('errcode')}, 错误信息: {result.get('errmsg')}"
            }
    except Exception as e:
        return {
            "success": False,
            "is_open": False,
            "error": str(e)
        }


def open_draft_switch(access_token: str) -> dict:
    """
    开启草稿箱开关（注意：开启后不可逆）
    
    Args:
        access_token: 微信 access_token
    
    Returns:
        {"success": bool, "error": str}
    """
    try:
        url = f"https://api.weixin.qq.com/cgi-bin/draft/switch?access_token={access_token}"
        response = requests.post(url, timeout=30)
        result = response.json()
        
        if result.get("errcode", 0) == 0:
            return {
                "success": True,
                "error": None
            }
        else:
            return {
                "success": False,
                "error": f"错误码: {result.get('errcode')}, 错误信息: {result.get('errmsg')}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


class WeChatPublisher:
    """微信公众号发布器"""
    
    def __init__(self, api_url: str = None, api_key: str = None, access_token: str = None, auto_token: bool = True):
        """
        初始化发布器
        
        Args:
            api_url: API 地址（如果使用第三方服务）
            api_key: API Key（如果使用第三方服务）
            access_token: 微信 access_token（如果直接使用官方 API）
            auto_token: 是否自动获取 access_token
        """
        self.api_url = api_url or WECHAT_API_URL
        self.api_key = api_key or WECHAT_API_KEY
        self.access_token = access_token
        
        # 如果没有提供 access_token，自动获取
        if not self.access_token and auto_token:
            token_result = get_access_token()
            if token_result["success"]:
                self.access_token = token_result["access_token"]
                print(f"✓ 自动获取 access_token 成功，有效期 {token_result['expires_in']} 秒")
        
        # 微信官方 API 地址
        self.official_api_base = "https://api.weixin.qq.com/cgi-bin"
    
    def get_accounts(self) -> dict:
        """
        获取已绑定的公众号账号列表（第三方服务）
        
        Returns:
            {"success": bool, "data": list, "error": str}
        """
        if not self.api_url or not self.api_key:
            return {
                "success": False,
                "data": None,
                "error": "未配置微信 API，请在 config.py 中设置 WECHAT_API_URL 和 WECHAT_API_KEY"
            }
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            result = response.json()
            
            if result.get("success"):
                return {
                    "success": True,
                    "data": result.get("data", []),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "data": None,
                    "error": result.get("message", "获取账号列表失败")
                }
                
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }
    
    def upload_content_image(self, image_path: str) -> dict:
        """
        上传图文消息内的图片（用于文章正文中的图片）
        
        Args:
            image_path: 本地图片路径
        
        Returns:
            {"success": bool, "url": str, "error": str}
        """
        if not self.access_token:
            return {
                "success": False,
                "url": None,
                "error": "未设置 access_token"
            }
        
        try:
            url = f"{self.official_api_base}/media/uploadimg?access_token={self.access_token}"
            
            with open(image_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(url, files=files, timeout=60)
            
            result = response.json()
            
            if "url" in result:
                return {
                    "success": True,
                    "url": result["url"],
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "url": None,
                    "error": f"错误码: {result.get('errcode')}, 错误信息: {result.get('errmsg')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "url": None,
                "error": str(e)
            }
    
    def upload_thumb_media(self, image_path: str) -> dict:
        """
        上传封面图到微信素材库（永久素材）
        
        使用 type=image 上传图片素材
        微信要求：10MB 以内，支持 bmp/png/jpeg/jpg/gif 格式
        
        Args:
            image_path: 本地图片路径
        
        Returns:
            {"success": bool, "media_id": str, "error": str}
        """
        if not self.access_token:
            return {
                "success": False,
                "media_id": None,
                "error": "未设置 access_token"
            }
        
        try:
            url = f"{self.official_api_base}/material/add_material?access_token={self.access_token}&type=image"
            
            with open(image_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(url, files=files, timeout=60)
            
            result = response.json()
            
            if "media_id" in result:
                return {
                    "success": True,
                    "media_id": result["media_id"],
                    "url": result.get("url"),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "media_id": None,
                    "error": result.get("errmsg", "上传失败")
                }
                
        except Exception as e:
            return {
                "success": False,
                "media_id": None,
                "error": str(e)
            }
    
    def add_draft(self, articles: list) -> dict:
        """
        新增草稿
        
        根据微信官方 API 文档：
        https://developers.weixin.qq.com/doc/service/api/draftbox/draftmanage/api_draft_add.html
        
        Args:
            articles: 文章列表，每篇文章包含以下字段：
                - article_type: "news"（图文消息）或 "newspic"（图片消息）
                - title: 标题（必填）
                - author: 作者
                - digest: 摘要
                - content: 正文 HTML 内容（必填）
                - content_source_url: 原文链接
                - thumb_media_id: 封面图 media_id（必填）
                - need_open_comment: 是否打开评论 0/1
                - only_fans_can_comment: 是否仅粉丝可评论 0/1
                - pic_crop_235_1: 封面裁剪坐标（2.35:1）
                - pic_crop_1_1: 封面裁剪坐标（1:1）
        
        Returns:
            {"success": bool, "media_id": str, "error": str}
        """
        if not self.access_token:
            return {
                "success": False,
                "media_id": None,
                "error": "未设置 access_token，请先获取 access_token"
            }
        
        try:
            url = f"{self.official_api_base}/draft/add?access_token={self.access_token}"
            
            # 构建请求体
            payload = {
                "articles": articles
            }
            
            # 调试输出
            print(f"  发送文章标题: {articles[0].get('title', '')}")
            print(f"  标题长度: {len(articles[0].get('title', ''))}")
            
            # 使用 ensure_ascii=False 确保中文正确编码
            import json
            response = requests.post(
                url,
                data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=60
            )
            
            result = response.json()
            
            if "media_id" in result:
                return {
                    "success": True,
                    "media_id": result["media_id"],
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "media_id": None,
                    "error": f"错误码: {result.get('errcode')}, 错误信息: {result.get('errmsg')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "media_id": None,
                "error": str(e)
            }
    
    def add_draft_via_third_party(self, account_id: str, article: dict) -> dict:
        """
        通过第三方服务新增草稿（如 limyai 等服务）
        
        Args:
            account_id: 公众号账号 ID
            article: 文章信息
        
        Returns:
            {"success": bool, "media_id": str, "error": str}
        """
        if not self.api_url or not self.api_key:
            return {
                "success": False,
                "media_id": None,
                "error": "未配置第三方 API"
            }
        
        try:
            # 这里需要根据实际使用的第三方服务调整 API 路径和参数
            url = f"{self.api_url.replace('/wechat-accounts', '')}/wechat-draft/add"
            
            payload = {
                "account_id": account_id,
                "article": article
            }
            
            response = requests.post(
                url,
                json=payload,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=60
            )
            
            result = response.json()
            
            if result.get("success"):
                return {
                    "success": True,
                    "media_id": result.get("data", {}).get("media_id"),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "media_id": None,
                    "error": result.get("message", "发布失败")
                }
                
        except Exception as e:
            return {
                "success": False,
                "media_id": None,
                "error": str(e)
            }
    
    def publish_article(self, 
                       title: str, 
                       content: str, 
                       author: str = "",
                       digest: str = "",
                       thumb_media_id: str = None,
                       cover_image_path: str = None,
                       source_url: str = "",
                       need_open_comment: int = 0,
                       only_fans_can_comment: int = 0) -> dict:
        """
        发布文章到草稿箱（便捷方法）
        
        Args:
            title: 文章标题
            content: 文章 HTML 内容
            author: 作者
            digest: 摘要
            thumb_media_id: 封面图 media_id（如果已有）
            cover_image_path: 封面图本地路径（如果没有 media_id）
            source_url: 原文链接
            need_open_comment: 是否打开评论
            only_fans_can_comment: 是否仅粉丝可评论
        
        Returns:
            发布结果
        """
        # 如果提供了封面图路径但没有 media_id，先上传封面图
        if cover_image_path and not thumb_media_id:
            print("正在上传封面图...")
            upload_result = self.upload_thumb_media(cover_image_path)
            if upload_result["success"]:
                thumb_media_id = upload_result["media_id"]
                print(f"封面图上传成功: {thumb_media_id}")
            else:
                return {
                    "success": False,
                    "media_id": None,
                    "error": f"封面图上传失败: {upload_result['error']}"
                }
        
        if not thumb_media_id:
            return {
                "success": False,
                "media_id": None,
                "error": "缺少封面图 media_id"
            }
        
        # 截断标题（微信限制 32 个字）
        if len(title) > 32:
            title = title[:29] + "..."
        
        # 截断摘要（微信限制 120 字符）
        if len(digest) > 120:
            digest = digest[:117] + "..."
        
        # 计算封面裁剪坐标
        # 如果提供了封面图路径，根据实际尺寸计算裁剪坐标
        pic_crop_235_1 = "0_0_1_1"  # 默认整张图
        pic_crop_1_1 = "0_0_1_1"    # 默认整张图
        
        if cover_image_path:
            try:
                from PIL import Image
                img = Image.open(cover_image_path)
                width, height = img.size
                current_ratio = width / height
                
                # 计算 2.35:1 裁剪坐标
                target_ratio_235 = 2.35
                if current_ratio > target_ratio_235:
                    # 图片太宽，需要裁剪左右
                    new_width_ratio = target_ratio_235 / current_ratio
                    x1 = (1 - new_width_ratio) / 2
                    x2 = 1 - x1
                    pic_crop_235_1 = f"{x1:.6f}_{0}_{x2:.6f}_{1}"
                elif current_ratio < target_ratio_235:
                    # 图片太高，需要裁剪上下
                    new_height_ratio = current_ratio / target_ratio_235
                    y1 = (1 - new_height_ratio) / 2
                    y2 = 1 - y1
                    pic_crop_235_1 = f"{0}_{y1:.6f}_{1}_{y2:.6f}"
                
                # 计算 1:1 裁剪坐标
                if current_ratio > 1:
                    # 图片太宽，需要裁剪左右
                    new_width_ratio = 1 / current_ratio
                    x1 = (1 - new_width_ratio) / 2
                    x2 = 1 - x1
                    pic_crop_1_1 = f"{x1:.6f}_{0}_{x2:.6f}_{1}"
                elif current_ratio < 1:
                    # 图片太高，需要裁剪上下
                    new_height_ratio = current_ratio
                    y1 = (1 - new_height_ratio) / 2
                    y2 = 1 - y1
                    pic_crop_1_1 = f"{0}_{y1:.6f}_{1}_{y2:.6f}"
                
                print(f"  封面图尺寸: {width}x{height}, 比例: {current_ratio:.2f}")
                print(f"  2.35:1 裁剪坐标: {pic_crop_235_1}")
                print(f"  1:1 裁剪坐标: {pic_crop_1_1}")
            except Exception as e:
                print(f"  计算裁剪坐标失败: {e}，使用默认值")
        
        # 构建文章数据
        article = {
            "article_type": "news",
            "title": title,
            "author": author,
            "digest": digest,
            "content": content,
            "content_source_url": source_url,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": need_open_comment,
            "only_fans_can_comment": only_fans_can_comment,
            # 封面裁剪坐标
            "pic_crop_235_1": pic_crop_235_1,
            "pic_crop_1_1": pic_crop_1_1
        }
        
        return self.add_draft([article])


def create_article_payload(title: str,
                          content: str,
                          author: str = "",
                          digest: str = "",
                          thumb_media_id: str = "",
                          source_url: str = "",
                          need_open_comment: int = 0,
                          only_fans_can_comment: int = 0) -> dict:
    """
    创建文章数据结构（用于预览或手动调用 API）
    
    微信限制：
    - 标题最长 32 个字
    - 摘要最长 120 字符
    
    Returns:
        符合微信 API 格式的文章字典
    """
    # 截断标题（微信限制 32 个字）
    if len(title) > 32:
        title = title[:29] + "..."
    
    # 截断摘要（微信限制 120 字符）
    if not digest:
        digest = title
    if len(digest) > 120:
        digest = digest[:117] + "..."
    
    return {
        "article_type": "news",
        "title": title,
        "author": author,
        "digest": digest,
        "content": content,
        "content_source_url": source_url,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": need_open_comment,
        "only_fans_can_comment": only_fans_can_comment,
        "pic_crop_235_1": "0_0_1_1",
        "pic_crop_1_1": "0_0_1_1"
    }


if __name__ == "__main__":
    # 测试代码
    publisher = WeChatPublisher()
    
    # 测试获取账号列表
    print("测试获取账号列表...")
    result = publisher.get_accounts()
    print(result)

