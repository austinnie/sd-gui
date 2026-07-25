# core/pipeline/steps/lolita_step.py
"""洛丽塔风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class LolitaStep(BaseStyleStep):
    """洛丽塔风格转换步骤"""
    
    def __init__(self):
        super().__init__("lolita", "转换为洛丽塔风格")
        self._config = {
            "strength": 0.40,
            "cfg": 7.5,
            "steps": 28,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "hed",
            "controlnet_strength": 0.5,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.40, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 28, "min": 18, "max": 45},
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
                "name": "甜美洛丽塔",
                "prompt": "sweet lolita fashion, beautiful young woman, elegant dress, lace, ribbons, pastel colors, cute accessories, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, dark, gothic, mature"
            },
            {
                "name": "古典洛丽塔",
                "prompt": "classic lolita fashion, elegant young woman, vintage style dress, lace, pearls, refined, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, dark, casual"
            },
            {
                "name": "哥特洛丽塔",
                "prompt": "gothic lolita fashion, beautiful young woman, elegant black dress, lace, ribbons, dark accessories, mysterious, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, bright, pastel, sweet"
            },
            {
                "name": "中华洛丽塔",
                "prompt": "Chinese lolita fashion, beautiful young woman, elegant dress with Chinese elements, lace, ribbons, traditional fusion, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, dark, casual"
            }
        ]