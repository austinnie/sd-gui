# core/pipeline/steps/vaporwave_step.py
"""蒸汽波风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class VaporwaveStep(BaseStyleStep):
    """蒸汽波风格转换步骤"""
    
    def __init__(self):
        super().__init__("vaporwave", "转换为蒸汽波风格")
        self._config = {
            "strength": 0.45,
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
            "strength": {"type": "float", "default": 0.45, "min": 0.25, "max": 0.65},
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
        return [
            {
                "name": "蒸汽波女郎",
                "prompt": "vaporwave style, aesthetic, beautiful woman, pastel colors, pink and cyan, neon glow, 90s retro, synthwave, dreamy atmosphere, statues, tropical elements, high quality, masterpiece, detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, realistic, photorealistic, dark"
            },
            {
                "name": "蒸汽波风景",
                "prompt": "vaporwave aesthetic, pastel colors, pink and cyan, neon glow, 90s retro, synthwave, dreamy atmosphere, sunset, palm trees, grid, high quality, masterpiece, detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, realistic, photorealistic, dark"
            },
            {
                "name": "蒸汽波都市",
                "prompt": "vaporwave city, aesthetic, pastel colors, pink and cyan, neon glow, 90s retro, synthwave, dreamy atmosphere, sunset, high quality, masterpiece, detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, realistic, photorealistic, dark"
            }
        ]