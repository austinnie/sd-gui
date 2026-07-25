# core/pipeline/steps/watercolor_step.py
"""水彩风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class WatercolorStep(BaseStyleStep):
    """水彩风格转换步骤"""
    
    def __init__(self):
        super().__init__("watercolor", "转换为水彩画风格")
        self._config = {
            "strength": 0.40,
            "cfg": 8.0,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "canny",
            "controlnet_strength": 0.6,
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
                "default": "canny",
                "choices": ["canny", "hed", "lineart", "scribble"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        return [
            {
                "name": "水彩人物",
                "prompt": "watercolor painting, beautiful woman portrait, soft brush strokes, flowing colors, artistic watercolor, wet on wet technique, gentle color transitions, delicate paper texture, high quality, masterpiece, fine art",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, photorealistic, 3d render, oil painting, digital art"
            },
            {
                "name": "水彩风景",
                "prompt": "watercolor painting, beautiful scenery, mountains and river, soft brush strokes, flowing colors, artistic watercolor, wet on wet technique, gentle color transitions, delicate paper texture, high quality, masterpiece, fine art",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, photorealistic, 3d render, oil painting, digital art"
            },
            {
                "name": "水彩花卉",
                "prompt": "watercolor painting, beautiful flowers, soft brush strokes, flowing colors, artistic watercolor, wet on wet technique, gentle color transitions, delicate paper texture, high quality, masterpiece, fine art",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, photorealistic, 3d render, oil painting, digital art"
            }
        ]