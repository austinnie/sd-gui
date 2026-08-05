#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用生成器：根据提示词库自动出图（支持分层+扁平，全部生成）
用法：python generate.py <风格名称>
例如：python generate.py pure_serene

指定生成数量：
  python generate.py pure_serene_v2 -n 10
  python generate.py pure_serene_v2 --count 20

生成模式：
  --img2img, --i2i    图生图模式（默认，需要 input.jpg）
  --txt2img, --t2i    文生图模式（无需参考图，从零生成）

步数控制：
  --steps <数字>      临时指定生成步数（优先于 config.py 中的 STEPS）

图生图输入：
  --input <文件路径>   指定图生图的参考图（不指定则默认读取 config.py 中的 input.jpg）
"""
import os
import sys
import io

# ========== 修复 Windows 终端编码问题 ==========
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
# =================================================

import time
import cv2
import numpy as np
import torch
import time
import random
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

# 确保 tools 目录在路径中
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# ✅ 添加项目根目录到路径（让 utils 可以被导入）
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ✅ 验证路径
print(f"📁 PROJECT_ROOT: {PROJECT_ROOT}")

# ✅ 导入 utils
from utils.imagemeta_cleaner import smart_clean_image
from utils.exif_injector import inject_exif
from utils.photo_realistic import make_photo_realistic


# ========== ✅ 导入配置 ==========
from tools.config import (
    SD_MODEL_PATH, STEPS, MAX_LIMIT, INPUT_IMAGE_NAME, DEFAULT_STRENGTH,
    REMOVE_AI_TRACES, AI_CLEAR_METADATA, AI_INJECT_EXIF, AI_REALISTIC,
    AI_CAMERA, AI_STRENGTH, AI_STYLE, AI_RANDOMIZE,
    AI_FINGERPRINT_OBFUSCATION, AI_DISTORTION_STRENGTH,
    AI_CHROMATIC_ABERRATION, AI_CHROMATIC_STRENGTH,
    AI_REALISTIC_NOISE, AI_NOISE_ISO_BASE, AI_NOISE_RANDOMIZE,
    AI_MINOR_CROP, AI_CROP_PERCENT,
    AUTO_DETECT_STYLE, SKETCH_KEYWORDS,
    # ========== 🆕 导入互斥开关（去掉 0~3 死路径导入） ==========
    USE_OPENVINO_MODEL, ACTIVE_MODEL
    # 🛑 注意：不要在这里导入 SD_OV_MODEL_PATH, SD_MODEL_PATH_0/1/2/3 
)

print(f"📊 STEPS = {STEPS}")
print(f"📷 AI_CAMERA = {AI_CAMERA}")

from prompts_config import STYLE_PROMPTS

# ==================== ⚙️ 安全开关 ====================
SAFE_MODE = True  
# 安全模式策略：
#   "simple" = 简单模式：在提示词后加 "wearing clothes"
#   "filter" = 过滤模式：移除露骨词汇 (nude, naked, explicit, pornographic, sex, hentai)
SAFE_MODE_STRATEGY = "filter"  # 可选: "simple" 或 "filter"

# 是否启用去水印
REMOVE_WATERMARK = True

# ==================== ⚙️ 内容文本开关 ====================
# 是否启用 content_texts 字段（将文本内容添加到提示词中）
USE_CONTENT_TEXTS = True  # 默认关闭，设为 True 开启
# ========================================================

# ==================== 🛠️ 工具函数 ====================

def print_usage():
    """打印使用说明"""
    print("\n" + "="*60)
    print("📖 通用生成器使用说明")
    print("="*60)
    print("\n用法：")
    print("  python generate.py <风格名称>")
    print("  python generate.py <风格名称> -n <数量>")
    print("  python generate.py <风格名称> --count <数量>")
    print("  python generate.py <风格名称> --steps <数字>")
    print("  python generate.py <风格名称> --input <参考图路径>")
    print("\n生成模式：")
    print("  --img2img, --i2i    图生图模式（默认，需要 input.jpg）")
    print("  --txt2img, --t2i    文生图模式（无需参考图，从零生成）")
    print("\n步数控制：")
    print("  --steps <数字>      指定生成步数（不指定则使用 config.py 中的 STEPS）")
    print("\n图生图输入：")
    print("  --input <文件路径>  指定参考图（不指定则使用 config.py 中的默认 input.jpg）")
    print("\n示例：")
    print("  python generate.py anime_xxx_v3 --steps 30 -n 5   # 30步生成5张")
    print("  python generate.py anime_xxx_v3 --txt2img         # 使用config默认步数")
    print("  python generate.py anime_xxx_v3 --img2img --input my_pic.png -n 3 # 用指定图生图")
    print("\n其他命令：")
    print("  python generate.py --list     显示所有可用风格（分屏）")
    print("  python generate.py -l         显示所有可用风格（分屏）")
    print("\n💡 提示：")
    print("  - 图生图模式：需要 input.jpg 作为参考图")
    print("  - 文生图模式：不需要参考图，完全根据提示词生成")
    print("  - 文生图模式会自动随机选择尺寸，增加多样性")
    print("  - 去水印功能: " + ("✅ 已开启" if REMOVE_WATERMARK else "❌ 已关闭"))
    print("="*60)

def print_style_list():
    """分屏显示风格列表"""
    styles = list(STYLE_PROMPTS.keys())
    total = len(styles)
    
    print("\n" + "="*60)
    print(f"📋 当前支持的风格列表（共 {total} 个）")
    print("="*60)
    
    # 每页显示数量
    page_size = 20
    total_pages = (total + page_size - 1) // page_size
    
    for page in range(total_pages):
        start = page * page_size
        end = min(start + page_size, total)
        
        print(f"\n📄 第 {page+1}/{total_pages} 页")
        print("-"*40)
        
        for i in range(start, end):
            style_name = styles[i]
            folder_info = ""
            if style_name in STYLE_PROMPTS:
                folder = STYLE_PROMPTS[style_name].get("folder", "")
                if folder:
                    folder_info = f" -> {folder}"
            print(f"  {i+1:3d}. {style_name}{folder_info}")
        
        print("-"*40)
        print(f"显示 {end-start} 个，共 {total} 个风格")
        
        if page < total_pages - 1:
            input("\n按 Enter 继续查看下一页...")
    
    print("\n" + "="*60)
    print("💡 使用方式：python generate.py <风格名称> [-n <数量>]")
    print("="*60)

def find_input_image(custom_input=None):
    """查找参考图，支持自定义路径或默认路径"""
    if custom_input:
        if os.path.exists(custom_input):
            return custom_input
        else:
            print(f"⚠️ 警告：找不到指定的输入文件 '{custom_input}'，尝试查找默认 input 文件...")
    
    # 默认查找 INPUT_IMAGE_NAME
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = os.path.join(CURRENT_DIR, INPUT_IMAGE_NAME + ext)
        if os.path.exists(path):
            return path
    return None

# ==================== 去水印功能 ====================
def remove_watermark(image_path):
    """
    检测并去除图片水印
    返回: PIL Image 对象
    """
    if not REMOVE_WATERMARK:
        print("[系统] 去水印功能已关闭，直接使用原图")
        return Image.open(image_path).convert('RGB')
    
    print("\n[AI预处理] 检测并去除图片水印...")
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 检测白色/亮色区域（常见水印特征）
    _, mask = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    
    # 计算白色区域占比
    white_pixel_ratio = np.sum(mask > 0) / mask.size
    
    # 如果白色区域过少或过多，认为没有明显水印
    if white_pixel_ratio < 0.01 or white_pixel_ratio > 0.2:
        print("✅ 未检测到明显水印，继续生成。")
        return Image.open(image_path).convert('RGB')

    print("⚠️ 检测到水印，正在使用 OpenCV 修复去除...")
    result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    print("✅ 水印去除完成！")
    return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))

# ==================== 🚀 核心：加载模型管道 ====================
def setup_pipeline():
    print(f"\n[系统] 正在加载 AI 模型...")

    # ========== 🆕 明确双系统互斥的最终模型路径选择 ==========
    if USE_OPENVINO_MODEL:
        # 【开】OpenVINO 分支
        try:
            from tools.config import SD_OV_MODEL_PATH
            model_path = SD_OV_MODEL_PATH
        except ImportError:
            print("❌ 错误：试图使用 OpenVINO，但 config.py 中没有定义 SD_OV_MODEL_PATH。")
            sys.exit(1)

        print(f"⚡ [配置] 使用 OpenVINO 加速模式")
        print(f"   📂 模型路径: {model_path}")
        
        try:
            from optimum.intel import OVStableDiffusionPipeline
            print("⚡ 尝试加载 OpenVINO 接口...")
            
            if not (os.path.isdir(model_path) and any(f.endswith('.xml') for f in os.listdir(model_path))):
                raise FileNotFoundError(f"指定路径不是有效的 OpenVINO 模型目录: {model_path}")
                
            pipe = OVStableDiffusionPipeline.from_pretrained(model_path)
            print("✅ OpenVINO 模型加载成功！")
            
        except Exception as e:
            print(f"❌ OpenVINO 加载失败: {e}")
            sys.exit(1)

    else:
        # 【关】普通模型分支
        # 👑 核心修改：动态去 config.py 里面拿对应的 0~3 路径，只在进入这个分支时才触发
        try:
            from tools.config import SD_MODEL_PATH_0, SD_MODEL_PATH_1, SD_MODEL_PATH_2, SD_MODEL_PATH_3
            model_paths = [SD_MODEL_PATH_0, SD_MODEL_PATH_1, SD_MODEL_PATH_2, SD_MODEL_PATH_3]
            
            if 0 <= ACTIVE_MODEL < len(model_paths):
                model_path = model_paths[ACTIVE_MODEL]
            else:
                print(f"⚠️ [警告] ACTIVE_MODEL = {ACTIVE_MODEL} 超出范围，默认使用 SD_MODEL_PATH_0")
                model_path = SD_MODEL_PATH_0
        except ImportError:
            # 既然进入了 else 分支，说明在 config.py 里 USE_OPENVINO_MODEL=False，
            # 但即便这样，如果出现异常，也是以防万一的兜底。
            print("❌ 错误：普通模型分支无法加载路径。请检查 config.py 的 else 分支。")
            sys.exit(1)
            
        print(f"⚡ [配置] 使用普通模型模式 (ACTIVE_MODEL = {ACTIVE_MODEL})")
        print(f"   📂 模型路径: {model_path}")
        
        if os.path.isdir(model_path):
            import glob
            safetensors_files = glob.glob(os.path.join(model_path, "*.safetensors"))
            if safetensors_files:
                model_path = safetensors_files[0]
                print(f"   🔍 自动定位到目录内的模型文件: {os.path.basename(model_path)}")
            else:
                print(f"❌ 错误：在目录 {model_path} 中找不到任何 .safetensors 文件。")
                sys.exit(1)
                
        try:
            pipe = StableDiffusionPipeline.from_single_file(
                model_path,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                use_safetensors=True
            )
            pipe.to("cpu")
            print("✅ 普通模型加载成功！")
            
        except Exception as e:
            print(f"❌ 普通模型加载失败: {e}")
            sys.exit(1)
    
    # 公共配置
    try:
        pipe.enable_vae_slicing()
        pipe.enable_attention_slicing()
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
    except Exception as e:
        print(f"⚠️ 注意：模型后处理优化失败，但不影响主功能。错误: {e}")
        
    print("[系统] 模型管道已就绪！")
    return pipe
    
def build_prompt(config):
    """
    分层构建提示词
    支持三种格式：
    1. 分层格式：subjects + styles + moods
    2. 扁平格式：只有 subjects（兼容旧配置）
    3. 内容文本扩展：subjects + styles + moods + content_texts（需开启 USE_CONTENT_TEXTS）
    """
    if "styles" in config and "moods" in config:
        subject = random.choice(config["subjects"])
        style = random.choice(config["styles"])
        mood = random.choice(config["moods"])
        
        # 如果开启且存在 content_texts，随机选一句添加
        if USE_CONTENT_TEXTS and "content_texts" in config and config["content_texts"]:
            text = random.choice(config["content_texts"])
            # ✨ 修改点：去掉死板的 "calligraphy text: "，将文字融入画面描述
            prompt = f"{subject}, {style}, {mood}, the scroll features the Chinese characters '{text}' written in flowing calligraphy"
            print(f"   📜 已添加内容文本: {text[:20]}...")
        else:
            prompt = f"{subject}, {style}, {mood}"
        return prompt, "分层"
    else:
        prompt = random.choice(config["subjects"])
        return prompt, "扁平"
        
def generate_style(pipe, init_image, prompt, output_filename, strength, mode="img2img", steps=STEPS, target_style="unknown"):
    """
    生成单张图片
    mode: "img2img" 或 "txt2img"
    steps: 当前生成使用的步数
    """
    import random  # ✅ 添加这一行    
    max_limit = MAX_LIMIT
    
    if mode == "img2img":
        # 图生图：使用原图尺寸
        w, h = init_image.size
        if w > max_limit or h > max_limit:
            if w > h:
                scale = max_limit / w
            else:
                scale = max_limit / h
            w, h = int(w * scale), int(h * scale)
        w, h = ((w+31)//64)*64, ((h+31)//64)*64
        image = init_image.resize((w, h), Image.Resampling.LANCZOS)
        print(f"[图生图] {os.path.basename(output_filename)} ({w}x{h})")
    else:
        # 文生图：随机选择尺寸，增加多样性
        aspect_ratios = [
            (512, 512), (512, 576), (576, 512),
            (512, 640), (640, 512), 
            (512, 768), (768, 512), 
            (576, 768), (768, 576),
            (448, 640), (640, 448),
            # --- 手机壁纸（竖屏） ---
            (768, 1360), (1080, 1920), (768, 1024),
            # --- 电脑壁纸（横屏） ---
            (1024, 576), (1280, 720), (1360, 768),
            # --- 经典正方形 ---
            (768, 768), (1024, 1024)            
        ]
        w, h = random.choice(aspect_ratios)
        # 限制最大尺寸
        if w > max_limit: w = max_limit
        if h > max_limit: h = max_limit
        w, h = ((w+31)//64)*64, ((h+31)//64)*64
        image = None
        print(f"[文生图] {os.path.basename(output_filename)} ({w}x{h})")

    # ========== 安全模式处理 ==========
    if SAFE_MODE:
        if SAFE_MODE_STRATEGY == "simple":
            # 简单模式：直接加 wearing clothes
            full_prompt = f"{prompt}, wearing clothes"
            print(f"🛡️ [安全模式] 策略: 简单 (附加 wearing clothes)")
        elif SAFE_MODE_STRATEGY == "filter":
            # 过滤模式：移除露骨词汇
            safe_prompt = prompt.replace("nude", "").replace("naked", "").replace("explicit", "").replace("pornographic", "")
            safe_prompt = ", ".join([p for p in safe_prompt.split(",") if "sex" not in p.lower() and "hentai" not in p.lower() and "penetration" not in p.lower()])
            # 清理多余的逗号和空格
            safe_prompt = ", ".join([p.strip() for p in safe_prompt.split(",") if p.strip()])
            full_prompt = safe_prompt if safe_prompt.strip() else prompt
            print(f"🛡️ [安全模式] 策略: 过滤 (移除露骨词汇)")
        else:
            # 默认：简单模式
            full_prompt = f"{prompt}, wearing clothes"
            print(f"🛡️ [安全模式] 策略: 默认 (附加 wearing clothes)")
        
        # 统一使用强化版负面提示词
        neg_prompt = (
            "worst quality, low quality, ugly, deformed, blurry, watermark, signature, logo, brand, "
            "bad hands, extra fingers, missing fingers, fused fingers, deformed hands, "
            "mutated hands, poorly drawn hands, six fingers, eleven fingers, "
            "bad anatomy, malformed limbs, extra limbs, missing limbs, "
            "bad proportions, disfigured, gross proportions, "
            "bad feet, extra toes, missing toes, fused toes, "
            "jumbled text, gibberish characters, messy ink, smudged writing, illegible scribbles, unreadable signs"            
        )
    else:
        full_prompt = prompt
        neg_prompt = (
            "worst quality, low quality, ugly, deformed, blurry, watermark, signature, logo, brand, "
            "bad hands, extra fingers, missing fingers, fused fingers, deformed hands, "
            "mutated hands, poorly drawn hands, six fingers, eleven fingers, "
            "bad anatomy, malformed limbs, extra limbs, missing limbs, "
            "bad proportions, disfigured, gross proportions, "
            "bad feet, extra toes, missing toes, fused toes, "
            "extra arm, extra hand, missing arm, missing hand, "
            "fused hand, extra digit, wrong finger count, "
            "deformed finger, twisted finger, broken finger, "
            "claw hand, abnormal hand, mutant hand, "
            "bad pose, unnatural pose, contorted body, twisted body, "
            "jumbled text, gibberish characters, messy ink, smudged writing, illegible scribbles, meaningless strokes"
        )
        print(f"🔓 [自由模式已启用]")
    
    # ========== 🧠 自动添加解剖约束 ==========
    # 检测是否包含复杂姿势关键词，自动添加约束
    complex_pose_keywords = [
        "sex", "posing", "bending", "kneeling", "lying", 
        "standing", "spooning", "riding", "missionary", 
        "doggy", "cowgirl", "spread", "bent over", 
        "on top", "from behind", "oral", "blowjob", 
        "cunnilingus", "group", "threesome"
    ]
    
    # 检测是否包含多人关键词
    multi_person_keywords = ["two", "multiple", "group", "couple", "pair", "man and woman", "both bodies"]
    
    # 检测是否包含天使/翅膀关键词
    wing_keywords = ["angel wings", "feathered wings", "bird wings", "butterfly wings", "dragon wings", "wings spread", "winged figure"]
    
    # ✨ 草稿阻断逻辑：遇到结构草稿，清空翅膀检测
    sketch_keywords = ["sketch", "pencil", "draft", "wireframe", "construction", "anatomy", "lineart", "structural"]
    if any(keyword in prompt.lower() for keyword in sketch_keywords):
        wing_keywords = []
        
    # 构建约束
    constraints = []
    
    # 复杂姿势约束
    if any(keyword in prompt.lower() for keyword in complex_pose_keywords):
        constraints.append("natural body position")
        constraints.append("correct anatomy")
        constraints.append("realistic hands and feet")
    
    # 多人场景约束
    if any(keyword in prompt.lower() for keyword in multi_person_keywords):
        constraints.append("two hands per person")
        constraints.append("two feet per person")
        constraints.append("normal proportions")
    
    # 翅膀约束
    if any(keyword in prompt.lower() for keyword in wing_keywords):
        constraints.append("symmetrical wings")
        constraints.append("beautiful feathered wings")
    
    # 如果有约束，添加到提示词末尾
    if constraints:
        constraint_text = ", ".join(constraints)
        full_prompt = f"{full_prompt}, {constraint_text}"
        print(f"   🧠 已添加解剖约束: {constraint_text}")
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 提示词: {full_prompt[:80]}...")
    print(f"  步数: {steps}")
    
    generator = torch.Generator("cpu").manual_seed(int(time.time_ns() % 1000000000))
    
    if mode == "img2img":
        result = pipe(
            prompt=full_prompt,
            negative_prompt=neg_prompt,
            image=image,
            strength=strength,
            num_inference_steps=steps,
            guidance_scale=7.5,
            generator=generator,
            width=w,
            height=h
        )
    else:
        # 文生图：不传 image，用纯随机噪声
        result = pipe(
            prompt=full_prompt,
            negative_prompt=neg_prompt,
            num_inference_steps=steps,
            guidance_scale=7.5,
            generator=generator,
            width=w,
            height=h
        )
    
    # 保存图片
    result.images[0].save(output_filename, quality=95)

    # ========== 🆕 检测风格 ==========
    prompt_lower = prompt.lower()
    is_sketch = False
    if AUTO_DETECT_STYLE:
        is_sketch = any(kw in prompt_lower for kw in SKETCH_KEYWORDS)
        # 也检查目标风格名称
        if not is_sketch:
            is_sketch = any(kw in target_style.lower() for kw in SKETCH_KEYWORDS)
    
    if is_sketch:
        print(f"\n🎨 检测到素描/线稿风格，仅清除元数据，跳过相机相关处理")
    # ================================
    
    # ========== 🆕 消除AI痕迹 - 后期处理 ==========
    if REMOVE_AI_TRACES:
        try:
            print(f"\n📷 消除AI痕迹处理...")
            final_path = output_filename
            
            # 1️⃣ 清除元数据（如果需要）
            if AI_CLEAR_METADATA:

                # 转换为JPG并清除元数据
                jpg_path = output_filename.replace('.png', '.jpg')
                final_path = smart_clean_image(
                    final_path, 
                    output_path=jpg_path,
                    method='jpg',
                    jpg_quality=92
                )
                print(f"   ✅ 元数据已清除 -> JPG")

            # ========== 🆕 素描风格：跳过相机相关处理 ==========
            if is_sketch:
                print(f"   🎨 素描风格，跳过: 照片真实化 / EXIF注入 / 紫边模拟 / 真实噪点")
                # 跳过所有相机相关处理
                pass
            else:
                    
                # 2️⃣ 照片真实化（添加噪点、暗角、锐化）
                if AI_REALISTIC:
                    
                    final_path = make_photo_realistic(
                        final_path,
                        final_path,  # 覆盖原文件
                        camera=AI_CAMERA,
                        style="portrait",
                        inject_exif_data=AI_INJECT_EXIF,  # 同时注入EXIF
                        randomize=True,
                        strength=AI_STRENGTH
                    )
                    print(f"   ✅ 照片真实化完成 (强度: {AI_STRENGTH})")
                
                # 3️⃣ 如果只注入EXIF（不开启照片真实化）
                elif AI_INJECT_EXIF and not AI_REALISTIC:
                    # ⏳ 强制等待 0.5 秒，确保前一步的 opencv/PIL 文件句柄彻底释放
                    
                    time.sleep(0.5)
                    
                    # 使用 try 包裹，防止底层 shutil 依然引发 WinError
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
                        print(f"   ⚠️ EXIF 注入过程抛异常，已跳过: {e}")

                # ========== 🆕 图像指纹混淆 ==========
                if AI_FINGERPRINT_OBFUSCATION:
                    try:
                        print(f"   🔍 图像指纹混淆...")
                        from PIL import Image
                        import random
                        import numpy as np
                        
                        img = Image.open(final_path)
                        w, h = img.size
                        
                        # 1️⃣ 微小透视扭曲（破坏AI像素规律）
                        strength = AI_DISTORTION_STRENGTH
                        coeffs = [
                            1 + random.uniform(-strength, strength),
                            random.uniform(-strength * 0.5, strength * 0.5),
                            random.uniform(-2, 2),
                            random.uniform(-strength * 0.5, strength * 0.5),
                            1 + random.uniform(-strength, strength),
                            random.uniform(-2, 2),
                        ]
                        img = img.transform((w, h), Image.AFFINE, coeffs, Image.Resampling.BILINEAR)
                        print(f"      ✅ 微小扭曲完成")
                        
                        # ========== 🆕 2️⃣ 紫边模拟（真实镜头特征） ==========
                        if AI_CHROMATIC_ABERRATION:
                            # 转为numpy数组处理
                            arr = np.array(img).astype(np.float32)
                            h, w = arr.shape[:2]
                            strength = AI_CHROMATIC_STRENGTH
                            
                            # 在图像边缘添加红/蓝通道偏移（紫边特征）
                            for y in range(h):
                                for x in range(w):
                                    # 计算距离边缘的距离
                                    dist_from_edge = min(x, w-1-x, y, h-1-y)
                                    if dist_from_edge < 40:
                                        # 越靠近边缘，紫边越明显
                                        shift_factor = (40 - dist_from_edge) / 40
                                        shift = shift_factor * strength * random.uniform(0.5, 1.0)
                                        # 红色通道偏移（紫色倾向）
                                        arr[y, x, 0] += random.uniform(-shift, shift * 0.5)  # R
                                        arr[y, x, 2] += random.uniform(-shift * 0.5, shift)  # B
                            
                            # 裁剪到有效范围
                            arr = np.clip(arr, 0, 255).astype(np.uint8)
                            
                            # 🛡️ 修复：确保维度是 HWC 且转为 RGB 标准格式，防止 OpenCV 读取到 CV_64F
                            if arr.ndim == 3 and arr.shape[2] == 3:
                                img = Image.fromarray(arr).convert('RGB')
                            else:
                                # 兜底，如果是 RGBA，扔掉透明通道
                                img = Image.fromarray(arr[:, :, :3]).convert('RGB')
                            print(f"      ✅ 紫边模拟完成 (强度: {strength})")
                        # ===================================================

                        # ========== 🆕 3️⃣ 真实噪点 ==========
                        if AI_REALISTIC_NOISE:
                            import cv2
                            import numpy as np
                            
                            # 确定ISO值
                            if AI_NOISE_RANDOMIZE:
                                # 在基准值附近随机变化 ±200
                                iso = AI_NOISE_ISO_BASE + random.randint(-200, 200)
                                iso = max(100, min(1600, iso))  # 限制范围
                            else:
                                iso = AI_NOISE_ISO_BASE
                            
                            # 🛡️ 终极修复：强制转换为 uint8 类型，阻止 OpenCV 误判为 CV_64F
                            img_cv = cv2.cvtColor(np.array(img).astype(np.uint8), cv2.COLOR_RGB2BGR)
                            
                            # 基于ISO的噪声强度
                            noise_std = 0.005 * (iso / 100) ** 0.5
                            
                            # 高斯噪声（模拟传感器热噪声）
                            gaussian_noise = np.random.normal(0, noise_std * 255, img_cv.shape)
                            
                            # 散粒噪声（泊松分布模拟，光子噪声）
                            shot_noise = np.random.poisson(np.abs(img_cv) * 0.005) * 0.1
                            
                            # 合并噪声
                            img_cv = img_cv + gaussian_noise + shot_noise
                            
                            # 暗部噪点增强（真实相机特征：暗部噪点更明显）
                            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                            dark_mask = gray < 80
                            if np.any(dark_mask):
                                dark_noise = np.random.normal(0, noise_std * 255 * 0.5, img_cv.shape)
                                img_cv[dark_mask] = img_cv[dark_mask] + dark_noise[dark_mask]
                            
                            # 裁剪到有效范围
                            img_cv = np.clip(img_cv, 0, 255).astype(np.uint8)
                            img = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
                            print(f"      ✅ 真实噪点添加完成 (ISO: {iso})")
                        # ================================================

                        # ========== 🆕 4️⃣ 轻微裁剪 ==========
                        if AI_MINOR_CROP:
                            import random
                            
                            crop_pct = AI_CROP_PERCENT * random.uniform(0.5, 1.5)
                            crop_w = int(w * crop_pct)
                            crop_h = int(h * crop_pct)
                            
                            # 确保裁剪量合理
                            crop_w = max(5, min(crop_w, int(w * 0.05)))
                            crop_h = max(5, min(crop_h, int(h * 0.05)))
                            
                            # 随机选择裁剪位置（从左上、右上、左下、右下中选）
                            corners = [
                                (0, 0),                      # 左上
                                (0, crop_h),                 # 左下
                                (crop_w, 0),                 # 右上
                                (crop_w, crop_h),            # 右下
                            ]
                            # 也可以使用随机位置
                            if random.random() < 0.5:
                                left = random.randint(0, crop_w)
                                top = random.randint(0, crop_h)
                            else:
                                left, top = random.choice(corners)
                            
                            right = w - random.randint(0, crop_w)
                            bottom = h - random.randint(0, crop_h)
                            
                            # 确保裁剪区域有效
                            if right > left + 50 and bottom > top + 50:
                                img = img.crop((left, top, right, bottom))
                                # 重新缩放回原尺寸（保持一致性）
                                img = img.resize((w, h), Image.Resampling.LANCZOS)
                                print(f"      ✅ 轻微裁剪完成 (裁切: {crop_pct*100:.1f}%, 位置: {left},{top})")
                            else:
                                print(f"      ⚠️ 裁剪跳过 (区域无效)")
                        # ================================================
        
                        img.save(final_path, quality=92)
                        print(f"   ✅ 指纹混淆完成")
                        
                    except Exception as e:
                        print(f"   ⚠️ 指纹混淆失败: {e}")
            
            # 如果最终路径改变了，更新文件名
            if final_path != output_filename:
                # 删除原始PNG（如果存在）
                if os.path.exists(output_filename) and output_filename != final_path:
                    try:
                        os.remove(output_filename)
                    except:
                        pass
                output_filename = final_path

                
        except Exception as e:
            print(f"   ⚠️ 消除AI痕迹失败: {e}")
    # ================================================
    

    # 只要生成图片成功，就在同一目录下生成一个同名的 .txt 说明文件
    metadata_filename = output_filename.replace('.png', '.txt').replace('.jpg', '.txt')
    try:
        with open(metadata_filename, "w", encoding="utf-8") as f:
            f.write(f"【生成时间】: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"【风格名称】: {target_style}\n")
            f.write(f"【生成模式】: {mode}\n")
            f.write(f"【迭代步数】: {steps}\n")
            f.write(f"【提示词强度】: {strength}\n")
            f.write(f"【完整正向提示词】: \n{full_prompt}\n")
            if mode == "img2img":
                f.write(f"【参考图路径】: {input_path if 'input_path' in locals() else '默认 input.jpg'}\n")
            if REMOVE_AI_TRACES:
                f.write(f"【消除AI痕迹】: 已启用\n")
                f.write(f"   - 相机: {AI_CAMERA}\n")
                f.write(f"   - 强度: {AI_STRENGTH}\n")
                
                if is_sketch:
                    f.write(f"   - 风格: 素描/线稿 (跳过相机相关处理)\n")
            
                if AI_FINGERPRINT_OBFUSCATION:
                    f.write(f"   - 指纹混淆: 已启用\n")  
                    
                if AI_CHROMATIC_ABERRATION:  # 🆕
                    f.write(f"   - 紫边模拟: 已启用\n")

                if AI_REALISTIC_NOISE:  # 🆕
                    f.write(f"   - 真实噪点: 已启用 (ISO: {AI_NOISE_ISO_BASE})\n")

                if AI_MINOR_CROP:  # 🆕
                    f.write(f"   - 轻微裁剪: 已启用 ({AI_CROP_PERCENT*100:.1f}%)\n")        
        
        print(f"   📝 已生成提示词记录: {os.path.basename(metadata_filename)}")
    except Exception as e:
        print(f"   ⚠️ 提示词记录文件写入失败: {e}")
    
 
    
# ==================== 🚀 主入口 ====================

def parse_arguments(args):
    """
    解析命令行参数
    返回: (target_style, count, mode, search_keyword, steps, input_path)
    """
    target_style = None
    count = None
    mode = "img2img"
    search_keyword = None
    steps = None
    input_path = None

    # 新增参数
    clean_ai = True  # 默认启用
    no_clean = False
    
    i = 1
    while i < len(args):
        arg = args[i]
        if arg in ["-n", "--count"]:
            if i + 1 < len(args):
                try:
                    count = int(args[i + 1])
                    if count <= 0:
                        print(f"❌ 数量必须大于0，当前: {count}")
                        sys.exit(1)
                    i += 2
                except ValueError:
                    print(f"❌ 无效的数字: {args[i + 1]}")
                    sys.exit(1)
            else:
                print(f"❌ 参数 {arg} 需要指定数量")
                sys.exit(1)
        elif arg in ["--txt2img", "--t2i"]:
            mode = "txt2img"
            i += 1
        elif arg in ["--img2img", "--i2i"]:
            mode = "img2img"
            i += 1
        elif arg in ["--steps"]:
            if i + 1 < len(args):
                try:
                    steps = int(args[i + 1])
                    if steps <= 0:
                        print(f"❌ 步数必须大于0，当前: {steps}")
                        sys.exit(1)
                    i += 2
                except ValueError:
                    print(f"❌ 无效的步数: {args[i + 1]}")
                    sys.exit(1)
            else:
                print(f"❌ 参数 {arg} 需要指定步数")
                sys.exit(1)
        elif arg in ["--input"]:
            if i + 1 < len(args):
                input_path = args[i + 1]
                i += 2
            else:
                print(f"❌ 参数 {arg} 需要指定文件路径")
                sys.exit(1)
        elif arg in ["--search", "-s"]:
            if i + 1 < len(args):
                search_keyword = args[i + 1]
                i += 2
            else:
                print(f"❌ 参数 {arg} 需要指定搜索关键词")
                sys.exit(1)
        elif arg in ["--no-clean", "--noclean"]:
            no_clean = True
            i += 1                
        else:
            target_style = arg
            i += 1
    
    return target_style, count, mode, search_keyword, steps, input_path, no_clean

def main():
    # ========== 处理无参数情况 ==========
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)
    
    # ========== 解析参数 ==========
    target_style, user_count, mode, search_keyword, user_steps, user_input, no_clean = parse_arguments(sys.argv)

    # ========== 🆕 根据命令行参数控制消除AI痕迹 ==========
    global REMOVE_AI_TRACES
    if no_clean:
        REMOVE_AI_TRACES = False
        print(f"ℹ️ 已禁用消除AI痕迹 (--no-clean)")
    else:
        print(f"ℹ️ 消除AI痕迹已启用 (相机: {AI_CAMERA}, 强度: {AI_STRENGTH})")
    # =====================================================
    
    # ========== 处理搜索 ==========
    if search_keyword:
        print(f"\n🔍 搜索包含 '{search_keyword}' 的风格：")
        print("="*60)
        found = []
        for name, config in STYLE_PROMPTS.items():
            folder = config.get("folder", "")
            if search_keyword.lower() in name.lower() or search_keyword.lower() in folder.lower():
                found.append((name, folder))
        
        if found:
            print(f"找到 {len(found)} 个匹配的风格：\n")
            for i, (name, folder) in enumerate(found, 1):
                print(f"  {i:3d}. {name} -> {folder}")
        else:
            print(f"  ❌ 没有找到包含 '{search_keyword}' 的风格")
        
        print("\n" + "="*60)
        print("💡 使用方式：python generate.py <风格名称> [-n <数量>]")
        sys.exit(0)
    
    # ========== 处理 --list 或 -l ==========
    if target_style == "--list" or target_style == "-l":
        print_style_list()
        sys.exit(0)
    
    # ========== 解析参数 ==========
    target_style, user_count, mode, search_keyword, user_steps, user_input, no_clean = parse_arguments(sys.argv)
    
    if target_style is None:
        print("❌ 请指定风格名称")
        print_usage()
        sys.exit(1)
    
    if target_style not in STYLE_PROMPTS:
        print(f"\n❌ 错误：找不到风格 '{target_style}'！")
        print("📋 可用风格列表：")
        styles = list(STYLE_PROMPTS.keys())
        for i, key in enumerate(styles[:10]):
            print(f"   - {key}")
        if len(styles) > 10:
            print(f"   ... 共 {len(styles)} 个风格")
        print("\n💡 使用 python generate.py --list 查看完整列表")
        sys.exit(1)

    # ========== 处理输入图片 ==========
    if mode == "img2img":
        # ✨ 优先使用命令行指定的输入文件
        input_path = find_input_image(user_input)
        if not input_path:
            print(f"\n❌ 图生图模式需要参考图！请用 --input 指定或把图片命名为 {INPUT_IMAGE_NAME}.jpg/.png 放在 tools 目录下！")
            return
        init_image = remove_watermark(input_path)
    else:
        init_image = None
        print(f"\n🎨 文生图模式：无需参考图，从零生成")

    # ========== 加载模型 ==========
    pipe = setup_pipeline()

    config = STYLE_PROMPTS[target_style]
    
    # ========== 计算生成数量 ==========
    # 检查是分层还是扁平
    if "styles" in config and "moods" in config:
        mode_type = "分层"
        total_possible = len(config["subjects"]) * len(config["styles"]) * len(config["moods"])
        default_count = len(config["subjects"])
        combo_info = f" ({len(config['subjects'])}×{len(config['styles'])}×{len(config['moods'])}={total_possible}种组合)"
    else:
        mode_type = "扁平"
        total_possible = len(config["subjects"])
        default_count = len(config["subjects"])
        combo_info = ""
    
    # 确定实际生成数量
    if user_count is not None:
        total_count = user_count
        count_source = f"用户指定"
        if user_count > total_possible:
            print(f"\n⚠️ 提示：您指定生成 {user_count} 张，但该风格最多只有 {total_possible} 种不同组合")
            print(f"   将生成 {total_possible} 张（全部组合）")
            total_count = total_possible
    else:
        total_count = default_count
        count_source = "全部提示词"
    
    print(f"\n🎯 正在生成风格: {target_style} -> {config['folder']}")
    print(f"📊 模式: {mode_type}{combo_info}")
    print(f"📊 本次共生成 {total_count} 张图片（{count_source}）")
    if mode_type == "分层":
        print(f"   ├─ 主体: {len(config['subjects'])} 种")
        print(f"   ├─ 风格: {len(config['styles'])} 种")
        print(f"   └─ 情绪: {len(config['moods'])} 种")
    if user_count and user_count > total_possible:
        print(f"   └─ ⚠️ 注: 实际生成 {total_possible} 张（全部组合）")
    elif user_count:
        print(f"   └─ 💡 注: 从 {total_possible} 种组合中随机选 {total_count} 张")

    # ========== 确定最终步数 ==========
    if user_steps is not None:
        actual_steps = user_steps
        print(f"⚙️ 步数: 命令行指定为 {user_steps} 步")
    else:
        actual_steps = STEPS
        print(f"⚙️ 步数: 使用 config.py 中的默认 {STEPS} 步")
    # =================================

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # ✨ 使用配置中的 folder 作为文件夹名，避免重名
    folder_name = config['folder']
    output_root = os.path.join(CURRENT_DIR, "output", f"{folder_name}_{timestamp}")
    os.makedirs(output_root, exist_ok=True)

    # ========== 📁 新增：子文件夹分组逻辑 ==========
    # 每5张图片放一个子文件夹
    BATCH_SIZE = 5
    
    # 预计算需要创建多少个子文件夹
    total_batches = (total_count + BATCH_SIZE - 1) // BATCH_SIZE  # 向上取整
    
    # 预创建所有子文件夹
    subfolders = []
    for batch_idx in range(total_batches):
        subfolder_name = f"{batch_idx + 1:04d}"  # 从 0001 开始，四位数字
        subfolder_path = os.path.join(output_root, subfolder_name)
        os.makedirs(subfolder_path, exist_ok=True)
        subfolders.append(subfolder_path)
        print(f"📁 已创建子文件夹: {subfolder_name} (存放第 {batch_idx * BATCH_SIZE + 1} - {min((batch_idx + 1) * BATCH_SIZE, total_count)} 张)")
    
    print(f"\n📊 共 {total_count} 张图片，将分到 {total_batches} 个子文件夹中（每 {BATCH_SIZE} 张一组）\n")
    # ===============================================

    # ========== 生成循环 ==========
    from tqdm import tqdm
    for i in tqdm(range(total_count), desc="生成进度"):
        prompt, prompt_mode = build_prompt(config)
        
        # 🆕 计算当前图片属于哪个子文件夹（从 0 开始计数）
        batch_index = i // BATCH_SIZE
        current_subfolder = subfolders[batch_index]
        
        print(f"\n🔄 进度：第 {i+1}/{total_count} 张 [{prompt_mode}] → 子文件夹 {batch_index + 1:04d}")
        
        # ✨ 生成带前缀的文件名，避免重名冲突
        safe_prefix = folder_name.replace(" ", "_").replace("/", "_")
        filename = f"{target_style}_{i+1:02d}.png"
        
        # 🆕 修改：将图片保存到子文件夹
        generate_style(
            pipe, 
            init_image, 
            prompt, 
            os.path.join(current_subfolder, filename),  # 👈 保存到子文件夹
            config["strength"],
            mode,
            actual_steps,
            target_style
        )
    # =================================

    print(f"\n✅ 全部完成！共 {total_count} 张图片，保存在: {output_root}")
    print(f"📁 图片已按每 {BATCH_SIZE} 张分到 {total_batches} 个子文件夹中")

if __name__ == "__main__":
    main()