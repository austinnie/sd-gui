# gui/tabs/txt2img/generator.py
"""文生图核心生成逻辑"""

import gc
import random
import time
import torch
from datetime import datetime

from .utils import log, safe_del
from .callbacks import Txt2ImgStepCallback
from .saver import ImageSaver


from utils.logger import get_logger

logger = get_logger(__name__)
class ImageGenerator:
    """文生图图片生成器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.params = tab.params
        self.saver = ImageSaver(tab)
    
    def generate_single(self, prompt, negative, steps=None, cfg=None, seed=None,
                        height=None, width=None, index=1, total=1, callback=None, pipe=None):
        """生成单张图片"""
        from .utils import auto_shorten_prompt
        
        log(f"开始生成第 {index}/{total} 张")
        
        # 默认值
        if steps is None:
            steps = self.params.steps_var.get()
        if cfg is None:
            cfg = self.params.cfg_var.get()
        if seed is None:
            seed = self.params.seed_var.get()
        if height is None or height <= 0:
            height = self.params.height_var.get()
        if width is None or width <= 0:
            width = self.params.width_var.get()
        
        # 安全检查
        if pipe is None:
            self.tab._on_generation_error("未传入 Pipeline")
            return
        
        # 尺寸安全处理
        from config.app_config import app_config
        gen_cfg = app_config.generation
        size_cfg = gen_cfg.size
        
        width = max(1, width)
        height = max(1, height)
        width = ((width + 31) // 64) * 64
        height = ((height + 31) // 64) * 64
        
        max_cpu_w = size_cfg.get("cpu_safe_max_width", 1024)
        max_cpu_h = size_cfg.get("cpu_safe_max_height", 1024)
        width = min(max_cpu_w, max(size_cfg["min_width"], width))
        height = min(max_cpu_h, max(size_cfg["min_height"], height))
        steps = max(gen_cfg.steps["min"], min(gen_cfg.steps["max"], steps))
        cfg = max(gen_cfg.cfg["min"], min(gen_cfg.cfg["max"], cfg))
        
        if seed == -1:
            seed = random.randint(1, 2**32 - 1)
        
        # 精简提示词
        prompt = auto_shorten_prompt(prompt, max_len=150)
        negative = auto_shorten_prompt(negative, max_len=150)
        
        # 更新进度
        start_time = time.time()
        
        def progress_cb(value, msg):
            self.app.root.after(0, lambda: self.tab.update_progress(value, msg))
        
        progress_cb((index - 1) / total, f"🎨 生成第 {index}/{total} 张...")
        
        # 水印去除 - 增强负面提示词
        from utils.watermark_remover import WatermarkRemover
        watermark_remover = WatermarkRemover()
        enhanced_negative = negative
        if self.params.remove_watermark_var.get():
            strength = self.params.watermark_strength_var.get()
            enhanced_negative = watermark_remover.get_enhanced_negative(enhanced_negative, strength)
            logger.info(f"✅ 负面提示词已增强 (水印强度: {strength})")
        
        # 获取高清修复参数
        hires_enabled = self.params.hires_fix_var.get()
        hires_scale = self.params.hires_scale_var.get()
        hires_denoise = self.params.hires_denoise_var.get()
        
        # 获取 ControlNet 状态
        use_controlnet = getattr(self.tab, 'use_controlnet', False)
        controlnet_type = "openpose"
        control_image = None
        
        if use_controlnet and hasattr(self.app, 'img2img_tab'):
            if hasattr(self.app.img2img_tab, 'controlnet_type_var'):
                selected_type = self.app.img2img_tab.controlnet_type_var.get()
                controlnet_type = selected_type.split(" ")[0] if " " in selected_type else "openpose"
        
        # ControlNet 强度映射
        CONTROLNET_STRENGTH_MAP = {
            "openpose": 0.85, "openpose_full": 0.85, "dwpose": 0.90,
            "canny": 0.70, "hed": 0.75, "lineart": 0.70,
            "scribble": 0.70, "depth": 0.80, "midas": 0.80,
            "normal": 0.80, "reference": 0.55,
            "mlsd": 0.80, "seg": 0.85, "tile": 0.90,
        }
        conditioning_scale = CONTROLNET_STRENGTH_MAP.get(controlnet_type, 0.80)
        
        try:
            pipe.to("cpu")
            generator = torch.Generator("cpu").manual_seed(seed)
            cancel_flag = lambda: self.tab.cancel_generation
            step_callback = Txt2ImgStepCallback(progress_cb, steps, start_time, cancel_flag, source="文生图")
            
            log("调用 pipeline...")
            with torch.no_grad():
                if not hires_enabled:
                    if use_controlnet and control_image is not None:
                        result = pipe(
                            prompt=prompt,
                            negative_prompt=enhanced_negative,
                            control_image=control_image,
                            controlnet_conditioning_scale=conditioning_scale,
                            num_inference_steps=steps,
                            guidance_scale=cfg,
                            generator=generator,
                            height=height,
                            width=width,
                            num_images_per_prompt=1,
                            callback_on_step_end=step_callback
                        )
                    else:
                        result = pipe(
                            prompt=prompt,
                            negative_prompt=enhanced_negative,
                            num_inference_steps=steps,
                            guidance_scale=cfg,
                            generator=generator,
                            height=height,
                            width=width,
                            num_images_per_prompt=1,
                            callback_on_step_end=step_callback
                        )
                else:
                    low_res_w = int(width / hires_scale)
                    low_res_h = int(height / hires_scale)
                    low_res_w = max(512, ((low_res_w + 31) // 64) * 64)
                    low_res_h = max(512, ((low_res_h + 31) // 64) * 64)
                    
                    logger.info(f"📐 启用高清修复: 初稿 {low_res_w}x{low_res_h} -> 最终 {width}x{height}")
                    progress_cb((index - 1) / total, f"🎨 生成初稿 ({low_res_w}x{low_res_h})...")
                    
                    if use_controlnet and control_image is not None:
                        low_res_result = pipe(
                            prompt=prompt,
                            negative_prompt=enhanced_negative,
                            control_image=control_image,
                            controlnet_conditioning_scale=conditioning_scale,
                            num_inference_steps=steps,
                            guidance_scale=cfg,
                            generator=generator,
                            height=low_res_h,
                            width=low_res_w,
                            num_images_per_prompt=1,
                            callback_on_step_end=step_callback
                        )
                    else:
                        low_res_result = pipe(
                            prompt=prompt,
                            negative_prompt=enhanced_negative,
                            num_inference_steps=steps,
                            guidance_scale=cfg,
                            generator=generator,
                            height=low_res_h,
                            width=low_res_w,
                            num_images_per_prompt=1,
                            callback_on_step_end=step_callback
                        )
                    
                    low_res_img = low_res_result.images[0]
                    progress_cb((index - 1) / total, f"🔄 放大并重绘 (幅度 {hires_denoise})...")
                    
                    result = pipe(
                        prompt=prompt,
                        negative_prompt=enhanced_negative,
                        image=low_res_img,
                        strength=hires_denoise,
                        num_inference_steps=steps,
                        guidance_scale=cfg,
                        generator=generator,
                        height=height,
                        width=width,
                        num_images_per_prompt=1,
                        callback_on_step_end=step_callback
                    )
                    
                    safe_del(low_res_result)
                    safe_del(low_res_img)
            
            log("pipeline 调用完成")
            image = result.images[0]
            
            # 保存图片 - 使用 saver
            filepath = self.saver.save(
                image=image,
                prompt=prompt,
                index=index
            )
            
            # 添加到预览
            self.app.root.after(0, lambda fp=filepath, img=image: self.app.add_to_preview(fp, img))
            
            safe_del(result)
            safe_del(generator)
            
            from gui.components.memory_monitor import get_memory_usage, force_memory_cleanup
            mem_gb = get_memory_usage()
            if mem_gb > 8.0:
                force_memory_cleanup()
            
            progress_cb(index / total, f"✅ 已保存 {index}/{total}")
            
            if callback:
                callback()
                
        except Exception as e:
            error_msg = str(e)
            if "用户取消" in error_msg or "cancelled" in error_msg.lower():
                self.app.root.after(0, lambda: self.tab.update_status("⏹️ 已取消"))
            else:
                self.app.root.after(0, lambda err=error_msg: self.tab._on_generation_error(err))
                raise