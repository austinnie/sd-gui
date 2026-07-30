#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用生成器：根据提示词库自动出图（支持分层+扁平，全部生成）
用法：python generate.py <风格名称>
例如：python generate.py pure_serene

指定生成数量：
  python generate.py pure_serene_v2 -n 10
  python generate.py pure_serene_v2 --count 20
"""
import os
import sys
import time
import cv2
import numpy as np
import torch
import random
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

# 加载全局配置与提示词库
from config import SD_MODEL_PATH, STEPS, MAX_LIMIT, INPUT_IMAGE_NAME
from prompts_config import STYLE_PROMPTS

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== ⚙️ 安全开关 ====================
SAFE_MODE = True  
# 安全模式策略：
#   "simple" = 简单模式：在提示词后加 "wearing clothes"
#   "filter" = 过滤模式：移除露骨词汇 (nude, naked, explicit, pornographic, sex, hentai)
SAFE_MODE_STRATEGY = "filter"  # 可选: "simple" 或 "filter"


# 是否启用去水印
REMOVE_WATERMARK = True
# =======================================================

# ==================== 🛠️ 工具函数 ====================

def print_usage():
    """打印使用说明"""
    print("\n" + "="*60)
    print("📖 通用生成器使用说明")
    print("="*60)
    print("\n用法：")
    print("  python generate.py <风格名称>")
    print("  python generate.py <风格名称> -n <数量>")
    print("  python generate.py <风格名称> --count <数量>")
    print("\n示例：")
    print("  python generate.py pure_serene_v2              # 全部生成")
    print("  python generate.py pure_serene_v2 -n 10        # 生成10张")
    print("  python generate.py curvy_daily_v2 --count 20   # 生成20张")
    print("  python generate.py ancient_chinese_v2 -n 5     # 生成5张")
    print("\n其他命令：")
    print("  python generate.py --list     显示所有可用风格（分屏）")
    print("  python generate.py -l         显示所有可用风格（分屏）")
    print("\n💡 提示：")
    print("  - 确保输入图片放在 tools 目录下")
    print("  - 图片命名为 input.jpg 或 input.png")
    print("  - 生成图片保存在 tools/output/ 目录下")
    print("  - 去水印功能: " + ("✅ 已开启" if REMOVE_WATERMARK else "❌ 已关闭"))
    print("="*60)

def print_style_list():
    """分屏显示风格列表"""
    styles = list(STYLE_PROMPTS.keys())
    total = len(styles)
    
    print("\n" + "="*60)
    print(f"📋 当前支持的风格列表（共 {total} 个）")
    print("="*60)
    
    # 每页显示数量
    page_size = 20
    total_pages = (total + page_size - 1) // page_size
    
    for page in range(total_pages):
        start = page * page_size
        end = min(start + page_size, total)
        
        print(f"\n📄 第 {page+1}/{total_pages} 页")
        print("-"*40)
        
        for i in range(start, end):
            style_name = styles[i]
            folder_info = ""
            if style_name in STYLE_PROMPTS:
                folder = STYLE_PROMPTS[style_name].get("folder", "")
                if folder:
                    folder_info = f" -> {folder}"
            print(f"  {i+1:3d}. {style_name}{folder_info}")
        
        print("-"*40)
        print(f"显示 {end-start} 个，共 {total} 个风格")
        
        if page < total_pages - 1:
            input("\n按 Enter 继续查看下一页...")
    
    print("\n" + "="*60)
    print("💡 使用方式：python generate.py <风格名称> [-n <数量>]")
    print("="*60)

def find_input_image():
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = os.path.join(CURRENT_DIR, INPUT_IMAGE_NAME + ext)
        if os.path.exists(path):
            return path
    return None

# ==================== 去水印功能 ====================
def remove_watermark(image_path):
    """
    检测并去除图片水印
    返回: PIL Image 对象
    """
    if not REMOVE_WATERMARK:
        print("[系统] 去水印功能已关闭，直接使用原图")
        return Image.open(image_path).convert('RGB')
    
    print("\n[AI预处理] 检测并去除图片水印...")
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 检测白色/亮色区域（常见水印特征）
    _, mask = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    
    # 计算白色区域占比
    white_pixel_ratio = np.sum(mask > 0) / mask.size
    
    # 如果白色区域过少或过多，认为没有明显水印
    if white_pixel_ratio < 0.01 or white_pixel_ratio > 0.2:
        print("✅ 未检测到明显水印，继续生成。")
        return Image.open(image_path).convert('RGB')

    print("⚠️ 检测到水印，正在使用 OpenCV 修复去除...")
    result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    print("✅ 水印去除完成！")
    return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))

def setup_pipeline():
    print(f"\n[系统] 正在加载 AI 模型...")
    model_path = SD_MODEL_PATH

    pipe = StableDiffusionPipeline.from_single_file(
        model_path,
        torch_dtype=torch.float32,
        safety_checker=None,
        requires_safety_checker=False,
        use_safetensors=True
    )
    pipe.to("cpu")
    pipe.enable_vae_slicing()
    pipe.enable_attention_slicing()
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
    print("[系统] 模型加载完成！")
    return pipe

def build_prompt(config):
    """
    分层构建提示词
    支持两种格式：
    1. 分层格式：subjects + styles + moods
    2. 扁平格式：只有 subjects（兼容旧配置）
    """
    if "styles" in config and "moods" in config:
        subject = random.choice(config["subjects"])
        style = random.choice(config["styles"])
        mood = random.choice(config["moods"])
        prompt = f"{subject}, {style}, {mood}"
        return prompt, "分层"
    else:
        prompt = random.choice(config["subjects"])
        return prompt, "扁平"

def generate_style(pipe, init_image, prompt, output_filename, strength):
    w, h = init_image.size
    max_limit = MAX_LIMIT
    target_w, target_h = w, h
    if target_w > max_limit or target_h > max_limit:
        if target_w > target_h:
            scale = max_limit / target_w
        else:
            scale = max_limit / target_h
        target_w, target_h = int(target_w * scale), int(target_h * scale)
    target_w, target_h = ((target_w+31)//64)*64, ((target_h+31)//64)*64
    image = init_image.resize((target_w, target_h), Image.Resampling.LANCZOS)

    if SAFE_MODE:
        if SAFE_MODE_STRATEGY == "simple":
            # 简单模式：直接加 wearing clothes
            full_prompt = f"{prompt}, wearing clothes"
            print(f"🛡️ [安全模式] 策略: 简单 (附加 wearing clothes)")
        elif SAFE_MODE_STRATEGY == "filter":
            # 过滤模式：移除露骨词汇
            safe_prompt = prompt.replace("nude", "").replace("naked", "").replace("explicit", "").replace("pornographic", "")
            safe_prompt = ", ".join([p for p in safe_prompt.split(",") if "sex" not in p.lower() and "hentai" not in p.lower() and "penetration" not in p.lower()])
            # 清理多余的逗号和空格
            safe_prompt = ", ".join([p.strip() for p in safe_prompt.split(",") if p.strip()])
            full_prompt = safe_prompt if safe_prompt.strip() else prompt
            print(f"🛡️ [安全模式] 策略: 过滤 (移除露骨词汇)")
        else:
            # 默认：简单模式
            full_prompt = f"{prompt}, wearing clothes"
            print(f"🛡️ [安全模式] 策略: 默认 (附加 wearing clothes)")
        
        # 统一使用强化版负面提示词
        neg_prompt = (
            "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, logo, brand, "
            "bad hands, extra fingers, missing fingers, fused fingers, deformed hands, "
            "mutated hands, poorly drawn hands, six fingers, eleven fingers, "
            "bad anatomy, malformed limbs, extra limbs, missing limbs, "
            "bad proportions, disfigured, gross proportions, "
            "bad feet, extra toes, missing toes, fused toes"
        )
    else:
        full_prompt = prompt
        neg_prompt = (
            "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, logo, brand, "
            "bad hands, extra fingers, missing fingers, fused fingers, deformed hands, "
            "mutated hands, poorly drawn hands, six fingers, eleven fingers, "
            "bad anatomy, malformed limbs, extra limbs, missing limbs"
        )
        print(f"🔓 [自由模式已启用]")
        
    
    print(f"[生成] {os.path.basename(output_filename)} ({target_w}x{target_h})")
    print(f"  提示词: {full_prompt[:80]}...")
    
    generator = torch.Generator("cpu").manual_seed(int(time.time_ns() % 1000000000))
    
    result = pipe(
        prompt=full_prompt, 
        negative_prompt=neg_prompt, 
        image=image,
        strength=strength, 
        num_inference_steps=STEPS, 
        guidance_scale=7.5,
        generator=generator, 
        width=target_w, 
        height=target_h
    )
    result.images[0].save(output_filename, quality=95)

# ==================== 🚀 主入口 ====================

def parse_arguments(args):
    """
    解析命令行参数
    返回: (target_style, count)
    """
    target_style = None
    count = None
    
    i = 1
    while i < len(args):
        arg = args[i]
        if arg in ["-n", "--count"]:
            if i + 1 < len(args):
                try:
                    count = int(args[i + 1])
                    if count <= 0:
                        print(f"❌ 数量必须大于0，当前: {count}")
                        sys.exit(1)
                    i += 2
                except ValueError:
                    print(f"❌ 无效的数字: {args[i + 1]}")
                    sys.exit(1)
            else:
                print(f"❌ 参数 {arg} 需要指定数量")
                sys.exit(1)
        else:
            target_style = arg
            i += 1
    
    return target_style, count

def main():
    # ========== 处理无参数情况 ==========
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)
    
    # ========== 处理 --list 或 -l ==========
    if sys.argv[1] == "--list" or sys.argv[1] == "-l":
        print_style_list()
        sys.exit(0)
    
    # ========== 解析参数 ==========
    target_style, user_count = parse_arguments(sys.argv)
    
    if target_style is None:
        print("❌ 请指定风格名称")
        print_usage()
        sys.exit(1)
    
    if target_style not in STYLE_PROMPTS:
        print(f"\n❌ 错误：找不到风格 '{target_style}'！")
        print("📋 可用风格列表：")
        styles = list(STYLE_PROMPTS.keys())
        for i, key in enumerate(styles[:10]):
            print(f"   - {key}")
        if len(styles) > 10:
            print(f"   ... 共 {len(styles)} 个风格")
        print("\n💡 使用 python generate.py --list 查看完整列表")
        sys.exit(1)

    # ========== 只有确认有有效风格后才加载模型 ==========
    input_path = find_input_image()
    if not input_path:
        print(f"\n❌ 没找到图片！请把图片命名为 {INPUT_IMAGE_NAME}.jpg/.png 放在 tools 目录下！")
        return

    # ========== 去水印处理 ==========
    init_image = remove_watermark(input_path)

    # ========== 加载模型 ==========
    pipe = setup_pipeline()

    config = STYLE_PROMPTS[target_style]
    
    # ========== 计算生成数量 ==========
    # 检查是分层还是扁平
    if "styles" in config and "moods" in config:
        mode = "分层"
        total_possible = len(config["subjects"]) * len(config["styles"]) * len(config["moods"])
        default_count = len(config["subjects"])
        combo_info = f" ({len(config['subjects'])}×{len(config['styles'])}×{len(config['moods'])}={total_possible}种组合)"
    else:
        mode = "扁平"
        total_possible = len(config["subjects"])
        default_count = len(config["subjects"])
        combo_info = ""
    
    # 确定实际生成数量
    if user_count is not None:
        # 用户指定了数量
        total_count = user_count
        count_source = f"用户指定"
        # 如果用户指定的数量超过总组合数，给出提示
        if user_count > total_possible:
            print(f"\n⚠️ 提示：您指定生成 {user_count} 张，但该风格最多只有 {total_possible} 种不同组合")
            print(f"   将生成 {total_possible} 张（全部组合）")
            total_count = total_possible
    else:
        # 默认：全部生成（subjects数量）
        total_count = default_count
        count_source = "全部提示词"
    
    print(f"\n🎯 正在生成风格: {target_style} -> {config['folder']}")
    print(f"📊 模式: {mode}{combo_info}")
    print(f"📊 本次共生成 {total_count} 张图片（{count_source}）")
    if mode == "分层":
        print(f"   ├─ 主体: {len(config['subjects'])} 种")
        print(f"   ├─ 风格: {len(config['styles'])} 种")
        print(f"   └─ 情绪: {len(config['moods'])} 种")
    if user_count and user_count > total_possible:
        print(f"   └─ ⚠️ 注: 实际生成 {total_possible} 张（全部组合）")
    elif user_count:
        print(f"   └─ 💡 注: 从 {total_possible} 种组合中随机选 {total_count} 张")
    # =================================

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_root = os.path.join(CURRENT_DIR, "output", f"{config['folder']}_{timestamp}")
    os.makedirs(output_root, exist_ok=True)

    # ========== 生成循环 ==========
    for i in range(total_count):
        prompt, mode_used = build_prompt(config)
        
        print(f"\n🔄 进度：第 {i+1}/{total_count} 张 [{mode_used}]")
        
        generate_style(
            pipe, 
            init_image, 
            prompt, 
            os.path.join(output_root, f"{i+1:02d}.png"), 
            config["strength"]
        )
    # =================================

    print(f"\n✅ 全部完成！共 {total_count} 张图片，保存在: {output_root}")

if __name__ == "__main__":
    main()