# core/pipeline/steps/couple_step.py
"""情侣场景转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class CoupleStep(BaseStyleStep):
    """情侣场景转换步骤"""
    
    def __init__(self):
        super().__init__("couple", "生成情侣拥抱/接吻场景")
        self._config = {
            "strength": 0.45,
            "cfg": 7.0,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "openpose",
            "controlnet_strength": 0.6,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.3, "max": 0.7},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "openpose",
                "choices": ["openpose", "canny", "hed", "lineart"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        return [
            {
                "name": "深情拥抱",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a man and woman hugging each other, warm embrace, intimate moment, loving couple, affectionate, close up, soft lighting, emotional expression, romantic atmosphere, tender touch, cozy environment, natural pose, both faces visible",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, extra limbs, missing limbs"
            },
            {
                "name": "浪漫接吻",
                "prompt": "masterpiece, best quality, photorealistic, 8k, couple kissing, romantic moment, passionate kiss, close up shot, soft focus, dreamy atmosphere, warm lighting, intimate expression, beautiful composition, love story, emotional connection, tender moment, both faces visible",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, extra limbs"
            },
            {
                "name": "夕阳拥抱",
                "prompt": "masterpiece, best quality, photorealistic, 8k, couple hugging in sunset, golden hour, warm romantic atmosphere, embracing each other, loving couple, silhouette, dramatic sky, emotional moment, beautiful lighting",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "街头接吻",
                "prompt": "masterpiece, best quality, photorealistic, 8k, couple kissing on street, urban romance, city background, passionate moment, intimate couple, soft lighting, romantic atmosphere, modern love",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            }
        ]