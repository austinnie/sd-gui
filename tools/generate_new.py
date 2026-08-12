#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用生成器：根据提示词库自动出图（支持分层+扁平，全部生成）
用法：python generate.py <风格名称>
"""

import os
import sys
import io
import glob
import random
import time
from datetime import datetime
from tqdm import tqdm

# ========== 修复 Windows 终端编码 ==========
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 确保 tools 目录在路径中
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
    
    
from tools.config import (
    DEFAULT_STRENGTH, STEPS, INPUT_IMAGE_NAME, REMOVE_AI_TRACES,
    AI_APPRECIATION_ENGINE, FINAL_STEPS,
)
from tools.core import setup_pipeline, build_prompt, generate_style, Appraiser
from tools.core.postprocessor import is_sketch_style
from tools.utils.watermark import remove_watermark
from tools.utils.doc_generator import generate_word_doc, generate_text_summary
from prompts_config import STYLE_PROMPTS


def print_usage():
    """打印使用说明"""
    print("\n" + "=" * 60)
    print("📖 通用生成器使用说明")
    print("=" * 60)
    print("\n用法：")
    print("  python generate.py <风格名称>")
    print("  python generate.py <风格名称> -n <数量>")
    print("  python generate.py <风格名称> --steps <数字>")
    print("  python generate.py <风格名称> --input <参考图路径>")
    print("\n生成模式：")
    print("  --img2img, --i2i    图生图模式（默认，需要 input.jpg）")
    print("  --txt2img, --t2i    文生图模式（无需参考图）")
    print("\n其他命令：")
    print("  python generate.py --list     显示所有可用风格")
    print("  python generate.py -l         显示所有可用风格")
    print("  python generate.py --search <关键词>  搜索风格")
    print("=" * 60)


def print_style_list():
    """分屏显示风格列表"""
    styles = list(STYLE_PROMPTS.keys())
    total = len(styles)
    
    print("\n" + "=" * 60)
    print(f"📋 当前支持的风格列表（共 {total} 个）")
    print("=" * 60)
    
    page_size = 20
    total_pages = (total + page_size - 1) // page_size
    
    for page in range(total_pages):
        start = page * page_size
        end = min(start + page_size, total)
        
        print(f"\n📄 第 {page+1}/{total_pages} 页")
        print("-" * 40)
        
        for i in range(start, end):
            style_name = styles[i]
            folder = STYLE_PROMPTS[style_name].get("folder", "")
            folder_info = f" -> {folder}" if folder else ""
            print(f"  {i+1:3d}. {style_name}{folder_info}")
        
        if page < total_pages - 1:
            input("\n按 Enter 继续查看下一页...")


def find_input_image(custom_input=None):
    """查找参考图"""
    if custom_input and os.path.exists(custom_input):
        return custom_input
    
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = os.path.join(CURRENT_DIR, INPUT_IMAGE_NAME + ext)
        if os.path.exists(path):
            return path
    return None


def parse_arguments(args):
    """解析命令行参数"""
    from tools.config import DEFAULT_MODE
    
    target_style = None
    count = None
    mode = DEFAULT_MODE
    search_keyword = None
    steps = None
    input_path = None
    use_old = False
    no_clean = False
    
    i = 1
    while i < len(args):
        arg = args[i]
        if arg in ["-n", "--count"]:
            if i + 1 < len(args):
                try:
                    count = int(args[i + 1])
                    if count <= 0:
                        print(f"❌ 数量必须大于0")
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
                    i += 2
                except ValueError:
                    print(f"❌ 无效的步数")
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
        elif arg in ["--use-old", "--use_old"]:
            use_old = True
            i += 1
        else:
            target_style = arg
            i += 1
    
    return target_style, count, mode, search_keyword, steps, input_path, no_clean, use_old


def main():
    # ========== 处理无参数 ==========
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)
    
    # ========== 解析参数 ==========
    target_style, user_count, mode, search_keyword, user_steps, user_input, no_clean, use_old = parse_arguments(sys.argv)
    
    # ========== 全局 REMOVE_AI_TRACES 覆盖 ==========
    if no_clean:
        global REMOVE_AI_TRACES
        REMOVE_AI_TRACES = False
        print(f"ℹ️ 已禁用消除AI痕迹 (--no-clean)")
    
    # ========== 搜索 ==========
    if search_keyword:
        print(f"\n🔍 搜索包含 '{search_keyword}' 的风格：")
        print("=" * 60)
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
        sys.exit(0)
    
    # ========== 列出风格 ==========
    if target_style in ["--list", "-l"]:
        print_style_list()
        sys.exit(0)
    
    # ========== 验证风格 ==========
    if target_style not in STYLE_PROMPTS:
        print(f"\n❌ 错误：找不到风格 '{target_style}'！")
        styles = list(STYLE_PROMPTS.keys())
        for i, key in enumerate(styles[:10]):
            print(f"   - {key}")
        if len(styles) > 10:
            print(f"   ... 共 {len(styles)} 个风格")
        print("\n💡 使用 python generate.py --list 查看完整列表")
        sys.exit(1)
    
    # ========== 处理输入图片 ==========
    if mode == "img2img":
        input_path = find_input_image(user_input)
        if not input_path:
            print(f"\n❌ 图生图模式需要参考图！请用 --input 指定")
            return
        init_image = remove_watermark(input_path)
    else:
        init_image = None
        print(f"\n🎨 文生图模式：无需参考图，从零生成")
    
    # ========== 加载模型 ==========
    pipe = setup_pipeline()
    
    # ========== 获取配置 ==========
    config = STYLE_PROMPTS[target_style]
    
    # 计算生成数量
    if "styles" in config and "moods" in config:
        mode_type = "分层"
        total_possible = len(config["subjects"]) * len(config["styles"]) * len(config["moods"])
        default_count = len(config["subjects"])
    else:
        mode_type = "扁平"
        total_possible = len(config["subjects"])
        default_count = len(config["subjects"])
    
    if user_count is not None:
        total_count = min(user_count, total_possible)
    else:
        total_count = default_count
    
    # ========== 步数 ==========
    actual_steps = user_steps if user_steps is not None else FINAL_STEPS
    
    # ========== 输出目录 ==========
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = config['folder']
    output_root = os.path.join(CURRENT_DIR, "output", f"{folder_name}_{timestamp}")
    os.makedirs(output_root, exist_ok=True)
    
    # 子文件夹分组
    BATCH_SIZE = 5
    total_batches = (total_count + BATCH_SIZE - 1) // BATCH_SIZE
    subfolders = []
    for batch_idx in range(total_batches):
        subfolder_name = f"{batch_idx + 1:04d}"
        subfolder_path = os.path.join(output_root, subfolder_name)
        os.makedirs(subfolder_path, exist_ok=True)
        subfolders.append(subfolder_path)
    
    print(f"\n📊 共 {total_count} 张图片，分到 {len(subfolders)} 个子文件夹中")
    
    # ========== 初始化鉴赏器 ==========
    appraiser = Appraiser()
    
    # ========== 生成循环 ==========
    batch_reviews = []
    DOCX_AVAILABLE = True
    try:
        from docx import Document
    except ImportError:
        DOCX_AVAILABLE = False
    
    for i in range(total_count):
        prompt, prompt_mode = build_prompt(config)
        
        batch_index = i // BATCH_SIZE
        if batch_index >= len(subfolders):
            batch_index = len(subfolders) - 1
        current_subfolder = subfolders[batch_index]
        
        print(f"\n🔄 进度：第 {i+1}/{total_count} 张 [{prompt_mode}]")
        
        filename = f"{target_style}_{i+1:02d}.png"
        
        # 决定 strength
        final_strength = DEFAULT_STRENGTH
        for arg in sys.argv:
            if arg.startswith('--strength='):
                try:
                    final_strength = float(arg.split('=')[1])
                    break
                except:
                    pass
        
        # 生成图片
        final_output_path = generate_style(
            pipe,
            init_image,
            prompt,
            os.path.join(current_subfolder, filename),
            final_strength,
            mode,
            actual_steps,
            target_style
        )
        
        # ========== AI 鉴赏 ==========
        caption = appraiser.appraise(final_output_path, prompt)
        
        # 构建鉴赏段落
        if "masterpiece" in caption or "best quality" in caption:
            content_desc = prompt[:100] + "..." if len(prompt) > 100 else prompt
        else:
            content_desc = caption[:100] + "..." if len(caption) > 100 else caption
        
        review_paragraph = (
            f"本次 AI 艺术创作描绘了这样一幅画面：“{content_desc}”。\n"
            f"在细腻的笔触和先进的大模型算法加持下，图片不仅呈现出逼真的手办质感，\n"
            f"更通过精准的光影构图，传递出独特的视觉氛围与角色气质。\n"
            f"这是一张兼具技术质感与艺术审美的精致作品。"
        )
        
        batch_reviews.append(f"【第 {len(batch_reviews)+1} 张作品】\n{review_paragraph}")
        
        # ========== 批量生成文档 ==========
        is_last_item = (i == total_count - 1)
        is_batch_end = ((i + 1) % BATCH_SIZE == 0)
        
        if is_batch_end or is_last_item:
            if DOCX_AVAILABLE:
                generate_word_doc(current_subfolder, folder_name, batch_reviews)
            generate_text_summary(current_subfolder, folder_name, batch_reviews)
            batch_reviews = []
    
    print(f"\n✅ 全部完成！共 {total_count} 张图片，保存在: {output_root}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ 用户取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()