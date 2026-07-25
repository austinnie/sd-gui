# core/pipeline/steps/kimono_step.py
"""和服风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class KimonoStep(BaseStyleStep):
    """和服风格转换步骤"""
    
    def __init__(self):
        super().__init__("kimono", "转换为和服风格")
        self._config = {
            "strength": 0.40,
            "cfg": 7.5,
            "steps": 28,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "hed",
            "controlnet_strength": 0.5,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.40, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 28, "min": 18, "max": 45},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "hed",
                "choices": ["hed", "canny", "lineart"]
            },
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        return [
            {
                "name": "传统和服",
                "prompt": "beautiful Japanese woman in elegant kimono, traditional Japanese clothing, obi, cherry blossoms, Japanese garden background, soft lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, modern clothes, casual, western"
            },
            {
                "name": "和服庭院",
                "prompt": "Japanese woman in kimono, traditional Japanese garden, pagoda, cherry blossoms, serene atmosphere, soft lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, modern, western"
            },
            {
                "name": "和服樱花",
                "prompt": "woman in kimono, cherry blossoms falling, pink petals, spring atmosphere, Japanese beauty, soft lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, winter, snow"
            },
            {
                "name": "和服雪景",
                "prompt": "Japanese woman in winter kimono, snow falling, Japanese garden, serene atmosphere, soft lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, summer, spring"
            }
        ]