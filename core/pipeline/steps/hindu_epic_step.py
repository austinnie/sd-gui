# core/pipeline/steps/hindu_epic_step.py
"""印度史诗角色风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class HinduEpicStep(BaseStyleStep):
    """印度史诗角色风格转换步骤"""
    
    def __init__(self):
        super().__init__("hindu_epic", "转换为印度史诗风格")
        self._config = {
            "strength": 0.45,
            "cfg": 8.0,
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
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.4), watermark, text, signature, "
            "modern, 3d render, cartoon, anime, western, mundane"
        )
        return [
            {
                "name": "神猴_哈奴曼",
                "prompt": "Hanuman, Hindu monkey god, powerful monkey face, muscular body, holding a giant mace (Gada), flying across the sky, fierce devotion, orange-red fur, majestic warrior presence, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "战神_卡尔提克亚",
                "prompt": "Lord Kartikeya, Hindu god of war, handsome youthful warrior, holding a divine spear (Vel), riding on a peacock, golden armor and crown, fierce and brave divine presence, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "财富女神_拉克什米",
                "prompt": "Goddess Lakshmi, Hindu goddess of wealth and fortune, beautiful woman with golden skin, wearing magnificent gold jewelry and silk garments, standing on a lotus flower, radiant divine presence, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "天女_阿普萨拉",
                "prompt": "Apsara, celestial dancer in Hindu mythology, beautiful woman with exquisite features, wearing elaborate golden jewelry and sheer garments, flying gracefully in the clouds, heavenly divine presence, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]