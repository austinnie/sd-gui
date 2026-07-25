# core/pipeline/steps/group_photo_step.py
"""团队照片风格化 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class GroupPhotoStep(BaseStyleStep):
    """团队照片风格化"""
    
    def __init__(self):
        super().__init__("group_photo", "团队照片风格化")
        self._config = {
            "strength": 0.35,
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
            "strength": {"type": "float", "default": 0.35, "min": 0.2, "max": 0.55},
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
                "name": "团队合影_正式",
                "prompt": "professional team photo, group of people, formal attire, office background, professional atmosphere, full body, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, single person, casual"
            },
            {
                "name": "团队合影_商务",
                "prompt": "business team photo, group of professionals, suits, modern office, professional atmosphere, full body, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, single person, casual"
            },
            {
                "name": "团队合影_创意",
                "prompt": "creative team photo, group of people, casual, creative atmosphere, modern office, full body, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, single person, formal"
            }
        ]