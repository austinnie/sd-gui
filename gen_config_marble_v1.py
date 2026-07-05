#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大理石雕像专用 - 配置文件生成器 (完整版 - 14个场景)
支持自动分析图片特征，推荐最佳参数
"""

import sys
import os
import json
import argparse
from datetime import datetime
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def analyze_image(image_path):
    """
    自动分析图片特征，推荐最佳参数
    
    返回:
        dict: {
            "strength": 推荐强度,
            "max_strength": 推荐最大强度,
            "type": 图片类型,
            "confidence": 置信度
        }
    """
    try:
        img = Image.open(image_path)
        w, h = img.size
        aspect_ratio = w / h
        
        # 1. 基于宽高比判断
        if aspect_ratio > 1.3:
            # 横图 → 可能是多人、全身照、躺姿、风景
            if aspect_ratio > 1.8:
                # 超宽 → 可能多人或躺姿
                return {
                    "strength": 0.18,
                    "max_strength": 0.25,
                    "type": "wide_multi",
                    "confidence": 0.7
                }
            else:
                return {
                    "strength": 0.22,
                    "max_strength": 0.28,
                    "type": "wide",
                    "confidence": 0.6
                }
        elif aspect_ratio < 0.75:
            # 竖图（接近 3:4）→ 单人正面/全身
            if aspect_ratio < 0.6:
                # 超窄 → 全身照
                return {
                    "strength": 0.25,
                    "max_strength": 0.30,
                    "type": "full_body",
                    "confidence": 0.7
                }
            else:
                # 标准竖图 → 半身/正面
                return {
                    "strength": 0.30,
                    "max_strength": 0.35,
                    "type": "portrait",
                    "confidence": 0.75
                }
        else:
            # 方图或接近方图 → 坐姿、半身、双人、躺姿
            if 0.9 < aspect_ratio < 1.1:
                # 接近正方形 → 坐姿或双人
                return {
                    "strength": 0.20,
                    "max_strength": 0.25,
                    "type": "seated_or_couple",
                    "confidence": 0.6
                }
            else:
                return {
                    "strength": 0.25,
                    "max_strength": 0.30,
                    "type": "medium",
                    "confidence": 0.5
                }
    except Exception as e:
        print(f"   ⚠️ 图片分析失败: {e}，使用默认参数")
        return {
            "strength": 0.25,
            "max_strength": 0.30,
            "type": "unknown",
            "confidence": 0.0
        }


class MarbleConfigGenerator:
    """大理石雕像专用配置生成器"""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(__file__), "output", "configs")
        os.makedirs(self.config_dir, exist_ok=True)
        self.results = {"single": [], "couple": []}

    def generate_marble_scenes(self, target_image=None, target_gender="female", base_strength=0.25):
        """
        生成大理石雕像场景配置 - 14个场景（含躺姿+接吻）
        
        参数:
            target_image: 目标图片路径（用于自动分析）
            target_gender: 性别（保留参数，暂未使用）
            base_strength: 基础强度（会被自动分析覆盖）
        """
        # 自动分析图片
        analysis = {}
        if target_image and os.path.exists(target_image):
            analysis = analyze_image(target_image)
            print(f"   📊 图片分析结果: {analysis}")
        else:
            analysis = {
                "strength": base_strength,
                "max_strength": min(base_strength + 0.05, 0.40),
                "type": "default",
                "confidence": 0.0
            }
        
        # 根据分析结果调整各场景的强度
        base_s = analysis.get("strength", 0.25)
        
        # 强度调整规则
        if analysis.get("type") in ["portrait", "full_body"]:
            s_high = base_s + 0.05
            s_low = base_s - 0.02
            s_very_low = base_s - 0.05
            s_extreme_low = base_s - 0.08
        elif analysis.get("type") in ["seated_or_couple", "wide_multi"]:
            s_high = base_s - 0.03
            s_low = base_s - 0.08
            s_very_low = base_s - 0.12
            s_extreme_low = base_s - 0.15
        else:
            s_high = base_s
            s_low = base_s - 0.03
            s_very_low = base_s - 0.06
            s_extreme_low = base_s - 0.09
        
        # 限制范围
        s_high = max(0.15, min(0.40, s_high))
        s_low = max(0.12, min(0.35, s_low))
        s_very_low = max(0.10, min(0.30, s_very_low))
        s_extreme_low = max(0.08, min(0.25, s_extreme_low))
        
        # 核心提示词
        base_prompt = "a beautiful woman turned into a flawless pure white marble statue, same woman, same face, same features, feminine figure, elegant pose"
        marble_quality = "pure white marble, flawless stone, no color, monochrome white, classical sculpture, highly detailed stone texture, matte finish, no shine, 8k, photorealistic, masterpiece"
        marble_quality_enhanced = "pure white marble, flawless stone, no color, monochrome white, classical sculpture, intricate carving details, smooth stone texture, matte finish, no shine, 8k, photorealistic, masterpiece, high contrast, dramatic shadows"
        
        # 公共 negative 词
        neg_common = "worst quality, low quality, deformed, blurry, ugly"
        neg_no_color = "color, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, colored, warm tones, beige, yellow, gray"
        neg_no_skin = "skin, flesh, clothes, fabric"
        neg_no_shadow = "shadow, dark, underexposed"
        neg_multi = "messy, cluttered, chaotic"

        scenes = [
            # ==================== 单人场景 (9个) ====================
            # 1. 展厅 - 标准正面
            {
                "name": "单人大理石_展厅",
                "prompt": f"{base_prompt}, {marble_quality}, museum gallery, soft lighting, marble pedestal, white background",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}",
                "width": 768,
                "height": 1024,
                "strength": s_high
            },
            # 2. 宫殿 - 豪华背景
            {
                "name": "单人大理石_宫殿",
                "prompt": f"{base_prompt}, {marble_quality}, grand classical palace, ornate columns, marble floor, dramatic spotlight, chandelier",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}",
                "width": 1024,
                "height": 768,
                "strength": s_high - 0.02
            },
            # 3. 坐姿 - 王座
            {
                "name": "单人大理石_坐姿",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, sitting on marble throne, classical Greek sculpture, museum, regal pose",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}",
                "width": 1024,
                "height": 1024,
                "strength": s_low
            },
            # 4. 侧身 - 侧面轮廓
            {
                "name": "单人大理石_侧身",
                "prompt": f"{base_prompt}, {marble_quality}, side profile, elegant pose, classical art, marble pedestal, profile view",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, front view",
                "width": 768,
                "height": 1024,
                "strength": s_low + 0.03
            },
            # 5. 全身 - 站立全身
            {
                "name": "单人大理石_全身",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, full body standing, heroic pose, classical sculpture, museum gallery, marble pedestal",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, cropped, partial",
                "width": 768,
                "height": 1024,
                "strength": s_low
            },
            # 6. 半身特写 - 面部细节
            {
                "name": "单人大理石_半身特写",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, bust sculpture, close-up, detailed face, classical art, museum display, white marble",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}",
                "width": 768,
                "height": 1024,
                "strength": s_high
            },
            # 7. 花园 - 户外场景
            {
                "name": "单人大理石_花园",
                "prompt": f"{base_prompt}, {marble_quality}, classical garden setting, ancient ruins, ivy, soft sunlight, marble pedestal, outdoor sculpture",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, overgrown, moss",
                "width": 1024,
                "height": 768,
                "strength": s_high - 0.02
            },
            # 8. 动态 - 运动感
            {
                "name": "单人大理石_动态",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, dynamic pose, movement, classical sculpture, museum, dramatic lighting, action",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, static, stiff",
                "width": 1024,
                "height": 1024,
                "strength": s_low
            },
            # 9. ✨ 新增: 躺姿 - 卧姿/休息
            {
                "name": "单人大理石_躺姿",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, lying down, reclining pose, sleeping beauty, classical sculpture, marble bed, museum, peaceful expression, elegant drapery, soft lighting",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, standing, sitting, upright",
                "width": 1024,
                "height": 768,
                "strength": s_very_low
            },

            # ==================== 双人场景 (5个) ====================
            # 10. 拥抱 - 亲密
            {
                "name": "双人大理石_拥抱",
                "prompt": f"a man and a woman couple turned into flawless pure white marble statues, intimate embrace, {marble_quality_enhanced}, romantic pose, museum hall, marble pedestal, dramatic lighting, masterpiece, heterosexual couple",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, same gender, two women, two men, lesbian, gay",
                "width": 1024,
                "height": 1024,
                "strength": s_very_low
            },
            # 11. 深情对视 - 眼神交流
            {
                "name": "双人大理石_深情对视",
                "prompt": f"a man and a woman couple turned into pure white marble statues, holding hands, looking at each other, {marble_quality_enhanced}, classical art, palace exhibition, glowing light, high detail, romantic atmosphere, heterosexual couple",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, same gender, two women, two men, lesbian, gay",
                "width": 1024,
                "height": 768,
                "strength": s_very_low
            },
            # 12. 双人并肩 - 站立
            {
                "name": "双人大理石_并肩",
                "prompt": f"a couple turned into pure white marble statues, standing side by side, {marble_quality_enhanced}, classical sculpture, museum gallery, marble pedestals, elegant, formal",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}",
                "width": 1024,
                "height": 768,
                "strength": s_very_low + 0.02
            },
            # 13. 双人舞蹈 - 动态
            {
                "name": "双人大理石_舞蹈",
                "prompt": f"a couple turned into pure white marble statues, dancing together, elegant pose, {marble_quality_enhanced}, classical art, museum, dramatic lighting, graceful movement, masterpiece",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, stiff, static",
                "width": 1024,
                "height": 1024,
                "strength": s_very_low
            },
            # 14. ✨ 新增: 接吻 - 浪漫亲吻
            {
                "name": "双人大理石_接吻",
                "prompt": f"a man and a woman couple turned into pure white marble statues, kissing, romantic kiss, intimate moment, {marble_quality_enhanced}, classical sculpture, museum, marble pedestal, dramatic lighting, passionate, masterpiece, heterosexual couple, love",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, ugly, distorted, inappropriate, explicit, same gender, two women, two men",
                "width": 1024,
                "height": 1024,
                "strength": s_extreme_low
            },
        ]
        
        self.results["single"] = scenes
        return scenes

    def export_config(self,
                      target_image: str,
                      model_path: str = "../models/sd-v1-5/aiiiiii01_v10.safetensors",
                      strength: float = None,
                      max_strength: float = None,
                      cfg: float = 7.5,
                      steps: int = 25,
                      output_file: str = None,
                      scene_count: int = 14) -> str:
        """
        导出为 marble_batch_config.json
        
        参数:
            target_image: 目标图片路径
            strength: 手动指定强度（如果为 None，则自动分析）
            max_strength: 手动指定最大强度
            cfg: CFG Scale
            steps: 推理步数
            output_file: 输出文件名
            scene_count: 场景数量 (6, 12, 或 14)
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.config_dir, f"marble_batch_config_{timestamp}.json")

        # 自动分析图片
        analysis = analyze_image(target_image)
        print(f"\n   📊 图片分析结果:")
        print(f"      类型: {analysis.get('type', 'unknown')}")
        print(f"      推荐强度: {analysis.get('strength', 0.25)}")
        print(f"      置信度: {analysis.get('confidence', 0):.0%}")
        
        # 如果用户指定了 strength，使用用户指定的值
        if strength is None:
            auto_strength = analysis.get("strength", 0.25)
            if analysis.get("type") == "portrait":
                auto_strength = 0.30
            elif analysis.get("type") == "full_body":
                auto_strength = 0.28
            elif analysis.get("type") == "seated_or_couple":
                auto_strength = 0.20
            elif analysis.get("type") == "wide_multi":
                auto_strength = 0.18
            strength = auto_strength
        
        if max_strength is None:
            max_strength = min(strength + 0.05, 0.40)

        print(f"\n   ⚙️  最终参数:")
        print(f"      strength: {strength}")
        print(f"      max_strength: {max_strength}")
        print(f"      cfg: {cfg}")
        print(f"      steps: {steps}")
        print(f"      scene_count: {scene_count}")

        # 生成场景配置
        self.generate_marble_scenes(target_image=target_image, base_strength=strength)

        # 根据 scene_count 选择场景
        all_scenes = self.results["single"]
        if scene_count == 6:
            # 只取前6个场景（原始版本）
            selected_scenes = all_scenes[:6]
        elif scene_count == 12:
            # 取前12个场景（不含躺姿+接吻）
            selected_scenes = all_scenes[:12]
        else:
            # 取全部14个场景
            selected_scenes = all_scenes

        # 构建完整配置
        config = {
            "model_path": model_path,
            "target_image": target_image,
            "output_dir": "./output/batch_marble",
            "strength": strength,
            "max_strength": max_strength,
            "cfg": cfg,
            "steps": steps,
            "scene_count": scene_count,
            "analysis": analysis,
            "jobs": selected_scenes
        }

        # 确保每个 job 都有 strength
        for job in config["jobs"]:
            if "strength" not in job:
                job["strength"] = strength

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 大理石配置已生成: {output_file}")
        print(f"   📊 共 {len(config['jobs'])} 个大理石雕像任务")
        
        # 打印各场景的强度分布
        strengths = {}
        for job in config["jobs"]:
            s = job.get("strength", strength)
            name = job.get("name", "unknown")
            strengths[name] = s
        
        print(f"   📋 各场景强度:")
        for name, s in strengths.items():
            print(f"      {name}: {s:.2f}")
        
        return output_file


