# core/pipeline/steps/western_god_step.py
"""西方上帝/造物主风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class WesternGodStep(BaseStyleStep):
    """西方上帝/造物主风格转换步骤"""
    
    def __init__(self):
        super().__init__("western_god", "转换为西方上帝/造物主风格")
        self._config = {
            "strength": 0.40,
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
            "strength": {"type": "float", "default": 0.40, "min": 0.25, "max": 0.65},
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
            "modern, 3d render, cartoon, anime, dark, horror, demonic"
        )
        return [
            {
                "name": "上帝_造物主",
                "prompt": "God the creator, majestic old man with long white beard and hair, wearing brilliant white radiant robes, divine light shining from behind, reaching out hand, classical renaissance oil painting style, heavenly clouds and sky, sacred awe-inspiring presence, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "上帝_创世纪",
                "prompt": "God creating the world, divine figure emerging from chaos, bright light piercing darkness, classical Michelangelo style, supreme being with flowing robes, sacred atmosphere, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "上帝_圣光",
                "prompt": "God descending from heaven, brilliant white and golden holy light rays, divine savior figure, wearing immaculate white robes, ethereal and majestic, heavenly realm background, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "上帝_审判",
                "prompt": "God the judge, stern and majestic expression, sitting on a divine throne, radiant light and clouds, classical oil painting, sacred solemn atmosphere, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]