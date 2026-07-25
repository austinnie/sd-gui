# core/pipeline/steps/friends_style_step.py
"""朋友聚会风格化 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class FriendsStyleStep(BaseStyleStep):
    """朋友聚会风格化"""
    
    def __init__(self):
        super().__init__("friends_style", "朋友聚会风格化")
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
                "name": "朋友聚会_城市",
                "prompt": "group of friends, multiple people, urban style, trendy, city background, natural lighting, full body, happy atmosphere, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, single person, sad, lonely"
            },
            {
                "name": "朋友聚会_街头",
                "prompt": "friends hanging out, group of people, street style, urban background, natural lighting, full body, joyful atmosphere, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, single person"
            },
            {
                "name": "朋友聚会_咖啡厅",
                "prompt": "friends gathering at cafe, group of people, cozy atmosphere, warm lighting, full body, happy expression, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, single person"
            }
        ]