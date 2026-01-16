"""工具函数模块"""
import os
import hashlib
import uuid
from pathlib import Path
from typing import Optional
from loguru import logger


def generate_ppt_id() -> str:
    """生成PPT唯一ID"""
    return f"ppt_{uuid.uuid4().hex[:12]}"


def generate_file_hash(file_path: str) -> str:
    """计算文件MD5哈希"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def ensure_dir(directory: str) -> Path:
    """确保目录存在"""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_allowed_file(filename: str, allowed_extensions: list) -> bool:
    """检查文件扩展名是否允许"""
    return Path(filename).suffix.lower() in allowed_extensions


def get_file_size(file_path: str) -> int:
    """获取文件大小(字节)"""
    return os.path.getsize(file_path)
