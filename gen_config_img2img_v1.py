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
        
    def run_single_batch(self):
        """生成单人配置"""
        ethnicities = self.builder.get_all_options("种族_亚洲")[:5] + \
                     self.builder.get_all_options("种族_欧洲")[:3]
        genders = ["female", "male"]
        ages = ["young_adult", "adult", "middle_aged"]
        
        for ethnicity in ethnicities:
            for gender in genders:
                for age in ages:
                    prompt, negative = self.single_gen.generate(
                        age=age,
                        gender=gender,
                        ethnicity=ethnicity,
                        clothing="casual",
                        quality="photorealistic"
                    )
                    self.results["single"].append({
                        "name": f"{ethnicity}_{gender}_{age}",
                        "prompt": prompt,
                        "negative": negative,
                        "width": 512,
                        "height": 768
                    })
    
    def run_couple_batch(self):
        """生成双人配置"""
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
    
    def run_group_batch(self):
        """生成多人配置"""
        ethnicities = ["chinese", "japanese", "korean", "indian", "american"]
        for ethnicity in ethnicities:
            results = self.group_gen.generate_family(ethnicity=ethnicity)
            for r in results:
                r["name"] = r["type"]
                r["width"] = 1024
                r["height"] = 768
                self.results["group"].append(r)
    
    def run_all(self):
        """运行所有生成（使用定制场景）"""
        # 这里我们不生成那些通用的单人（因为它只会生成 casual 服装）
        # 而是只生成用户想要的特定场景
        self.generate_single_batch_with_scenes()
        
        # 双人和多人保持原样（或者您也可以给双人加场景）
        self.run_couple_batch()
        self.run_group_batch()
    
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