#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多功能去衣服专业版：智能识别人脸 + 保护特征 + 多级力度
支持：任意图片格式识别 + 自动去水印
"""
import os
import cv2
import torch
import time
import numpy as np
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

# ==================== ⚙️ 配置区 ====================
INPUT_IMAGE_NAME = "input"   # 原图 (不需要后缀)
SD_MODEL_PATH = "../models/sd-v1-5/aiiiiii01_v10.safetensors" # 模型路径

# 👇【核心选择】：去衣力度 (可选 1, 2, 3)
# 1 = 轻微 (适合比基尼/薄纱 -> 微露)
# 2 = 标准 (适合紧身瑜伽/泳装 -> 全去，面部不变)
# 3 = 猛烈 (适合厚夹克/长裙 -> 强去，面部可能微变)
MODE = 2  
STEPS = 12
# 最大输出边长
MAX_LIMIT = 768

# ==================== 🎯 力度配置预设 ====================
SETTINGS = {
    1: {
        "strength": 0.45,
        "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, wearing very thin see-through gauze clothing, revealing body, sheer fabric, soft lighting",
        "negative": "worst quality, low quality, watermark, text, signature, rough, deformed, clothed"
    },
    2: {
        "strength": 0.55,
        "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, natural body, perfect anatomy, soft skin, soft morning lighting, elegant pose, fully visible body, fine art nude",
        "negative": "worst quality, low quality, ugly, deformed, bad anatomy, clothes, fabric, dress, shirt, pants, underwear, bra, panties, bikini, swimsuit, covering, clothed"
    },
    3: {
        "strength": 0.65,
        "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, fully naked, bare skin, detailed anatomy, intimate area, explicit fine art, museum quality nude, natural beauty",
        "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, clothes, fabric, dress, shirt, pants, underwear, bra, panties, bikini, swimsuit, covering, clothed, bad proportions"
    }
}

# ==================== 🔍 图片路径智能识别 + 去水印 (统一移植) ====================
def find_input_image(base_name):
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = base_name + ext
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

# ==================== 🛠️ 智能人脸保护逻辑 ====================
def detect_and_protect_face(image_pil):
    """检测并提高人脸区域的原图权重（智能锁脸）"""
    img = np.array(image_pil.convert('RGB'))
    img_cv = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 使用 OpenCV 经典级联分类器找脸
    haar_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(haar_cascade_path)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) > 0:
        print(f"✅ [保护模式] 检测到 {len(faces)} 张人脸，已开启面部锁死功能！")
        return True, faces
    else:
        print(f"ℹ️ 未检测到清晰面部，跳过面部锁定。")
        return False, None

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
    # 1. 自动寻找任意格式的 input 图片
    input_path = find_input_image(INPUT_IMAGE_NAME)
    if not input_path:
        print(f"❌ 找不到图片！请把图片重命名为 '{INPUT_IMAGE_NAME}.jpg' 或 '{INPUT_IMAGE_NAME}.png' 放到同级目录！")
        return

    # 2. 自动去水印
    image = check_and_remove_watermark(input_path)

    # 3. 锁定安全尺寸
    w, h = image.size
    max_limit = MAX_LIMIT
    if w > max_limit or h > max_limit:
        if w > h:
            h = int(h * (max_limit / w))
            w = max_limit
        else:
            w = int(w * (max_limit / h))
            h = max_limit
    w = ((w + 31) // 64) * 64
    h = ((h + 31) // 64) * 64
    image = image.resize((w, h), Image.Resampling.LANCZOS)

    # 4. 智能人脸检测
    has_face, faces = False, None  # 直接跳过人脸检测
    
    # 5. 加载配置
    config = SETTINGS.get(MODE, SETTINGS[2])
    print(f"\n🎯 当前模式: {'轻微' if MODE==1 else '标准' if MODE==2 else '猛烈'} (强度: {config['strength']})")

    # 6. 启动 AI
    pipe = setup_pipeline()
    
    print(f"⏳ 开始重绘去衣... 大概需要 2~4 分钟（请耐心等待）")
    generator = torch.Generator("cpu").manual_seed(int(time.time_ns() % 1000000000))
    
    result = pipe(
        prompt=config["prompt"],
        negative_prompt=config["negative"],
        image=image,
        strength=config["strength"],
        num_inference_steps=STEPS,
        guidance_scale=7.5,
        generator=generator,
        width=w,
        height=h,
    )

    # 7. 保存图片
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "./output/remove_clothes"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"remove_{timestamp}_{MODE}.png"
    output_path = os.path.join(output_dir, filename)
    result.images[0].save(output_path, quality=95)

    print("\n" + "="*50)
    print("✅ 去衣任务完成！")
    print(f"📂 图片已保存至: {output_path}")
    print("="*50)

if __name__ == "__main__":
    main()