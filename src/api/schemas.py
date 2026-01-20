"""
Pydantic 请求/响应模型
"""
from typing import Optional
from pydantic import BaseModel, Field


# ========== 机器人管理 ==========

class BotCreate(BaseModel):
    """创建机器人请求"""
    name: str = Field(..., description="机器人名称", min_length=1, max_length=100)
    app_id: str = Field(..., description="飞书 App ID", min_length=1)
    app_secret: str = Field(..., description="飞书 App Secret", min_length=1)


class BotResponse(BaseModel):
    """机器人响应"""
    id: int
    name: str
    app_id: str
    enabled: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BotListResponse(BaseModel):
    """机器人列表响应"""
    total: int
    items: list[BotResponse]


# ========== 消息发送 ==========

class SendMessageRequest(BaseModel):
    """
    发送消息请求 (JSON 方式, 不含图片)
    注意: 带图片时应使用 FormData 方式
    """
    bot_name: str = Field(..., description="机器人名称")
    receive_id: str = Field(..., description="接收者 ID")
    receive_id_type: str = Field(default="open_id", description="ID 类型: open_id/user_id/email")
    title: Optional[str] = Field(None, description="消息标题 (富文本时使用)")
    content: Optional[str] = Field(None, description="文本内容")


# ========== 通用响应 ==========

class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
