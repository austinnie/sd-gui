#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图生图批量 - 配置文件生成器
自动生成 img2img_batch_config_时间戳.json
保存位置: output/configs/img2img_batch_config_时间戳.json
"""

import sys
import os
import json
import argparse
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.person_builder import PersonBuilder
from generators.single_generator import SingleGenerator
from generators.couple_generator import CoupleGenerator
from generators.group_generator import GroupGenerator


class Img2ImgConfigGenerator:
    """图生图配置文件生成器 - 基于人物模板生成配置"""
    
    def __init__(self):
        # 配置保存到 output/configs/
        self.config_dir = os.path.join(os.path.dirname(__file__), "output", "configs")
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.single_gen = SingleGenerator()
        self.couple_gen = CoupleGenerator()
        self.group_gen = GroupGenerator()
        self.builder = PersonBuilder()
        
        self.results = {
            "single": [],
            "couple": [],
            "group": []
        }

    def generate_single_batch_with_scenes(self, target_gender="female"):
        """
        生成单人的定制化场景配置（床上、性感、各种服装）
        """
        # 核心提示词前缀（用来固定人物特征）
        base_prompt = "same woman, same face, same body shape"
        
        # --- 定义您想要的场景库（扩张版） ---
        scenes = [
            # ====== 原版保留 ======
            # 场景 1：沙滩比基尼
            {
                "name": "沙滩比基尼",
                "prompt": f"{base_prompt}, wearing bikini, on a beach, ocean background, sunny day, full body, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothes",
                "width": 1024,
                "height": 768
            },
            # 场景 2：卧室情趣内衣
            {
                "name": "卧室情趣内衣",
                "prompt": f"{base_prompt}, wearing sexy lace lingerie, in a bedroom, soft warm lighting, lying on bed, seductive pose, high quality",
                "negative": "worst quality, low quality, deformed, blurry, bad anatomy, extra limbs",
                "width": 768,
                "height": 1024
            },
            # 场景 3：深夜私密照（氛围感）
            {
                "name": "深夜私密照",
                "prompt": f"{base_prompt}, naked, lying on silk sheets, dim lighting, sensual atmosphere, intimate, soft focus, artistic nude",
                "negative": "worst quality, low quality, deformed, blurry, bad anatomy, extra limbs, clothed",
                "width": 1024,
                "height": 1024
            },
            # 场景 4：红毯晚礼服
            {
                "name": "红毯晚礼服",
                "prompt": f"{base_prompt}, wearing elegant red evening dress, standing on a red carpet, flash photography, glamorous, high quality",
                "negative": "worst quality, low quality, deformed, blurry, bad anatomy, casual clothes",
                "width": 768,
                "height": 1024
            },
            # 场景 5：泳池边湿身
            {
                "name": "泳池边湿身",
                "prompt": f"{base_prompt}, wearing wet bikini, sitting by a swimming pool, sunny, water drops, high quality, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothes",
                "width": 1024,
                "height": 768
            },
            # 场景 6：日式和服
            {
                "name": "日式和服",
                "prompt": f"{base_prompt}, wearing traditional japanese kimono, in a zen garden, cherry blossoms, elegant, high quality",
                "negative": "worst quality, low quality, deformed, blurry, western clothes",
                "width": 768,
                "height": 1024
            },
            # 场景 7：居家白衬衫
            {
                "name": "白衬衫居家",
                "prompt": f"{base_prompt}, wearing oversize white shirt, sitting on bed, morning light, casual, seductive glance, high quality",
                "negative": "worst quality, low quality, deformed, blurry, lingerie, naked",
                "width": 1024,
                "height": 1024
            },

            # ====== 新增：躺姿与坐姿系列 ======
            {
                "name": "床上慵懒躺姿",
                "prompt": f"{base_prompt}, naked, lying on stomach on white bed, looking over shoulder at camera, soft morning light, intimate",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 1024,
                "height": 768
            },
            {
                "name": "沙发上侧躺",
                "prompt": f"{base_prompt}, wearing silk pajamas, lying sideways on a plush sofa, relaxed and elegant, warm lamp light, luxurious",
                "negative": "worst quality, low quality, deformed, blurry, casual clothes",
                "width": 1024,
                "height": 768
            },
            {
                "name": "浴缸水光",
                "prompt": f"{base_prompt}, nude, soaking in a bathtub, water reflections, steam, soft candlelight, intimate and sensual",
                "negative": "worst quality, low quality, deformed, blurry, clothes, bad anatomy",
                "width": 768,
                "height": 1024
            },
            {
                "name": "沙发慵懒坐姿",
                "prompt": f"{base_prompt}, wearing loose knit sweater and panties, sitting cross-legged on a modern sofa, cozy home atmosphere",
                "negative": "worst quality, low quality, deformed, blurry, lingerie",
                "width": 1024,
                "height": 1024
            },

            # ====== 新增：动态与场景反差 ======
            {
                "name": "厨房里做饭",
                "prompt": f"{base_prompt}, wearing casual apron and t-shirt, standing in modern kitchen, turning around to look at camera, natural daylight",
                "negative": "worst quality, low quality, deformed, blurry, lingerie",
                "width": 1024,
                "height": 768
            },
            {
                "name": "赛博朋克霓虹",
                "prompt": f"{base_prompt}, wearing black latex dress, standing in a neon-lit cyberpunk alley, rain, reflections, dramatic contrast, edgy",
                "negative": "worst quality, low quality, deformed, blurry, casual clothes",
                "width": 768,
                "height": 1024
            },
            {
                "name": "哥特女仆装",
                "prompt": f"{base_prompt}, wearing gothic maid outfit, black lace, white apron, dark mansion background, mysterious atmosphere",
                "negative": "worst quality, low quality, deformed, blurry, modern clothes, colorful",
                "width": 768,
                "height": 1024
            },

            # ====== 新增：职业风与特殊氛围 ======
            {
                "name": "职场极简西装",
                "prompt": f"{base_prompt}, wearing tailored grey business suit, standing in a high-rise office, floor to ceiling windows, professional and confident",
                "negative": "worst quality, low quality, deformed, blurry, casual clothes, lingerie",
                "width": 768,
                "height": 1024
            },
            {
                "name": "黎明晨光私密",
                "prompt": f"{base_prompt}, nude, curled up by a window, gentle morning glow on skin, intimate atmosphere, realistic skin texture",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "古典油画光",
                "prompt": f"{base_prompt}, wearing renaissance-style white gown, sitting by a window, Rembrandt lighting, warm golden hour, oil painting style",
                "negative": "worst quality, low quality, deformed, blurry, modern clothes, bad anatomy",
                "width": 768,
                "height": 1024
            },
            {
                "name": "户外月光裸体",
                "prompt": f"{base_prompt}, nude, standing in a moonlit forest, ethereal lighting, atmospheric, mystical, artistic nude, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "床上晨光",
                "prompt": f"{base_prompt}, naked, sitting up in bed, morning sunlight hitting skin, intimate, soft shadows, realistic skin texture",
                "negative": "worst quality, low quality, deformed, blurry, clothes, bad anatomy",
                "width": 768,
                "height": 1024
            },
            # ===== 1. 床上与慵懒私密 =====
            {
                "name": "深夜丝绸床单",
                "prompt": f"{base_prompt}, naked, lying on silk sheets, dim lighting, sensual atmosphere, intimate, soft focus, artistic nude",
                "negative": "worst quality, low quality, deformed, blurry, bad anatomy, extra limbs, clothed",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "床上晨光苏醒",
                "prompt": f"{base_prompt}, naked, sitting up in bed, morning sunlight hitting skin, intimate, soft shadows, realistic skin texture",
                "negative": "worst quality, low quality, deformed, blurry, clothes, bad anatomy",
                "width": 768,
                "height": 1024
            },
            {
                "name": "慵懒趴姿回眸",
                "prompt": f"{base_prompt}, naked, lying on stomach on white bed, looking over shoulder at camera, soft morning light, intimate",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 1024,
                "height": 768
            },

            # ===== 2. 浴缸、浴室与水 =====
            {
                "name": "浴缸光影",
                "prompt": f"{base_prompt}, nude, soaking in a bathtub, water reflections, steam, soft candlelight, intimate and sensual",
                "negative": "worst quality, low quality, deformed, blurry, clothes, bad anatomy",
                "width": 768,
                "height": 1024
            },
            {
                "name": "淋浴水花",
                "prompt": f"{base_prompt}, naked, standing under shower, water streaming down, steam, sensual, close up",
                "negative": "worst quality, low quality, deformed, blurry, clothes, bad anatomy",
                "width": 768,
                "height": 1024
            },

            # ===== 3. 沙发与居家放松 =====
            {
                "name": "沙发侧躺",
                "prompt": f"{base_prompt}, naked, lying sideways on a plush sofa, relaxed and elegant, warm lamp light, luxurious",
                "negative": "worst quality, low quality, deformed, blurry, casual clothes, bad anatomy",
                "width": 1024,
                "height": 768
            },
            {
                "name": "地毯盘坐",
                "prompt": f"{base_prompt}, naked, sitting cross-legged on a thick rug, morning light, cozy, intimate atmosphere",
                "negative": "worst quality, low quality, deformed, blurry, clothes, bad anatomy",
                "width": 1024,
                "height": 1024
            },

            # ===== 4. 自然、户外与艺术光 =====
            {
                "name": "户外森林裸体",
                "prompt": f"{base_prompt}, nude, standing in a moonlit forest, ethereal lighting, atmospheric, mystical, artistic nude, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "古典油画裸体",
                "prompt": f"{base_prompt}, nude, renaissance-style, lying on velvet, Rembrandt lighting, warm golden hour, oil painting style, artistic nude",
                "negative": "worst quality, low quality, deformed, blurry, modern clothes, bad anatomy",
                "width": 768,
                "height": 1024
            },
            {
                "name": "落地窗剪影",
                "prompt": f"{base_prompt}, nude, standing by a large window, backlight, soft silhouette, intimate, high quality, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothes, bad anatomy",
                "width": 1024,
                "height": 1024
            },

            # ===== 5. 光影与环境特写 =====
            {
                "name": "黎明晨光私密",
                "prompt": f"{base_prompt}, nude, curled up by a window, gentle morning glow on skin, intimate atmosphere, realistic skin texture",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "蜡烛氛围",
                "prompt": f"{base_prompt}, naked, lying on bed, candlelight flickering, soft shadows, romantic, sensual, warm ambiance",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 768,
                "height": 1024
            },
            {
                "name": "深色背景棚拍",
                "prompt": f"{base_prompt}, naked, dark background, dramatic lighting, studio portrait, high contrast, high quality, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothes, bad anatomy, bright background",
                "width": 768,
                "height": 1024
            }, 
            # ====== 新增：不同构图与特写 ======
            {
                "name": "仰卧双臂伸展",
                "prompt": f"{base_prompt}, naked, lying on back, arms stretched above head, soft studio light, peaceful, high quality, full body",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 1024,
                "height": 768
            },
            {
                "name": "跪姿回眸",
                "prompt": f"{base_prompt}, nude, kneeling on bed, looking back over shoulder, soft window light, sensual, high quality, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 768,
                "height": 1024
            },
            {
                "name": "半身私密特写",
                "prompt": f"{base_prompt}, naked, close up shot, shoulders and torso visible, intimate atmosphere, soft skin, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, full body, legs",
                "width": 768,
                "height": 1024
            },
            {
                "name": "坐姿落地窗",
                "prompt": f"{base_prompt}, nude, sitting on floor by a large window, side profile, natural light, peaceful, elegant",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "沙滩裸体",
                "prompt": f"{base_prompt}, nude, standing on a beach, ocean waves, warm sunset light, artistic, high quality, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, swimsuit, bikini",
                "width": 1024,
                "height": 768
            },
            {
                "name": "暗调情绪人像",
                "prompt": f"{base_prompt}, naked, dark moody portrait, dramatic chiaroscuro lighting, emotional, cinematic, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, bright, cheerful",
                "width": 768,
                "height": 1024
            },
            {
                "name": "俯卧床上",
                "prompt": f"{base_prompt}, naked, lying face down on bed, arms resting, soft morning light, intimate, relaxed atmosphere",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 1024,
                "height": 768
            },  
            # ====== 新增：特殊构图与环境 ======
            {
                "name": "水中漂浮",
                "prompt": f"{base_prompt}, naked, floating in calm water, water surface reflections, soft ripples, ethereal, serene, artistic nude",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, clothes",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "逆光剪影",
                "prompt": f"{base_prompt}, nude, standing against bright sunset light, silhouette, dramatic rim light, atmospheric, emotional",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, visible face",
                "width": 1024,
                "height": 768
            },
            {
                "name": "地面俯拍",
                "prompt": f"{base_prompt}, nude, lying on a textured rug, top-down view, soft natural light, creative angle, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "窗帘半遮",
                "prompt": f"{base_prompt}, naked, partially hidden behind sheer curtains, soft diffused light, mysterious, sensual, artistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, fully visible",
                "width": 768,
                "height": 1024
            },
            {
                "name": "咖啡厅裸体（艺术）",
                "prompt": f"{base_prompt}, nude, sitting at a café table, morning sunlight, casual atmosphere, artistic nude, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, explicit",
                "width": 1024,
                "height": 768
            },
            {
                "name": "深邃森林",
                "prompt": f"{base_prompt}, nude, standing in a deep forest, dappled sunlight filtering through trees, mystical, natural, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy",
                "width": 1024,
                "height": 1024
            },
                        # ====== 瑜伽 + 不穿衣（艺术人体） ======
            {
                "name": "瑜伽树式裸体",
                "prompt": f"{base_prompt}, naked, standing in yoga tree pose, balanced on one leg, graceful and peaceful, soft studio lighting, artistic nude, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, yoga pants, sports bra, extra limbs",
                "width": 768,
                "height": 1024
            },
            {
                "name": "瑜伽下犬式裸体",
                "prompt": f"{base_prompt}, nude, in downward-facing dog yoga pose, stretching back and legs, gentle natural light, elegant, artistic nude, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, yoga clothes, leggings",
                "width": 1024,
                "height": 768
            },
            {
                "name": "瑜伽冥想裸体",
                "prompt": f"{base_prompt}, naked, sitting in lotus pose, meditating on a yoga mat, serene, soft ambient light, spiritual, artistic nude, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, yoga clothes, sports wear",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "瑜伽战士式裸体",
                "prompt": f"{base_prompt}, nude, in warrior yoga pose, strong and confident, body stretching, dramatic light, artistic nude, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, yoga pants, extra limbs, misshapen limbs",
                "width": 768,
                "height": 1024
            },
            # ====== 芭蕾舞 + 不穿衣（艺术人体摄影） ======
            {
                "name": "芭蕾站立大位",
                "prompt": f"{base_prompt}, naked, standing in ballet first position, graceful lines, elegant posture, soft studio lighting, artistic nude, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, ballet tutu, leotard, ballet shoes",
                "width": 768,
                "height": 1024
            },
            {
                "name": "芭蕾腾跃瞬间",
                "prompt": f"{base_prompt}, nude, in mid-air ballet leap, graceful pose, legs extended, dynamic movement, dramatic photography, artistic nude",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, ballet clothes, extra limbs",
                "width": 1024,
                "height": 768
            },
            {
                "name": "芭蕾下腰舒展",
                "prompt": f"{base_prompt}, naked, performing ballet arabesque, balancing on one leg, arms extended, elegant, soft window light, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, ballet wear, tutu",
                "width": 768,
                "height": 1024
            },
            {
                "name": "芭蕾舞者背影",
                "prompt": f"{base_prompt}, naked, ballet dancer from behind, graceful back muscles, standing on toes, dramatic lighting, artistic nude",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, ballet clothes, front view",
                "width": 768,
                "height": 1024
            },
            {
                "name": "古典唯美芭蕾",
                "prompt": f"{base_prompt}, nude, in ballet pose, soft vintage lighting, romantic atmosphere, classical art style, beautiful composition, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, ballet shoes, tutu, modern clothes",
                "width": 1024,
                "height": 1024
            },
            # ====== 户外 + 不穿衣（自然人体艺术） ======
            {
                "name": "海边礁石",
                "prompt": f"{base_prompt}, nude, standing on a rocky beach, ocean waves crashing behind, golden sunset light, wind blowing hair, artistic nude, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, swimsuit, bikini, sunglasses",
                "width": 1024,
                "height": 768
            },
            {
                "name": "森林溪流",
                "prompt": f"{base_prompt}, naked, standing in a shallow forest stream, dappled sunlight filtering through trees, water reflections, ethereal, natural, serene",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, clothes, shoes",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "草原奔跑",
                "prompt": f"{base_prompt}, nude, running through a tall grass field, arms stretched, bright summer sun, motion blur, emotional, free-spirited, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, extra limbs, clothes, sneakers",
                "width": 1024,
                "height": 768
            },
            {
                "name": "悬崖俯瞰",
                "prompt": f"{base_prompt}, nude, standing on a cliff edge overlooking a valley, dramatic clouds, wind, powerful pose, artistic nude, cinematic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, clothes, safety gear",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "花园藤蔓",
                "prompt": f"{base_prompt}, naked, sitting among blooming flowers and green vines, soft sunlight, intimate with nature, delicate, artistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, clothes, dress, shoes",
                "width": 768,
                "height": 1024
            },
            {
                "name": "沙漠夕阳",
                "prompt": f"{base_prompt}, nude, standing in a desert landscape, warm sand, golden sunset, solitude, powerful silhouette, high quality, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, clothes, shoes, urban",
                "width": 1024,
                "height": 768
            
            },            
            # ====== 做家务 + 不穿衣 ======
            {
                "name": "晨间煮咖啡",
                "prompt": f"{base_prompt}, naked, making coffee in a modern kitchen, morning sunlight coming through window, casual and intimate, high quality, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, apron, bathrobe, slippers, clothes",
                "width": 1024,
                "height": 768
            },
            {
                "name": "赤足拖地",
                "prompt": f"{base_prompt}, naked, holding a mop, cleaning the floor, bright sunny room, candid moment, bare feet, artistic, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, apron, dress, shoes, mop blending with hands",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "阳台晾衣",
                "prompt": f"{base_prompt}, naked, hanging laundry on a sunny balcony, gentle breeze, natural light, everyday intimacy, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, underwear, bra, pajamas",
                "width": 768,
                "height": 1024
            },
            {
                "name": "整理书架",
                "prompt": f"{base_prompt}, nude, reaching up to organize books on a shelf, relaxed, natural home atmosphere, soft warm light, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, clothes, pajamas, slippers",
                "width": 768,
                "height": 1024
            },   
            # ====== 洗澡 + 不穿衣 ======
            {
                "name": "淋浴水雾",
                "prompt": f"{base_prompt}, naked, standing under shower, water streaming down, steam rising, soft window light, sensual, intimate, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, towel, bathrobe, soap, opaque water",
                "width": 768,
                "height": 1024
            },
            {
                "name": "浴缸擦身",
                "prompt": f"{base_prompt}, nude, sitting in bathtub, holding a sponge, washing shoulder, bubbly water, candlelight, cozy, intimate, high quality",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, towel, bathrobe, clothes, messy water",
                "width": 1024,
                "height": 1024
            },
            {
                "name": "蒸汽镜前",
                "prompt": f"{base_prompt}, naked, standing in front of steamed bathroom mirror, wiping mirror, soft lighting, moody, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, towel, bathrobe, clothes, clear mirror",
                "width": 768,
                "height": 1024
            },
            {
                "name": "晨浴暖光",
                "prompt": f"{base_prompt}, nude, bathing in warm morning light, water droplets on skin, relaxed, peaceful, high quality, photorealistic",
                "negative": "worst quality, low quality, deformed, blurry, clothed, bad anatomy, towel, bathrobe, swimsuit",
                "width": 1024,
                "height": 768
            },            
            {
                "name": "暗黑甜心皮衣",
                "prompt": f"{base_prompt}, wearing black leather jacket and mini skirt, standing on a dark rooftop, city night lights, rebellious and confident",
                "negative": "worst quality, low quality, deformed, blurry, elegant clothes, dress",
                "width": 1024,
                "height": 768
            },
            {
                "name": "雪地氛围感",
                "prompt": f"{base_prompt}, wearing white fur coat, standing in a snowy forest, soft snow falling, winter wonderland, serene and elegant",
                "negative": "worst quality, low quality, deformed, blurry, summer clothes",
                "width": 1024,
                "height": 768
            }
        ]
        
        # 把生成的场景直接加入 results["single"]
        self.results["single"] = scenes
        return scenes

    # ==================== JSON 加载器 ====================
    def _load_scene_patterns(self):
        """加载 scene_patterns.json 并解析"""
        scene_path = os.path.join(os.path.dirname(__file__), "scene_patterns.json")
        if not os.path.exists(scene_path):
            print(f"⚠️ 找不到 scene_patterns.json，使用默认配置")
            return {}
        try:
            with open(scene_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"⚠️ 加载 scene_patterns.json 失败: {e}")
            return {}

    # ==================== 单人场景（从 JSON 补充） ====================
    def generate_single_scenes_from_json(self):
        """
        从 scene_patterns.json 中提取女性特征配置
        (作为备用场景库，如果 JSON 里没有合适的单人场景，则跳过)
        """
        data = self._load_scene_patterns()
        if not data:
            return []
        # 直接返回，因为您已经在 generate_single_batch_with_scenes 里写了场景
        return []

    # ==================== 双人场景（从 JSON 自动生成） ====================
    def generate_couple_scenes_from_json(self):
        """
        从 scene_patterns.json 的“两人亲密场景”中提取组合模板
        自动生成双人亲密场景配置
        """
        data = self._load_scene_patterns()
        if not data:
            return []
            
        scenes_data = data.get("scenes", {})
        couple_scene = scenes_data.get("两人亲密场景", {})
        if not couple_scene:
            print("⚠️ 场景配置中未找到 '两人亲密场景'")
            return []
        
        # 解析分类
        categories = couple_scene.get("categories", {})
        pose_dict = categories.get("基本姿势", {})
        intimacy_dict = categories.get("亲密程度", {})
        view_dict = categories.get("视角", {})
        env_dict = categories.get("环境氛围", {})
        clothing_dict = categories.get("服装状态", {})
        emotion_dict = categories.get("情感表达", {})
        man_body_dict = categories.get("男士特征", {})
        woman_body_dict = categories.get("女士特征", {})
        
        # 获取组合模板（预定义的模板比随机组合更合理）
        templates = data.get("组合模板", {})
        
        results = []
        # 基础提示词前缀（固定人物特征）
        base_prompt = "same woman, same face, same body shape, couple scene"
        
        # 遍历组合模板
        for template_name, template in templates.items():
            # 从模板中提取配置
            pose_key = template.get("basic_pose", "missionary")
            intimacy_key = template.get("intimacy_level", "lovemaking")
            view_key = template.get("view_angle", "profile_view")
            env_key = template.get("environment", "bedroom")
            clothing_key = template.get("clothing", "nude")
            emotion_key = template.get("emotion", "passionate_desire")
            man_key = template.get("body_features_man", "average_man")
            woman_key = template.get("body_features_woman", "curvy_figure")
            suffix = template.get("prompt_suffix", "")
            
            # 从各分类中提取中文描述
            pose_desc = pose_dict.get(pose_key, {}).get("prompt", "")
            intimacy_desc = intimacy_dict.get(intimacy_key, {}).get("prompt", "")
            view_desc = view_dict.get(view_key, {}).get("prompt", "")
            env_desc = env_dict.get(env_key, {}).get("prompt", "")
            clothing_desc = clothing_dict.get(clothing_key, {}).get("prompt", "")
            emotion_desc = emotion_dict.get(emotion_key, {}).get("prompt", "")
            man_desc = man_body_dict.get(man_key, {}).get("prompt", "")
            woman_desc = woman_body_dict.get(woman_key, {}).get("prompt", "")
            
            # 组合成英文提示词（因为图生图主要用英文效果更好）
            prompt_parts = [
                base_prompt,
                "intimate couple",
                f"two people, {pose_desc}",
                f"{intimacy_desc}",
                f"{view_desc}",
                f"{env_desc}",
                f"{clothing_desc}",
                f"{emotion_desc}",
                suffix,
                "high quality, photorealistic, detailed"
            ]
            
            # 过滤空字符串
            prompt = ", ".join([p for p in prompt_parts if p])
            
            # 负面提示词
            negative_parts = [
                "worst quality, low quality, deformed, blurry, bad anatomy",
                "extra limbs, mutated hands, missing fingers, too many fingers",
                "watermark, text, signature"
            ]
            negative = ", ".join(negative_parts)
            
            # 添加到结果
            results.append({
                "name": f"双人_{template_name}",
                "prompt": prompt,
                "negative": negative,
                "width": 768,
                "height": 512
            })
        
        return results

    # ==================== 双人原始方法 ====================
    def run_couple_batch(self):
        """生成双人配置（原始方法 - 保留备用）"""
        combinations = [
            ({"ethnicity": "chinese", "gender": "male"}, {"ethnicity": "chinese", "gender": "female"}),
            ({"ethnicity": "japanese", "gender": "male"}, {"ethnicity": "japanese", "gender": "female"}),
            ({"ethnicity": "korean", "gender": "male"}, {"ethnicity": "korean", "gender": "female"}),
            ({"ethnicity": "chinese", "gender": "male"}, {"ethnicity": "russian", "gender": "female"}),
            ({"ethnicity": "chinese", "gender": "female"}, {"ethnicity": "american", "gender": "male"}),
            ({"ethnicity": "japanese", "gender": "female"}, {"ethnicity": "british", "gender": "male"}),
            ({"ethnicity": "korean", "gender": "female"}, {"ethnicity": "french", "gender": "male"}),
        ]
        scenes = ["restaurant", "beach", "city_street", "bedroom"]
        intimacies = ["romantic", "kissing", "hugging"]
        
        for (p1, p2) in combinations:
            for scene in scenes:
                for intimacy in intimacies:
                    p1_full = {**p1, "age": "adult", "clothing": "formal" if scene == "restaurant" else "casual"}
                    p2_full = {**p2, "age": "adult", "clothing": "elegant" if scene == "restaurant" else "casual"}
                    
                    prompt, negative = self.couple_gen.generate(
                        person1=p1_full,
                        person2=p2_full,
                        relationship="couple",
                        intimacy=intimacy,
                        scene=scene,
                        lighting="warm" if intimacy == "romantic" else "natural",
                        quality="photorealistic"
                    )
                    self.results["couple"].append({
                        "name": f"{p1['ethnicity']}_{p1['gender']}+{p2['ethnicity']}_{p2['gender']}@{scene}",
                        "prompt": prompt,
                        "negative": negative,
                        "width": 768,
                        "height": 512
                    })
    
    # ==================== 多人场景 ====================
    def run_group_batch(self):
        """生成多人配置（家庭照）"""
        ethnicities = ["chinese", "japanese", "korean", "indian", "american"]
        for ethnicity in ethnicities:
            results = self.group_gen.generate_family(ethnicity=ethnicity)
            for r in results:
                r["name"] = r["type"]
                r["width"] = 1024
                r["height"] = 768
                self.results["group"].append(r)

    # ==================== 全部运行（整合所有） ====================
    def run_all(self):
        """运行所有生成 - 整合单人、双人（从 JSON）、多人"""
        # 1. 单人场景（您的手写场景库）
        self.generate_single_batch_with_scenes()
        
        ## 2. 双人场景（从 JSON 自动生成）
        #couple_jobs = self.generate_couple_scenes_from_json()
        #if couple_jobs:
        #    self.results["couple"] = couple_jobs
        #    print(f"✅ 从 scene_patterns.json 生成了 {len(couple_jobs)} 个双人场景")
        #else:
        #    # 如果 JSON 解析失败，回退到原始的双人生成方法
        #    print("⚠️ 回退到原始双人生成方法")
        #    self.results["couple"] = []
        #    self.run_couple_batch()
        #
        ## 3. 多人场景（家庭照）
        #self.run_group_batch()
    
    # ==================== 导出配置 ====================
    def export_config(self,
                      target_image: str,
                      model_path: str = "../models/sd-v1-5/aiiiiii01_v10.safetensors",
                      strength: float = 0.45,
                      cfg: float = 7.5,
                      steps: int = 25,
                      output_file: str = None) -> str:
        """导出为 img2img_batch_config.json"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.config_dir, f"img2img_batch_config_{timestamp}.json")
        
        config = {
            "model_path": model_path,
            "target_image": target_image,
            "output_dir": "./output/batch_img2img",
            "strength": strength,
            "cfg": cfg,
            "steps": steps,
            "jobs": []
        }
        
        # 合并所有结果
        for items in [self.results["single"], self.results["couple"], self.results["group"]]:
            config["jobs"].extend(items)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 图生图配置已生成: {output_file}")
        print(f"   📊 共 {len(config['jobs'])} 个任务")
        print("\n📌 下一步运行命令:")
        print(f"   python batch_img2img_generator.py -c {output_file}")
        return output_file


def main():
    parser = argparse.ArgumentParser(description="图生图批量 - 配置文件生成器")
    parser.add_argument("--target-image", type=str, required=True,
                        help="图生图目标图片路径 (例如: ./test_imgs/my_girl.png)")
    parser.add_argument("--output", type=str, default=None, help="输出文件名")
    parser.add_argument("--model", type=str,
                        default="../models/sd-v1-5/aiiiiii01_v10.safetensors",
                        help="基础模型路径")
    parser.add_argument("--strength", type=float, default=0.45,
                        help="重绘强度 (0.2-0.8)")
    parser.add_argument("--cfg", type=float, default=7.5,
                        help="CFG Scale")
    parser.add_argument("--steps", type=int, default=25,
                        help="推理步数")
    
    args = parser.parse_args()
    
    generator = Img2ImgConfigGenerator()
    generator.run_all()
    generator.export_config(
        target_image=args.target_image,
        model_path=args.model,
        strength=args.strength,
        cfg=args.cfg,
        steps=args.steps,
        output_file=args.output
    )


if __name__ == "__main__":
    main()