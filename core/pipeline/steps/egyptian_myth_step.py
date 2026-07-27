# core/pipeline/steps/egyptian_myth_step.py
"""古埃及神话风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class EgyptianMythStep(BaseStyleStep):
    """古埃及神话风格转换步骤"""
    
    def __init__(self):
        super().__init__("egyptian_myth", "转换为古埃及神话风格")
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
            "strength": {"type": "float", "default": 0.45, "min": 0.3, "max": 0.7},
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
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.4), watermark, text, signature, "
            "modern, 3d render, cartoon, anime, dark, medieval"
        )
        return [
            {
                "name": "法老黄金面具",
                "prompt": "Ancient Egyptian Pharaoh, wearing brilliant gold burial mask, intricate hieroglyphics, lapis lazuli inlays, majestic and powerful expression, dark tomb background, golden light, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "女神_伊西斯",
                "prompt": "Egyptian goddess Isis, beautiful woman with wings, wearing traditional Egyptian headdress with cow horns and solar disc, holding an ankh, majestic divine presence, ancient temple background, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "太阳神_拉",
                "prompt": "Egyptian sun god Ra, falcon-headed man, wearing a golden solar disk headdress, holding a divine staff, radiant golden sunlight, powerful divine presence, ancient Egyptian mythology, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "阿努比斯_冥神",
                "prompt": "Anubis, Egyptian god of the dead, jackal-headed man, wearing black and gold ceremonial robes, holding a sacred Ankh, mysterious and solemn atmosphere, ancient Egyptian underworld, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]