# core/pipeline/steps/greek_temple_step.py
"""古希腊神庙风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class GreekTempleStep(BaseStyleStep):
    """古希腊神庙风格转换步骤"""
    
    def __init__(self):
        super().__init__("greek_temple", "转换为古希腊神庙风格")
        self._config = {
            "strength": 0.50,
            "cfg": 8.0,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "canny",
            "controlnet_strength": 0.5,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.50, "min": 0.3, "max": 0.7},
            "cfg": {"type": "float", "default": 8.0, "min": 6, "max": 12},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "canny",
                "choices": ["canny", "hed", "lineart", "scribble"]
            },
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, "
            "modern, 3d render, oil painting, asian architecture, "
            "dark, gloomy, horror, cartoon, anime"
        )
        return [
            {
                "name": "帕特农神庙_遗迹",
                "prompt": "Ancient Greek temple ruins of the Parthenon, white marble columns, weathered stone structure, golden hour sunlight, majestic architectural ruins, historical site, high quality, masterpiece, photorealistic",
                "negative": base_negative
            },
            {
                "name": "雅典卫城_远眺",
                "prompt": "View of the Acropolis of Athens, ancient Greek temple complex on a rocky hill, white marble structures, blue Mediterranean sky, golden sunlight, historical landmark, high quality, masterpiece, photorealistic",
                "negative": base_negative
            },
            {
                "name": "神庙_黎明",
                "prompt": "Ancient Greek marble temple, majestic stone columns, morning fog lifting, golden sunrise shining through the columns, serene and divine atmosphere, historical archaeological site, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "神庙_废墟_雕像",
                "prompt": "Ancient Greek temple ruins, weathered marble columns, fallen statues of gods, overgrown green grass, dramatic sunset lighting, historical atmosphere, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "空中神庙_幻想",
                "prompt": "Fantasy ancient Greek temple floating high in the clouds, white marble columns, golden light piercing through clouds, magical divine atmosphere, ancient mythology concept art, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]