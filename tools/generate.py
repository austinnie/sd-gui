#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用生成器：根据提示词库自动出图
用法：python generate.py <风格名称>
例如：python generate.py curvy_daily
"""
import os
import sys
import time
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
# True  = 安全模式（强制穿衣服，防止生成裸体，适合发公众号）
# False = 自由模式（不干预提示词，适合生成性感、去衣等特殊风格）
SAFE_MODE = True  
# =======================================================

# ==================== 🛠️ 核心函数 ====================

def find_input_image():
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = os.path.join(CURRENT_DIR, INPUT_IMAGE_NAME + ext)
        if os.path.exists(path):
            return path
    return None

def setup_pipeline():
    print(f"\n[系统] 正在加载 AI 模型...")
    model_path = SD_MODEL_PATH

    # 纯本地加载，绝不联网
    pipe = StableDiffusionPipeline.from_single_file(
        model_path,
        torch_dtype=torch.float32,
        safety_checker=None,
        requires_safety_checker=False,
        use_safetensors=True
    )
    # 引擎优化
    pipe.to("cpu")
    pipe.enable_vae_slicing()
    pipe.enable_attention_slicing()
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
    print("[系统] 模型加载完成！")
    return pipe
    
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

    # ==================== 根据开关生成提示词 ====================
    full_prompt = f"masterpiece, best quality, photorealistic, highly detailed, {prompt}"
    neg_prompt = "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, logo, brand"

    if SAFE_MODE:
        # ✅ 安全模式：强制穿衣服 + 锁定原图脸部
        full_prompt = f"masterpiece, best quality, photorealistic, highly detailed, {prompt}, wearing clothes, fully clothed, same person, soft natural expression, looking away, candid moment, relaxed atmosphere"
        neg_prompt = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "nude, naked, no clothes, bare skin, lingerie, underwear, see-through, "
            "watermark, text, signature, logo, brand"
        )
        print(f"🛡️ [安全模式已启用] 强制穿衣服 + 锁定原图脸部")
    else:
        # ❌ 自由模式：不加干预
        full_prompt = f"masterpiece, best quality, photorealistic, highly detailed, {prompt}"
        neg_prompt = "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, logo, brand"
        print(f"🔓 [自由模式已启用] 不干预内容")
    # ============================================================
    
    print(f"[生成] {os.path.basename(output_filename)} ({target_w}x{target_h})")
    generator = torch.Generator("cpu").manual_seed(int(time.time_ns() % 1000000000))
    
    result = pipe(
        prompt=full_prompt, negative_prompt=neg_prompt, image=image,
        strength=strength, num_inference_steps=STEPS, guidance_scale=7.5,
        generator=generator, width=target_w, height=target_h
    )
    result.images[0].save(output_filename, quality=95)

# ==================== 🚀 主入口 ====================

def main():
    # 1. 检查命令行参数
    if len(sys.argv) < 2 or sys.argv[1] == "--list" or sys.argv[1] == "-l":
        print("\n📋 当前支持的风格列表：")
        for key in STYLE_PROMPTS.keys():
            print(f"   - {key}")
        print("\n💡 用法：python generate.py <风格名称>")
        sys.exit(0)

    target_style = sys.argv[1]

    if target_style not in STYLE_PROMPTS:
        print(f"\n❌ 错误：找不到风格 '{target_style}'！")
        print("📋 可用风格列表：")
        for key in STYLE_PROMPTS.keys():
            print(f"   - {key}")
        sys.exit(1)

    input_path = find_input_image()
    if not input_path:
        print(f"\n❌ 没找到图片！请把图片命名为 {INPUT_IMAGE_NAME}.jpg/.png 放在 tools 目录下！")
        return

    init_image = Image.open(input_path).convert('RGB')
    pipe = setup_pipeline()

    config = STYLE_PROMPTS[target_style]
    
    # ========== 新增：固定生成数量（可配置） ==========
    GENERATE_COUNT = 4  # 想要生成几张就改这里
    # =================================================
    
    print(f"\n🎯 正在生成风格: {target_style} -> {config['folder']}")
    print(f"📊 本次共生成 {GENERATE_COUNT} 张图片")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_root = os.path.join(CURRENT_DIR, "output", f"{config['folder']}_{timestamp}")
    os.makedirs(output_root, exist_ok=True)

    # ========== 修复：明确生成指定数量 ==========
    for i in range(GENERATE_COUNT):
        # 从配置的 subjects 列表中随机选一个提示词
        prompt = random.choice(config["subjects"])
        
        # 实时进度提示
        print(f"\n🔄 进度：第 {i+1}/{GENERATE_COUNT} 张")
        
        generate_style(
            pipe, 
            init_image, 
            prompt, 
            os.path.join(output_root, f"{i+1:02d}.png"), 
            config["strength"]
        )
    # =============================================

    print(f"\n✅ 全部完成！共 {GENERATE_COUNT} 张图片，保存在: {output_root}")
    
if __name__ == "__main__":
    main()