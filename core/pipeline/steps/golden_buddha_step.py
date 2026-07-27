# core/pipeline/steps/golden_buddha_step.py
"""金身佛像风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class GoldenBuddhaStep(BaseStyleStep):
    """金身佛像风格转换步骤"""
    
    def __init__(self):
        super().__init__("golden_buddha", "转换为金身佛像风格")
        self._config = {
            "strength": 0.40,
            "cfg": 7.5,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "canny",
            "controlnet_strength": 0.6,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.40, "min": 0.25, "max": 0.65},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "canny",
                "choices": ["canny", "hed", "lineart", "scribble"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.4), watermark, text, signature, "
            "photorealistic, 3d render, oil painting, color, wooden, clay, "
            "modern, western, broken, damaged, cloudy sky"
        )
        return [
            {
                "name": "金身佛像_立像",
                "prompt": "golden buddha statue, pure gold material, sacred religious art, meditating pose, intricate details, gleaming gold, dark background, dramatic lighting, ancient temple, high quality, masterpiece, fine art, gold sculpture",
                "negative": base_negative
            },
            {
                "name": "金身佛像_坐姿冥想",
                "prompt": "golden buddha statue, sitting in lotus position, serene expression, polished gold, soft golden glow, sacred atmosphere, ancient oriental temple, high quality, masterpiece, fine art, gold sculpture",
                "negative": base_negative
            },
            {
                "name": "金身佛像_半身特写",
                "prompt": "golden buddha statue close-up, gentle smile, golden skin tone, ornate headdress, rich gold texture, dramatic shadow and light, sacred mood, high quality, masterpiece, fine art, gold sculpture",
                "negative": base_negative
            },
            {
                "name": "金身卧佛",
                "prompt": "golden reclining buddha statue, lying on side, serene expression, pure gold material, grand scale, warm golden light, ancient temple, high quality, masterpiece, fine art, gold sculpture",
                "negative": base_negative
            }
        ]