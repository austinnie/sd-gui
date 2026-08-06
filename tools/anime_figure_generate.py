# tools/anime_figure_generate.py
import os
import sys
import time
import random
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

# ========== 修复路径，确保可以导入 tools 模块 ==========
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(CURRENT_DIR))

# ========== 复用 generate.py 的核心环境 ==========
from tools.config import (
    SD_MODEL_PATH, STEPS,
    REMOVE_AI_TRACES, AI_CLEAR_METADATA, AI_INJECT_EXIF, AI_REALISTIC,
    AI_CAMERA, AI_STRENGTH, AI_STYLE, AI_RANDOMIZE,
    AI_CHROMATIC_ABERRATION, AI_CHROMATIC_STRENGTH,
    AI_REALISTIC_NOISE, AI_NOISE_ISO_BASE, AI_NOISE_RANDOMIZE,
    AI_MINOR_CROP, AI_CROP_PERCENT,
    AUTO_DETECT_STYLE
)

from utils.imagemeta_cleaner import smart_clean_image
from utils.exif_injector import inject_exif
from utils.photo_realistic import make_photo_realistic

# ==================== 🎨 雕塑/手办风格提示词模板 ====================
# ==================== 🎨 雕塑/手办风格提示词模板 ====================
FIGURE_PROMPTS = [
    # 1. 白毛红眼/恶魔女孩 坐姿（对应图1、图2）
    "high quality 3D figure of a white-haired girl with red eyes and black hair streaks, wearing a dark purple slip dress and beige oversized jacket, sitting on a white cylindrical pedestal, crossed legs, dark choker necklace, white geometric halo accessory, black bow, soft grey background, studio photography, macro product shot, glossy PVC finish",

    # 2. 兔女郎 紫发 跪姿/坐姿（对应图3）
    "beautiful 3D resin figure of a purple-haired anime girl, wearing black bunny girl outfit with purple ribbon details, sitting posture, long straight hair, cute expression, glossy lips, studio lighting, soft white background, collectible statue, high definition",

    # 3. 浅蓝色头发 白兔女郎 动态坐姿（对应图4）
    "anime collectible figure of a light blue-haired girl in a white bunny girl suit, teal ribbon bow and matching high heels, sitting pose with one leg kicked up, holding a small teddy bear, glossy painted texture, warm product photography background with bokeh, high end figurine",

    # 4. 粉发天使 飘浮/站立姿势 三视图（对应图5）
    "sculpted anime figurine of a pink-haired angel girl, white translucent fantasy dress, large white feathered wings, holding two stacked wooden boxes, standing pose, neutral grey background, product studio shot, high-resolution collectible model",

    # 5. 黑发 黑皮兔女郎 站姿（对应图6）
    "realistic anime figure of a long black-haired girl, black bunny girl outfit with black tights, leaning pose, hand on hip, glossy latex look, pure white background, studio lighting, high detail, macro photography, hand-painted PVC model",

    # 6. 金发 恶魔小翅膀 黑色连体衣 站姿（对应图7）
    "3D anime statue of a long blonde-haired girl, black outfit with devil horn ears and small bat wings, black and red claws, dynamic standing pose, black background, dramatic studio lighting, high gloss finish, premium collectible",

    # 7. 浅蓝发 居家风 坐姿（对应图8）
    "cute anime figure of a light blue-haired girl with messy hair bun, wearing a soft lavender babydoll dress and white thigh-high socks, sitting pose, pure white background, soft lighting, pastel colors, painted resin figurine",

    # 8. 通用的多角度展示模型（类似三视图/旋转展示）
    "3D collectible display of an anime girl figurine, multiple angle rotation view, sitting on a pedestal, precise sculpting, realistic shading, grey studio background, product demonstration photo, high fidelity"
]

def generate_figure(prompt, output_dir):
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

    # 设置分辨率（接近正方形，适合手办展示）
    w, h = 640, 768

    # 负面提示词
    negative_prompt = "worst quality, low quality, blurry, deformed hands, jumbled body parts, extra fingers, missing limbs, watermark, logo, text, 2D drawing"

    generator = torch.Generator("cpu").manual_seed(int(time.time_ns() % 1000000000))

    print(f"🎨 正在生成 3D 雕塑/手办风格 ({w}x{h})...")
    print(f"📝 提示词: {prompt[:60]}...")
    
    result = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=STEPS,
        guidance_scale=7.5,
        generator=generator,
        width=w,
        height=h
    )

    # 保存中间产物 PNG
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_png_path = os.path.join(output_dir, f"figure_{timestamp}_raw.png")
    result.images[0].save(raw_png_path)

    print(f"✅ 初步生成完成，准备调用消除AI痕迹流程...")

    # ==================== 复用 config.py 的消除AI痕迹流程 ====================
    final_path = raw_png_path
    
    if REMOVE_AI_TRACES:
        try:
            print(f"\n📷 正在执行消除AI痕迹处理...")
            
            # 1️⃣ 清除元数据
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

            # 3️⃣ EXIF
            if AI_INJECT_EXIF:
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

            # 清理原始 PNG
            if os.path.exists(raw_png_path) and raw_png_path != final_path:
                try:
                    os.remove(raw_png_path)
                except:
                    pass

        except Exception as e:
            print(f"   ⚠️ 消除AI痕迹流程异常: {e}")

    print(f"\n✅ 全部完成！最终手办图已保存至: {final_path}")


if __name__ == "__main__":
    output_folder = os.path.join(CURRENT_DIR, "output")
    os.makedirs(output_folder, exist_ok=True)

    # 随机选取一种风格提示词（或者你可以指定索引）
    selected_prompt = random.choice(FIGURE_PROMPTS)
    
    generate_figure(selected_prompt, output_folder)