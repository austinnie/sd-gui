# core/pipeline/steps/dunhuang_fresco_step.py
"""敦煌壁画飞天风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class DunhuangFrescoStep(BaseStyleStep):
    """敦煌壁画飞天风格转换步骤"""
    
    def __init__(self):
        super().__init__("dunhuang_fresco", "转换为敦煌壁画风格")
        self._config = {
            "strength": 0.40,
            "cfg": 8.0,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "lineart",
            "controlnet_strength": 0.4,
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
                "default": "lineart",
                "choices": ["canny", "hed", "lineart", "scribble"]
            },
            "controlnet_strength": {"type": "float", "default": 0.4, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.4), watermark, text, signature, "
            "photorealistic, 3d render, oil painting, modern, shiny, "
            "metal, neon, over-saturated"
        )
        return [
            {
                "name": "敦煌飞天_反弹琵琶",
                "prompt": "Dunhuang Mogao Caves fresco, flying Apsaras, heavenly maiden playing pipa behind her back, flowing silk ribbons, mineral pigment colors, red and blue tones, ancient wall painting, majestic religious art, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "敦煌飞天_散花",
                "prompt": "Dunhuang Mogao Caves fresco, flying Apsaras, heavenly maiden scattering flower petals, flowing ribbons, soft earthy colors, ancient wall painting texture, religious art, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "敦煌飞天_双人飞天",
                "prompt": "Dunhuang Mogao Caves fresco, two flying Apsaras, celestial dancers, intertwining silk ribbons, mineral pigments, warm earthy tones, ancient wall painting, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "敦煌飞天_独舞",
                "prompt": "Dunhuang Mogao Caves fresco, apsaras dancing in the sky, dynamic movement, flowing silk robes, ancient mural texture, mineral pigment colors, red and turquoise hues, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]