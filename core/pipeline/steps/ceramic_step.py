# core/pipeline/steps/ceramic_step.py
"""瓷器风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class CeramicStep(BaseStyleStep):
    """瓷器风格转换步骤"""
    
    def __init__(self):
        super().__init__("ceramic", "转换为瓷器风格")
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
            "strength": {"type": "float", "default": 0.45, "min": 0.3, "max": 0.6},
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
            "worst quality, low quality, ugly, deformed, blurry, "
            "watermark, text, signature, "
            "photorealistic, 3d render, plastic, paper, modern, "
            "cracked, broken, damaged, chipped"
        )
        return [
            {
                "name": "宋代汝窑_天青釉",
                "prompt": "ancient Chinese ceramic, Song dynasty Ru kiln, celadon glaze, sky blue color, elegant minimalist form, fine crackle texture, glossy porcelain surface, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "元代青花瓷_缠枝莲",
                "prompt": "ancient Chinese ceramic, Yuan dynasty blue and white porcelain, underglaze blue, intricate lotus scroll motif, white glazed porcelain, elegant vase shape, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "明代斗彩_鸡缸杯",
                "prompt": "ancient Chinese ceramic, Ming dynasty doucai porcelain, small wine cup, chicken and flower motif, soft and colorful enamel overglaze, fine porcelain, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "清代粉彩_花卉纹",
                "prompt": "ancient Chinese ceramic, Qing dynasty famille rose porcelain, delicate floral pattern, soft pastel colors, fine enamel overglaze, white porcelain base, elegant vase form, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "现代青瓷_梅子青",
                "prompt": "modern Chinese ceramic, celadon, plum green glaze, smooth warm jade like texture, elegant minimalist design, glossy porcelain surface, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]