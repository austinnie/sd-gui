# core/pipeline/steps/vintage_step.py
"""复古照片风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class VintageStep(BaseStyleStep):
    """复古照片风格转换步骤"""
    
    def __init__(self):
        super().__init__("vintage", "转换为复古照片风格")
        self._config = {
            "strength": 0.35,
            "cfg": 7.0,
            "steps": 25,
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
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 9},
            "steps": {"type": "int", "default": 25, "min": 15, "max": 40},
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
                "name": "复古胶片",
                "prompt": "vintage film photography, retro style, warm tones, grain, nostalgic atmosphere, beautiful woman, classic beauty, high quality, masterpiece, photorealistic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, modern, digital, cold tones"
            },
            {
                "name": "旧时光",
                "prompt": "old fashioned style, vintage photography, sepia tones, nostalgic atmosphere, classic beauty, retro clothing, high quality, masterpiece, photorealistic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, modern, digital"
            },
            {
                "name": "古典肖像",
                "prompt": "classic portrait photography, vintage style, soft lighting, timeless beauty, elegant pose, high quality, masterpiece, photorealistic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, modern, casual"
            },
            {
                "name": "复古街拍",
                "prompt": "vintage street photography, retro style, nostalgic atmosphere, classic fashion, high quality, masterpiece, photorealistic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, modern, digital"
            }
        ]