# core/pipeline/steps/norse_myth_step.py
"""北欧神话风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class NorseMythStep(BaseStyleStep):
    """北欧神话风格转换步骤"""
    
    def __init__(self):
        super().__init__("norse_myth", "转换为北欧神话风格")
        self._config = {
            "strength": 0.45,
            "cfg": 7.5,
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
            "strength": {"type": "float", "default": 0.45, "min": 0.3, "max": 0.7},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
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
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.4), watermark, text, signature, "
            "modern, cartoon, anime, sunny, vibrant, asian"
        )
        return [
            {
                "name": "雷神_索尔",
                "prompt": "Norse god Thor, muscular bearded man, wearing dark armor and red cape, holding Mjolnir the war hammer, stormy sky with lightning, cold and powerful atmosphere, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "众神之父_奥丁",
                "prompt": "Norse god Odin, one-eyed wise old man, wearing a wide-brimmed hat and dark cloak, holding a spear, surrounded by ravens, majestic and mysterious presence, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "女武神_瓦尔基里",
                "prompt": "Valkyrie, female warrior of Norse mythology, wearing winged helmet and shining silver armor, carrying a sword, long flowing hair, riding through the clouds, majestic divine presence, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "世界树_尤克特拉希尔",
                "prompt": "Yggdrasil, the world tree of Norse mythology, massive ancient evergreen tree connecting different realms, mystical glowing runes on the bark, majestic and sacred presence, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]