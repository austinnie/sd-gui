# core/pipeline/steps/olympian_gods_step.py
"""奥林匹斯众神风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class OlympianGodsStep(BaseStyleStep):
    """奥林匹斯众神风格转换步骤"""
    
    def __init__(self):
        super().__init__("olympian_gods", "转换为奥林匹斯众神风格")
        self._config = {
            "strength": 0.40,
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
            "strength": {"type": "float", "default": 0.40, "min": 0.25, "max": 0.65},
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
            "modern, 3d render, cartoon, anime, oil painting, asian, "
            "dark, gloomy, gothic, horror, deformed body"
        )
        return [
            {
                "name": "众神之王_宙斯",
                "prompt": "Greek god Zeus, king of Olympus, majestic bearded man, holding a golden thunderbolt, wearing a golden laurel wreath, classical white marble background, divine golden light, powerful and commanding presence, ancient mythology, high quality, masterpiece, photorealistic, fine art",
                "negative": base_negative
            },
            {
                "name": "智慧女神_雅典娜",
                "prompt": "Greek goddess Athena, goddess of wisdom and war, beautiful woman wearing golden helmet and armor, holding a shield and spear, piercing grey eyes, classical white marble temple background, divine golden light, majestic and intelligent, ancient Greek mythology, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "爱与美之神_阿芙洛狄忒",
                "prompt": "Greek goddess Aphrodite, goddess of love and beauty, incredibly beautiful woman emerging from sea foam, flowing golden hair, flawless marble skin, wearing delicate white peplos, gentle and seductive expression, divine romantic lighting, ancient Greek mythology, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "太阳神_阿波罗",
                "prompt": "Greek god Apollo, god of sun and music, handsome young man with golden hair, holding a golden lyre, radiant sunbeams shining behind him, classical white marble temple background, majestic and artistic presence, ancient Greek mythology, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "海神_波塞冬",
                "prompt": "Greek god Poseidon, god of the sea, muscular bearded man, holding a golden trident, standing on marble cliffs with ocean waves crashing behind, majestic and powerful, stormy sky, ancient Greek mythology, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]