"""
数据库模型定义
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from src.db.database import Base


class Bot(Base):
    """机器人配置模型"""
    
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True, comment="机器人名称")
    app_id = Column(String(100), nullable=False, comment="飞书 App ID")
    app_secret = Column(String(200), nullable=False, comment="飞书 App Secret")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    def __repr__(self):
        return f"<Bot(id={self.id}, name='{self.name}', enabled={self.enabled})>"
    
    def to_dict(self):
        """转换为字典 (隐藏敏感信息)"""
        return {
            "id": self.id,
            "name": self.name,
            "app_id": self.app_id,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
