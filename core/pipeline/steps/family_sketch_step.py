# core/pipeline/steps/family_sketch_step.py
"""家庭素描风格 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class FamilySketchStep(BaseStyleStep):
    """家庭素描风格"""
    
    def __init__(self):
        super().__init__("family_sketch", "家庭素描风格")
        self._config = {
            "strength": 0.35,
            "cfg": 7.0,
            "steps": 25,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "lineart",
            "controlnet_strength": 0.6,
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
                "default": "lineart",
                "choices": ["lineart", "canny", "hed", "scribble"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        return [
            {
                "name": "家庭素描_全家福",
                "prompt": "pencil sketch, family portrait, multiple people, parents and children, detailed drawing, fine art, shading, texture, monochrome, high quality, masterpiece, realistic sketch",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, single person"
            },
            {
                "name": "家庭素描_温馨",
                "prompt": "pencil sketch, loving family, parents and children, warm atmosphere, detailed drawing, fine art, shading, texture, monochrome, high quality, masterpiece, realistic sketch",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render"
            },
            {
                "name": "家庭素描_合影",
                "prompt": "pencil sketch, family group photo, multiple people, detailed drawing, fine art, shading, texture, monochrome, high quality, masterpiece, realistic sketch",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render"
            }
        ]