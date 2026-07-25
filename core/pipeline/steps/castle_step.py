# core/pipeline/steps/castle_step.py
"""古堡场景转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class CastleStep(BaseStyleStep):
    """古堡场景转换步骤"""
    
    def __init__(self):
        super().__init__("castle", "将人物放到古堡背景")
        self._config = {
            "strength": 0.40,
            "cfg": 7.5,
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
            "strength": {"type": "float", "default": 0.40, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "canny",
                "choices": ["canny", "hed", "lineart", "depth"]
            },
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        return [
            {
                "name": "古堡公主",
                "prompt": "in a medieval castle, beautiful woman, elegant gown, stone walls, dramatic lighting, royal atmosphere, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, modern, city, street"
            },
            {
                "name": "古堡庭院",
                "prompt": "in a castle courtyard, stone architecture, ancient atmosphere, dramatic lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, modern, city"
            },
            {
                "name": "古堡舞会",
                "prompt": "castle ballroom, elegant, chandeliers, grand atmosphere, beautiful woman in formal gown, dramatic lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, modern, casual"
            },
            {
                "name": "古堡黄昏",
                "prompt": "standing in front of ancient castle, sunset, golden lighting, dramatic sky, medieval atmosphere, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, modern, city"
            }
        ]