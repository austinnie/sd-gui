# core/pipeline/steps/hindu_lingam_step.py
"""印度生殖崇拜/性力神明风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class HinduLingamStep(BaseStyleStep):
    """印度生殖崇拜风格转换步骤"""
    
    def __init__(self):
        super().__init__("hindu_lingam", "转换为印度生殖崇拜风格")
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
        # 使用极为严格的负面词，避免生成低俗真人色情图，确保是宗教、雕塑、艺术层面
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.4), watermark, text, signature, "
            "modern, 3d render, cartoon, anime, western, "
            "explicit, pornographic, vulgar, real human, naked, nude, "
            "photorealistic human, flesh, skin texture, gore, blood"
        )
        return [
            {
                "name": "湿婆林伽_圣物",
                "prompt": "Sacred Shiva Lingam, ancient stone sculpture, abstract phallic symbol representing cosmic creation, resting on Yoni base, decorated with sacred cobras and offerings, carved in black stone, divine and mystical presence, high quality, masterpiece, fine art, antique bronze texture",
                "negative": base_negative
            },
            {
                "name": "舞王湿婆_创造之舞",
                "prompt": "Lord Shiva as Nataraja, king of dance, cosmic dancer, bronze Chola dynasty statue, multiple arms holding symbolic objects, standing on a demon, surrounded by a ring of fire, representing the cycle of creation and destruction, magnificent ancient Indian art, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "湿婆与雪山神女_双神融合",
                "prompt": "Lord Shiva and Goddess Parvati, divine couple, half-man half-woman form (Ardhanarishvara), representing the ultimate union of male and female principles, ancient Indian stone temple carving, intricate details, majestic and spiritual presence, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "阿周那_苦行与繁衍",
                "prompt": "Ancient Indian mythological scene, depiction of fertility and life force, divine figures surrounded by nature, growing vines and blooming flowers, classic Indian temple relief carving, stone texture, spiritual and symbolic representation of life, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]