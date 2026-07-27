# core/pipeline/steps/greek_hero_step.py
"""希腊神话英雄风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class GreekHeroStep(BaseStyleStep):
    """希腊神话英雄风格转换步骤"""
    
    def __init__(self):
        super().__init__("greek_hero", "转换为希腊神话英雄风格")
        self._config = {
            "strength": 0.45,
            "cfg": 7.5,
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
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
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
            "modern, 3d render, cartoon, anime, asian, modern clothing"
        )
        return [
            {
                "name": "英雄_珀尔修斯",
                "prompt": "Greek hero Perseus, holding a polished bronze shield and a curved sword, wearing classical Greek armor and a winged helmet, fierce and determined expression, dramatic battlefield background, ancient Greek mythology epic scene, high quality, masterpiece, photorealistic",
                "negative": base_negative
            },
            {
                "name": "英雄_赫拉克勒斯",
                "prompt": "Greek hero Heracles, incredibly muscular powerful man, wearing the Nemean lion skin, holding a massive wooden club, heroic stance, surrounded by glowing divine light, ancient Greek mythology, high quality, masterpiece, photorealistic",
                "negative": base_negative
            },
            {
                "name": "怪物_美杜莎",
                "prompt": "Medusa, legendary Greek monster, beautiful woman with a mass of living poisonous snakes for hair, glowing serpentine eyes, petrifying gaze, ancient dark temple background, terrifying and beautiful, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "半人马_喀戎",
                "prompt": "Greek myth Centaur Chiron, half human half horse, wise old centaur holding a bow, wearing a simple tunic, teaching heroes in the forest, majestic and knowledgeable, ancient Greek mythology, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "怪物_九头蛇",
                "prompt": "Greek myth Hydra, massive multi-headed water serpent, multiple heads hissing, huge coiled body, emerging from a dark swamp, terrifying powerful monster, ancient Greek mythology, high quality, masterpiece, photorealistic",
                "negative": base_negative
            }
        ]