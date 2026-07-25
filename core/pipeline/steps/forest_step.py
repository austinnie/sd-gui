# core/pipeline/steps/forest_step.py
"""森林场景转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class ForestStep(BaseStyleStep):
    """森林场景转换步骤"""
    
    def __init__(self):
        super().__init__("forest", "将人物放到森林背景")
        self._config = {
            "strength": 0.40,
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
            "strength": {"type": "float", "default": 0.40, "min": 0.2, "max": 0.6},
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
                "name": "森林仙境",
                "prompt": "in a magical forest, sunlight filtering through trees, green moss, wild flowers, mystical atmosphere, ethereal lighting, full body, natural pose, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, urban, city, building"
            },
            {
                "name": "森林小径",
                "prompt": "walking on a forest path, tall trees, dappled sunlight, peaceful atmosphere, natural lighting, full body, serene expression, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, urban, city"
            },
            {
                "name": "森林溪流",
                "prompt": "standing by a forest stream, clear water, rocks, green trees, soft natural lighting, peaceful atmosphere, full body, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, urban, city"
            },
            {
                "name": "森林精灵",
                "prompt": "ethereal forest spirit, magical forest, soft glowing light, mystical atmosphere, fairy tale, full body, dreamy, high quality, photorealistic, 8k",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, urban, city"
            }
        ]