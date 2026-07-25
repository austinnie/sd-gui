# core/pipeline/steps/oil_painting_step.py
"""油画风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class OilPaintingStep(BaseStyleStep):
    """油画风格转换步骤"""
    
    def __init__(self):
        super().__init__("oil_painting", "转换为油画风格")
        self._config = {
            "strength": 0.35,
            "cfg": 8.0,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "hed",
            "controlnet_strength": 0.5,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.35, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 8.0, "min": 6, "max": 12},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 60},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "hed",
                "choices": ["canny", "hed", "lineart", "scribble"]
            },
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        return [
            {
                "name": "文艺复兴裸体",
                "prompt": "masterpiece, best quality, oil painting, renaissance style, a beautiful European woman, classical nude, soft lighting, warm skin tones, rich colors, elegant pose, velvet drapery, renaissance background, fine art, high quality, detailed, timeless beauty, classical painting style",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, explicit, pornographic"
            },
            {
                "name": "维纳斯诞生",
                "prompt": "masterpiece, best quality, oil painting, botticelli style, venus rising from sea, classical beauty, nude goddess, flowing hair, renaissance painting, shell, soft warm lighting, rich colors, fine art, masterpiece, timeless beauty",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, explicit, pornographic"
            },
            {
                "name": "古典油画裸体",
                "prompt": "masterpiece, best quality, oil painting, classical art, a beautiful European woman, nude, soft warm lighting, rich golden tones, elegant reclining pose, luxurious fabrics, classical background, baroque style, fine art, high quality, detailed, masterpiece painting",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, explicit, pornographic"
            },
            {
                "name": "巴洛克裸体",
                "prompt": "masterpiece, best quality, oil painting, baroque style, a beautiful European woman, classical nude, dramatic chiaroscuro lighting, rich dark background, elegant pose, luxurious fabrics, fine art, high quality, detailed, masterpiece, old masters style",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, explicit, pornographic"
            },
            {
                "name": "洛可可裸体",
                "prompt": "masterpiece, best quality, oil painting, rococo style, a beautiful European woman, classical nude, soft pastel colors, elegant pose, luxurious boudoir, ornate background, fine art, high quality, detailed, masterpiece, feminine beauty, 18th century style",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, explicit, pornographic"
            },
            {
                "name": "新古典主义裸体",
                "prompt": "masterpiece, best quality, oil painting, neoclassical style, a beautiful European woman, classical nude, soft lighting, marble background, elegant pose, ancient Greek inspiration, fine art, high quality, detailed, masterpiece, timeless beauty",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, explicit, pornographic"
            }
        ]