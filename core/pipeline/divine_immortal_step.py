# core/pipeline/steps/divine_immortal_step.py
"""紫气金身仙人风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class DivineImmortalStep(BaseStyleStep):
    """紫气金身仙人风格转换步骤"""
    
    def __init__(self):
        super().__init__("divine_immortal", "转换为紫气仙人风格")
        self._config = {
            "strength": 0.50,
            "cfg": 8.5,
            "steps": 35,
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
            "cfg": {"type": "float", "default": 8.5, "min": 6, "max": 12},
            "steps": {"type": "int", "default": 35, "min": 20, "max": 50},
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
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.4), watermark, text, signature, "
            "photorealistic, 3d render, dark, gloomy, horror, modern"
        )
        return [
            {
                "name": "紫气东来_真人",
                "prompt": "Divine immortal, purple auspicious clouds surrounding the figure, golden sacred glow, flowing silk robes, majestic expression, heavenly realm background, oriental fantasy, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "金身法相_仙尊",
                "prompt": "Golden divine immortal, magnificent celestial being, glowing golden skin, surrounded by radiant holy light and clouds, holding a magical artifact, awe-inspiring presence, ancient oriental myth, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "飞升成仙_金光",
                "prompt": "A person ascending to immortality, bathed in brilliant golden holy light, rising through the clouds, ethereal robes, divine glory, oriental fantasy, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "天宫仙姬_紫霞",
                "prompt": "Heavenly fairy maiden, wearing flowing colorful celestial robes, surrounded by purple and gold auspicious clouds, elegant and divine, heavenly palace background, oriental myth, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "炼丹炉_仙人",
                "prompt": "Immortal alchemist, beside a traditional Chinese elixir furnace (Danding), glowing purple smoke rising, flowing Taoist robes, ancient mystical atmosphere, oriental fantasy, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]