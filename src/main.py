"""
LarkMsgServer - 飞书消息发送服务

程序入口，整合 FastAPI 和 CLI
"""
from fastapi import FastAPI

from src.config import settings
from src.db.database import init_db
from src.api.router import router


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="LarkMsgServer",
        description="飞书消息发送服务 - 支持多机器人、文本/图片/富文本消息",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 注册路由
    app.include_router(router)
    
    # 启动事件
    @app.on_event("startup")
    async def startup():
        init_db()
    
    return app


# CLI 入口
def main():
    """CLI 入口"""
    from src.cli.commands import app as cli_app
    cli_app()


if __name__ == "__main__":
    main()
