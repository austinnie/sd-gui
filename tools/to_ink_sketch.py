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

# ✅ 核心加固：定义当前脚本所在的绝对路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

from config import SD_MODEL_PATH, STEPS, MAX_LIMIT, INPUT_IMAGE_NAME, DEFAULT_STRENGTH

def find_input_image(base_name):
    """在 CURRENT_DIR (tools目录) 下寻找 input 图片"""
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

def main():
    input_path = find_input_image(INPUT_IMAGE_NAME)
    if not input_path:
        print("❌ 没找到图片！请放一张 input.jpg/png 在目录下。")
        return

    init_image = Image.open(input_path).convert('RGB')
    w, h = init_image.size
    
    # 👇 注意：你当前脚本单独设了 max_limit = 768
    # 如果发现速度慢，可以统一改成 MAX_LIMIT (即从 config 里读的 512)
    max_limit = 768
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

    result = pipe(
        prompt=prompt,
        negative_prompt=negative,
        image=init_image,
        strength=STRENGTH,
        num_inference_steps=STEPS,
        guidance_scale=7.5,
        generator=generator,
        width=w, height=h
    )

    # ✅ 核心修改：绝对路径拼接到 tools/output/ink_sketch
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(CURRENT_DIR, "output", "ink_sketch")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"ink_sketch_{timestamp}.png")
    result.images[0].save(output_path, quality=95)
    print(f"\n✅ 完成！图片已保存: {output_path}")

if __name__ == "__main__":
    main()