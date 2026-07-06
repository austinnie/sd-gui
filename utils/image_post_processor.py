# utils/image_post_processor.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片后处理器 - 统一处理文生图和图生图的图片后处理逻辑
"""

import os
from typing import Optional


def post_process_image(
    filepath: str,
    params_panel,  # 参数面板对象，用于读取开关状态
    prompt: str = "",
    log_prefix: str = ""
) -> str:
    """
    图片后处理：清理元数据 / EXIF 注入 / 照片真实化
    """
    if not log_prefix:
        log_prefix = "[图片后处理]"
    
    # 检查开关状态 - 使用新的属性名
    need_clean = hasattr(params_panel, 'clear_metadata_var') and params_panel.clear_metadata_var.get()
    need_exif = hasattr(params_panel, 'inject_exif_var') and params_panel.inject_exif_var.get()
    need_realistic = hasattr(params_panel, 'realistic_var') and params_panel.realistic_var.get()
    
    # 如果所有开关都关闭，直接返回
    if not (need_clean or need_exif or need_realistic):
        return filepath
    
    final_path = filepath
    
    # ===== 1. 清理元数据 =====
    if need_clean:
        try:
            from utils.imagemeta_cleaner import smart_clean_image
            final_path = smart_clean_image(final_path, method='jpg', jpg_quality=92)
            print(f"🧹 {log_prefix} 元数据已清理: {os.path.basename(final_path)}")
        except Exception as e:
            print(f"⚠️ {log_prefix} 元数据清理失败: {e}")
    
    # ===== 2. 照片真实化（包含 EXIF 注入） =====
    if need_realistic:
        try:
            from utils.photo_realistic import make_photo_realistic
            
            camera = params_panel.camera_var.get() if hasattr(params_panel, 'camera_var') else "sony_a7iv"
            strength = params_panel.realistic_strength_var.get() if hasattr(params_panel, 'realistic_strength_var') else "medium"
            
            final_path = make_photo_realistic(
                final_path,
                camera=camera,
                strength=strength,
                inject_exif_data=True
            )
            print(f"📷 {log_prefix} 照片真实化完成: {os.path.basename(final_path)}")
        except Exception as e:
            print(f"⚠️ {log_prefix} 照片真实化失败: {e}")
    
    # ===== 3. 只注入 EXIF（如果真实化没开，但 EXIF 开关开了） =====
    if need_exif and not need_realistic:
        try:
            from utils.exif_injector import inject_exif
            
            camera = params_panel.camera_var.get() if hasattr(params_panel, 'camera_var') else "sony_a7iv"
            final_path = inject_exif(final_path, camera=camera)
            print(f"📷 {log_prefix} EXIF 已注入: {os.path.basename(final_path)}")
        except Exception as e:
            print(f"⚠️ {log_prefix} EXIF 注入失败: {e}")
    
    return final_path