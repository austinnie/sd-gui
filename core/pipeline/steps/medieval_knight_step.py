# core/pipeline/steps/medieval_knight_step.py
"""中世纪骑士风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class MedievalKnightStep(BaseStyleStep):
    """中世纪骑士风格转换步骤"""
    
    def __init__(self):
        super().__init__("medieval_knight", "转换为中世纪骑士风格")
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
            "modern, 3d render, cartoon, anime, asian"
        )
        return [
            {
                "name": "圣骑士_重甲",
                "prompt": "Medieval knight, fully clad in gleaming steel plate armor, holding a large broadsword, knight helmet with visor down, dramatic lighting, standing in a castle courtyard, heroic and majestic, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "飞龙_幻想",
                "prompt": "Majestic Western dragon, huge wings and scales, breathing fire, soaring above a medieval castle, epic fantasy battle scene, incredible detail, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "女骑士",
                "prompt": "Female medieval knight, beautiful woman with flowing hair, wearing ornate plate armor, holding a sword and shield, confident and heroic posture, dramatic golden sunset background, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "屠龙者",
                "prompt": "Medieval knight facing a huge dragon, holding a glowing sword raised high, dynamic combat pose, fierce mythical beast, epic fantasy battle, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]