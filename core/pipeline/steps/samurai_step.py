# core/pipeline/steps/samurai_step.py
"""日本战国武士风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class SamuraiStep(BaseStyleStep):
    """日本战国武士风格转换步骤"""
    
    def __init__(self):
        super().__init__("samurai", "转换为日本战国武士风格")
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
            "modern, 3d render, chinese, western, sunny, colorful"
        )
        return [
            {
                "name": "武士_拔刀",
                "prompt": "Japanese Samurai, wearing traditional O-yoroi armor, holding a Katana sword, battle-ready posture, fierce expression, dark dramatic atmosphere, ancient Japanese warfare, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "天狗_妖怪",
                "prompt": "Tengu, legendary Japanese creature, half bird half human, wearing monk robes, with a long red nose and large wings, mysterious supernatural atmosphere, Japanese folklore, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "阴阳师_式神",
                "prompt": "Onmyoji Japanese sorcerer, wearing traditional Heian era robes, holding a sacred talisman, summoning a magical Shikigami spirit, glowing paper charm, mystical and haunting atmosphere, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "甲胄_女武者",
                "prompt": "Japanese female warrior, wearing elaborate black and red lacquered armor, a graceful yet fierce figure, holding a long yari spear, cherry blossom petals falling, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]