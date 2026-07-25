# core/pipeline/steps/marble_yoga_step.py
"""大理石瑜伽雕像风格 - 组合 Marble 材质 + Yoga 姿势 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class MarbleYogaStep(BaseStyleStep):
    """大理石瑜伽雕像转换步骤"""
    
    def __init__(self):
        super().__init__("marble_yoga", "将人物转换为大理石雕像瑜伽姿势")
        self._config = {
            "strength": 0.40,
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
            "strength": {"type": "float", "default": 0.40, "min": 0.2, "max": 0.6},
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
        """生成大理石瑜伽雕像的 16 种体式"""
        return [
            {
                "name": "大理石瑜伽_单腿鸽王式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing king pigeon pose, one leg bent back, body arched gracefully, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_战士二式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing warrior pose II, lunge, arms extended parallel to the ground, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_弓式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing bow pose, lying on stomach, hands pulling feet, body arched like a bow, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_树式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing tree pose, standing on one leg, hands clasped above head, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_金刚坐冥想",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing thunderbolt pose, kneeling, hands resting on knees, meditating, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_上犬式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing upward facing dog pose, chest open, arms straight, legs extended, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_舞王式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing dancer pose, standing on one leg, holding back foot with hand, body arched gracefully, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_头倒立",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing headstand, balancing on forearms, legs straight up in the air, inverted pose, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_半月式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing half moon pose, balancing on one leg and one hand, body extended sideways, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_头倒立变体",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing headstand with legs crossed, balancing on forearms, legs intertwined in air, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_鹤禅式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing crane pose, balancing on hands, knees resting on upper arms, focused look, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_双人支撑",
                "prompt": "masterpiece, best quality, photorealistic, 8k, two beautiful women, pure white marble statues, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing partner acroyoga, one standing on the other's back, balancing beautifully, full bodies visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_骆驼式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing camel pose, kneeling, arching back, hands reaching heels, chest open, intense stretch, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_战士一式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing warrior pose I, lunge stance, arms raised straight up, looking forward, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_站立前屈",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing standing forward fold, bending forward from the hips, hands reaching to the ground, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_轮式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing wheel pose, hands and feet on the ground, body arched like a bridge, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            }
        ]