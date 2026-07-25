# core/pipeline/steps/cinematic_step.py
"""电影质感风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class CinematicStep(BaseStyleStep):
    """电影质感风格转换步骤"""
    
    def __init__(self):
        super().__init__("cinematic", "转换为电影质感风格")
        self._config = {
            "strength": 0.40,
            "cfg": 7.5,
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
            "strength": {"type": "float", "default": 0.40, "min": 0.25, "max": 0.6},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
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
                "name": "电影镜头",
                "prompt": "cinematic shot, movie still, dramatic lighting, film grain, beautiful composition, emotional atmosphere, high quality, masterpiece, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, amateur, snap shot"
            },
            {
                "name": "电影特写",
                "prompt": "cinematic close-up, dramatic lighting, film grain, emotional expression, movie still, high quality, masterpiece, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, amateur, snap shot"
            },
            {
                "name": "电影氛围",
                "prompt": "cinematic atmosphere, dramatic lighting, film grain, moody, emotional, movie still, high quality, masterpiece, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, amateur, flat lighting"
            },
            {
                "name": "电影大片",
                "prompt": "epic cinematic shot, dramatic lighting, film grain, grand atmosphere, movie still, high quality, masterpiece, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, amateur, flat"
            }
        ]