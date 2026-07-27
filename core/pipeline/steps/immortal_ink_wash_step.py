# core/pipeline/steps/immortal_ink_wash_step.py
"""画中仙水墨风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class ImmortalInkWashStep(BaseStyleStep):
    """画中仙水墨风格转换步骤"""
    
    def __init__(self):
        super().__init__("immortal_ink_wash", "转换为画中仙水墨风格")
        self._config = {
            "strength": 0.40,
            "cfg": 7.5,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "lineart",
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
                "default": "lineart",
                "choices": ["canny", "hed", "lineart", "scribble"]
            },
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.4), (red stamp:1.4), watermark, text, signature, "
            "photorealistic, 3d render, oil painting, color, neon, modern"
        )
        return [
            {
                "name": "画中仙_云雾",
                "prompt": "ink wash painting style, traditional Chinese painting, immortal figure in mist, flowing robes, translucent ink shades, black ink on rice paper, ethereal and dreamy, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "画中仙_踏云",
                "prompt": "ink wash painting style, traditional Chinese painting, immortal riding clouds, minimalist composition, splashed ink, dry brush, black ink on rice paper, elegant minimalist style, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "仙人论道_水墨",
                "prompt": "ink wash painting style, traditional Chinese painting, two immortals discussing Taoism, sitting on a mountain, flowing robes, soft ink diffusion, black ink on rice paper, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "仙人抚琴_水墨",
                "prompt": "ink wash painting style, traditional Chinese painting, immortal playing Guqin on a cliff, flowing ink brush strokes, misty valley, black ink on rice paper, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "云海山门_水墨",
                "prompt": "ink wash painting style, traditional Chinese landscape, ancient Taoist mountain gate standing in the sea of clouds, majestic mountains, dry brush technique, black ink on rice paper, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            }
        ]