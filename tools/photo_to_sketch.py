# tools/photo_to_sketch.py
import os
import sys
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

# ========== 复用 generate.py 的核心环境 ==========
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# ✅ 导入 generate.py 里导入的所有配置和工具
# 这样就不用重复写 config 和 utils 了
from tools.config import (
    SD_MODEL_PATH, STEPS, INPUT_IMAGE_NAME,
    REMOVE_AI_TRACES, AI_CLEAR_METADATA, AI_INJECT_EXIF, AI_REALISTIC,
    AI_CAMERA, AI_STRENGTH, AI_STYLE, AI_RANDOMIZE,
    AI_FINGERPRINT_OBFUSCATION, AI_DISTORTION_STRENGTH,
    AI_CHROMATIC_ABERRATION, AI_CHROMATIC_STRENGTH,
    AI_REALISTIC_NOISE, AI_NOISE_ISO_BASE, AI_NOISE_RANDOMIZE,
    AI_MINOR_CROP, AI_CROP_PERCENT,
    AUTO_DETECT_STYLE, SKETCH_KEYWORDS
)

from utils.imagemeta_cleaner import smart_clean_image
from utils.exif_injector import inject_exif
from utils.photo_realistic import make_photo_realistic

# ==================== 🚀 核心转换函数 ====================
def convert_to_sketch(image_path, output_dir, strength=0.45):
    print(f"✏️ 正在加载模型 (使用 config.py 中的路径)...")
    pipe = StableDiffusionPipeline.from_single_file(
        SD_MODEL_PATH,
        torch_dtype=torch.float32,
        safety_checker=None,
        requires_safety_checker=False,
        use_safetensors=True
    )
    pipe.to("cpu")
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)

    print(f"🖼️ 正在处理图片: {image_path}")
    init_image = Image.open(image_path).convert('RGB')
    
    # 自动调整尺寸以适应模型
    w, h = init_image.size
    max_limit = 768
    if w > max_limit or h > max_limit:
        scale = max_limit / max(w, h)
        w, h = int(w * scale), int(h * scale)
    w, h = ((w + 31) // 64) * 64, ((h + 31) // 64) * 64
    init_image = init_image.resize((w, h), Image.Resampling.LANCZOS)

    # 核心素描提示词
    prompt = "pencil sketch of the subject, black and white, minimalist line art, detailed drawing, white background, monochrome"
    negative_prompt = "photorealistic, 3d, color, noise, blur"

    generator = torch.Generator("cpu").manual_seed(int(time.time_ns() % 1000000000))

    print(f"🎨 正在生成素描图 ({w}x{h})...")
    result = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=init_image,
        strength=strength,
        num_inference_steps=STEPS,  # 复用 config.py 的 STEPS
        guidance_scale=7.5,
        generator=generator,
        width=w,
        height=h
    )

    # 保存中间产物 PNG
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_png_path = os.path.join(output_dir, f"sketch_{timestamp}_raw.png")
    result.images[0].save(raw_png_path)

    print(f"✅ 初步生成完成，准备调用 config.py 的消除AI痕迹流程...")

    # ==================== 复用 config.py 的消除AI痕迹流程 ====================
    final_path = raw_png_path
    
    if REMOVE_AI_TRACES:
        try:
            print(f"\n📷 正在执行消除AI痕迹处理...")
            
            # 1️⃣ 清除元数据（转换为JPG）
            if AI_CLEAR_METADATA:
                jpg_path = raw_png_path.replace('.png', '.jpg')
                final_path = smart_clean_image(
                    raw_png_path,
                    output_path=jpg_path,
                    method='jpg',
                    jpg_quality=92
                )
                print(f"   ✅ 元数据已清除 -> JPG")

            # 2️⃣ 照片真实化
            if AI_REALISTIC:
                final_path = make_photo_realistic(
                    final_path,
                    final_path,
                    camera=AI_CAMERA,
                    style="portrait",
                    inject_exif_data=False,
                    randomize=True,
                    strength=AI_STRENGTH,
                    add_noise_flag=AI_REALISTIC_NOISE
                )
                print(f"   ✅ 照片真实化完成 (强度: {AI_STRENGTH})")

            # 3️⃣ EXIF 注入
            if AI_INJECT_EXIF:
                import time
                time.sleep(0.5)
                try:
                    final_path = inject_exif(
                        final_path,
                        final_path,
                        camera=AI_CAMERA,
                        style="portrait",
                        randomize=True
                    )
                    print(f"   ✅ EXIF 已注入")
                except Exception as e:
                    print(f"   ⚠️ EXIF 注入跳过: {e}")

            # 4️⃣ 紫边模拟
            if AI_CHROMATIC_ABERRATION:
                try:
                    import numpy as np
                    from PIL import Image
                    img = Image.open(final_path)
                    arr = np.array(img).astype(np.float32)
                    h, w = arr.shape[:2]
                    strength = AI_CHROMATIC_STRENGTH
                    for y in range(h):
                        for x in range(w):
                            dist_from_edge = min(x, w-1-x, y, h-1-y)
                            if dist_from_edge < 40:
                                shift_factor = (40 - dist_from_edge) / 40
                                shift = shift_factor * strength * random.uniform(0.5, 1.0)
                                arr[y, x, 0] += random.uniform(-shift, shift * 0.5)
                                arr[y, x, 2] += random.uniform(-shift * 0.5, shift)
                    arr = np.clip(arr, 0, 255).astype(np.uint8)
                    if arr.ndim == 3 and arr.shape[2] == 3:
                        img = Image.fromarray(arr).convert('RGB')
                    else:
                        img = Image.fromarray(arr[:, :, :3]).convert('RGB')
                    img.save(final_path, quality=92)
                    print(f"      ✅ 紫边模拟完成 (强度: {strength})")
                except Exception as e:
                    print(f"   ⚠️ 紫边模拟跳过: {e}")

            # 5️⃣ 轻微裁剪
            if AI_MINOR_CROP:
                try:
                    import random
                    from PIL import Image
                    img = Image.open(final_path)
                    w, h = img.size
                    crop_pct = AI_CROP_PERCENT * random.uniform(0.5, 1.5)
                    crop_w = int(w * crop_pct)
                    crop_h = int(h * crop_pct)
                    crop_w = max(5, min(crop_w, int(w * 0.05)))
                    crop_h = max(5, min(crop_h, int(h * 0.05)))
                    corners = [(0, 0), (0, crop_h), (crop_w, 0), (crop_w, crop_h)]
                    if random.random() < 0.5:
                        left = random.randint(0, crop_w)
                        top = random.randint(0, crop_h)
                    else:
                        left, top = random.choice(corners)
                    right = w - random.randint(0, crop_w)
                    bottom = h - random.randint(0, crop_h)
                    if right > left + 50 and bottom > top + 50:
                        img = img.crop((left, top, right, bottom))
                        img = img.resize((w, h), Image.Resampling.LANCZOS)
                        img.save(final_path, quality=92)
                        print(f"      ✅ 轻微裁剪完成 (裁切: {crop_pct*100:.1f}%)")
                except Exception as e:
                    print(f"   ⚠️ 轻微裁剪跳过: {e}")

            # 清理原始 PNG
            if os.path.exists(raw_png_path) and raw_png_path != final_path:
                try:
                    os.remove(raw_png_path)
                except:
                    pass

        except Exception as e:
            print(f"   ⚠️ 消除AI痕迹流程异常: {e}")

    # 如果最终生成的是 JPG，调整记录文件
    metadata_filename = raw_png_path.replace('.png', '.txt').replace('.jpg', '.txt')
    if os.path.exists(metadata_filename):
        try:
            os.remove(metadata_filename)
        except:
            pass

    print(f"\n✅ 全部完成！最终素描图已保存至: {final_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n❌ 错误：请指定图片路径！")
        print("👉 用法: python photo_to_sketch.py \"D:\\你的图片.jpg\"")
        sys.exit(1)

    input_file = sys.argv[1].strip('"')
    output_folder = os.path.join(CURRENT_DIR, "output")
    
    if not os.path.exists(input_file):
        print(f"\n❌ 错误：找不到图片文件 '{input_file}'！")
        sys.exit(1)
        
    os.makedirs(output_folder, exist_ok=True)
    
    # 🔥 将素描强度设定为 0.45 (你可以在代码里随时修改)
    convert_to_sketch(input_file, output_folder, strength=0.45)