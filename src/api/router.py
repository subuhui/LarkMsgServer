"""
FastAPI 路由定义
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db.models import Bot
from src.lark.client import LarkClient
from src.api.schemas import (
    BotCreate, BotResponse, BotListResponse,
    SuccessResponse, ErrorResponse
)

router = APIRouter()


# ==================== 机器人管理 ====================

@router.post("/api/bots", response_model=SuccessResponse, tags=["机器人管理"])
async def create_bot(bot: BotCreate, db: Session = Depends(get_db)):
    """添加机器人"""
    # 检查名称是否已存在
    existing = db.query(Bot).filter(Bot.name == bot.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"机器人 '{bot.name}' 已存在")
    
    new_bot = Bot(
        name=bot.name,
        app_id=bot.app_id,
        app_secret=bot.app_secret
    )
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    
    return SuccessResponse(message="机器人添加成功", data=new_bot.to_dict())


@router.get("/api/bots", response_model=BotListResponse, tags=["机器人管理"])
async def list_bots(db: Session = Depends(get_db)):
    """列出所有机器人"""
    bots = db.query(Bot).all()
    return BotListResponse(
        total=len(bots),
        items=[BotResponse(**b.to_dict()) for b in bots]
    )


@router.delete("/api/bots/{bot_id}", response_model=SuccessResponse, tags=["机器人管理"])
async def delete_bot(bot_id: int, db: Session = Depends(get_db)):
    """删除机器人"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail=f"机器人 ID={bot_id} 不存在")
    
    db.delete(bot)
    db.commit()
    
    return SuccessResponse(message=f"机器人 '{bot.name}' 已删除")


# ==================== 消息发送 ====================

@router.post("/api/send", response_model=SuccessResponse, tags=["消息发送"])
async def send_message(
    bot_name: str = Form(..., description="机器人名称"),
    receive_id: str = Form(..., description="接收者 ID"),
    receive_id_type: str = Form(default="open_id", description="ID 类型: open_id/user_id/email"),
    title: Optional[str] = Form(None, description="消息标题 (富文本时使用)"),
    content: Optional[str] = Form(None, description="文本内容"),
    image: Optional[UploadFile] = File(None, description="图片文件"),
    db: Session = Depends(get_db)
):
    """
    统一消息发送接口
    
    根据参数自动判断消息类型:
    - 只有 content -> 纯文本
    - content + title -> 富文本
    - 只有 image -> 纯图片
    - image + content (+ title) -> 图文混合
    """
    # 参数验证
    if not content and not image:
        raise HTTPException(status_code=400, detail="content 或 image 至少提供一个")
    
    # 获取机器人配置
    bot = db.query(Bot).filter(Bot.name == bot_name, Bot.enabled == True).first()
    if not bot:
        raise HTTPException(status_code=404, detail=f"机器人 '{bot_name}' 不存在或已禁用")
    
    # 读取图片数据
    image_data = None
    if image:
        image_data = await image.read()
    
    # 创建飞书客户端并发送消息
    client = LarkClient(app_id=bot.app_id, app_secret=bot.app_secret)
    
    try:
        result = await client.send_message(
            receive_id=receive_id,
            receive_id_type=receive_id_type,
            title=title,
            content=content,
            image_data=image_data
        )
        
        return SuccessResponse(
            message="消息发送成功",
            data={
                "message_id": result.get("data", {}).get("message_id"),
                "bot_name": bot_name,
                "receive_id": receive_id
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 健康检查 ====================

@router.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "LarkMsgServer"}
