# core/pipeline/steps/yoga_step.py
"""瑜伽姿势转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class YogaStep(BaseStyleStep):
    """瑜伽姿势转换步骤"""
    
    def __init__(self):
        super().__init__("yoga", "转换为瑜伽姿势")
        self._config = {
            "strength": 0.40,
            "cfg": 7.5,
            "steps": 25,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "openpose",
            "controlnet_strength": 0.6,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.40, "min": 0.25, "max": 0.65},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 25, "min": 15, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "openpose",
                "choices": ["openpose", "dwpose", "canny", "hed", "lineart"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        """生成瑜伽姿势的 20 种场景"""
        return [
            {
                "name": "瑜伽冥想",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing yoga pose, meditation, peaceful atmosphere, gym studio, yoga mat, fitness, healthy lifestyle, stretching, flexible body, calming environment, natural lighting, serene expression, athletic wear, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "树式瑜伽",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing tree pose yoga, balance pose, peaceful expression, yoga studio, natural lighting, fitness, healthy lifestyle, flexible body, serene atmosphere, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽伸展",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman stretching yoga pose, flexible body, yoga mat, peaceful atmosphere, gym studio, natural lighting, fitness, healthy lifestyle, serene expression, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽海滩",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing yoga on beach, sunrise, peaceful atmosphere, ocean background, fitness, healthy lifestyle, flexible body, serene expression, full body, golden lighting",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_树式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing tree pose yoga, standing on one leg, hands clasped above head, balance pose, peaceful expression, yoga studio, natural lighting, fitness, healthy lifestyle, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_战士一式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing warrior pose I, lunge stance, arms raised straight up, looking forward, powerful pose, confident, studio setting, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_战士二式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing warrior pose II, lunge, arms extended parallel to the ground, gaze forward, strength and stability, full body, natural lighting",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_下犬式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing downward facing dog, hands and feet on mat, hips raised, stretching back and legs, full body, yoga pose, athletic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_上犬式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing upward facing dog, chest open, arms straight, legs extended, backbend, full body, dynamic pose",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_骆驼式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing camel pose, kneeling, arching back, hands reaching heels, chest open, intense stretch, full body, dramatic posture",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_舞王式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing dancer pose, standing on one leg, holding back foot with hand, body arched gracefully, balance, elegant full body pose",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_弓式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing bow pose, lying on stomach, hands pulling feet, back arched, full body stretch, flexible, dynamic yoga",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_眼镜蛇式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing cobra pose, lying on stomach, hands pushing chest up, looking upward, opening chest, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_鹤禅式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing crane pose, balancing on hands, knees resting on upper arms, focused look, intense balance, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_头倒立",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing headstand, balancing on forearms, legs straight up in the air, inverted pose, strength and focus, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_手倒立",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing handstand, balancing entirely on hands, legs raised vertically, powerful, dynamic, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_鱼式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing fish pose, lying on back, chest raised, head touching the mat, opening throat and chest, meditative, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_莲花坐冥想",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman in lotus pose meditation, sitting cross-legged, hands on knees, eyes closed, peaceful atmosphere, zen, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_半月式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing half moon pose, balancing on one leg and one hand, body extended sideways, open and expansive, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽_双人瑜伽",
                "prompt": "masterpiece, best quality, photorealistic, 8k, two women doing acroyoga, partner yoga, one person standing supporting the other, trust and balance, full body, studio setting",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            }
        ]