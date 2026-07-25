# core/pipeline/steps/couple_oil_painting_step.py
"""情侣油画风格 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class CoupleOilPaintingStep(BaseStyleStep):
    """情侣油画风格"""
    
    def __init__(self):
        super().__init__("couple_oil_painting", "情侣油画风格")
        self._config = {
            "strength": 0.35,
            "cfg": 8.0,
            "steps": 35,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "hed",
            "controlnet_strength": 0.5,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.35, "min": 0.2, "max": 0.55},
            "cfg": {"type": "float", "default": 8.0, "min": 6, "max": 12},
            "steps": {"type": "int", "default": 35, "min": 25, "max": 60},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "hed",
                "choices": ["hed", "canny", "lineart"]
            },
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        return [
            {
                "name": "情侣油画_古典",
                "prompt": "oil painting, renaissance style, a loving couple, man and woman, two people, classical beauty, soft warm lighting, rich colors, elegant pose, velvet drapery, fine art, high quality, detailed, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, single person"
            },
            {
                "name": "情侣油画_浪漫",
                "prompt": "oil painting, romantic style, a loving couple, man and woman, two people, intimate embrace, soft warm lighting, rich colors, fine art, high quality, detailed, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, single person"
            },
            {
                "name": "情侣油画_宫廷",
                "prompt": "oil painting, baroque style, a noble couple, man and woman, two people, elegant clothing, dramatic lighting, rich colors, luxurious background, fine art, high quality, detailed, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, single person"
            }
        ]