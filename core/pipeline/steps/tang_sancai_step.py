# core/pipeline/steps/tang_sancai_step.py
"""唐三彩风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class TangSancaiStep(BaseStyleStep):
    """唐三彩风格转换步骤"""
    
    def __init__(self):
        super().__init__("tang_sancai", "转换为唐三彩风格")
        self._config = {
            "strength": 0.50,
            "cfg": 7.5,
            "steps": 30,
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
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "canny",
                "choices": ["canny", "hed", "lineart", "scribble"]
            },
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.4), watermark, text, signature, "
            "photorealistic, 3d render, oil painting, modern, "
            "plaster, stone, wood, cold tones"
        )
        return [
            {
                "name": "唐三彩_骆驼",
                "prompt": "Tang Sancai pottery, tri-color glazed ceramic, camel sculpture, amber yellow and green glaze, glossy ceramic surface, ancient Chinese art, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "唐三彩_仕女俑",
                "prompt": "Tang Sancai pottery, tri-color glazed ceramic, beautiful tang dynasty court lady figure, elegant flowing dress, amber and green glaze, glossy surface, ancient Chinese art, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "唐三彩_马",
                "prompt": "Tang Sancai pottery, tri-color glazed ceramic, magnificent war horse sculpture, amber yellow glaze, glossy ceramic surface, dynamic pose, ancient Chinese art, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "唐三彩_胡人乐俑",
                "prompt": "Tang Sancai pottery, tri-color glazed ceramic, musician figure, playing instrument, amber and white glaze, glossy ceramic, ancient Chinese art, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]