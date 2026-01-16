"""
核心配置模块
负责加载和管理应用配置
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    """应用配置"""
    name: str
    version: str
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


class UploadConfig(BaseModel):
    """上传配置"""
    max_size: int = 52428800  # 50MB
    allowed_extensions: List[str] = [".pptx"]
    upload_dir: str = "./uploads"
    temp_dir: str = "./temp"


class ModelConfig(BaseModel):
    """单个模型配置"""
    enabled: bool = True
    name: str
    api_url: str
    api_key: str = ""
    timeout: int = 30
    max_retries: int = 3
    core_strength: str
    focus_dimensions: List[str]

    # 讯飞星火特有字段
    app_id: str = ""
    api_secret: str = ""

    # 百度文心特有字段
    secret_key: str = ""

    # 腾讯混元特有字段
    secret_id: str = ""


class IterationConfig(BaseModel):
    """迭代修正配置"""
    enabled: bool = True
    max_rounds: int = 2
    conflict_threshold: float = 0.05
    manual_threshold: float = 0.10
    workflow: List[Dict[str, Any]] = []


class ConflictResolutionConfig(BaseModel):
    """冲突调和配置"""
    rules: Dict[str, Dict[str, List[str]]] = {}
    arbiter_model: str = "hunyuan"


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    log_dir: str = "./logs"
    rotation: str = "100 MB"
    retention: str = "30 days"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"


class CORSConfig(BaseModel):
    """CORS配置"""
    allow_origins: List[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]


class Settings(BaseSettings):
    """全局配置类"""
    app: AppConfig
    upload: UploadConfig
    models: Dict[str, ModelConfig]
    iteration: IterationConfig
    conflict_resolution: ConflictResolutionConfig
    logging: LoggingConfig
    cors: CORSConfig

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config(config_path: str = None) -> Settings:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径,默认为 config/config.yaml

    Returns:
        Settings: 配置对象
    """
    if config_path is None:
        # 获取当前文件所在目录的父目录,然后拼接config路径
        current_dir = Path(__file__).parent.parent
        config_path = current_dir / "config" / "config.yaml"

    # 检查文件是否存在
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    # 读取YAML配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)

    # 创建配置对象
    return Settings(**config_dict)


# 全局配置实例
_settings: Settings = None


def get_settings() -> Settings:
    """获取全局配置实例(单例模式)"""
    global _settings
    if _settings is None:
        _settings = load_config()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _settings = load_config()
    return _settings
