# core/pipeline/steps/marble_step.py
"""大理石雕像风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class MarbleStep(BaseStyleStep):
    """大理石雕像转换步骤"""
    
    def __init__(self):
        super().__init__("marble", "将人物转换为大理石雕像")
        self._config = {
            "strength": 0.45,
            "cfg": 7.0,
            "steps": 20,
            "scenes": 14,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "canny",
            "controlnet_strength": 0.6,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.1, "max": 0.8},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 20, "min": 10, "max": 40},
            "scenes": {"type": "int", "default": 14, "choices": [6, 12, 14]},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "canny",
                "choices": ["canny", "hed", "lineart", "depth"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        """生成大理石场景的 14 种提示词"""
        return [
            {
                "name": "纯白大理石雕像",
                "prompt": "same person, same pose, transform into pure white marble statue, classical sculpture, flawless white marble, smooth stone texture, elegant pose, dramatic lighting, no color, monochrome white, intricate carving details, high quality, masterpiece",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person, different face"
            },
            {
                "name": "纯白大理石半身像",
                "prompt": "same person, same face, pure white marble bust, classical sculpture, white stone, smooth texture, detailed face, elegant expression, museum pedestal, soft dramatic lighting, monochrome white, high quality, masterpiece",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"
            },
            {
                "name": "纯白希腊女神",
                "prompt": "same person, same pose, pure white Greek goddess statue, classical Greek sculpture, flawless marble, flowing robes, elegant pose, ancient temple background, dramatic lighting, monochrome white, intricate details, high quality, masterpiece",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"
            },
            {
                "name": "纯白大理石全身像",
                "prompt": "same person, same pose, pure white marble statue, full body sculpture, flawless white stone, classical pose, museum gallery, marble pedestal, soft dramatic lighting, monochrome white, intricate carving details, high quality, masterpiece",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"
            },
            {
                "name": "纯白大理石卧像",
                "prompt": "same person, same pose, pure white marble reclining statue, lying down, classical sculpture, smooth white stone, peaceful expression, elegant pose, museum display, soft lighting, monochrome white, high quality, masterpiece",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"
            },
            {
                "name": "纯白石膏雕像",
                "prompt": "same person, same pose, pure white plaster cast statue, matte white finish, classical sculpture, smooth surface, elegant pose, studio photography, dramatic lighting, monochrome white, high quality, masterpiece",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"
            },
            {
                "name": "纯白大理石坐像",
                "prompt": "same person, same pose, pure white marble seated statue, sitting gracefully, classical sculpture, flawless white stone, elegant posture, museum pedestal, dramatic lighting, monochrome white, intricate carving details, high quality, masterpiece",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"
            },
            {
                "name": "纯白大理石天使",
                "prompt": "same person, same pose, pure white marble angel statue, wings, heavenly, classical sculpture, flawless white stone, ethereal pose, soft dramatic lighting, monochrome white, intricate details, high quality, masterpiece",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"
            },
            {
                "name": "纯白大理石维纳斯",
                "prompt": "same person, same pose, pure white marble Venus statue, goddess of beauty, classical sculpture, flawless white stone, elegant pose, soft dramatic lighting, monochrome white, intricate details, high quality, masterpiece, timeless beauty",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"
            },
            {
                "name": "纯白大理石艺术裸体",
                "prompt": "same person, same pose, pure white marble nude statue, classical sculpture, artistic nude, flawless white stone, elegant pose, museum display, dramatic lighting, monochrome white, intricate carving details, high quality, fine art",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, explicit, pornographic, different person"
            },
            {
                "name": "纯白大理石思考者",
                "prompt": "same person, same pose, pure white marble thinker statue, classical sculpture, contemplative pose, flawless white stone, smooth texture, museum setting, dramatic lighting, monochrome white, high quality, masterpiece",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"
            },
            {
                "name": "纯白大理石舞者",
                "prompt": "same person, same pose, pure white marble dancer statue, dynamic pose, classical sculpture, flawless white stone, elegant movement, museum gallery, soft dramatic lighting, monochrome white, intricate details, high quality, masterpiece",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"
            },
            {
                "name": "纯白大理石战士",
                "prompt": "same person, same pose, pure white marble warrior statue, classical sculpture, heroic pose, flawless white stone, detailed armor, museum display, dramatic lighting, monochrome white, high quality, masterpiece",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"
            },
            {
                "name": "纯白大理石母与子",
                "prompt": "same people, same pose, pure white marble mother and child statue, classical sculpture, loving embrace, flawless white stone, smooth texture, museum setting, soft dramatic lighting, monochrome white, high quality, masterpiece",
                "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different people"
            }
        ]