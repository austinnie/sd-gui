# gui/tabs/txt2img/utils.py
"""文生图辅助函数"""

import math
import random
import re
from datetime import datetime
from typing import Optional, Tuple


from utils.logger import get_logger

logger = get_logger(__name__)
def log(msg: str):
    """打印日志"""
    logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def safe_del(obj):
    """安全删除对象"""
    try:
        if obj is not None:
            del obj
    except:
        pass


def get_smart_size(width: int, height: int, prompt: str = "", 
                   aspect_ratio: Optional[float] = None, 
                   max_pixels: int = 1024 * 1024) -> Tuple[int, int, str]:
    """智能尺寸调整"""
    from config.app_config import app_config
    size_cfg = app_config.generation.size
    
    max_cpu_w = size_cfg.get("cpu_safe_max_width", 1024)
    max_cpu_h = size_cfg.get("cpu_safe_max_height", 1024)
    
    prompt_lower = prompt.lower()
    
    is_portrait = any(k in prompt_lower for k in ['portrait', 'headshot', 'close up', 'face', '头像', '特写', '面部'])
    is_full_body = any(k in prompt_lower for k in ['full body', 'standing', '全身', '站立'])
    is_landscape = any(k in prompt_lower for k in ['landscape', 'scenery', 'building', 'city', '风景', '建筑', '城市'])
    is_couple = any(k in prompt_lower for k in ['couple', 'two people', '双人', '情侣', '两人'])
    is_group = any(k in prompt_lower for k in ['group', 'three people', '多人', '三人'])
    
    if width > 0 and height > 0:
        new_w = ((width + 31) // 64) * 64
        new_h = ((height + 31) // 64) * 64
        if new_w * new_h > max_pixels:
            scale = math.sqrt(max_pixels / (new_w * new_h))
            new_w = int(new_w * scale)
            new_h = int(new_h * scale)
            new_w = ((new_w + 31) // 64) * 64
            new_h = ((new_h + 31) // 64) * 64
        new_w = min(max_cpu_w, new_w)
        new_h = min(max_cpu_h, new_h)
        return new_w, new_h, f"用户指定 {width}x{height} → {new_w}x{new_h}"
    
    if aspect_ratio:
        target_ratio = aspect_ratio
    elif is_portrait:
        target_ratio = 0.9
    elif is_full_body or is_couple:
        target_ratio = 0.7
    elif is_landscape:
        target_ratio = 1.5
    elif is_group:
        target_ratio = 1.3
    else:
        target_ratio = 0.75
    
    base_pixels = min(max_pixels, 512 * 768)
    
    if target_ratio >= 1.0:
        new_w = int(math.sqrt(base_pixels * target_ratio))
        new_h = int(new_w / target_ratio)
    else:
        new_h = int(math.sqrt(base_pixels / target_ratio))
        new_w = int(new_h * target_ratio)
    
    new_w = ((new_w + 31) // 64) * 64
    new_h = ((new_h + 31) // 64) * 64
    
    min_size = 512
    if new_w < min_size:
        new_w = min_size
        new_h = int(new_w / target_ratio)
        new_h = ((new_h + 31) // 64) * 64
    if new_h < min_size:
        new_h = min_size
        new_w = int(new_h * target_ratio)
        new_w = ((new_w + 31) // 64) * 64
    
    new_w = min(max_cpu_w, new_w)
    new_h = min(max_cpu_h, new_h)
    
    return new_w, new_h, f"智能推荐 → {new_w}x{new_h}"


def get_smart_params(prompt: str, steps: Optional[int] = None, 
                     cfg: Optional[float] = None, 
                     strength: Optional[float] = None) -> Tuple[int, float, float, str]:
    """智能参数调整"""
    prompt_lower = prompt.lower()
    
    is_portrait = any(k in prompt_lower for k in ['portrait', 'headshot', 'close up', 'face', '头像', '特写'])
    is_nude = any(k in prompt_lower for k in ['nude', 'naked', '裸体', '裸'])
    is_complex = any(k in prompt_lower for k in ['detailed', 'intricate', 'complex', '详细', '复杂'])
    is_anime = any(k in prompt_lower for k in ['anime', 'manga', '动漫', '二次元'])
    is_realistic = any(k in prompt_lower for k in ['photorealistic', 'realistic', '真实', '写实'])
    
    if steps is None or steps <= 0:
        if is_portrait:
            steps = 15
        elif is_nude:
            steps = 25
        elif is_complex:
            steps = 30
        elif is_anime:
            steps = 20
        else:
            steps = 20
    
    if cfg is None or cfg <= 0:
        if is_nude:
            cfg = 6.0
        elif is_portrait:
            cfg = 7.5
        elif is_anime:
            cfg = 8.0
        else:
            cfg = 7.0
    
    if strength is None or strength <= 0:
        if is_portrait:
            strength = 0.35
        elif is_nude:
            strength = 0.45
        else:
            strength = 0.40
    
    adjustments = []
    if steps:
        adjustments.append(f"步数={steps}")
    if cfg:
        adjustments.append(f"CFG={cfg}")
    if strength:
        adjustments.append(f"强度={strength}")
    
    return steps, cfg, strength, f"智能调整: {', '.join(adjustments)}"


def auto_shorten_prompt(prompt: str, max_len: int = 350) -> str:
    """自动精简提示词"""
    if not prompt or len(prompt) <= max_len:
        return prompt
    
    parts = [p.strip() for p in prompt.split(',') if p.strip()]
    seen = set()
    unique_parts = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            unique_parts.append(p)
    unique_parts.sort(key=lambda x: len(x), reverse=True)
    result = []
    current_len = 0
    for part in unique_parts:
        add_len = len(part) + 2
        if current_len + add_len <= max_len:
            result.append(part)
            current_len += add_len
    if not result:
        return prompt[:max_len]
    shortened = ", ".join(result)
    if len(shortened) < len(prompt):
        logger.info(f"✂️ 提示词已精简: {len(prompt)} -> {len(shortened)} 字符")
    return shortened