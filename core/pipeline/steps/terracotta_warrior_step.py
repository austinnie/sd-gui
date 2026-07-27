# core/pipeline/steps/terracotta_warrior_step.py
"""兵马俑风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class TerracottaWarriorStep(BaseStyleStep):
    """兵马俑风格转换步骤"""
    
    def __init__(self):
        super().__init__("terracotta_warrior", "转换为兵马俑风格")
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
        # 强力防御：保持陶土质感，避免变成普通的真人照片或青铜雕像
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.4), watermark, text, signature, "
            "photorealistic, 3d render, oil painting, shiny, glossy, wet, "
            "colorful, modern, metal, gold, silver, bronze, plastic, alive"
        )
        return [
            {
                "name": "兵马俑_将军俑",
                "prompt": "Terracotta Warriors, ancient Chinese Qin dynasty sculpture, general figurine, reddish terracotta clay, detailed armored uniform, weathered earthen texture, dust on surface, historical archaeological site, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "兵马俑_跪射俑",
                "prompt": "Terracotta Warriors, ancient Chinese Qin dynasty sculpture, kneeling archer, reddish terracotta clay, dynamic pose holding crossbow, detailed armor plates, weathered clay texture, historical archaeological site, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "兵马俑_战马",
                "prompt": "Terracotta Warriors, ancient Chinese Qin dynasty sculpture, terracotta war horse, reddish clay, harness and saddle details, weathered earthen surface, historical archaeological site, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "兵马俑_群像",
                "prompt": "Terracotta Warriors, ancient Chinese Qin dynasty sculpture, a group of terracotta soldiers standing in formation, reddish clay, various martial poses, weathered earthen texture, historical archaeological site, dramatic lighting, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "兵马俑_面部特写",
                "prompt": "Terracotta Warriors, ancient Chinese Qin dynasty sculpture, close up warrior face, distinct facial features, moustache and topknot, reddish terracotta clay, weathered dusty texture, historical archaeological site, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]