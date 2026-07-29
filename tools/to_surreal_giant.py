#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立特效脚本：一键生成【超现实巨大遗迹 / 废土科幻】风格
"""
import os
import torch
import time
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

# ✅ 核心加固：定义当前脚本所在的绝对路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ 从全局配置导入统一参数
from config import SD_MODEL_PATH, STEPS, MAX_LIMIT, INPUT_IMAGE_NAME, DEFAULT_STRENGTH

def find_input_image(base_name):
    """在 CURRENT_DIR 目录下寻找 input 图片"""
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
    max_limit = MAX_LIMIT # 稍微大一点，保留遗迹的细节
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

    # 👇 核心：超现实主义风格提示词
    prompt = (
        "surreal landscape, giant ancient stone ruins, a colossal face carved into the rock, "
        "a massive overhanging mushroom-shaped monolith, "
        "tiny woman in pink dress standing below, extreme scale contrast, "
        "intense bright light emitting between the rocks, lens flare, "
        "desolate sandy ground, dark starry night sky, dust particles in the air, "
        "surrealism, dreamlike, cinematic, atmospheric, masterpiece"
    )
    negative = "modern city, bustling, colorful, cartoon, 3d render, anime, text, watermark"

    print(f"🗿 正在生成超现实巨大遗迹...")
    generator = torch.Generator("cpu").manual_seed(int(time.time_ns() % 1000000000))

    result = pipe(
        prompt=prompt,
        negative_prompt=negative,
        image=init_image,
        strength=0.45, # 0.45 可以保留原图结构，但自由度足以生成奇观
        num_inference_steps=STEPS,
        guidance_scale=7.5,
        generator=generator,
        width=w,
        height=h
    )

    # ✅ 输出路径彻底修正：使用 CURRENT_DIR 进行安全拼接
    output_dir = os.path.join(CURRENT_DIR, "output", "surreal_giant")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(
        output_dir,
        f"surreal_giant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    result.images[0].save(output_path, quality=95)
    print(f"\n✅ 完成！图片已保存至: {output_path}")

if __name__ == "__main__":
    main()