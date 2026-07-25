# core/pipeline/steps/evening_gown_step.py
"""晚礼服风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class EveningGownStep(BaseStyleStep):
    """晚礼服风格转换步骤"""
    
    def __init__(self):
        super().__init__("evening_gown", "转换为晚礼服风格")
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
                "name": "红毯晚礼服",
                "prompt": "stunning woman in elegant evening gown, red carpet style, glamorous, high fashion, dramatic lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, casual, informal"
            },
            {
                "name": "奢华晚礼服",
                "prompt": "beautiful woman in luxurious evening gown, silk, sequins, elegant, dramatic lighting, high fashion, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, casual, simple"
            },
            {
                "name": "舞会晚礼服",
                "prompt": "woman in elegant ball gown, grand ballroom, chandeliers, dramatic lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, casual, modern"
            },
            {
                "name": "长裙晚礼服",
                "prompt": "beautiful woman in floor-length evening gown, elegant, flowing fabric, dramatic lighting, full body, high quality, photorealistic, 8k, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, short, casual"
            }
        ]