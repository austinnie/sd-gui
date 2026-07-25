# core/pipeline/steps/bronze_statue_step.py
"""青铜雕像风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class BronzeStatueStep(BaseStyleStep):
    """青铜雕像转换步骤"""
    
    def __init__(self):
        super().__init__("bronze_statue", "将人物转换为青铜雕像风格")
        self._config = {
            "strength": 0.45,
            "cfg": 7.0,
            "steps": 25,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "canny",
            "controlnet_strength": 0.6,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 25, "min": 15, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "canny",
                "choices": ["canny", "hed", "lineart", "depth", "openpose"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        """生成青铜雕像场景的 12 种提示词"""
        return [
            {
                "name": "青铜古典雕像",
                "prompt": "same person, same pose, transform into ancient bronze statue, classical sculpture, rich green patina, weathered bronze texture, dark metallic finish, aged copper tone, intricate casting details, dramatic lighting, museum pedestal, high quality, masterpiece",
                "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"
            },
            {
                "name": "青铜希腊神像",
                "prompt": "same person, same pose, ancient Greek bronze god statue, dark patina, weathered bronze, classical Greek sculpture, flowing robes, temple background, dramatic shadow and light, metallic texture, high quality, masterpiece",
                "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"
            },
            {
                "name": "青铜战士雕像",
                "prompt": "same person, same pose, heroic bronze warrior statue, dark metal, battle armor, weathered copper tone, commanding pose, historical museum display, dramatic lighting, high quality, masterpiece",
                "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"
            },
            {
                "name": "青铜全身像",
                "prompt": "same person, same pose, full body bronze statue, rich patina, textured metal surface, dark bronze color, elegant pose, museum gallery display, dramatic spotlight, high quality, masterpiece",
                "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"
            },
            {
                "name": "青铜女神雕塑",
                "prompt": "same person, same pose, classical bronze goddess sculpture, ornate metalwork, flowing drapery, greenish patina, soft dramatic lighting, museum pedestal, intricate details, high quality, masterpiece",
                "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"
            },
            {
                "name": "青铜半身像",
                "prompt": "same person, same face, bronze bust, detailed facial features, dark metallic finish, weathered bronze texture, museum display, classical art style, dramatic lighting, high quality, masterpiece",
                "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"
            },
            {
                "name": "青铜坐像",
                "prompt": "same person, same pose, seated bronze statue, classic pose, dark metal, rich patina, elegant, museum gallery, dramatic lighting, high quality, masterpiece",
                "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"
            },
            {
                "name": "青铜骑士像",
                "prompt": "same person, same pose, medieval bronze knight statue, armored, holding a sword, dark metallic tone, weathered patina, castle background, dramatic lighting, high quality, masterpiece",
                "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"
            },
            {
                "name": "青铜天使像",
                "prompt": "same person, same pose, bronze angel statue, wings, ethereal pose, dark metallic patina, classical sculpture, dramatic lighting, museum display, high quality, masterpiece",
                "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"
            },
            {
                "name": "青铜舞蹈者",
                "prompt": "same person, same pose, bronze dancer statue, dynamic pose, elegant movement, dark patina, metallic texture, museum display, dramatic lighting, high quality, masterpiece",
                "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"
            },
            {
                "name": "青铜裸体艺术",
                "prompt": "same person, same pose, classical bronze nude statue, artistic nude, dark metallic finish, weathered bronze texture, museum display, dramatic lighting, high quality, fine art, masterpiece",
                "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, explicit, pornographic, different person"
            },
            {
                "name": "青铜母子像",
                "prompt": "same people, same pose, bronze mother and child statue, loving embrace, dark metal, rich patina, soft dramatic lighting, classical sculpture, museum pedestal, high quality, masterpiece",
                "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different people"
            }
        ]