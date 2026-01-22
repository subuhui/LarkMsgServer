"""
飞书 API 客户端
"""
import time
import httpx
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from src.config import settings


@dataclass
class TokenInfo:
    """Token 信息"""
    token: str
    expire_at: float  # 过期时间戳


class LarkClient:
    """
    飞书 API 客户端
    
    功能:
    - Token 获取与缓存
    - 图片上传
    - 消息发送 (文本/图片/富文本)
    """
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = settings.lark_base_url
        self._token_cache: Optional[TokenInfo] = None
    
    async def _get_tenant_access_token(self) -> str:
        """
        获取 tenant_access_token (带缓存)
        文档: https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal
        """
        # 检查缓存是否有效 (提前5分钟过期)
        if self._token_cache and self._token_cache.expire_at > time.time() + 300:
            return self._token_cache.token
        
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        
        if data.get("code") != 0:
            raise Exception(f"获取 token 失败: {data.get('msg')}")
        
        token = data["tenant_access_token"]
        expire = data.get("expire", 7200)  # 默认2小时
        
        self._token_cache = TokenInfo(
            token=token,
            expire_at=time.time() + expire
        )
        
        return token
    
    async def upload_image(self, image_data: bytes, image_type: str = "message") -> str:
        """
        上传图片到飞书
        文档: https://open.feishu.cn/document/server-docs/im-v1/image/create
        
        Args:
            image_data: 图片二进制数据
            image_type: 图片类型 (message/avatar)
        
        Returns:
            image_key: 图片唯一标识
        """
        token = await self._get_tenant_access_token()
        url = f"{self.base_url}/im/v1/images"
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        files = {
            "image": ("image.png", image_data, "image/png")
        }
        data = {
            "image_type": image_type
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, files=files, data=data)
            resp.raise_for_status()
            result = resp.json()
        
        if result.get("code") != 0:
            raise Exception(f"上传图片失败: {result.get('msg')}")
        
        return result["data"]["image_key"]
    
    async def send_message(
        self,
        receive_id: str,
        receive_id_type: str = "open_id",
        title: Optional[str] = None,
        content: Optional[str] = None,
        image_data_list: Optional[list[bytes]] = None
    ) -> Dict[str, Any]:
        """
        发送消息 (统一接口)

        根据参数自动判断消息类型:
        - 只有 content -> text (纯文本)
        - content + title -> post (富文本)
        - 只有 image_data_list -> image (单图) 或 post (多图)
        - image_data_list + content (+ title) -> post (图文混合)

        Args:
            receive_id: 接收者 ID
            receive_id_type: ID 类型 (open_id/user_id/email)
            title: 消息标题 (可选)
            content: 文本内容 (可选)
            image_data_list: 图片二进制数据列表 (可选)

        Returns:
            飞书 API 响应
        """
        if not content and not image_data_list:
            raise ValueError("content 或 image_data_list 至少提供一个")

        # 确定消息类型和构建消息体
        msg_type, msg_content = await self._build_message(title, content, image_data_list)

        token = await self._get_tenant_access_token()
        url = f"{self.base_url}/im/v1/messages"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        params = {
            "receive_id_type": receive_id_type
        }

        payload = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": msg_content
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, params=params, json=payload)
            resp.raise_for_status()
            result = resp.json()

        if result.get("code") != 0:
            raise Exception(f"发送消息失败: {result.get('msg')}")

        return result
    
    async def _build_message(
        self,
        title: Optional[str],
        content: Optional[str],
        image_data_list: Optional[list[bytes]]
    ) -> Tuple[str, str]:
        """
        构建消息体

        Returns:
            (msg_type, content_json_str)
        """
        import json

        # 情况1: 只有单张图片且无标题无内容 -> image 类型
        if image_data_list and len(image_data_list) == 1 and not content and not title:
            image_key = await self.upload_image(image_data_list[0])
            return "image", json.dumps({"image_key": image_key})

        # 情况2: 只有文本,无标题,无图片 -> text 类型
        if content and not title and not image_data_list:
            return "text", json.dumps({"text": content})

        # 情况3: 有标题 或 有图文混合 或 多张图片 -> post (富文本) 类型
        # 构建富文本内容
        post_content = []

        # 添加文本
        if content:
            post_content.append([{"tag": "text", "text": content}])

        # 添加图片 (支持多张)
        if image_data_list:
            for image_data in image_data_list:
                image_key = await self.upload_image(image_data)
                post_content.append([{"tag": "img", "image_key": image_key}])

        post_body = {
            "zh_cn": {
                "title": title or "",
                "content": post_content
            }
        }

        return "post", json.dumps(post_body)
