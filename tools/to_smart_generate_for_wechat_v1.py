#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能生成器：根据提示词库自动出图
用法：python to_smart_generate_for_wechat.py
"""
import os
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

# 当前目录 (tools)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 选择模型 (1, 2, 或 3)
ACTIVE_MODEL = 1  

# 模型路径配置
SD_MODEL_PATH_1 = "../models/sd-v1-5/anytimeRealistic_v10.safetensors"      # 写实/真实
SD_MODEL_PATH_2 = "../models/sd-v1-5/henmixreal_v10_henmixrealV10.safetensors" # 写真写实/唯美
SD_MODEL_PATH_3 = "../models/sd-v1-5/sd-v1-5-tiny.safetensors"              # 轻量快速

# 生成类型 (美女 / 风景 / 动物 / 建筑 / 雕塑)
TARGET_TYPE = "美女"  

# 每种类型生成数量 (总数量 = GEN_COUNT * 3)
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
    
# ==================== 工具函数 ====================
def find_input_image(base_name):
    """在 CURRENT_DIR (tools目录) 查找输入图片"""
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = os.path.join(CURRENT_DIR, base_name + ext)
        if os.path.exists(path):
            print(f"✅ 找到输入图片: {path}")
            return path
    return None

# ==================== 水印去除 ====================
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

# ==================== 生成提示词 ====================
def build_prompts():
    """根据 TARGET_TYPE 生成指定数量的提示词"""
    
    base_style = {
        "daily": ["breathtaking scene", "cinematic lighting", "magical atmosphere", "golden hour", "moody sky", "ethereal vibe"],
        "ancient": ["traditional Chinese", "ancient oriental", "classical beauty", "Han dynasty", "Tang dynasty", "Zen garden"],
        "gallery": ["museum piece", "fine art", "artistic masterpiece", "surreal", "Renaissance style", "minimalist"]
    }

    prompts_engine = {}

    for category in ["daily", "ancient", "gallery"]:
        prompts_engine[category] = []
        base_words = base_style[category]
        target = TARGET_TYPE

        if target == "美女":
            subjects = [
                "a beautiful woman, elegant and serene, hands resting naturally on lap, sitting elegantly",
                "an elegant girl, refined beauty, gentle smile, hand lightly touching face, thoughtful expression",
                "a graceful lady, standing gracefully, arms relaxed at sides, soft expression",
                "a stunning female, sitting peacefully, hands clasped gently together, delicate beauty",
                "a charming goddess, pure and ethereal, elegant pose, focusing on upper body and face",
                "a serene maiden, sitting elegantly, soft features, holding a small flower stem gently"
            ]
        elif target == "风景":
            subjects = ["mountain and river", "forest and lake", "sunset valley", "winter snowscape", "crystal ocean", "starry night"]
        elif target == "动物":
            subjects = ["a majestic tiger", "a graceful deer", "a soaring eagle", "a mystical fox", "a white wolf", "a colorful parrot"]
        elif target == "建筑":
            subjects = ["ancient temple", "modern skyscraper", "medieval castle", "futuristic city", "glass bridge", "oriental pagoda"]
        elif target == "雕塑":
            subjects = ["classical Greek statue", "ancient Chinese terracotta", "Renaissance sculpture", "golden Buddha", "marble bust", "bronze warrior"]
        else:
            subjects = ["a beautiful scene", "a stunning view", "a majestic landscape", "a serene environment", "a peaceful nature", "an artistic display"]

        for i in range(GEN_COUNT):
            subj = random.choice(subjects)
            style = random.choice(base_words)
            mood = random.choice(["soft lighting", "golden hour", "dramatic shadows", "morning mist", "warm sunlight", "blue hour"])
            prompt = f"{subj}, {style}, {mood}, elegant composition, highly detailed"
            prompts_engine[category].append(prompt)

    return prompts_engine
    
# ==================== 核心生成 ====================
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

    full_prompt = f"masterpiece, best quality, photorealistic,highly detailed,{prompt}"
    negative_prompt = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, logo, brand"

    print(f"[生成] {os.path.basename(output_filename)} ({target_w}x{target_h})")
    
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
    # 1. 查找输入图片
    input_path = find_input_image(INPUT_IMAGE_NAME)
    if not input_path:
        print(f"❌ 找不到输入图片，请将图片命名为 '{INPUT_IMAGE_NAME}.jpg' 或 '{INPUT_IMAGE_NAME}.png' 放在 tools 目录下！")
        return

    # 2. 去除水印
    init_image = check_and_remove_watermark(input_path)

    # 3. 加载模型
    pipe = setup_pipeline()

    # 4. 生成提示词
    prompt_variants = build_prompts()
    print(f"\n🎯 生成类型: {TARGET_TYPE}，每种类型生成 {GEN_COUNT} 张")

    # 5. 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_root = os.path.join(CURRENT_DIR, "output", "wechat", f"{TARGET_TYPE}_批量_{timestamp}")
    os.makedirs(output_root, exist_ok=True)

    # 6. 循环生成
    for i in range(GEN_COUNT):
        print(f"\n{'='*40}")
        print(f"📄 生成第 {i+1} 张 / 共 {GEN_COUNT} 张")
        print('='*40)

        categories = [
            ("1_每日壁纸_日常", "daily", 0.40),
            ("2_每日壁纸_古风", "ancient", 0.45),
            ("3_每日壁纸_艺术", "gallery", 0.50)
        ]

        for folder_name, key, strength in categories:
            print(f"\n📁 生成类别: {folder_name}")
            d = os.path.join(output_root, folder_name)
            os.makedirs(d, exist_ok=True)
            
            for i in range(GEN_COUNT):
                prompt_text = prompt_variants[key][i]
                filename = f"{i+1:02d}.png"
                generate_style(pipe, init_image, prompt_text, os.path.join(d, filename), strength=strength)

    print("\n" + "="*50)
    print(f"✅ 全部完成！总共生成 {GEN_COUNT * 3} 张图片！")
    print(f"📂 保存位置：\n   {output_root}")
    print("="*50)

if __name__ == "__main__":
    main()