def main():
    parser = argparse.ArgumentParser(
        description="大理石雕像 - 配置文件生成器 (完整版 - 14个场景)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 自动分析图片，生成14个场景（含躺姿+接吻）
  python gen_config_marble.py --target-image "output/good/photo.png"
  
  # 只生成12个场景（不含躺姿+接吻）
  python gen_config_marble.py --target-image "output/good/photo.png" --scenes 12
  
  # 只生成6个场景（原始版本）
  python gen_config_marble.py --target-image "output/good/photo.png" --scenes 6
  
  # 手动指定参数
  python gen_config_marble.py --target-image "output/good/photo.png" --strength 0.25 --cfg 8.0 --steps 30
  
  # 查看图片分析结果（不生成配置）
  python gen_config_marble.py --target-image "output/good/photo.png" --dry-run
        """
    )
    parser.add_argument("--target-image", type=str, required=True,
                        help="图生图目标图片路径")
    parser.add_argument("--output", type=str, default=None, 
                        help="输出文件名（默认自动生成）")
    parser.add_argument("--model", type=str,
                        default="../models/sd-v1-5/aiiiiii01_v10.safetensors",
                        help="基础模型路径")
    parser.add_argument("--strength", type=float, default=None,
                        help="重绘强度 (0.10-0.45)，不指定则自动分析")
    parser.add_argument("--max-strength", type=float, default=None,
                        help="最大强度限制，不指定则自动计算")
    parser.add_argument("--cfg", type=float, default=7.5,
                        help="CFG Scale (推荐 7.0-8.0)")
    parser.add_argument("--steps", type=int, default=25,
                        help="推理步数 (推荐 20-30)")
    parser.add_argument("--scenes", type=int, default=14, choices=[6, 12, 14],
                        help="场景数量: 6, 12, 或 14 (默认 14)")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅分析图片，不生成配置")

    args = parser.parse_args()

    if not os.path.exists(args.target_image):
        print(f"❌ 目标图片不存在: {args.target_image}")
        return

    # 如果是 dry-run，只分析图片
    if args.dry_run:
        print("\n🔍 图片分析模式")
        print("=" * 60)
        analysis = analyze_image(args.target_image)
        print(f"\n📊 分析结果:")
        print(f"   图片路径: {args.target_image}")
        print(f"   类型: {analysis.get('type', 'unknown')}")
        print(f"   推荐强度: {analysis.get('strength', 0.25)}")
        print(f"   置信度: {analysis.get('confidence', 0):.0%}")
        print("\n💡 运行以下命令生成配置:")
        print(f"   python gen_config_marble.py --target-image \"{args.target_image}\"")
        return

    # 生成配置
    generator = MarbleConfigGenerator()
    generator.export_config(
        target_image=args.target_image,
        model_path=args.model,
        strength=args.strength,
        max_strength=args.max_strength,
        cfg=args.cfg,
        steps=args.steps,
        output_file=args.output,
        scene_count=args.scenes
    )


if __name__ == "__main__":
    main()