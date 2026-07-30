#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能生成器（分层版）：根据分层提示词自动出图
用法：python to_smart_generate_for_wechat_v2.py
      python to_smart_generate_for_wechat_v2.py -n 10
      python to_smart_generate_for_wechat_v2.py --count 20
"""
import os
import sys
import cv2
import numpy as np
import torch
import time
import random
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

# ==================== 基础配置 ====================
from config import SD_MODEL_PATH, STEPS, MAX_LIMIT, INPUT_IMAGE_NAME, DEFAULT_STRENGTH

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 选择模型 (1, 2, 或 3)
ACTIVE_MODEL = 1  

# 模型路径配置
SD_MODEL_PATH_1 = "../models/sd-v1-5/anytimeRealistic_v10.safetensors"
SD_MODEL_PATH_2 = "../models/sd-v1-5/henmixreal_v10_henmixrealV10.safetensors"
SD_MODEL_PATH_3 = "../models/sd-v1-5/sd-v1-5-tiny.safetensors"

# ==================== 🎯 分层提示词配置 ====================
# 三层结构：主体(Subjects) + 风格(Styles) + 情绪(Moods)
# 所有分类共用这套分层配置

# ========== 第一层：主体 (不同分类共用) ==========
SUBJECTS = {
    "美女": [
        "a beautiful woman, elegant and serene",
        "an elegant girl, refined beauty",
        "a graceful lady, standing gracefully",
        "a stunning female, sitting peacefully",
        "a charming goddess, pure and ethereal",
        "a serene maiden, sitting elegantly",
        "a beautiful young woman, soft natural beauty",
        "an ethereal goddess, flowing white dress",
    ],
    "风景": [
        "mountain and river, breathtaking view",
        "forest and lake, peaceful nature",
        "sunset valley, golden landscape",
        "winter snowscape, pure white silence",
        "crystal ocean, endless blue horizon",
        "starry night, cosmic beauty",
        "misty morning, foggy valley",
        "golden desert, vast sand dunes",
    ],
    "动物": [
        "a majestic tiger, powerful and fierce",
        "a graceful deer, gentle and wild",
        "a soaring eagle, freedom in the sky",
        "a mystical fox, clever and mysterious",
        "a white wolf, majestic and loyal",
        "a colorful parrot, vibrant and tropical",
        "a wise owl, ancient and watchful",
        "a playful dolphin, joyful and intelligent",
    ],
    "建筑": [
        "ancient temple, historical and sacred",
        "modern skyscraper, futuristic and sleek",
        "medieval castle, majestic and fortified",
        "futuristic city, advanced and dynamic",
        "glass bridge, transparent and daring",
        "oriental pagoda, elegant and traditional",
        "roman colosseum, ancient and monumental",
        "gothic cathedral, dark and magnificent",
    ],
    "雕塑": [
        "classical Greek statue, perfect proportions",
        "ancient Chinese terracotta, historical army",
        "Renaissance sculpture, artistic mastery",
        "golden Buddha, serene and sacred",
        "marble bust, elegant and refined",
        "bronze warrior, heroic and powerful",
        "abstract modern sculpture, creative and bold",
        "wooden carving, organic and intricate",
    ],
    "科幻": [
        "a cyberpunk warrior, neon armor",
        "a space explorer, futuristic suit",
        "an alien being, mysterious and strange",
        "a robotic humanoid, sleek and metallic",
    ],    
}

# ========== 第二层：风格 (所有分类共用) ==========
STYLES = [
    "breathtaking scene, majestic atmosphere",
    "cinematic lighting, dramatic shadows",
    "magical atmosphere, enchanting glow",
    "golden hour, warm rich light",
    "moody sky, dramatic clouds",
    "ethereal vibe, dreamy and soft",
    "soft natural lighting, gentle and warm",
    "dramatic chiaroscuro, high contrast",
    "misty morning, soft fog",
    "vibrant sunset, fiery colors",
]

# ========== 第三层：情绪 (所有分类共用) ==========
MOODS = [
    "peaceful and serene",
    "romantic and dreamy",
    "mysterious and enchanting",
    "grand and epic",
    "intimate and personal",
    "joyful and vibrant",
    "melancholic and thoughtful",
    "powerful and commanding",
    "soft and gentle",
    "ethereal and transcendent",
]

# ========== 分类权重/参数 ==========
CATEGORIES = [
    ("1_每日壁纸_日常", 0.40, "daily"),
    ("2_每日壁纸_古风", 0.45, "ancient"),
    ("3_每日壁纸_艺术", 0.50, "gallery"),
    ("4_每日壁纸_科幻", 0.45, "sci-fi"), 
]

# 默认每种类型生成数量 (总数量 = GEN_COUNT * len(CATEGORIES))
GEN_COUNT = 4

# ==================== 根据配置选择模型 ====================
if ACTIVE_MODEL == 1:
    SD_MODEL_PATH = SD_MODEL_PATH_1
    print(f"✅ 当前使用模型: 1 (写实/真实)")
elif ACTIVE_MODEL == 2:
    SD_MODEL_PATH = SD_MODEL_PATH_2
    print(f"✅ 当前使用模型: 2 (写真写实/唯美)")
elif ACTIVE_MODEL == 3:
    SD_MODEL_PATH = SD_MODEL_PATH_3
    print(f"✅ 当前使用模型: 3 (轻量快速)")
else:
    SD_MODEL_PATH = SD_MODEL_PATH_1
    print(f"⚠️ ACTIVE_MODEL 设置无效，默认使用模型 1")


# ==================== 命令行参数解析 ====================
def print_usage():
    """打印使用说明"""
    print("\n" + "="*60)
    print("📖 智能生成器（分层版）使用说明")
    print("="*60)
    print("\n用法：")
    print("  python to_smart_generate_for_wechat_v2.py")
    print("  python to_smart_generate_for_wechat_v2.py -n <数量>")
    print("  python to_smart_generate_for_wechat_v2.py --count <数量>")
    print("\n示例：")
    print("  python to_smart_generate_for_wechat_v2.py           # 默认生成 4×4=16张")
    print("  python to_smart_generate_for_wechat_v2.py -n 10     # 每种类型生成10张")
    print("  python to_smart_generate_for_wechat_v2.py --count 3 # 每种类型生成3张")
    print("\n💡 提示：")
    print(f"  - 当前配置: {len(CATEGORIES)} 个分类")
    print(f"  - 总张数 = 每类张数 × {len(CATEGORIES)}")
    print("  - 确保输入图片放在 tools 目录下")
    print("  - 图片命名为 input.jpg 或 input.png")
    print("="*60)

def parse_arguments(args):
    """
    解析命令行参数
    返回: (gen_count, show_help)
    """
    gen_count = None
    show_help = False
    
    i = 1
    while i < len(args):
        arg = args[i]
        if arg in ["-h", "--help"]:
            show_help = True
            i += 1
        elif arg in ["-n", "--count"]:
            if i + 1 < len(args):
                try:
                    gen_count = int(args[i + 1])
                    if gen_count <= 0:
                        print(f"❌ 数量必须大于0，当前: {gen_count}")
                        sys.exit(1)
                    i += 2
                except ValueError:
                    print(f"❌ 无效的数字: {args[i + 1]}")
                    sys.exit(1)
            else:
                print(f"❌ 参数 {arg} 需要指定数量")
                sys.exit(1)
        else:
            # 未知参数
            print(f"❌ 未知参数: {arg}")
            print_usage()
            sys.exit(1)
    
    return gen_count, show_help


# ==================== 工具函数 ====================
def find_input_image(base_name):
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = os.path.join(CURRENT_DIR, base_name + ext)
        if os.path.exists(path):
            print(f"✅ 找到输入图片: {path}")
            return path
    return None

def check_and_remove_watermark(image_path):
    print("\n[AI预处理] 检测并去除图片水印...")
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    white_pixel_ratio = np.sum(mask > 0) / mask.size
    if white_pixel_ratio < 0.01 or white_pixel_ratio > 0.2:
        print("✅ 未检测到明显水印，继续生成。")
        return Image.open(image_path).convert('RGB')

    print("⚠️ 检测到水印，正在使用 OpenCV 修复去除...")
    result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    print("✅ 水印去除完成！")
    return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))

def build_layer_prompts(target_type, count):
    """
    分层构建提示词
    从 SUBJECTS[target_type] 随机选主体
    从 STYLES 随机选风格
    从 MOODS 随机选情绪
    """
    prompts = []
    
    # 获取该类型的主体列表
    if target_type not in SUBJECTS:
        print(f"⚠️ 未知类型 '{target_type}'，使用默认主体")
        subjects = SUBJECTS["美女"]  # 默认用"美女"
    else:
        subjects = SUBJECTS[target_type]
    
    for i in range(count):
        subject = random.choice(subjects)
        style = random.choice(STYLES)
        mood = random.choice(MOODS)
        prompt = f"{subject}, {style}, {mood}"
        prompts.append(prompt)
    
    return prompts

def setup_pipeline():
    print(f"\n[系统] 正在加载 AI 模型...")
    pipe = StableDiffusionPipeline.from_single_file(
        SD_MODEL_PATH,
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

def generate_style(pipe, init_image, prompt, output_filename, strength=0.45):
    original_w, original_h = init_image.size
    
    max_limit = MAX_LIMIT 
    target_w, target_h = original_w, original_h
    if target_w > max_limit or target_h > max_limit:
        if target_w > target_h:
            scale = max_limit / target_w
        else:
            scale = max_limit / target_h
        target_w = int(target_w * scale)
        target_h = int(target_h * scale)
        print(f"  📐 缩放图片到 {target_w}x{target_h} 以内")
    
    target_w = ((target_w + 31) // 64) * 64
    target_h = ((target_h + 31) // 64) * 64
    
    if original_w != target_w or original_h != target_h:
        image = init_image.resize((target_w, target_h), Image.Resampling.LANCZOS)
    else:
        image = init_image

    full_prompt = f"masterpiece, best quality, photorealistic, highly detailed, {prompt}"
    negative_prompt = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, logo, brand"

    print(f"[生成] {os.path.basename(output_filename)} ({target_w}x{target_h})")
    print(f"  提示词: {full_prompt[:80]}...")
    
    random_seed = int(time.time_ns() % 1000000000)
    generator = torch.Generator("cpu").manual_seed(random_seed)
    
    result = pipe(
        prompt=full_prompt,
        negative_prompt=negative_prompt,
        image=image,
        strength=strength,
        num_inference_steps=STEPS,
        guidance_scale=7.5,
        generator=generator,
        width=target_w,
        height=target_h,
    )
    result.images[0].save(output_filename, quality=95)

def main():
    # ==================== 处理命令行参数 ====================
    # 如果无参数，使用默认配置
    if len(sys.argv) < 2:
        gen_count = GEN_COUNT  # 使用默认值
    else:
        # 解析参数
        if sys.argv[1] in ["-h", "--help"]:
            print_usage()
            sys.exit(0)
        
        gen_count, show_help = parse_arguments(sys.argv)
        
        if show_help:
            print_usage()
            sys.exit(0)
        
        if gen_count is None:
            gen_count = GEN_COUNT  # 使用默认值
    
    # ==================== 主流程 ====================
    # 1. 查找输入图片
    input_path = find_input_image(INPUT_IMAGE_NAME)
    if not input_path:
        print(f"❌ 找不到输入图片，请将图片命名为 '{INPUT_IMAGE_NAME}.jpg' 或 '{INPUT_IMAGE_NAME}.png' 放在 tools 目录下！")
        return

    # 2. 去除水印
    init_image = check_and_remove_watermark(input_path)

    # 3. 加载模型
    pipe = setup_pipeline()

    # 4. 显示配置信息
    print(f"\n🎯 当前使用模型: {ACTIVE_MODEL}")
    print(f"📊 主体库: {len(SUBJECTS)} 个分类")
    print(f"📊 可用风格: {len(STYLES)} 种")
    print(f"📊 可用情绪: {len(MOODS)} 种")
    print(f"📊 每种类型生成: {gen_count} 张")
    print(f"📊 分类数量: {len(CATEGORIES)} 个")
    print(f"📊 总计生成: {gen_count * len(CATEGORIES)} 张")

    # 5. 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_root = os.path.join(CURRENT_DIR, "output", "wechat", f"分层_批量_{timestamp}")
    os.makedirs(output_root, exist_ok=True)

    # 6. 循环生成（分层模式）
    for i in range(gen_count):
        print(f"\n{'='*40}")
        print(f"📄 生成第 {i+1} 张 / 共 {gen_count} 张")
        print('='*40)

        for folder_name, strength, category_key in CATEGORIES:
            print(f"\n📁 生成类别: {folder_name}")
            d = os.path.join(output_root, folder_name)
            os.makedirs(d, exist_ok=True)
            
            # 每次重新生成提示词（随机组合）
            prompt_text = build_layer_prompts(category_key, 1)[0]
            filename = f"{i+1:02d}.png"
            generate_style(pipe, init_image, prompt_text, os.path.join(d, filename), strength=strength)

    print("\n" + "="*50)
    print(f"✅ 全部完成！总共生成 {gen_count * len(CATEGORIES)} 张图片！")
    print(f"📂 保存位置：\n   {output_root}")
    print("="*50)

if __name__ == "__main__":
    main()