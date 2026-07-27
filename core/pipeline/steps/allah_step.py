# core/pipeline/steps/allah_step.py
"""伊斯兰神圣风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class AllahStep(BaseStyleStep):
    """伊斯兰神圣风格转换步骤"""
    
    def __init__(self):
        super().__init__("allah", "转换为伊斯兰神圣风格")
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
            "strength": {"type": "float", "default": 0.45, "min": 0.3, "max": 0.7},
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
            "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, "
            "3d render, cartoon, anime, photorealistic, human face, idolatry, figurine"
        )
        return [
            {
                "name": "安拉之光",
                "prompt": "Divine light of Allah, sacred golden rays piercing through dark clouds, ethereal holy light, abstract spiritual art, peaceful and majestic atmosphere, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "清真寺_黄昏",
                "prompt": "Grand Islamic mosque, magnificent domes and minarets, golden sunset light, clear blue sky, crescent moon appearing, peaceful holy atmosphere, Middle Eastern architecture, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "伊斯兰几何_金砖",
                "prompt": "Intricate Islamic geometric pattern, sacred geometry, golden arabesque motifs, complex tessellation on traditional tiles, beautiful Islamic art, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "麦加_朝圣",
                "prompt": "Kaaba in Mecca, sacred black cube covered in black silk, illuminated by divine golden light, surrounded by thousands of pilgrims, holy atmosphere, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "阿拉伯书法_神圣",
                "prompt": "Elegant Arabic calligraphy, holy verses written with gold ink on parchment paper, intricate script, Islamic sacred art, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]