# core/pipeline/steps/hanfu_step.py
"""汉服风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class HanfuStep(BaseStyleStep):
    """汉服风格转换步骤"""
    
    def __init__(self):
        super().__init__("hanfu", "将人物转换为古风汉服风格")
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
            "steps": {"type": "int", "default": 28, "min": 15, "max": 50},
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
                "name": "汉服唐制",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman wearing traditional Tang dynasty hanfu, flowing silk robes, elegant ancient Chinese style, classical beauty, traditional makeup, ancient palace background, soft golden lighting, full body shot, graceful pose, high quality, detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, modern clothes, casual"
            },
            {
                "name": "汉服宋制",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman wearing Song dynasty hanfu, elegant traditional Chinese clothing, subtle colors, refined style, classical beauty, ancient garden background, soft lighting, full body shot, graceful pose",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, modern clothes"
            },
            {
                "name": "汉服明制",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman wearing Ming dynasty hanfu, magnificent traditional clothing, intricate embroidery, classical beauty, imperial palace background, dramatic lighting, full body shot, elegant pose, high quality",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, modern clothes"
            },
            {
                "name": "汉服魏晋",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman wearing Wei-Jin dynasty hanfu, flowing fairy-like robes, ethereal style, classical beauty, bamboo forest background, soft misty lighting, full body shot, elegant pose, high quality",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, modern clothes"
            }
        ]