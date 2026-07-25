# core/pipeline/steps/couple_watercolor_step.py
"""情侣水彩风格 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class CoupleWatercolorStep(BaseStyleStep):
    """情侣水彩风格"""
    
    def __init__(self):
        super().__init__("couple_watercolor", "情侣水彩风格")
        self._config = {
            "strength": 0.40,
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
            "strength": {"type": "float", "default": 0.40, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 8.0, "min": 6, "max": 12},
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
                "name": "情侣水彩_拥抱",
                "prompt": "watercolor painting, a loving couple hugging, man and woman, two people, intimate embrace, soft brush strokes, flowing colors, artistic watercolor, romantic atmosphere, high quality, masterpiece, fine art",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, photorealistic, 3d render, oil painting, single person"
            },
            {
                "name": "情侣水彩_接吻",
                "prompt": "watercolor painting, a loving couple kissing, man and woman, two people, passionate kiss, soft brush strokes, flowing colors, artistic watercolor, romantic atmosphere, high quality, masterpiece, fine art",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, photorealistic, 3d render, oil painting, single person"
            },
            {
                "name": "情侣水彩_散步",
                "prompt": "watercolor painting, a loving couple walking together, hand in hand, man and woman, two people, soft brush strokes, flowing colors, artistic watercolor, romantic atmosphere, high quality, masterpiece, fine art",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, photorealistic, 3d render, oil painting, single person"
            }
        ]