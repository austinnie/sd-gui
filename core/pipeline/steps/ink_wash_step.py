# core/pipeline/steps/ink_wash_step.py
"""国风水墨风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class InkWashStep(BaseStyleStep):
    """国风水墨风格转换步骤"""
    
    def __init__(self):
        super().__init__("ink_wash", "转换为国风水墨风格")
        self._config = {
            "strength": 0.45,
            "cfg": 7.5,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "lineart",
            "controlnet_strength": 0.6,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.25, "max": 0.65},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "lineart",
                "choices": ["canny", "hed", "lineart", "scribble"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        return [
            {
                "name": "水墨人物",
                "prompt": "ink wash painting style, traditional Chinese painting, a beautiful woman, flowing brush strokes, black ink on rice paper, elegant minimalist style, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, photorealistic, 3d render, oil painting, color"
            },
            {
                "name": "水墨山水",
                "prompt": "ink wash painting style, traditional Chinese landscape, mountains and rivers, flowing brush strokes, black ink on rice paper, elegant minimalist style, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, photorealistic, 3d render, oil painting, color"
            },
            {
                "name": "水墨花鸟",
                "prompt": "ink wash painting style, traditional Chinese flower and bird painting, elegant brush strokes, black ink on rice paper, minimalist style, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, photorealistic, 3d render, oil painting, color"
            },
            {
                "name": "水墨古风",
                "prompt": "ink wash painting style, ancient Chinese style, elegant lady in traditional clothing, flowing brush strokes, black ink on rice paper, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, photorealistic, 3d render, oil painting, color"
            }
        ]