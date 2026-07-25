# core/pipeline/steps/qipao_step.py
"""旗袍风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class QipaoStep(BaseStyleStep):
    """旗袍风格转换步骤"""
    
    def __init__(self):
        super().__init__("qipao", "将人物转换为旗袍风格")
        self._config = {
            "strength": 0.35,
            "cfg": 7.5,
            "steps": 25,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "hed",
            "controlnet_strength": 0.5,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.35, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 25, "min": 15, "max": 50},
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
        """生成旗袍风格的 4 种场景"""
        return [
            {
                "name": "传统旗袍",
                "prompt": "masterpiece, best quality, photorealistic, 8k, beautiful woman wearing traditional Chinese qipao, elegant cheongsam, silk fabric, intricate embroidery, mandarin collar, side slit, classic Chinese style, vintage atmosphere, graceful pose, soft lighting, porcelain skin, red lipstick",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, modern clothes, casual"
            },
            {
                "name": "现代旗袍",
                "prompt": "masterpiece, best quality, photorealistic, 8k, beautiful woman wearing modern qipao, stylish cheongsam, silk satin fabric, elegant design, high slit, modern setting, confident pose, dramatic lighting, flawless skin, high fashion",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, traditional only"
            },
            {
                "name": "旗袍花园",
                "prompt": "masterpiece, best quality, photorealistic, 8k, beautiful woman wearing elegant qipao, traditional Chinese garden, blooming flowers, soft golden lighting, graceful pose, silk cheongsam, vintage beauty, serene atmosphere, detailed embroidery",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, modern setting"
            },
            {
                "name": "旗袍夜景",
                "prompt": "masterpiece, best quality, photorealistic, 8k, beautiful woman wearing qipao, night scene, city lights, elegant pose, silk cheongsam, dramatic lighting, sophisticated atmosphere, modern traditional fusion",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            }
        ]