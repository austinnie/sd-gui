# core/pipeline/steps/aesthetic_step.py
"""
唯美风格转换步骤 - 支持 ControlNet
专门处理唯美风景和唯美人物
"""

from ..base_step import BaseStyleStep


class AestheticStep(BaseStyleStep):
    """唯美风格转换步骤"""
    
    def __init__(self):
        super().__init__("aesthetic", "转换为唯美风格")
        self._config = {
            "strength": 0.35,
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
            "strength": {"type": "float", "default": 0.35, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "hed",
                "choices": ["hed", "canny", "lineart", "depth"]
            },
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        """生成唯美风格提示词 - 风景和人物"""
        return [
            # ===== 唯美风景 =====
            {
                "name": "唯美日出",
                "prompt": "masterpiece, best quality, 8k, breathtaking sunrise, golden sky, misty mountains, lake reflection, warm golden lighting, serene atmosphere, nature, photorealistic, highly detailed, dreamy, peaceful, stunning landscape",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, city, building, people, dark, gloomy"
            },
            {
                "name": "唯美日落",
                "prompt": "masterpiece, best quality, 8k, stunning sunset, golden orange sky, ocean waves, palm trees silhouette, warm romantic lighting, breathtaking view, photorealistic, highly detailed, dreamy atmosphere, peaceful",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, city, building, people, dark, gloomy"
            },
            {
                "name": "唯美花海",
                "prompt": "masterpiece, best quality, 8k, beautiful flower field, colorful wildflowers, soft golden sunlight, gentle breeze, rolling hills, nature paradise, photorealistic, highly detailed, dreamy, peaceful, vibrant colors",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, city, building, winter, dead, dark"
            },
            {
                "name": "唯美森林",
                "prompt": "masterpiece, best quality, 8k, magical forest, sunlight filtering through canopy, green moss, ancient trees, wild flowers, ethereal lighting, fantasy nature, photorealistic, highly detailed, dreamy, peaceful",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, urban, city, deforested, dark"
            },
            {
                "name": "唯美星空",
                "prompt": "masterpiece, best quality, 8k, stunning starry night, milky way, mountain silhouette, starry sky reflection, cosmic atmosphere, magical, photorealistic, highly detailed, dreamy, ethereal, peaceful",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, city light pollution, cloudy, daytime"
            },
            {
                "name": "唯美极光",
                "prompt": "masterpiece, best quality, 8k, stunning aurora borealis, colorful northern lights dancing in the sky, starry night, snow-covered landscape, magical atmosphere, photorealistic, highly detailed, breathtaking, dreamy",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, cloudy, daytime, city"
            },
            # ===== 唯美人物 =====
            {
                "name": "唯美仙女",
                "prompt": "masterpiece, best quality, 8k, a beautiful ethereal goddess, flowing white dress, soft glowing light, flower crown, mystical atmosphere, fairy tale, dreamy, ethereal beauty, photorealistic, highly detailed, soft pastel colors, magical",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, dark, scary, heavy makeup"
            },
            {
                "name": "唯美森系",
                "prompt": "masterpiece, best quality, 8k, a beautiful forest girl, nature lover, flowing floral dress, barefoot, surrounded by trees and flowers, dappled sunlight, peaceful and serene, natural beauty, full body shot, high quality, detailed face, ethereal, soft lighting",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, urban, city, dark, heavy makeup"
            },
            {
                "name": "唯美花仙子",
                "prompt": "masterpiece, best quality, 8k, a beautiful flower fairy, surrounded by blooming flowers, colorful petals floating, soft magical light, delicate wings, fantasy garden, dreamy atmosphere, ethereal beauty, photorealistic, highly detailed, soft pastel colors",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, dark, scary, heavy makeup"
            },
            {
                "name": "唯美少女",
                "prompt": "masterpiece, best quality, 8k, a beautiful young woman, pure and elegant, soft natural makeup, flowing hair, gentle smile, soft natural lighting, peaceful atmosphere, natural beauty, high quality, detailed face, dreamy, ethereal, soft pastel colors",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, heavy makeup, artificial, plastic, dark"
            },
            {
                "name": "唯美古风",
                "prompt": "masterpiece, best quality, 8k, a beautiful Chinese woman in elegant Hanfu, flowing silk robes, traditional Chinese garden, cherry blossoms, soft golden lighting, graceful pose, classical beauty, ethereal, dreamy, photorealistic, highly detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, modern clothes, heavy makeup, dark"
            },
            {
                "name": "唯美和风",
                "prompt": "masterpiece, best quality, 8k, a beautiful Japanese woman in elegant kimono, traditional Japanese garden, cherry blossoms falling, soft pink lighting, graceful pose, serene atmosphere, ethereal, dreamy, photorealistic, highly detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, western clothes, heavy makeup, dark"
            },
            # ===== 唯美意境 =====
            {
                "name": "唯美剪影",
                "prompt": "masterpiece, best quality, 8k, a beautiful woman in dramatic silhouette, backlighting, golden sunset, elegant pose, artistic composition, high contrast, emotional atmosphere, fine art photography, ethereal, dreamy, breathtaking",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, explicit, pornographic, vulgar"
            },
            {
                "name": "唯美光影",
                "prompt": "masterpiece, best quality, 8k, artistic photography, beautiful woman, soft window light, warm golden tones, elegant pose, delicate skin, feminine beauty, intimate atmosphere, ethereal, dreamy, photorealistic, highly detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, explicit, pornographic, vulgar"
            },
            {
                "name": "唯美晨光",
                "prompt": "masterpiece, best quality, 8k, a beautiful woman in morning light, soft golden sunlight, peaceful expression, cozy bedroom, natural beauty, intimate atmosphere, ethereal, dreamy, photorealistic, highly detailed, warm tones",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, heavy makeup, artificial, dark"
            },
            {
                "name": "唯美梦境",
                "prompt": "masterpiece, best quality, 8k, surreal dreamscape, floating flowers, ethereal woman, soft glowing light, mystical atmosphere, fantasy art, dreamy, ethereal beauty, photorealistic, highly detailed, soft pastel colors, magical",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, dark, scary, horror"
            },
        ]