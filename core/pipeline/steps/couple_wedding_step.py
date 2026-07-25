# core/pipeline/steps/couple_wedding_step.py
"""婚纱照双人风格 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class CoupleWeddingStep(BaseStyleStep):
    """婚纱照双人风格"""
    
    def __init__(self):
        super().__init__("couple_wedding", "婚纱照双人风格")
        self._config = {
            "strength": 0.40,
            "cfg": 7.5,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "hed",
            "controlnet_strength": 0.5,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.40, "min": 0.25, "max": 0.6},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
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
                "name": "婚纱双人_拥抱",
                "prompt": "couple wedding photo, bride and groom, hugging, wedding dress and suit, romantic atmosphere, soft lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, single person, sad, dark"
            },
            {
                "name": "婚纱双人_接吻",
                "prompt": "couple wedding photo, bride and groom, kissing, wedding dress and suit, romantic atmosphere, soft lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, single person, sad, dark"
            },
            {
                "name": "婚纱双人_牵手",
                "prompt": "couple wedding photo, bride and groom, holding hands, wedding dress and suit, romantic atmosphere, soft lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, single person, sad, dark"
            },
            {
                "name": "婚纱双人_背影",
                "prompt": "couple wedding photo from behind, bride and groom, wedding dress and suit, romantic atmosphere, soft lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, single person, sad, dark"
            }
        ]