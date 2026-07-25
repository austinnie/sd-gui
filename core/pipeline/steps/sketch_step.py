# core/pipeline/steps/sketch_step.py
"""素描风格转换步骤 - 使用 BaseStyleStep (ControlNet 增强)"""

from ..base_step import BaseStyleStep


class SketchStep(BaseStyleStep):
    """素描风格转换步骤 - ControlNet 增强"""
    
    def __init__(self):
        super().__init__("sketch", "转换为素描风格 (ControlNet增强)")
        self._config = {
            "strength": 0.25,
            "cfg": 7.0,
            "steps": 25,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": True,
            "controlnet_type": "canny",
            "controlnet_strength": 0.6,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.25, "min": 0.15, "max": 0.45},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 9},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": True},
            "controlnet_type": {
                "type": "choice",
                "default": "canny",
                "choices": ["canny", "hed", "lineart", "scribble", "openpose", "depth"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        """生成素描风格的 8 种场景"""
        return [
            {
                "name": "素描肖像_精细",
                "prompt": "pencil sketch, same person, same face, same pose, ultra detailed portrait drawing, fine art, realistic pencil shading, high contrast, monochrome, texture, masterpiece, best quality",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, cartoon, anime"
            },
            {
                "name": "炭笔素描",
                "prompt": "charcoal drawing, same person, same face, same pose, rich dark tones, smudged texture, dramatic shading, fine art, monochrome, high quality, masterpiece, realistic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, clean lines"
            },
            {
                "name": "素描人体_艺术",
                "prompt": "pencil sketch, detailed drawing, beautiful woman nude, fine art, charcoal drawing, shading, texture, monochrome, high quality, masterpiece, realistic sketch, artistic nude",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, explicit"
            },
            {
                "name": "速写风格",
                "prompt": "quick pencil sketch, same person, same face, same pose, loose expressive lines, gestural drawing, artistic, monochrome, high quality, sketchy style, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, over-detailed"
            },
            {
                "name": "素描动物",
                "prompt": "pencil sketch, detailed drawing of an animal, fine art, charcoal drawing, shading, texture, monochrome, high quality, masterpiece, realistic sketch, animal portrait",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, cartoon"
            },
            {
                "name": "素描风景",
                "prompt": "pencil sketch, detailed landscape drawing, mountains and nature, fine art, charcoal drawing, shading, texture, monochrome, high quality, masterpiece, realistic sketch",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, color, photorealistic, oil painting, 3d render, cartoon"
            },
            {
                "name": "素描城市",
                "prompt": "pencil sketch, detailed cityscape drawing, urban architecture, fine art, charcoal drawing, shading, texture, monochrome, high quality, masterpiece, realistic sketch",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, color, photorealistic, oil painting, 3d render, cartoon"
            },
            {
                "name": "交叉排线素描",
                "prompt": "cross-hatching pencil sketch, detailed drawing, fine art, intricate line work, shading, texture, monochrome, high quality, masterpiece, realistic sketch, artistic technique",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, smooth shading"
            }
        ]