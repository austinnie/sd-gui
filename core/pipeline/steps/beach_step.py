# core/pipeline/steps/beach_step.py
"""海滩场景转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class BeachStep(BaseStyleStep):
    """海滩场景转换步骤"""
    
    def __init__(self):
        super().__init__("beach", "将人物放到海滩背景")
        self._config = {
            "strength": 0.45,
            "cfg": 7.5,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "depth",
            "controlnet_strength": 0.5,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.25, "max": 0.65},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "depth",
                "choices": ["depth", "canny", "hed", "lineart"]
            },
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        return [
            {
                "name": "阳光海滩",
                "prompt": "on a beautiful tropical beach, golden sand, crystal clear ocean, palm trees, sunny day, warm golden lighting, full body, natural pose, vacation atmosphere, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, winter, snow, cold"
            },
            {
                "name": "海滩日落",
                "prompt": "on a beautiful beach at sunset, golden sky, ocean waves, warm romantic lighting, silhouette, full body, dreamy atmosphere, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, daylight, noon"
            },
            {
                "name": "海滩漫步",
                "prompt": "walking on the beach, ocean waves, golden sand, sunny day, warm lighting, full body, natural pose, relaxed atmosphere, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, winter, snow"
            },
            {
                "name": "海滩躺椅",
                "prompt": "lying on beach chair, tropical beach, palm trees, ocean view, relaxing, summer atmosphere, warm lighting, full body, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, winter, snow"
            }
        ]