# utils/controlnet/__init__.py
"""
ControlNet 辅助模块
提供单层和多层 ControlNet 支持
"""

from .types import (
    CONTROLNET_TYPES,
    get_controlnet_types,
    get_controlnet_display_names,
    get_controlnet_info,
    is_controlnet_available,
)

from .config import (
    CONTROLNET_CONFIG,
    ControlNetConfig,
    controlnet_config,
)

from .preprocess import (
    preprocess_image_for_controlnet,
    extract_pose,  # 别名，兼容旧代码
)

from .pipeline import (
    get_controlnet_pipeline,
    get_multi_controlnet_pipeline,
)

from .single import (
    process_with_controlnet,
)

from .multi import (
    process_with_multi_controlnet,
    get_recommended_multi_controlnet_combos,
)

__all__ = [
    # types
    'CONTROLNET_TYPES',
    'get_controlnet_types',
    'get_controlnet_display_names',
    'get_controlnet_info',
    'is_controlnet_available',
    # config
    'CONTROLNET_CONFIG',
    'ControlNetConfig',
    'controlnet_config',
    # preprocess
    'preprocess_image_for_controlnet',
    'extract_pose',
    # pipeline
    'get_controlnet_pipeline',
    'get_multi_controlnet_pipeline',
    # single
    'process_with_controlnet',
    # multi
    'process_with_multi_controlnet',
    'get_recommended_multi_controlnet_combos',
]