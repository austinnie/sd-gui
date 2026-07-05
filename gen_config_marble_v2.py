#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大理石雕像专用 - 配置文件生成器 (完整版 - 14个场景)
支持自动分析图片特征，推荐最佳参数
支持自动检测性别
"""

import sys
import io

# ✅ 强制 stdout 使用 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    
import sys
import os
import json
import argparse
from datetime import datetime
from PIL import Image

# ==================== 统一缓存目录 ====================
CACHE_ROOT = r"E:\hf_cache\.cache"
os.environ['DEEPFACE_HOME'] = os.path.join(CACHE_ROOT, "deepface")
os.makedirs(os.environ['DEEPFACE_HOME'], exist_ok=True)

# 尝试导入 deepface（可选）
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
    print(f"✅ deepface 已加载，缓存目录: {os.environ['DEEPFACE_HOME']}")
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("⚠️ deepface 未安装，性别检测将使用默认值")
    print("   安装: pip install deepface")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def detect_gender(image_path):
    """
    自动检测图片中人物的性别
    
    返回:
        "male" 或 "female"
    """
    if not DEEPFACE_AVAILABLE:
        return "female"
    
    try:
        result = DeepFace.analyze(
            img_path=image_path, 
            actions=['gender'], 
            enforce_detection=False  # 即使检测不到人脸也返回结果
        )
        
        # DeepFace 可能返回列表或字典
        if isinstance(result, list):
            result = result[0]
        
        gender = result.get('gender', {})
        if isinstance(gender, dict):
            man_score = gender.get('Man', 0)
            woman_score = gender.get('Woman', 0)
            detected = 'male' if man_score > woman_score else 'female'
            print(f"   🧑 性别检测: {detected} (Man: {man_score:.1%}, Woman: {woman_score:.1%})")
            return detected
        else:
            return "female"
            
    except Exception as e:
        print(f"   ⚠️ 性别检测失败: {e}，默认使用 female")
        return "female"


def analyze_image(image_path):
    """
    自动分析图片特征，推荐最佳参数
    
    返回:
        dict: {
            "strength": 推荐强度,
            "max_strength": 推荐最大强度,
            "type": 图片类型,
            "gender": 检测到的性别,
            "confidence": 置信度
        }
    """
    result = {
        "strength": 0.25,
        "max_strength": 0.30,
        "type": "unknown",
        "gender": "female",
        "confidence": 0.0
    }
    
    try:
        # 1. 检测性别
        result["gender"] = detect_gender(image_path)
        
        # 2. 分析宽高比
        img = Image.open(image_path)
        w, h = img.size
        aspect_ratio = w / h
        
        if aspect_ratio > 1.3:
            if aspect_ratio > 1.8:
                result.update({
                    "strength": 0.18,
                    "max_strength": 0.25,
                    "type": "wide_multi",
                    "confidence": 0.7
                })
            else:
                result.update({
                    "strength": 0.22,
                    "max_strength": 0.28,
                    "type": "wide",
                    "confidence": 0.6
                })
        elif aspect_ratio < 0.75:
            if aspect_ratio < 0.6:
                result.update({
                    "strength": 0.25,
                    "max_strength": 0.30,
                    "type": "full_body",
                    "confidence": 0.7
                })
            else:
                result.update({
                    "strength": 0.30,
                    "max_strength": 0.35,
                    "type": "portrait",
                    "confidence": 0.75
                })
        else:
            if 0.9 < aspect_ratio < 1.1:
                result.update({
                    "strength": 0.20,
                    "max_strength": 0.25,
                    "type": "seated_or_couple",
                    "confidence": 0.6
                })
            else:
                result.update({
                    "strength": 0.25,
                    "max_strength": 0.30,
                    "type": "medium",
                    "confidence": 0.5
                })
                
    except Exception as e:
        print(f"   ⚠️ 图片分析失败: {e}，使用默认参数")
    
    return result


class MarbleConfigGenerator:
    """大理石雕像专用配置生成器"""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(__file__), "output", "configs")
        os.makedirs(self.config_dir, exist_ok=True)
        self.results = {"single": [], "couple": []}

    # ===== 【新增】在这里添加精简函数 =====
    def _shorten_for_clip(self, text, max_len=300):
        """
        精简提示词以适应 CLIP 77 token 限制
        按逗号分割，去重，优先保留重要的词
        
        参数:
            text: 原始提示词
            max_len: 最大字符长度 (建议 300)
        
        返回:
            精简后的提示词
        """
        if not text or len(text) <= max_len:
            return text
        
        # 按逗号分割
        parts = [p.strip() for p in text.split(',') if p.strip()]
        
        # 去重
        seen = set()
        unique_parts = []
        for p in parts:
            if p not in seen:
                seen.add(p)
                unique_parts.append(p)
        
        # 按长度排序（长的更具体，优先保留）
        unique_parts.sort(key=lambda x: len(x), reverse=True)
        
        # 构建结果，限制长度
        result = []
        current_len = 0
        for part in unique_parts:
            add_len = len(part) + 2  # +2 for ", "
            if current_len + add_len <= max_len:
                result.append(part)
                current_len += add_len
            else:
                # 如果当前部分太长，尝试截断
                remaining = max_len - current_len
                if remaining > 10:
                    # 取前几个词
                    words = part.split()
                    truncated = ' '.join(words[:remaining // 10])
                    if truncated and len(truncated) > 5:
                        result.append(truncated + "...")
                break
        
        shortened = ', '.join(result)
        if len(shortened) < len(text):
            print(f"   ✂️ 提示词已精简: {len(text)} -> {len(shortened)} 字符")
        
        return shortened if result else text[:max_len]
    
    def _count_tokens(self, text):
        """粗略计算 token 数（CLIP 约 1-2 token/词）"""
        if not text:
            return 0
        # 每个词约 1-2 token，加 2 个特殊 token
        return len(text.split()) + 2
        
    def generate_marble_scenes(self, target_image=None, target_gender="auto", base_strength=0.25):
        """
        生成大理石雕像场景配置 - 14个场景（含躺姿+接吻）
        
        参数:
            target_image: 目标图片路径（用于自动分析）
            target_gender: 性别 ("male", "female", "auto")
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
                "gender": "female",
                "confidence": 0.0
            }
        
        # ✅ 确定性别
        if target_gender == "auto":
            detected_gender = analysis.get("gender", "female")
        else:
            detected_gender = target_gender
        
        print(f"   🧑 最终使用性别: {detected_gender}")
        
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
        
        # ✅ 根据性别生成提示词
        if detected_gender == "male":
            base_prompt = "a man turned into a flawless pure white marble statue, full body, full length, entire figure, same man, same face, same body shape, same pose, same composition, masculine"
            gender_negative = "woman, female, feminine, breasts, curvy, soft features, girly"
            pronoun = "he"
        else:
            base_prompt = "a beautiful woman turned into a flawless pure white marble statue, full body, full length, entire figure, same woman, same face, same features, feminine figure, elegant pose"
            gender_negative = "man, male, masculine, beard, mustache, muscular, broad shoulders, masculine features, bodybuilder"
            pronoun = "she"
        
        marble_quality = "pure white marble, flawless stone, no color, monochrome white, classical sculpture, highly detailed stone texture, matte finish, no shine, 8k, photorealistic, masterpiece"
        marble_quality_enhanced = "pure white marble, flawless stone, no color, monochrome white, classical sculpture, intricate carving details, smooth stone texture, matte finish, no shine, 8k, photorealistic, masterpiece, high contrast, dramatic shadows"
        
        # 公共 negative 词
        neg_common = "worst quality, low quality, deformed, blurry, ugly"
        neg_no_color = "color, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, colored, warm tones, beige, yellow, gray"
        neg_no_skin = "skin, flesh, clothes, fabric"
        neg_no_shadow = "shadow, dark, underexposed"
        neg_multi = "messy, cluttered, chaotic"
        neg_crop = "cropped, partial, close-up, face only, head only"  # ✅ 新增：防止只生成头像
        
        scenes = [
            # ==================== 单人场景 (9个) ====================
            {
                "name": "单人大理石_展厅",
                "prompt": f"{base_prompt}, {marble_quality}, museum gallery, soft lighting, marble pedestal, white background",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_crop},{gender_negative}",
                "width": 768,
                "height": 1024,
                "strength": s_high
            },
            {
                "name": "单人大理石_宫殿",
                "prompt": f"{base_prompt}, {marble_quality}, grand classical palace, ornate columns, marble floor, dramatic spotlight, chandelier",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow},{neg_crop}, {gender_negative}",
                "width": 1024,
                "height": 768,
                "strength": s_high - 0.02
            },
            {
                "name": "单人大理石_坐姿",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, sitting on marble throne, classical Greek sculpture, museum, regal pose",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, {neg_crop},{gender_negative}",
                "width": 1024,
                "height": 1024,
                "strength": s_low
            },
            {
                "name": "单人大理石_侧身",
                "prompt": f"{base_prompt}, {marble_quality}, side profile, elegant pose, classical art, marble pedestal, profile view",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, front view,{neg_crop}, {gender_negative}",
                "width": 768,
                "height": 1024,
                "strength": s_low + 0.03
            },
            {
                "name": "单人大理石_全身",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, full body standing, heroic pose, classical sculpture, museum gallery, marble pedestal",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, cropped, partial, {neg_crop},{gender_negative}",
                "width": 768,
                "height": 1024,
                "strength": s_low
            },
            {
                "name": "单人大理石_半身特写",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, bust sculpture, close-up, detailed face, classical art, museum display, white marble",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_crop},{gender_negative}",
                "width": 768,
                "height": 1024,
                "strength": s_high
            },
            {
                "name": "单人大理石_花园",
                "prompt": f"{base_prompt}, {marble_quality}, classical garden setting, ancient ruins, ivy, soft sunlight, marble pedestal, outdoor sculpture",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, overgrown, moss, {neg_crop},{gender_negative}",
                "width": 1024,
                "height": 768,
                "strength": s_high - 0.02
            },
            {
                "name": "单人大理石_动态",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, dynamic pose, movement, classical sculpture, museum, dramatic lighting, action",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, static, stiff, {neg_crop},{gender_negative}",
                "width": 1024,
                "height": 1024,
                "strength": s_low
            },
            {
                "name": "单人大理石_躺姿",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, lying down, reclining pose, sleeping beauty, classical sculpture, marble bed, museum, peaceful expression, elegant drapery, soft lighting",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, standing, sitting, upright, {neg_crop},{gender_negative}",
                "width": 1024,
                "height": 768,
                "strength": s_very_low
            },

            # ==================== 双人场景 (5个) ====================
            {
                "name": "双人大理石_拥抱",
                "prompt": f"a man and a woman couple turned into flawless pure white marble statues, intimate embrace, {marble_quality_enhanced}, romantic pose, museum hall, marble pedestal, dramatic lighting, masterpiece, heterosexual couple",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi},{neg_crop}, same gender, two women, two men, lesbian, gay",
                "width": 1024,
                "height": 1024,
                "strength": s_very_low
            },
            {
                "name": "双人大理石_深情对视",
                "prompt": f"a man and a woman couple turned into pure white marble statues, holding hands, looking at each other, {marble_quality_enhanced}, classical art, palace exhibition, glowing light, high detail, romantic atmosphere, heterosexual couple",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, {neg_crop},same gender, two women, two men, lesbian, gay",
                "width": 1024,
                "height": 768,
                "strength": s_very_low
            },
            {
                "name": "双人大理石_并肩",
                "prompt": f"a man and a woman couple turned into pure white marble statues, standing side by side, {marble_quality_enhanced}, classical sculpture, museum gallery, marble pedestals, elegant, formal, heterosexual couple",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, {neg_crop},same gender, two women, two men, lesbian, gay",
                "width": 1024,
                "height": 768,
                "strength": s_very_low + 0.02
            },
            {
                "name": "双人大理石_舞蹈",
                "prompt": f"a man and a woman couple turned into pure white marble statues, dancing together, elegant pose, {marble_quality_enhanced}, classical art, museum, dramatic lighting, graceful movement, masterpiece, heterosexual couple",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, stiff, static, {neg_crop},same gender, two women, two men, lesbian, gay",
                "width": 1024,
                "height": 1024,
                "strength": s_very_low
            },
            {
                "name": "双人大理石_接吻",
                "prompt": f"a man and a woman couple turned into pure white marble statues, kissing, romantic kiss, intimate moment, {marble_quality_enhanced}, classical sculpture, museum, marble pedestal, dramatic lighting, passionate, masterpiece, heterosexual couple, love",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, {neg_crop},ugly, distorted, inappropriate, explicit, same gender, two women, two men, lesbian, gay",
                "width": 1024,
                "height": 1024,
                "strength": s_extreme_low
            },
        ]

        # ===== 【新增】在这里精简所有场景的提示词 =====
        for scene in scenes:
            if "prompt" in scene:
                scene["prompt"] = self._shorten_for_clip(scene["prompt"], max_len=300)
                # 检查 token 数并打印警告
                token_count = self._count_tokens(scene["prompt"])
                if token_count > 75:
                    print(f"   ⚠️ {scene['name']} token 数: {token_count}，可能被截断")
            
            if "negative" in scene:
                scene["negative"] = self._shorten_for_clip(scene["negative"], max_len=250)
            
        self.results["single"] = scenes
        return scenes

    def export_config(self,
                      target_image: str,
                      model_path: str = "../models/sd-v1-5/aiiiiii01_v10.safetensors",
                      strength: float = None,
                      max_strength: float = None,
                      gender: str = "auto",
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
            gender: 性别 ("male", "female", "auto")
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
        print(f"      性别: {analysis.get('gender', 'unknown')}")
        print(f"      推荐强度: {analysis.get('strength', 0.25)}")
        print(f"      置信度: {analysis.get('confidence', 0):.0%}")
        
        # 确定性别
        if gender == "auto":
            detected_gender = analysis.get("gender", "female")
        else:
            detected_gender = gender
        print(f"   🧑 最终使用性别: {detected_gender}")
        
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
        print(f"      gender: {detected_gender}")
        print(f"      cfg: {cfg}")
        print(f"      steps: {steps}")
        print(f"      scene_count: {scene_count}")

        # 生成场景配置（传入检测到的性别）
        self.generate_marble_scenes(
            target_image=target_image, 
            target_gender=detected_gender,
            base_strength=strength
        )

        # 根据 scene_count 选择场景
        all_scenes = self.results["single"]
        if scene_count == 6:
            selected_scenes = all_scenes[:6]
        elif scene_count == 12:
            selected_scenes = all_scenes[:12]
        else:
            selected_scenes = all_scenes

        # 构建完整配置
        config = {
            "model_path": model_path,
            "target_image": target_image,
            "output_dir": "./output/batch_marble",
            "strength": strength,
            "max_strength": max_strength,
            "gender": detected_gender,
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
  # 自动检测性别，生成14个场景
  python gen_config_marble.py --target-image "output/good/photo.png"
  
  # 手动指定性别（覆盖自动检测）
  python gen_config_marble.py --target-image "output/good/photo.png" --gender male
  
  # 只生成12个场景
  python gen_config_marble.py --target-image "output/good/photo.png" --scenes 12
  
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
    parser.add_argument("--gender", type=str, default="auto", choices=["auto", "male", "female"],
                        help="性别: auto(自动检测), male, female (默认 auto)")
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
        print(f"   性别: {analysis.get('gender', 'unknown')}")
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
        gender=args.gender,
        cfg=args.cfg,
        steps=args.steps,
        output_file=args.output,
        scene_count=args.scenes
    )


if __name__ == "__main__":
    main()