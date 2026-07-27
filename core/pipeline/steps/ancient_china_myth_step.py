# core/pipeline/steps/ancient_china_myth_step.py
"""中国上古神话风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class AncientChinaMythStep(BaseStyleStep):
    """中国上古神话风格转换步骤"""
    
    def __init__(self):
        super().__init__("ancient_china_myth", "转换为中国上古神话风格")
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
            "strength": {"type": "float", "default": 0.45, "min": 0.3, "max": 0.65},
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
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.4), watermark, text, signature, "
            "modern, 3d render, western, anime, cartoon"
        )
        return [
            {
                "name": "女娲补天",
                "prompt": "Nuwa mending the sky, ancient Chinese goddess, half human half snake, magnificent divine being, holding sacred colorful stones, filling the celestial gap, ancient chaos era, oriental mythology, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "盘古开天",
                "prompt": "Pangu separating heaven and earth, giant primal being, holding a massive divine axe, breaking the cosmic egg, emerging chaos and light, ancient Chinese creation myth, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "山海经_麒麟",
                "prompt": "Qilin, ancient auspicious beast, dragon-like head, deer-like body, covered in scales, fiery mane and tail, majestic mythical creature, surrounded by mist and clouds, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "山海经_九尾狐",
                "prompt": "Nine-tailed fox, mythical fox beast, elegant and enchanting, nine flowing tails, ancient Chinese mythology, spiritual creature, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "洪荒_神龙",
                "prompt": "Ancient Chinese dragon, majestic mythological beast, long serpentine body with scales, horned head, powerful claws, soaring through clouds, vibrant colors, oriental legend, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]