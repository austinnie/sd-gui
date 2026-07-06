#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工具模块
"""

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
from .scheduler_factory import (
    get_scheduler,
    get_scheduler_description
)

__all__ = [
    # watermark_remover
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
    
    # scheduler_factory
    'get_scheduler',
    'get_scheduler_description',
]