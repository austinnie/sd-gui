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
import random
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

# 加载全局配置与提示词库
from config import SD_MODEL_PATH, STEPS, MAX_LIMIT, INPUT_IMAGE_NAME
from prompts_config import STYLE_PROMPTS

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

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

def setup_pipeline():
    print(f"\n[系统] 正在加载 AI 模型...")
    model_path = SD_MODEL_PATH

    pipe = StableDiffusionPipeline.from_single_file(
        model_path,
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
        
def generate_style(pipe, init_image, prompt, output_filename, strength, mode="img2img", steps=STEPS):
    """
    生成单张图片
    mode: "img2img" 或 "txt2img"
    steps: 当前生成使用的步数
    """
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
    
    print(f"  提示词: {full_prompt[:80]}...")
    print(f"  步数: {steps}")
    
    generator = torch.Generator("cpu").manual_seed(int(time.time_ns() % 1000000000))
    
    if mode == "img2img":
        result = pipe(
            prompt=full_prompt,
            negative_prompt=neg_prompt,
            image=image,
            strength=strength,
            num_inference_steps=steps, # 👈 使用传入的步数
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
            num_inference_steps=steps, # 👈 使用传入的步数
            guidance_scale=7.5,
            generator=generator,
            width=w,
            height=h
        )
    
    result.images[0].save(output_filename, quality=95)
    
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
        else:
            target_style = arg
            i += 1
    
    return target_style, count, mode, search_keyword, steps, input_path

def main():
    # ========== 处理无参数情况 ==========
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)
    
    # ========== 解析参数 ==========
    target_style, user_count, mode, search_keyword, user_steps, user_input = parse_arguments(sys.argv)
    
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
    target_style, user_count, mode, search_keyword, user_steps, user_input = parse_arguments(sys.argv)
    
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

    # ========== 生成循环 ==========
    for i in range(total_count):
        prompt, prompt_mode = build_prompt(config)
        
        print(f"\n🔄 进度：第 {i+1}/{total_count} 张 [{prompt_mode}]")
        
        # ✨ 生成带前缀的文件名，避免重名冲突
        safe_prefix = folder_name.replace(" ", "_").replace("/", "_")
        filename = f"{safe_prefix}-{i+1:02d}.png"
        
        generate_style(
            pipe, 
            init_image, 
            prompt, 
            os.path.join(output_root, filename), 
            config["strength"],
            mode,
            actual_steps  # 👈 传递最终确定的步数
        )
    # =================================

    print(f"\n✅ 全部完成！共 {total_count} 张图片，保存在: {output_root}")

if __name__ == "__main__":
    main()