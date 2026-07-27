# core/pipeline/steps/roman_empire_step.py
"""古罗马帝国风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class RomanEmpireStep(BaseStyleStep):
    """古罗马帝国风格转换步骤"""
    
    def __init__(self):
        super().__init__("roman_empire", "转换为古罗马帝国风格")
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
            "modern, 3d render, cartoon, anime, asian, dark, gloomy"
        )
        return [
            {
                "name": "罗马帝国_军团士兵",
                "prompt": "Roman legionary soldier, wearing steel segmented armor (lorica segmentata), carrying a large scutum shield, wearing a Roman helmet with crest, standing confidently in a battlefield, high quality, masterpiece, photorealistic",
                "negative": base_negative
            },
            {
                "name": "凯撒大帝_凯旋",
                "prompt": "Julius Caesar, Roman Emperor, wearing a golden laurel wreath and purple toga, majestic and powerful expression, standing in front of a Roman triumphal arch, grand imperial atmosphere, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "罗马角斗士",
                "prompt": "Roman gladiator, muscular warrior, wearing bronze armor and a gladiator helmet, holding a sword and net, fierce battle-ready posture, stands inside the Colosseum, ancient epic scene, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "罗马元老院",
                "prompt": "Roman Senators gathered in the Curia Julia, wearing white togas with purple borders, debating passionately in the grand chamber, marble statues and architecture, ancient Roman politics, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]