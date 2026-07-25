# gui/tabs/img2img/saver.py
"""图生图图片保存和后处理"""

import os
from datetime import datetime
from PIL import Image

from utils.watermark_remover import WatermarkRemover
from utils.image_post_processor import post_process_image


from utils.logger import get_logger, info, warning, error, debug

logger = get_logger(__name__)
class ImageSaver:
    """图生图图片保存器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.params = tab.params
    
    def save(self, image: Image.Image, prompt: str, img_idx: int = 1,
             var_idx: int = 1, prefix: str = "img2img") -> str:
        """保存图片并应用后处理"""
        from config.app_config import app_config
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_preview = "".join(c for c in prompt[:30] if c.isalnum() or c in " _-") or "image"
        if len(prompt_preview) > 50:
            prompt_preview = prompt_preview[:50]
        
        filename = f"{timestamp}_{prefix}_img{img_idx+1}_var{var_idx+1}_{prompt_preview}.png"
        
        output_dir = app_config.paths.output_dir
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        # 水印去除
        if self.params.remove_watermark_var.get() and self.params.watermark_post_process_var.get():
            from utils.watermark_remover import WatermarkRemover
            watermark_remover = WatermarkRemover()
            methods = ["opencv_inpaint", "opencv_blur"]
            cleaned = watermark_remover.remove_watermark(
                image,
                methods=methods,
                strength=self.params.watermark_strength_var.get(),
                auto_detect=self.params.watermark_auto_detect_var.get()
            )
            cleaned.save(filepath, quality=95)
            logger.info(f"✅ 图生图水印已去除: {filename}")
        else:
            image.save(filepath)
        
        # 图片后期处理
        final_path = post_process_image(
            filepath,
            self.params,
            prompt=prompt,
            log_prefix="[图生图]"
        )
        
        if final_path != filepath:
            try:
                os.remove(filepath)
            except:
                pass
            filepath = final_path
        
        # 添加到预览
        self.app.root.after(0, lambda: self.app.add_to_preview(filepath, image))
        
        return filepath