#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立特效脚本：一键生成【性感曲线/大胸】风格的每日壁纸
"""
import os
import torch
import time
import random
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
from config import SD_MODEL_PATH, STEPS, MAX_LIMIT, INPUT_IMAGE_NAME

def find_input_image(base_name):
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = os.path.join(CURRENT_DIR, base_name + ext)
        if os.path.exists(path):
            print(f"✅ 找到输入图片: {path}")
            return path
    return None

def setup_pipeline():
    print("\n[系统] 正在加载 AI 模型...")
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
        print(f"  📐 缩放至 {target_w}x{target_h}")
    target_w = ((target_w + 31) // 64) * 64
    target_h = ((target_h + 31) // 64) * 64
    if original_w != target_w or original_h != target_h:
        image = init_image.resize((target_w, target_h), Image.Resampling.LANCZOS)
    else:
        image = init_image

    full_prompt = f"masterpiece, best quality, photorealistic, highly detailed, {prompt}"
    negative_prompt = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, logo, brand"

    print(f"[正在生成] {os.path.basename(output_filename)} ({target_w}x{target_h})")
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
        width=target_w, height=target_h,
    )
    result.images[0].save(output_filename, quality=95)

def main():
    input_path = find_input_image(INPUT_IMAGE_NAME)
    if not input_path:
        print("❌ 没找到图片！请放一张 input.jpg/png 在目录下。")
        return

    init_image = Image.open(input_path).convert('RGB')
    w, h = init_image.size
    max_limit = MAX_LIMIT
    if w > max_limit or h > max_limit:
        if w > h:
            h = int(h * (max_limit / w))
            w = max_limit
        else:
            w = int(w * (max_limit / h))
            h = max_limit
    w, h = ((w+31)//64)*64, ((h+31)//64)*64
    init_image = init_image.resize((w, h), Image.Resampling.LANCZOS)

    pipe = setup_pipeline()

    # 👇 核心：性感/大胸专属提示词库
    sexy_subjects = [
        "a beautiful woman, huge breasts, large cleavage, perfect curvy body, hands resting naturally on lap, sitting elegantly",
        "an elegant girl, big chest, full bust, sexy curvy figure, hand lightly touching face, thoughtful expression",
        "a graceful lady, voluptuous body, attractive figure, standing gracefully, arms relaxed at sides",
        "a stunning female, massive breasts, alluring curvy body, sitting, hands clasped gently together"
    ]

    base_style = ["breathtaking scene", "cinematic lighting", "golden hour", "ethereal vibe"]
    mood = ["soft lighting", "golden hour", "warm sunlight"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_root = os.path.join(CURRENT_DIR, "output", "curvy_daily", f"curvy_{timestamp}")
    os.makedirs(output_root, exist_ok=True)

    for i in range(6):
        subj = random.choice(sexy_subjects)
        style = random.choice(base_style)
        mood_text = random.choice(mood)
        prompt = f"{subj}, {style}, {mood_text}, elegant composition, highly detailed"
        filename = f"{i+1:02d}.png"
        generate_style(pipe, init_image, prompt, os.path.join(output_root, filename), strength=0.40)

    print(f"\n✅ 完成！共生成 6 张图片！")
    print(f"📂 请前往以下目录挑选图片：\n   {output_root}")

if __name__ == "__main__":
    main()