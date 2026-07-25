# core/pipeline/scene_counter.py
"""场景数统计工具 - 从 pipeline_tab.py 移出"""

from typing import Optional, Dict, Any


# 默认场景数配置
DEFAULT_SCENE_COUNTS = {
    # 风格转换类
    "sketch": 8,
    "watercolor": 3,
    "ink_wash": 4,
    "oil_painting": 6,
    "cyberpunk": 3,
    "vaporwave": 3,
    "three_d_render": 3,
    "aesthetic": 16,
    
    # 场景/主题类
    "beach": 4,
    "forest": 4,
    "space": 4,
    "castle": 4,
    "wedding": 4,
    
    # 服装/造型类
    "lolita": 4,
    "kimono": 4,
    "evening_gown": 4,
    "vintage": 4,
    "cinematic": 4,
    "hanfu": 4,
    "qipao": 4,
    
    # 双人/多人场景
    "couple": 4,
    "couple_watercolor": 3,
    "couple_oil_painting": 3,
    "couple_wedding": 4,
    "family_sketch": 3,
    "friends_style": 3,
    "group_photo": 3,
    "yoga": 20,
    "marble_yoga": 16,
    "bronze_statue": 12,
    
    # 特殊
    "marble": 14,
    "anime_xxx": 40,
    "remove_clothes": 28,
    "cyber_hanfu": 10,
}


def get_step_scene_count(step_type: str, config: dict) -> Optional[int]:
    """
    获取步骤的场景数量
    
    参数:
        step_type: 步骤类型
        config: 步骤配置
    
    返回:
        场景数量，如果无法确定则返回 None
    """
    # 1. 配置覆盖（用户指定的场景数）
    if "scenes" in config:
        try:
            return int(config["scenes"])
        except (ValueError, TypeError):
            pass
    
    # 2. 动态获取（从步骤类读取实际场景数）
    try:
        from core.pipeline import PipelineRegistry
        step_class = PipelineRegistry.get_step(step_type)
        if step_class:
            step_instance = step_class()
            if hasattr(step_instance, 'get_prompts'):
                prompts = step_instance.get_prompts()
                return len(prompts)
    except Exception:
        pass
    
    # 3. 默认硬编码（降级方案）
    return DEFAULT_SCENE_COUNTS.get(step_type)


def get_total_scenes(steps: list) -> tuple:
    """
    获取所有步骤的总场景数
    
    参数:
        steps: 步骤列表
    
    返回:
        (total_scenes, scene_details)
        - total_scenes: 总场景数
        - scene_details: 每个步骤的详情列表
    """
    total = 0
    details = []
    
    for step in steps:
        step_type = step.get("type", "unknown")
        config = step.get("config", {})
        count = get_step_scene_count(step_type, config)
        if count is not None:
            total += count
            details.append(f"{step_type}: {count}")
    
    return total, details


def get_step_default_scenes(step_type: str) -> Optional[int]:
    """获取步骤类型的默认场景数"""
    return DEFAULT_SCENE_COUNTS.get(step_type)


def get_scene_limit_from_config(config: dict) -> Optional[int]:
    """
    从配置中获取场景数限制
    
    支持多个键名:
        - max_scenes: 通用键名
        - scene_limit: 通用键名
        - scenes: 兼容旧配置
    """
    for key in ["max_scenes", "scene_limit", "scenes"]:
        if key in config:
            try:
                value = int(config[key])
                if value > 0:
                    return value
            except (ValueError, TypeError):
                pass
    return None


def limit_prompts(prompts: list, max_scenes: Optional[int]) -> list:
    """
    根据场景数限制裁剪提示词列表
    """
    if max_scenes is None or max_scenes <= 0:
        return prompts
    
    if len(prompts) <= max_scenes:
        return prompts
    
    return prompts[:max_scenes]