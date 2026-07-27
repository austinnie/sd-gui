# core/pipeline/steps/folk_myth_step.py
"""中国民间神话风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class FolkMythStep(BaseStyleStep):
    """中国民间神话风格转换步骤"""
    
    def __init__(self):
        super().__init__("folk_myth", "转换为中国民间神话风格")
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
            "(mutated hands and fingers:1.4), watermark, text, signature, "
            "modern, 3d render, western, anime, cartoon"
        )
        return [
            {
                "name": "哪吒闹海",
                "prompt": "Nezha, Chinese folk myth hero, child deity with sacred red sash (Hun Tian Ling), holding fire-tipped spear, riding the wind fire wheels, conquering the dragon king's sea, fierce and young divine warrior, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "封神榜_姜子牙",
                "prompt": "Jiang Ziya, ancient Chinese strategist and sage, wearing traditional Taoist robes, holding the Divine Whip (Da Shen Bian), summoning gods, mythical battlefield, epic oriental fantasy, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "八仙过海_铁拐李",
                "prompt": "Li Tieguai, one of the Eight Immortals, old man with crutch and magic gourd, riding a magical gourd across the ocean, legendary Taoist immortal, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "关公_武财神",
                "prompt": "Guan Gong, general and deity of war and wealth, majestic bearded man wearing green robe and heavy armor, holding the Green Dragon Crescent Blade, righteous and powerful presence, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "妈祖_护航",
                "prompt": "Mazu, goddess of the sea, beautiful Chinese goddess wearing elegant traditional robes and heavenly crown, standing on the waves, guiding ships safely, divine marine atmosphere, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]