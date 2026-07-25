# gui/tabs/lora_manager/utils.py
"""LoRA 管理辅助函数"""

import os
import re
import json
from datetime import datetime
from typing import List, Dict, Optional


def format_size(size_mb: float) -> str:
    """格式化文件大小"""
    if size_mb < 1024:
        return f"{size_mb:.1f} MB"
    else:
        return f"{size_mb / 1024:.1f} GB"


def extract_lora_name(filename: str) -> str:
    """从文件名提取 LoRA 名称"""
    name = filename.replace('.safetensors', '').replace('.ckpt', '')
    match = re.match(r'^\d+_', name)
    if match:
        name = name[match.end():]
    return name


def get_lora_type_from_path(path: str) -> str:
    """根据路径判断 LoRA 类型"""
    path_lower = path.lower()
    if 'sd15' in path_lower or 'sd-1.5' in path_lower:
        return 'sd15'
    elif 'sdxl' in path_lower:
        return 'sdxl'
    return 'unknown'


def get_lora_type_display(lora_type: str) -> str:
    """获取类型显示名称"""
    type_map = {
        'sd15': '🟢 SD1.5',
        'sdxl': '🔵 SDXL',
        'unknown': '⚪ 未知',
        'both': '🟣 双兼容'
    }
    return type_map.get(lora_type, '⚪ 未知')


def log_timestamp() -> str:
    """获取时间戳"""
    return datetime.now().strftime("%H:%M:%S")


def load_run_log(log_path: str) -> dict:
    """加载运行日志"""
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_run_log(log_path: str, log_data: dict):
    """保存运行日志"""
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
    except:
        pass