# core/pipeline/steps/ancient_china_myth_step.py
"""中国上古神话风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class AncientChinaMythStep(BaseStyleStep):
    """中国上古神话风格转换步骤"""
    
    def __init__(self):
        super().__init__("ancient_china_myth", "转换为中国上古神话风格")
        self._config = {
            "strength": 0.45,
            "cfg": 7.5,
            "steps": 35,  # 调整为35步，给AI多一点时间构图
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
            "steps": {"type": "int", "default": 35, "min": 20, "max": 50},
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
        # 核心防御：强力降维打击“现代游戏CG感”
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.5), (modern 3d render:1.5), (game cg:1.5), "
            "(anime style:1.4), (anime eyes:1.4), (colorful fantasy:1.3), watermark, text, "
            "signature, photorealistic, oil painting, western fantasy, "
            "glowing smooth skin, plastic skin, latex"
        )
        
        return [
            {
                "name": "女娲补天",
                "prompt": "ancient Chinese mythology, Nuwa mending the sky, female goddess with serpent tail, wearing primitive jade and bronze ornaments, holding sacred five-colored stones, ancient mountain cave background, mysterious mist, ancient rock carving style, epic mural painting, oriental primitive art, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "盘古开天",
                "prompt": "ancient Chinese myth, Pangu separating heaven and earth, colossal giant figure, holding a massive ancient stone axe, breaking the cosmic egg, emerging chaos and light, ancient rock carving texture, mysterious atmosphere, primitive orientation, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "山海经_麒麟",
                "prompt": "ancient Chinese myth, Qilin, legendary auspicious beast, dragon-like head, deer-like body, covered in ancient greenish scales, fiery mane and tail, majestic mythical creature, surrounded by swirling mist and ancient runes, bronze age aesthetic, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "山海经_九尾狐",
                "prompt": "ancient Chinese myth, Nine-tailed fox, mystical creature, elegant and enigmatic, nine flowing tails like golden clouds, intricate ancient silk pattern, deep forest and mysterious moonlight, ancient ritualistic atmosphere, oriental fantasy art, high quality, masterpiece, fine art",
                "negative": base_negative
            },
            {
                "name": "洪荒_神龙",
                "prompt": "ancient Chinese myth, primal great loong, ancient majestic mythological serpentine dragon, scales like ancient bronze, horned head, powerful claws, soaring through primordial clouds, thunder and lightning, oriental legend, high quality, masterpiece, fine art",
                "negative": base_negative
            }
        ]