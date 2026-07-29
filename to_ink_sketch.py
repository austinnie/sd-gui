#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立特效脚本：东方黑白线描/剪影风格 (复刻版)
对应原复杂流水线的特定水墨效果
"""
import os
import torch
import time
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

INPUT_IMAGE_NAME = "input"
SD_MODEL_PATH = "../models/sd-v1-5/anytimeRealistic_v10.safetensors"

STRENGTH = 0.40
STEPS = 20
MAX_LIMIT = 768

def find_input_image(base_name):
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = base_name + ext
        if os.path.exists(path): return path
    return None

def setup_pipeline():
    print("\n[系统] 正在加载 AI 模型...")
    pipe = StableDiffusionPipeline.from_single_file(SD_MODEL_PATH, torch_dtype=torch.float32, safety_checker=None, requires_safety_checker=False, use_safetensors=True)
    pipe.to("cpu")
    pipe.enable_vae_slicing()
    pipe.enable_attention_slicing()
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
    print("[系统] 模型加载完成！")
    return pipe

def main():
    input_path = find_input_image(INPUT_IMAGE_NAME)
    if not input_path:
        print("❌ 没找到图片！请放一张 input.jpg/png 在目录下。")
        return

    init_image = Image.open(input_path).convert('RGB')
    w, h = init_image.size
    max_limit = 768
    if w > max_limit or h > max_limit:
        if w > h: h = int(h * (max_limit / w)); w = max_limit
        else: w = int(w * (max_limit / h)); h = max_limit
    w, h = ((w+31)//64)*64, ((h+31)//64)*64
    init_image = init_image.resize((w, h), Image.Resampling.LANCZOS)

    pipe = setup_pipeline()

    # 👇 核心：高对比度黑白线描/剪影风格提示词
    prompt = (
        "black and white illustration, traditional oriental woodblock print, "
        "ink wash style, monochrome, high contrast, ink brush texture, "
        "rice paper background, elegant line art, minimalist, "
        "clean composition, fine art"
    )
    negative = "color, photorealistic, 3d render, blurry, messy, text, watermark, grey, shadows"

    print(f"🖋️ 正在生成东方黑白线描...")
    generator = torch.Generator("cpu").manual_seed(int(time.time_ns() % 1000000000))

    # 强度设置成 0.35 - 0.40 比较合适，能保留原图轮廓
    result = pipe(
        prompt=prompt, negative_prompt=negative, image=init_image,
        strength=STRENGTH,num_inference_steps=STEPS, guidance_scale=7.5,
        generator=generator, width=w, height=h
    )

    output_path = f"./output/ink_sketch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    os.makedirs("./output", exist_ok=True)
    result.images[0].save(output_path, quality=95)
    print(f"\n✅ 完成！图片已保存: {output_path}")

if __name__ == "__main__":
    main()