# core/pipeline/steps/cyber_hanfu_step.py
"""赛博古风场景转换步骤 - 汉服 + 赛博朋克融合 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class CyberHanfuStep(BaseStyleStep):
    """赛博古风转换步骤 - 汉服 + 赛博朋克融合"""
    
    def __init__(self):
        super().__init__("cyber_hanfu", "赛博古风 - 汉服+赛博朋克融合")
        self._config = {
            "strength": 0.40,
            "cfg": 7.5,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "hed",
            "controlnet_strength": 0.5,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.40, "min": 0.2, "max": 0.65},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "hed",
                "choices": ["hed", "canny", "lineart", "openpose"]
            },
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        """生成赛博古风场景的 10 种提示词"""
        return [
            {
                "name": "赛博汉服_霓虹",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman wearing futuristic hanfu, cyberpunk traditional Chinese clothing, glowing neon patterns on flowing silk robes, holographic embroidery, digital phoenix motifs, neon lights reflecting on silk, cyberpunk city background, rain, holographic elements, high tech traditional fusion, full body shot, dramatic lighting, high quality, detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull, dark, gloomy, medieval, primitive"
            },
            {
                "name": "赛博汉服_古风都会",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman in cyberpunk hanfu, traditional Chinese robes with LED trim, glowing jade ornaments, digital cloud patterns on silk, futuristic city skyline with Chinese architecture, holographic lanterns, neon signs with Chinese characters, cyberpunk atmosphere, full body shot, high quality, detailed, cinematic lighting",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull, dark"
            },
            {
                "name": "赛博汉服_夜雨",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman wearing glowing hanfu in rain, neon reflections on wet silk, cyberpunk traditional dress, holographic lotus patterns, umbrella with LED rim, rain at night, cyberpunk city with Chinese elements, dramatic lighting, full body shot, high quality, detailed, atmospheric",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull, dark, gloomy"
            },
            {
                "name": "赛博汉服_数据飞花",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman in futuristic hanfu, digital cherry blossoms falling, glowing silk robes, cyberpunk traditional wear, holographic butterflies, glass and steel pavilion, neon lights, sci-fi ancient fusion, full body shot, high quality, detailed, ethereal, cyberpunk fantasy",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull"
            },
            {
                "name": "赛博汉服_云端",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman in cyber hanfu, glowing flowing robes, holographic cloud patterns, futuristic Chinese palace floating in sky, neon aurora, cyberpunk traditional aesthetics, full body shot, high quality, detailed, dreamy, cyberpunk fairy tale",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull"
            },
            {
                "name": "赛博汉服_侠女",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful female swordsman in cyberpunk hanfu, glowing traditional armor, LED sword, holographic cape, cyberpunk city rooftop, neon lights, dramatic pose, full body shot, high quality, detailed, cyberpunk wuxia, powerful, majestic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull"
            },
            {
                "name": "赛博汉服_仙女",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful celestial being in cyber hanfu, glowing flowing ribbons, holographic wings, digital star patterns on silk, cyberpunk heavenly palace, neon galaxy background, full body shot, high quality, detailed, ethereal, cyberpunk goddess",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull"
            },
            {
                "name": "赛博汉服_琴师",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman playing a futuristic guqin, wearing cyber hanfu, glowing silk robes, holographic musical notes floating, cyberpunk traditional tea house, neon lights, full body shot, high quality, detailed, artistic, cyberpunk classical fusion",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull"
            },
            {
                "name": "赛博汉服_双人_并肩",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a man and woman in cyberpunk hanfu, traditional Chinese robes with glowing neon trim, standing side by side, cyberpunk city background with Chinese architecture, holographic lanterns, full body shot, high quality, detailed, dramatic lighting, cyberpunk couple, elegant and futuristic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull, single person"
            },
            {
                "name": "赛博汉服_双人_对视",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a man and woman in cyber hanfu, traditional fusion attire, glowing silk robes, facing each other intimately, cyberpunk Chinese garden, neon flowers, romantic atmosphere, full body shot, high quality, detailed, dramatic lighting, cyberpunk romance",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull, single person"
            }
        ]