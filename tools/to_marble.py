#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立特效脚本：一键转换为【纯白大理石雕像】风格（支持任意图片格式+自动去水印）
"""
import os
import cv2
import torch
import time
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

# ==================== ⚙️ 配置区 ====================
# ✅ 核心加固：定义当前脚本所在的绝对路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

from config import SD_MODEL_PATH, STEPS, MAX_LIMIT, INPUT_IMAGE_NAME, DEFAULT_STRENGTH

POSITIVE_PROMPT = (
    "transform into pure white marble statue, classical sculpture, "
    "flawless white marble, smooth stone texture, elegant pose, "
    "dramatic lighting, museum display, intricate carving details, "
    "monochrome white, high quality, masterpiece"
)
NEGATIVE_PROMPT = (
    "color, skin tone, warm tones, beige, yellow, gray, painting, "
    "cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, "
    "watermark, text, signature, different person"
)

# ==================== 通用核心函数 ====================
def find_input_image(base_name):
    """在 CURRENT_DIR (tools目录) 下寻找 input 图片"""
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = os.path.join(CURRENT_DIR, base_name + ext)
        if os.path.exists(path):
            print(f"✅ 找到输入图片: {path}")
            return path
    return None

def check_and_remove_watermark(image_path):
    print("\n[AI检测] 正在分析原图是否包含水印...")
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    white_pixel_ratio = np.sum(mask > 0) / mask.size
    if white_pixel_ratio < 0.01 or white_pixel_ratio > 0.2:
        print("✅ 未检测到明显水印，直接使用原图。")
        return Image.open(image_path).convert('RGB')
    print("⚠️ 检测到疑似水印区域！正在使用 OpenCV 算法进行智能修复去除...")
    result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    print("✅ 水印已去除！")
    return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))

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
        print(f"  📐 已锁定原图比例，缩放至 {target_w}x{target_h} 加速生成")
    target_w = ((target_w + 31) // 64) * 64
    target_h = ((target_h + 31) // 64) * 64
    if original_w != target_w or original_h != target_h:
        image = init_image.resize((target_w, target_h), Image.Resampling.LANCZOS)
    else:
        image = init_image

    full_prompt = f"masterpiece, best quality, photorealistic,highly detailed,{prompt}"
    negative_prompt = NEGATIVE_PROMPT
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

# ==================== 主函数 ====================
def main():
    input_path = find_input_image(INPUT_IMAGE_NAME)
    if not input_path:
        print(f"❌ 找不到图片！请把图片重命名为 '{INPUT_IMAGE_NAME}.jpg' 或 '{INPUT_IMAGE_NAME}.png' 放到同级目录！")
        return

    init_image = check_and_remove_watermark(input_path)
    pipe = setup_pipeline()
    print(f"🎨 正在转换为大理石雕像...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # ✅ 核心修改：绝对路径拼接到 tools/output/marble
    output_dir = os.path.join(CURRENT_DIR, "output", "marble")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"marble_{timestamp}.png")
    generate_style(pipe, init_image, POSITIVE_PROMPT, output_path, STRENGTH)
    print(f"\n✅ 完成！图片已保存至: {output_path}")

if __name__ == "__main__":
    main()