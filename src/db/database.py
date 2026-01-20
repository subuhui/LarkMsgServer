"""
SQLCipher 数据库连接管理
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator

from src.config import settings

# 数据库 URL
DATABASE_URL = f"sqlite:///{settings.db_path}"

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    连接时设置 SQLCipher 加密密钥
    """
    cursor = dbapi_connection.cursor()
    if settings.db_key:
        # 设置 SQLCipher 加密密钥
        cursor.execute(f"PRAGMA key = '{settings.db_key}'")
    cursor.close()


# Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话 (用于 FastAPI 依赖注入)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库 (创建所有表)
    """
    from src.db.models import Bot  # noqa
    Base.metadata.create_all(bind=engine)
