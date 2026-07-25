# core/pipeline/steps/space_step.py
"""太空场景转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class SpaceStep(BaseStyleStep):
    """太空场景转换步骤"""
    
    def __init__(self):
        super().__init__("space", "将人物放到太空背景")
        self._config = {
            "strength": 0.50,
            "cfg": 8.0,
            "steps": 35,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "canny",
            "controlnet_strength": 0.5,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.50, "min": 0.3, "max": 0.7},
            "cfg": {"type": "float", "default": 8.0, "min": 6, "max": 12},
            "steps": {"type": "int", "default": 35, "min": 25, "max": 60},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "canny",
                "choices": ["canny", "hed", "lineart", "depth"]
            },
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        return [
            {
                "name": "太空漫步",
                "prompt": "floating in space, stars, galaxy, nebula, cosmic background, astronaut or futuristic, sci-fi atmosphere, dramatic lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, earth, ground, building"
            },
            {
                "name": "星际旅行",
                "prompt": "space travel, futuristic, stars, galaxy, spaceship, cosmic background, sci-fi atmosphere, dramatic lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, earth, ground"
            },
            {
                "name": "星云女神",
                "prompt": "goddess in space, floating, stars, colorful nebula, cosmic background, ethereal, mystical, dramatic lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, earth, ground"
            },
            {
                "name": "月球表面",
                "prompt": "standing on the moon, earth in background, stars, cosmic atmosphere, dramatic lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, building, city"
            }
        ]