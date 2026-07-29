#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
纯净版去衣脚本（极速重写）
去除所有可能导致卡顿的人脸检测，保留核心重绘逻辑
"""
import os
import torch
import time
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

# ==================== ⚙️ 配置区 ====================
INPUT_IMAGE_NAME = "input"  # 原图 (不用写后缀)
SD_MODEL_PATH = "../models/sd-v1-5/anytimeRealistic_v10.safetensors" # 使用你最顺手的模型

STRENGTH = 0.40  # 👈 【核心参数】先设为 0.40，速度最快！
STEPS = 20       # 👈 【核心提速】步数改成 20（公众号出图10-15步都没问题）

# ==================== 🔍 路径查找 ====================
def find_input_image(base_name):
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = base_name + ext
        if os.path.exists(path):
            print(f"✅ 找到输入图片: {path}")
            return path
    return None

# ==================== 🛠️ 核心逻辑 ====================
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

def main():
    # 1. 找图
    input_path = find_input_image(INPUT_IMAGE_NAME)
    if not input_path:
        print(f"❌ 找不到图片，请放入 {INPUT_IMAGE_NAME}.png 或 .jpg 在同目录！")
        return

    # 2. 读取并锁定安全尺寸 (768以保证面部不崩且速度正常)
    print(f"\n📂 正在加载图片: {os.path.basename(input_path)}")
    image = Image.open(input_path).convert('RGB')
    w, h = image.size
    max_limit = 768
    if w > max_limit or h > max_limit:
        if w > h: h = int(h * (max_limit / w)); w = max_limit
        else: w = int(w * (max_limit / h)); h = max_limit
    w, h = ((w + 31) // 64) * 64, ((h + 31) // 64) * 64
    image = image.resize((w, h), Image.Resampling.LANCZOS)

    # 3. 加载模型
    pipe = setup_pipeline()
    
    # 4. 纯净版提示词（没有任何多余修饰，只告诉AI去衣服）
    # 这里的负面提示词重点罗列了衣服种类，促使AI强烈排斥衣物
    positive_prompt = f"masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, natural body, full body"
    negative_prompt = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, clothes, fabric, dress, shirt, pants, underwear, bra, panties, bikini, swimsuit, covering, clothed"

    print(f"🎯 开始去衣 (强度: {STRENGTH}, 步数: {STEPS})")
    print(f"⏳ 预计耗时 1~3 分钟...")
    
    generator = torch.Generator("cpu").manual_seed(int(time.time_ns() % 1000000000))
    
    result = pipe(
        prompt=positive_prompt,
        negative_prompt=negative_prompt,
        image=image,
        strength=STRENGTH,
        num_inference_steps=STEPS,
        guidance_scale=7.5,
        generator=generator,
        width=w, height=h,
    )

    # 5. 保存图片
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "./output/remove_clothes"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"remove_{timestamp}.png")
    result.images[0].save(output_path, quality=95)

    print("\n" + "="*50)
    print("✅ 去衣任务完成！")
    print(f"📂 图片已保存至: {output_path}")
    print("="*50)

if __name__ == "__main__":
    main()