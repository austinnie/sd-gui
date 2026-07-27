# core/pipeline/steps/hindu_gods_step.py
"""印度教三大主神风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class HinduGodsStep(BaseStyleStep):
    """印度教三大主神风格转换步骤"""
    
    def __init__(self):
        super().__init__("hindu_gods", "转换为印度教主神风格")
        self._config = {
            "strength": 0.45,
            "cfg": 8.0,
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
            "cfg": {"type": "float", "default": 8.0, "min": 6, "max": 12},
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
            "modern, 3d render, cartoon, anime, western, mundane, plain"
        )
        return [
            {
                "name": "创世神_梵天",
                "prompt": "Lord Brahma, Hindu creator god, four faces, four arms, wearing magnificent golden crown and sacred robes, holding a Vedas book and a lotus, sitting on a lotus throne, majestic divine presence, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "守护神_毗湿奴",
                "prompt": "Lord Vishnu, Hindu preserver god, four arms, beautiful blue skin, wearing a golden crown and sacred garlands, holding a golden discus (Sudarshana Chakra) and a conch shell, reclining on the cosmic serpent Shesha, divine and serene presence, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "毁灭神_湿婆",
                "prompt": "Lord Shiva, Hindu destroyer god, third eye, crescent moon in his hair, holding a trident (Trishula), blue skin, wearing tiger skin, dancing the cosmic dance (Tandava), fierce and powerful divine presence, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "湿婆_冥想",
                "prompt": "Lord Shiva meditating on Mount Kailash, sitting in lotus position, wearing sacred rudraksha beads, mystical spiritual atmosphere, peaceful but powerful cosmic energy, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]