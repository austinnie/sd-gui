# core/pipeline/steps/hindu_temple_step.py
"""印度神庙与神兽风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class HinduTempleStep(BaseStyleStep):
    """印度神庙与神兽风格转换步骤"""
    
    def __init__(self):
        super().__init__("hindu_temple", "转换为印度神庙风格")
        self._config = {
            "strength": 0.50,
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
            "strength": {"type": "float", "default": 0.50, "min": 0.3, "max": 0.7},
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
            "modern, 3d render, western, plain, flat"
        )
        return [
            {
                "name": "印度神庙_塔门",
                "prompt": "Ancient Hindu temple, magnificent Dravidian architecture, towering pyramidal gate (Gopuram), intricately carved stone sculptures covering every surface, golden sunrise light, incredible architectural detail, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "神牛_南迪",
                "prompt": "Nandi, the sacred bull of Hindu mythology, guardian of Lord Shiva, majestic white bull, decorated with gold and flowers, lying peacefully in front of a temple, spiritual and serene presence, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "神象_象头神",
                "prompt": "Lord Ganesha, Hindu god with an elephant head, four arms, holding sacred objects, wearing a red and golden crown, riding on a giant rat, removing obstacles and bringing fortune, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "神庙_恒河祭",
                "prompt": "Hindu temple on the banks of the Ganges river at sunrise, ancient stone steps (Ghats) leading to the water, devotees performing holy rituals, golden sunlight reflecting on water, sacred divine atmosphere, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]