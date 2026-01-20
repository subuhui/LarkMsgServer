"""
配置管理模块
使用 pydantic-settings 从环境变量加载配置
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    server_host: str = "0.0.0.0"
    server_port: int = 234
    
    # 数据库配置
    db_path: str = "data.db"
    db_key: str = ""  # SQLCipher 加密密钥
    
    # 飞书 API 配置
    lark_base_url: str = "https://open.feishu.cn/open-apis"
    
    # API 认证 (可选)
    api_key: str = ""
    
    class Config:
        env_prefix = "LARK_"  # 环境变量前缀: LARK_DB_KEY, LARK_SERVER_PORT 等
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 便捷访问
settings = get_settings()
