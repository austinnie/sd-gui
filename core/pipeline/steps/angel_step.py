# core/pipeline/steps/angel_step.py
"""天使/天军风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class AngelStep(BaseStyleStep):
    """天使/天军风格转换步骤"""
    
    def __init__(self):
        super().__init__("angel", "转换为天使/天军风格")
        self._config = {
            "strength": 0.45,
            "cfg": 8.0,
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
            "strength": {"type": "float", "default": 0.45, "min": 0.25, "max": 0.65},
            "cfg": {"type": "float", "default": 8.0, "min": 6, "max": 12},
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
            "modern, 3d render, cartoon, anime, dark, demonic, horror, "
            "asymmetric wings, broken wings"
        )
        return [
            {
                "name": "大天使_米迦勒",
                "prompt": "Archangel Michael, majestic celestial warrior, wearing golden and white holy armor, large brilliant white wings, holding a flaming sword, halo glowing above head, radiant light, heavenly clouds background, divine protector, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "天使_加百列",
                "prompt": "Angel Gabriel, messenger of God, beautiful androgynous figure, long flowing white robes, large white wings, holding a golden trumpet, glowing halo, ethereal and pure, heavenly light, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "六翼天使_炽天使",
                "prompt": "Seraphim, six-winged angel, divine being glowing with fiery golden light, multiple wings covering body, intense radiant power, in the presence of divine glory, sacred art, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "堕天使_路西法",
                "prompt": "Fallen angel Lucifer, magnificent dark wings, wearing dark robes, melancholic and rebellious expression, dark but beautiful, dramatic lighting, heavenly and hellish dual background, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "天使军团_天军",
                "prompt": "Host of angels in heaven, numerous angels with wings, golden holy light, flowing white robes, celestial realm, grand majestic scene, sacred religious art, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]