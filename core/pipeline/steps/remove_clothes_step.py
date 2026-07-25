# core/pipeline/steps/remove_clothes_step.py
"""去掉衣服 - 将人物转换为裸体风格 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class RemoveClothesStep(BaseStyleStep):
    """去掉衣服转换步骤"""
    
    def __init__(self):
        super().__init__("remove_clothes", "去掉衣服 - 转换为裸体")
        self._config = {
            "strength": 0.55,
            "cfg": 7.0,
            "steps": 35,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "openpose",
            "controlnet_strength": 0.7,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.55, "min": 0.35, "max": 0.75},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 35, "min": 25, "max": 60},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "openpose",
                "choices": ["openpose", "canny", "hed", "lineart"]
            },
            "controlnet_strength": {"type": "float", "default": 0.7, "min": 0.3, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        """生成去掉衣服的 28 种场景"""
        return [
            # ===== 比基尼/泳装 → 裸体 (强度: 0.45-0.55) =====
            {
                "name": "比基尼→裸体_海滩",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, standing on tropical beach, ocean waves, golden sunset, full body, perfect body, natural beauty, sun-kissed skin, artistic nude, high quality, detailed face",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, bikini, swimsuit, bathing suit, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
            },
            {
                "name": "比基尼→裸体_泳池",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, sitting by swimming pool, water reflections, summer atmosphere, full body, perfect body, natural beauty, artistic nude, high quality, detailed face",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, bikini, swimsuit, bathing suit, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
            },
            {
                "name": "比基尼→裸体_游艇",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, on a luxury yacht, ocean background, golden lighting, full body, perfect body, glamorous, artistic nude, high quality, detailed face",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, bikini, swimsuit, bathing suit, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
            },
            {
                "name": "比基尼→裸体_温泉",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in hot spring, steam rising, natural rock background, relaxing atmosphere, full body, perfect body, artistic nude, high quality, detailed face",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, bikini, swimsuit, bathing suit, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
            },
            # ===== 紧身衣/瑜伽服 → 裸体 (强度: 0.50-0.60) =====
            {
                "name": "瑜伽服→裸体_瑜伽",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, doing yoga pose, flexible body, yoga mat, peaceful atmosphere, full body, perfect body, natural lighting, artistic nude, high quality, detailed face",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, yoga pants, leggings, sports bra, gym clothes, fitness wear, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
            },
            {
                "name": "紧身衣→裸体_健身房",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in gym, fit body, defined muscles, workout atmosphere, full body, perfect body, natural lighting, artistic nude, high quality, detailed face",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, sports bra, leggings, gym clothes, fitness wear, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
            },
            {
                "name": "紧身衣→裸体_跑步",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, running, dynamic pose, fit body, outdoor setting, full body, perfect body, natural lighting, artistic nude, high quality, detailed face",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, sports bra, leggings, running clothes, gym clothes, fitness wear, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
            },
            # ===== 正装/外套 → 裸体 (强度: 0.55-0.65) =====
            {
                "name": "西装→裸体_办公室",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in modern office, professional setting, confident pose, full body, perfect body, dramatic lighting, artistic nude, high quality, detailed face",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, suit, blazer, jacket, tie, dress shirt, business wear, formal wear, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
            },
            {
                "name": "风衣→裸体_街头",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, urban street background, city atmosphere, confident pose, full body, perfect body, dramatic lighting, artistic nude, high quality, detailed face",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, trench coat, jacket, outerwear, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
            },
            {
                "name": "大衣→裸体_雪地",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in snowy landscape, winter atmosphere, contrast of warm skin and cold snow, full body, perfect body, artistic nude, high quality, detailed face",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, coat, parka, winter jacket, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
            },
            {
                "name": "礼服→裸体_红毯",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, glamorous red carpet setting, dramatic lighting, elegant pose, full body, perfect body, artistic nude, high quality, detailed face",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, evening gown, formal dress, red carpet dress, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
            },
            # ===== 宽松衣物 → 裸体 (强度: 0.60-0.70) =====
            {
                "name": "连衣裙→裸体_花园",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in flower garden, natural beauty, surrounded by flowers, full body, perfect body, soft lighting, artistic nude, high quality, detailed face",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, dress, sundress, floral dress, clothes, fabric, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
            },