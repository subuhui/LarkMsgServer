"""
Typer CLI 命令行接口
"""
import asyncio
from pathlib import Path
from typing import Optional

import typer

from src.config import settings
from src.db.database import init_db, SessionLocal
from src.db.models import Bot
from src.lark.client import LarkClient

app = typer.Typer(help="飞书消息发送服务 CLI")


# ==================== 服务命令 ====================

@app.command()
def serve(
    host: str = typer.Option(settings.server_host, "--host", "-h", help="监听地址"),
    port: int = typer.Option(settings.server_port, "--port", "-p", help="监听端口")
):
    """启动 HTTP 服务"""
    import uvicorn
    from src.main import create_app
    
    # 初始化数据库
    init_db()
    
    typer.echo(f"🚀 启动服务: http://{host}:{port}")
    typer.echo(f"📖 API 文档: http://{host}:{port}/docs")
    
    uvicorn.run(create_app(), host=host, port=port)


@app.command()
def init():
    """初始化数据库"""
    init_db()
    typer.echo("✅ 数据库初始化完成")


# ==================== 机器人管理 ====================

bot_app = typer.Typer(help="机器人管理")
app.add_typer(bot_app, name="bot")


@bot_app.command("add")
def bot_add(
    name: str = typer.Option(..., "--name", "-n", help="机器人名称"),
    app_id: str = typer.Option(..., "--app-id", help="飞书 App ID"),
    app_secret: str = typer.Option(..., "--app-secret", help="飞书 App Secret")
):
    """添加机器人"""
    init_db()
    db = SessionLocal()
    
    try:
        # 检查名称是否已存在
        existing = db.query(Bot).filter(Bot.name == name).first()
        if existing:
            typer.echo(f"❌ 机器人 '{name}' 已存在", err=True)
            raise typer.Exit(1)
        
        new_bot = Bot(name=name, app_id=app_id, app_secret=app_secret)
        db.add(new_bot)
        db.commit()
        
        typer.echo(f"✅ 机器人 '{name}' 添加成功")
    finally:
        db.close()


@bot_app.command("list")
def bot_list():
    """列出所有机器人"""
    init_db()
    db = SessionLocal()
    
    try:
        bots = db.query(Bot).all()
        
        if not bots:
            typer.echo("📭 暂无机器人")
            return
        
        typer.echo(f"📋 机器人列表 (共 {len(bots)} 个):\n")
        for bot in bots:
            status = "✅" if bot.enabled else "❌"
            typer.echo(f"  {status} [{bot.id}] {bot.name} (App ID: {bot.app_id})")
    finally:
        db.close()


@bot_app.command("remove")
def bot_remove(
    name: str = typer.Argument(..., help="机器人名称")
):
    """删除机器人"""
    init_db()
    db = SessionLocal()
    
    try:
        bot = db.query(Bot).filter(Bot.name == name).first()
        if not bot:
            typer.echo(f"❌ 机器人 '{name}' 不存在", err=True)
            raise typer.Exit(1)
        
        db.delete(bot)
        db.commit()
        
        typer.echo(f"✅ 机器人 '{name}' 已删除")
    finally:
        db.close()


# ==================== 消息发送 ====================

@app.command()
def send(
    bot: str = typer.Option(..., "--bot", "-b", help="机器人名称"),
    to: str = typer.Option(..., "--to", "-t", help="接收者 ID"),
    id_type: str = typer.Option("open_id", "--id-type", help="ID 类型: open_id/user_id/email"),
    title: Optional[str] = typer.Option(None, "--title", help="消息标题"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="文本内容"),
    image: Optional[Path] = typer.Option(None, "--image", "-i", help="图片文件路径")
):
    """
    发送消息
    
    示例:
    
        # 发送纯文本
        python -m src.main send --bot mybot --to ou_xxx --content "Hello"
        
        # 发送图片
        python -m src.main send --bot mybot --to ou_xxx --image ./img.png
        
        # 发送图文混合
        python -m src.main send --bot mybot --to ou_xxx --title "通知" --content "详情" --image ./img.png
    """
    if not content and not image:
        typer.echo("❌ 请提供 --content 或 --image", err=True)
        raise typer.Exit(1)
    
    init_db()
    db = SessionLocal()
    
    try:
        # 获取机器人配置
        bot_obj = db.query(Bot).filter(Bot.name == bot, Bot.enabled == True).first()
        if not bot_obj:
            typer.echo(f"❌ 机器人 '{bot}' 不存在或已禁用", err=True)
            raise typer.Exit(1)
        
        # 读取图片
        image_data = None
        if image:
            if not image.exists():
                typer.echo(f"❌ 图片文件不存在: {image}", err=True)
                raise typer.Exit(1)
            image_data = image.read_bytes()
        
        # 发送消息
        client = LarkClient(app_id=bot_obj.app_id, app_secret=bot_obj.app_secret)
        
        async def do_send():
            return await client.send_message(
                receive_id=to,
                receive_id_type=id_type,
                title=title,
                content=content,
                image_data=image_data
            )
        
        result = asyncio.run(do_send())
        
        msg_id = result.get("data", {}).get("message_id", "unknown")
        typer.echo(f"✅ 消息发送成功 (message_id: {msg_id})")
        
    except Exception as e:
        typer.echo(f"❌ 发送失败: {e}", err=True)
        raise typer.Exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    app()
