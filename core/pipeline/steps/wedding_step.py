# core/pipeline/steps/wedding_step.py
"""婚纱风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class WeddingStep(BaseStyleStep):
    """婚纱风格转换步骤"""
    
    def __init__(self):
        super().__init__("wedding", "转换为婚纱/婚礼风格")
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
            "strength": {"type": "float", "default": 0.40, "min": 0.2, "max": 0.6},
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
                "name": "新娘肖像",
                "prompt": "beautiful bride in wedding dress, elegant white gown, veil, bouquet, romantic lighting, soft focus, wedding photography, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, casual, dark, sad"
            },
            {
                "name": "婚纱全身",
                "prompt": "bride in stunning wedding dress, full body, elegant pose, cathedral or garden background, romantic atmosphere, soft lighting, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, casual, dark"
            },
            {
                "name": "婚礼现场",
                "prompt": "wedding ceremony, bride and groom, beautiful venue, flowers, romantic atmosphere, soft lighting, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, sad, dark"
            },
            {
                "name": "婚纱背影",
                "prompt": "bride in wedding dress from behind, beautiful train, veil, elegant pose, romantic atmosphere, soft lighting, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, casual, dark"
            }
        ]