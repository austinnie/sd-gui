#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工具模块
"""
from .logger import (
    setup_logging,
    get_logger,
    set_level,
    get_log_file,
    get_log_dir,
    debug,
    info,
    warning,
    error,
    critical,
    print_info,
    print_debug,
    print_warning,
    print_error,
)

from .module_discovery import ModuleDiscovery
from .watermark_remover import WatermarkRemover, remove_watermark_from_file
from .imagemeta_cleaner import (
    clean_png_metadata,
    convert_to_jpg,
    remove_with_exiftool,
    remove_all_metadata,
    smart_clean_image,
    batch_clean_images,
    has_metadata
)
from .exif_injector import (
    inject_exif,
    batch_inject_exif,
    get_camera_list,
    get_style_list,
    CAMERA_PRESETS,
    PHOTO_STYLES
)
from .photo_realistic import (
    add_realistic_features,
    make_photo_realistic
)
from .image_post_processor import (
    post_process_image,
    PostProcessConfig,
    post_process_file
)

from .strength_tester import (
    StrengthTester,
    run_strength_test
)

from .scheduler_fix import (
    fix_euler_scheduler_for_img2img,
    fix_scheduler_before_step
)

from .scheduler_factory import (
    get_scheduler,
    get_scheduler_description
)

from .pipeline_pool import PipelinePool, pipeline_pool

from .vae_utils import load_vae

# ✅ ControlNet 模块 (拆分后)
from .controlnet import (
    # 单层 ControlNet
    process_with_controlnet,
    get_controlnet_pipeline,
    preprocess_image_for_controlnet,
    extract_pose,  # 别名，兼容旧代码
    # 类型信息
    get_controlnet_types,
    get_controlnet_display_names,
    get_controlnet_info,
    is_controlnet_available,
    # 多层 ControlNet
    process_with_multi_controlnet,
    get_recommended_multi_controlnet_combos,
    # 配置
    controlnet_config,
    CONTROLNET_CONFIG,
)

__all__ = [
    'ModuleDiscovery',
    
    'WatermarkRemover',
    'remove_watermark_from_file',
    
    # imagemeta_cleaner
    'clean_png_metadata',
    'convert_to_jpg',
    'remove_with_exiftool',
    'remove_all_metadata',
    'smart_clean_image',
    'batch_clean_images',
    'has_metadata',
    
    # exif_injector
    'inject_exif',
    'batch_inject_exif',
    'get_camera_list',
    'get_style_list',
    'CAMERA_PRESETS',
    'PHOTO_STYLES',
    
    # photo_realistic
    'add_realistic_features',
    'make_photo_realistic',
    
    # image_post_processor
    'post_process_image',
    'PostProcessConfig',
    'post_process_file',

    # strength_tester
    'StrengthTester',
    'run_strength_test',
    
    # scheduler_fix
    'fix_euler_scheduler_for_img2img',
    'fix_scheduler_before_step',
    
    # scheduler_factory
    'get_scheduler',
    'get_scheduler_description',
    
    'PipelinePool',
    'pipeline_pool',
    
    'load_vae',

    # ✅ ControlNet (单层)
    'process_with_controlnet',
    'get_controlnet_pipeline',
    'preprocess_image_for_controlnet',
    'extract_pose',
    'get_controlnet_types',
    'get_controlnet_display_names',
    'get_controlnet_info',
    'is_controlnet_available',
    
    # ✅ ControlNet (多层)
    'process_with_multi_controlnet',
    'get_recommended_multi_controlnet_combos',
    
    # ✅ ControlNet (配置)
    'controlnet_config',
    'CONTROLNET_CONFIG',
]