# gui/tabs/interrogate/backends/blip.py
"""BLIP 反推后端"""

import os
from PIL import Image
from .base import InterrogateBackend

# ✅ 在文件顶部添加
from services.cache_config import HF_HUB_CACHE

# 设置环境变量
os.environ["TRANSFORMERS_CACHE"] = HF_HUB_CACHE


class BlipBackend(InterrogateBackend):
    """BLIP 自然语言描述"""
    
    def interrogate(self, image_path: str, **kwargs) -> str:
        model_name = kwargs.get('model_name', 'BLIP-base (快速)')
        
        if self.tab.cancel_interrogate:
            return "已取消"
        
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
        except ImportError:
            return "BLIP 未安装"
        
        image = Image.open(image_path).convert('RGB')
        if max(image.size) > 512:
            image.thumbnail((512, 512))
        
        if "large" in model_name.lower():
            processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
            model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
            max_len = 80
        else:
            processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            max_len = 50
        
        if self.tab.cancel_interrogate:
            return "已取消"
        
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs, max_length=max_len, num_beams=3, repetition_penalty=1.1)
        caption = processor.decode(out[0], skip_special_tokens=True)
        return caption