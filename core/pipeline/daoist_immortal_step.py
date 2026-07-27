# core/pipeline/steps/daoist_immortal_step.py
"""道教仙人风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class DaoistImmortalStep(BaseStyleStep):
    """道教仙人风格转换步骤"""
    
    def __init__(self):
        super().__init__("daoist_immortal", "转换为道教仙人风格")
        self._config = {
            "strength": 0.45,
            "cfg": 7.5,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "lineart",
            "controlnet_strength": 0.6,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.3, "max": 0.65},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "lineart",
                "choices": ["canny", "hed", "lineart", "scribble"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.4), (fused fingers:1.4), watermark, text, signature, "
            "photorealistic, 3d render, oil painting, modern, "
            "buddhist, western, dark, gothic, demonic, armor"
        )
        return [
            {
                "name": "道教仙人_持拂尘",
                "prompt": "Daoist immortal, ancient Chinese deity, wearing traditional flowing black and white Taoist robe, holding a horsetail whisk (fuchen), sage expression, long flowing hair, mystical atmosphere, misty mountains background, oriental fantasy, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "道教女冠_云游",
                "prompt": "Daoist female immortal, elegant Taoist nun, wearing traditional layered robes, flying on clouds, holding a bamboo flute, ethereal and serene, immortal aura, ancient Chinese mythology, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "修仙者_打坐冥想",
                "prompt": "Cultivator sitting in meditation, cross-legged on a mountain peak, traditional Taoist robes, surrounded by swirling mist, serene expression, ancient Chinese fantasy, spiritual energy, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "道教祖师_太乙真人",
                "prompt": "Ancient Taoist master, immortal sage, holding a jade Ruyi scepter, flowing long beard, wearing magnificent Taoist priest robes, divine glow, magical mountain cave background, oriental myth, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "仙人降世_御剑飞行",
                "prompt": "Immortal sword cultivator, riding a flying sword through the clouds, wind blowing robes, dynamic pose, sky full of auspicious clouds, ancient oriental fantasy, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]