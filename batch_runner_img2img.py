#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多图片批量处理调度器
自动扫描 output/good 目录，对每张图片执行图生图配置生成和跑图
"""

import os
import subprocess
import sys
from pathlib import Path

# ==================== 配置 ====================
IMAGE_DIR = r"output\good"
CONFIG_GEN_SCRIPT = r"gen_config_img2img_v3.py"
IMG_GEN_SCRIPT = r"run_img2img.py"

# 图生图全局参数
MODEL_PATH = r"../models/sd-v1-5/aiiiiii01_v10.safetensors"
STRENGTH = 0.70
CFG = 7.5
STEPS = 25
# ===============================================

def get_image_files(directory):
    """获取目录下所有支持的图片文件"""
    extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    files = []
    for f in os.listdir(directory):
        if Path(f).suffix.lower() in extensions:
            files.append(os.path.join(directory, f))
    return sorted(files)

def run_command(cmd):
    """执行命令并打印结果"""
    print(f"\n🚀 执行: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode

def process_images():
    """对每个图片执行流水线"""
    image_files = get_image_files(IMAGE_DIR)
    total = len(image_files)
    
    print("=" * 60)
    print(f"📂 找到 {total} 张图片")
    print("=" * 60)
    
    for idx, img_path in enumerate(image_files, 1):
        print(f"\n{'='*60}")
        print(f"🖼️ 处理第 {idx}/{total} 张图: {os.path.basename(img_path)}")
        print(f"{'='*60}")
        
        # --- 步骤 1: 生成针对这张图的配置文件 ---
        print(f"\n[1/2] 生成配置文件...")
        config_cmd = (
            f"python {CONFIG_GEN_SCRIPT} "
            f"--target-image \"{img_path}\" "
            f"--model \"{MODEL_PATH}\" "
            f"--strength {STRENGTH} "
            f"--cfg {CFG} "
            f"--steps {STEPS}"
        )
        if run_command(config_cmd) != 0:
            print(f"❌ 生成配置失败，跳过这张图")
            continue
        
        # --- 寻找刚刚生成的配置文件 ---
        config_dir = Path("output/configs")
        if not config_dir.exists():
            print(f"❌ 找不到 configs 目录")
            continue
            
        # 获取最新的 json 文件
        config_files = sorted(config_dir.glob("img2img_batch_config_*.json"), key=os.path.getmtime, reverse=True)
        if not config_files:
            print(f"❌ 没有找到生成的配置文件")
            continue
            
        latest_config = config_files[0]
        print(f"✅ 找到最新配置: {latest_config.name}")
        
        # --- 步骤 2: 跑图 ---
        print(f"\n[2/2] 开始批量图生图...")
        run_cmd = f"python {IMG_GEN_SCRIPT} -c \"{latest_config}\""
        run_command(run_cmd)
        
        print(f"\n✅ 图片 {idx}/{total} 处理完成！")
    
    print("\n" + "=" * 60)
    print("🎉 所有图片处理完成！")
    print("=" * 60)

if __name__ == "__main__":
    # 确保在正确的虚拟环境中运行
    process_images()