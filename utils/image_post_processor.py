# utils/image_post_processor.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片后处理器 - 统一处理文生图和图生图的图片后处理逻辑
"""

import os
from typing import Optional


from utils.logger import get_logger

logger = get_logger(__name__)
class PostProcessConfig:
    """后期处理配置 - 用于命令行工具和模块化调用"""
    def __init__(self, clear_metadata=False, inject_exif=False, 
                 realistic=False, camera="sony_a7iv", strength="medium"):
        self.clear_metadata_var = self._make_var(clear_metadata)
        self.inject_exif_var = self._make_var(inject_exif)
        self.realistic_var = self._make_var(realistic)
        self.camera_var = self._make_var(camera)
        self.realistic_strength_var = self._make_var(strength)
    
    def _make_var(self, value):
        """创建一个简单的变量对象，模拟 tkinter.BooleanVar/StringVar"""
        class Var:
            def __init__(self, val):
                self._value = val
            def get(self):
                return self._value
        return Var(value)


def post_process_file(filepath, config, prompt="", log_prefix="[图片后处理]"):
    """
    便捷函数：对单个文件进行后期处理
    
    参数:
        filepath: 图片路径
        config: PostProcessConfig 实例
        prompt: 提示词（可选）
        log_prefix: 日志前缀
    
    返回:
        处理后的文件路径
    """
    if not config:
        return filepath
    
    # 检查是否有任何开关开启
    if not (config.clear_metadata_var.get() or 
            config.inject_exif_var.get() or 
            config.realistic_var.get()):
        return filepath
    
    return post_process_image(filepath, config, prompt, log_prefix)


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

    # ===== 添加这段安全检查 =====
    # 如果传入的不是文件（比如是一个目录），则不进行任何处理，直接返回
    import os
    if not os.path.isfile(filepath):
        logger.info(f"{log_prefix} 跳过非文件路径: {filepath}")
        return filepath
    # ===== 安全检查结束 =====
    
    # 检查开关状态 - 兼容 PostProcessConfig 和 ParamsPanel
    if hasattr(params_panel, 'clear_metadata_var'):
        need_clean = params_panel.clear_metadata_var.get()
        need_exif = params_panel.inject_exif_var.get()
        need_realistic = params_panel.realistic_var.get()
        camera = params_panel.camera_var.get() if hasattr(params_panel, 'camera_var') else "sony_a7iv"
        strength = params_panel.realistic_strength_var.get() if hasattr(params_panel, 'realistic_strength_var') else "medium"
    else:
        # 如果不是 ParamsPanel，假设是 PostProcessConfig 或类似对象
        need_clean = getattr(params_panel, 'clear_metadata_var', None)
        need_clean = need_clean.get() if need_clean and hasattr(need_clean, 'get') else False
        need_exif = getattr(params_panel, 'inject_exif_var', None)
        need_exif = need_exif.get() if need_exif and hasattr(need_exif, 'get') else False
        need_realistic = getattr(params_panel, 'realistic_var', None)
        need_realistic = need_realistic.get() if need_realistic and hasattr(need_realistic, 'get') else False
        camera = getattr(params_panel, 'camera_var', None)
        camera = camera.get() if camera and hasattr(camera, 'get') else "sony_a7iv"
        strength = getattr(params_panel, 'realistic_strength_var', None)
        strength = strength.get() if strength and hasattr(strength, 'get') else "medium"
    
    # 如果所有开关都关闭，直接返回
    if not (need_clean or need_exif or need_realistic):
        return filepath
    
    final_path = filepath
    
    # ===== 1. 清理元数据 =====
    if need_clean:
        try:
            from utils.imagemeta_cleaner import smart_clean_image
            final_path = smart_clean_image(final_path, method='jpg', jpg_quality=92)
            logger.info(f"🧹 {log_prefix} 元数据已清理: {os.path.basename(final_path)}")
        except Exception as e:
            logger.info(f"⚠️ {log_prefix} 元数据清理失败: {e}")
    
    # ===== 2. 照片真实化（包含 EXIF 注入） =====
    if need_realistic:
        try:
            from utils.photo_realistic import make_photo_realistic
            
            final_path = make_photo_realistic(
                final_path,
                camera=camera,
                strength=strength,
                inject_exif_data=True
            )
            logger.info(f"📷 {log_prefix} 照片真实化完成: {os.path.basename(final_path)}")
        except Exception as e:
            logger.info(f"⚠️ {log_prefix} 照片真实化失败: {e}")
    
    # ===== 3. 只注入 EXIF（如果真实化没开，但 EXIF 开关开了） =====
    if need_exif and not need_realistic:
        try:
            from utils.exif_injector import inject_exif
            
            final_path = inject_exif(final_path, camera=camera)
            logger.info(f"📷 {log_prefix} EXIF 已注入: {os.path.basename(final_path)}")
        except Exception as e:
            logger.info(f"⚠️ {log_prefix} EXIF 注入失败: {e}")
    
    return final_path