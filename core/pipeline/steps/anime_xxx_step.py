# core/pipeline/steps/anime_xxx_step.py
"""动漫爱爱风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class AnimeXxxStep(BaseStyleStep):
    """动漫爱爱风格转换步骤"""
    
    def __init__(self):
        super().__init__("anime_xxx", "转换为动漫爱爱风格")
        self._config = {
            "strength": 0.45,
            "cfg": 7.0,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "openpose",
            "controlnet_strength": 0.6,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.3, "max": 0.7},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "openpose",
                "choices": ["openpose", "canny", "hed", "lineart"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        """生成动漫爱爱场景的 40 种提示词"""
        return [
            # ===== 单人诱惑 (17种) =====
            {
                "name": "动漫巨乳御姐",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime woman, huge breasts, massive cleavage, seductive expression, long flowing hair, wearing revealing outfit, dramatic lighting, high quality, detailed, vibrant colors, anime art style, sensual pose, big boobs, perfect curves, bedroom setting, intimate atmosphere",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫巨乳女仆",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime maid, huge breasts, massive cleavage spilling out of maid outfit, wearing french maid costume, fishnet stockings, seductive pose, holding a feather duster, luxurious bedroom background, high quality, detailed, vibrant colors, big boobs, erotic roleplay",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫巨乳护士",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime nurse, huge breasts, massive cleavage barely contained in tight nurse uniform, short white dress, fishnet stockings, naughty smile, medical setting, dramatic lighting, sensual pose, high quality, detailed, vibrant colors, big boobs, erotic roleplay",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest, gore, blood"
            },
            {
                "name": "动漫巨乳教师",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime teacher, huge breasts, massive cleavage in tight blouse, glasses, tight pencil skirt, stockings, holding a pointer, classroom background, naughty smile, sensual pose, high quality, detailed, vibrant colors, big boobs, forbidden love",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest, underage"
            },
            {
                "name": "动漫巨乳兔女郎",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime bunny girl, huge breasts, massive cleavage, wearing tight black bunny suit, fishnet stockings, bunny ears, bow tie, high heels, playful pose, casino background, dramatic lighting, curvy body, high quality, detailed, vibrant colors, big boobs, erotic cosplay",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫猫女郎",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime cat girl, huge breasts, massive cleavage, wearing tight black cat suit, cat ears, tail, choker, high heels, playful pose, mysterious atmosphere, dramatic lighting, curvy body, high quality, detailed, vibrant colors, big boobs, erotic cosplay",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫巫女",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime shrine maiden, huge breasts, wearing revealing miko outfit, white and red, seductive pose, traditional Japanese shrine background, soft lighting, high quality, detailed, vibrant colors, big boobs, spiritual yet sensual",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫女王",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime queen, huge breasts, wearing revealing royal outfit, crown, holding a scepter, commanding presence, dramatic lighting, throne room, sensual and dominant, high quality, detailed, vibrant colors, big boobs, dominant beauty",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫精灵",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime elf, huge breasts, long pointed ears, flowing silver hair, wearing sheer translucent robes, visible body through thin fabric, magical forest background, soft ethereal lighting, high quality, detailed, vibrant colors, big boobs, fantasy beauty",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫恶魔娘",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime demon girl, huge breasts, horns, wings, tail, revealing dark outfit, seductive expression, hellfire background, dramatic lighting, high quality, detailed, vibrant colors, big boobs, dark fantasy beauty, forbidden desire",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫天使",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime angel, huge breasts, white wings, flowing white robes, heavenly glow, soft golden lighting, cloudy sky background, divine beauty, high quality, detailed, vibrant colors, big boobs, ethereal and sensual, fallen angel",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫新娘",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime bride, huge breasts, wearing revealing wedding dress, sheer veil, visible body through thin fabric, seductive pose, romantic wedding setting, soft lighting, high quality, detailed, vibrant colors, big boobs, wedding night",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫乳胶衣",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime woman, wearing tight shiny latex catsuit, huge breasts prominently displayed, glossy black material, curves accentuated, dramatic lighting, futuristic or BDSM setting, sensual pose, high quality, detailed, vibrant colors, fetish, latex",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫泳装",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime girl, huge breasts, wearing tiny bikini, massive cleavage, perfect body, beach background, summer atmosphere, playful pose, high quality, detailed, vibrant colors, big boobs, summer love",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫浴衣",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime girl, huge breasts, wearing yukata, loose fabric showing cleavage, traditional Japanese summer festival, soft lighting, playful expression, high quality, detailed, vibrant colors, big boobs, festival romance",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫运动服",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime athlete, huge breasts, wearing tight sports bra and shorts, massive cleavage, fit body, gym background, sweat, dynamic pose, high quality, detailed, vibrant colors, big boobs, sports romance",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            {
                "name": "动漫校服",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime schoolgirl, huge breasts, school uniform, tight white shirt, short skirt, innocent yet seductive, classroom background, soft lighting, high quality, detailed, vibrant colors, big boobs, forbidden school romance",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest, underage"
            },
            {
                "name": "动漫办公室OL",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime office lady, huge breasts, tight blouse, short skirt, stockings, glasses, seductive expression, office background, dramatic lighting, high quality, detailed, vibrant colors, big boobs, office romance",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            },
            # ===== 性爱场景 (14种) =====
            {
                "name": "动漫传教士体位",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex in missionary position, huge breasts, man on top, woman lying down, intimate lovemaking, passionate, romantic atmosphere, soft lighting, bedroom setting, both bodies visible, sensual, high quality, detailed, vibrant colors, hentai, erotic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫后入体位",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex in doggy style position, huge breasts, from behind, passionate sex, intimate, bedroom setting, soft lighting, both bodies visible, sensual, high quality, detailed, vibrant colors, hentai, erotic, deep penetration",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫骑乘体位",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex in cowgirl position, huge breasts, woman on top, riding, passionate lovemaking, intimate, bedroom setting, soft lighting, both bodies visible, sensual, high quality, detailed, vibrant colors, hentai, erotic, woman in control",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫站立后入",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex standing up from behind, huge breasts, passionate sex, intimate, bedroom or bathroom setting, soft lighting, both bodies visible, sensual, high quality, detailed, vibrant colors, hentai, erotic, standing sex",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫侧躺体位",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex in spooning position, huge breasts, side lying, intimate lovemaking, passionate, bedroom setting, soft lighting, both bodies visible, sensual, high quality, detailed, vibrant colors, hentai, erotic, spooning sex",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫69体位",
                "prompt": "masterpiece, best quality, anime style, two people in 69 position, huge breasts, mutual oral, intimate pleasure, both bodies visible, high quality, detailed, vibrant colors, hentai, erotic, mutual pleasure",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫口交",
                "prompt": "masterpiece, best quality, anime style, a woman giving oral sex to a man, huge breasts, blowjob, intimate, passionate, bedroom setting, soft lighting, both bodies visible, high quality, detailed, vibrant colors, hentai, erotic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫舔阴",
                "prompt": "masterpiece, best quality, anime style, a man giving oral sex to a woman, huge breasts, cunnilingus, intimate pleasure, passionate, bedroom setting, soft lighting, both bodies visible, high quality, detailed, vibrant colors, hentai, erotic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫捆绑性爱",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime woman, artistic shibari rope bondage, red ropes wrapped around huge breasts and curvy body, sensual submission, dramatic lighting, intimate atmosphere, high quality, detailed, vibrant colors, tasteful bondage art, hentai, BDSM",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury, extreme"
            },
            {
                "name": "动漫触手",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime woman, tentacles wrapped around curvy body, huge breasts, sensual expression, fantasy atmosphere, dark magical setting, dramatic lighting, high quality, detailed, vibrant colors, erotic fantasy art, hentai, tentacle",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury, extreme violence"
            },
            {
                "name": "动漫强制",
                "prompt": "masterpiece, best quality, anime style, a beautiful anime woman, forced submission, dominant male, intense expression, dramatic lighting, dark atmosphere, high quality, detailed, vibrant colors, hentai, rough sex, power exchange",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury, extreme violence"
            },
            {
                "name": "动漫群交",
                "prompt": "masterpiece, best quality, anime style, multiple people having group sex, huge breasts, threesome, passionate, intense, bedroom setting, all bodies visible, high quality, detailed, vibrant colors, hentai, group sex, erotic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫百合性爱",
                "prompt": "masterpiece, best quality, anime style, two beautiful anime women making love, huge breasts, intimate embrace, kissing, sensual pose, soft romantic lighting, bedroom setting, high quality, detailed, vibrant colors, yuri, girls love, erotic and artistic, lesbian",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, men, heterosexual"
            },
            {
                "name": "动漫BL性爱",
                "prompt": "masterpiece, best quality, anime style, two handsome anime men making love, intimate embrace, passionate kiss, sensual pose, soft romantic lighting, bedroom setting, high quality, detailed, vibrant colors, yaoi, boys love, erotic and artistic, gay",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, women, heterosexual"
            },
            # ===== 场景性爱 (9种) =====
            {
                "name": "动漫浴室性爱",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex in bathroom, huge breasts, wet bodies, steam, passionate, intimate, high quality, detailed, vibrant colors, hentai, erotic, shower sex",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫厨房性爱",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex in kitchen, huge breasts, passionate, intimate, dramatic lighting, both bodies visible, high quality, detailed, vibrant colors, hentai, erotic, forbidden kitchen sex",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫办公室性爱",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex in office, huge breasts, passionate, intimate, desk setting, dramatic lighting, both bodies visible, high quality, detailed, vibrant colors, hentai, erotic, office romance",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫教室性爱",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex in classroom, huge breasts, passionate, intimate, school setting, dramatic lighting, both bodies visible, high quality, detailed, vibrant colors, hentai, erotic, forbidden classroom",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury, underage"
            },
            {
                "name": "动漫户外性爱",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex outdoors, huge breasts, passionate, intimate, forest or nature setting, moonlight, both bodies visible, high quality, detailed, vibrant colors, hentai, erotic, outdoor sex",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫海滩性爱",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex on beach, huge breasts, passionate, intimate, sunset, ocean waves, both bodies visible, high quality, detailed, vibrant colors, hentai, erotic, beach sex",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫温泉性爱",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex in hot spring, huge breasts, wet bodies, steam, passionate, intimate, both bodies visible, high quality, detailed, vibrant colors, hentai, erotic, onsen sex",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫车内性爱",
                "prompt": "masterpiece, best quality, anime style, a man and woman having sex in car, huge breasts, passionate, intimate, cramped space, both bodies visible, high quality, detailed, vibrant colors, hentai, erotic, car sex",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, gore, blood, injury"
            },
            {
                "name": "动漫特写_巨乳",
                "prompt": "masterpiece, best quality, anime style, close-up of huge anime breasts, massive cleavage, big boobs, detailed, vibrant colors, high quality, seductive, perfect curves, anime art style, erotic, hentai",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, explicit, pornographic, vulgar, small chest, flat chest"
            }
        ]