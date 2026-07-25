# core/pipeline/steps/cyberpunk_step.py
"""赛博朋克风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class CyberpunkStep(BaseStyleStep):
    """赛博朋克风格转换步骤"""
    
    def __init__(self):
        super().__init__("cyberpunk", "转换为赛博朋克风格")
        self._config = {
            "strength": 0.50,
            "cfg": 8.0,
            "steps": 35,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "canny",
            "controlnet_strength": 0.6,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.50, "min": 0.3, "max": 0.7},
            "cfg": {"type": "float", "default": 8.0, "min": 6, "max": 12},
            "steps": {"type": "int", "default": 35, "min": 25, "max": 60},
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
                "name": "赛博朋克女郎",
                "prompt": "cyberpunk style, beautiful woman, neon lights, futuristic city, cybernetic implants, colorful hair, reflective jacket, dark atmosphere, rain, holographic elements, high tech, edgy, full body shot, high quality, masterpiece, detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, natural, daylight"
            },
            {
                "name": "赛博朋克都市",
                "prompt": "cyberpunk cityscape, neon lights, futuristic buildings, rain, holographic billboards, dark atmosphere, high tech, edgy, high quality, masterpiece, detailed, cinematic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, vintage, rustic, natural, daylight"
            },
            {
                "name": "赛博朋克战士",
                "prompt": "cyberpunk warrior, futuristic armor, neon lights, cybernetic enhancements, dark atmosphere, high tech, edgy, high quality, masterpiece, detailed, cinematic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, natural, daylight"
            }
        ]