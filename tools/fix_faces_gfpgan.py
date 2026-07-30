#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
脸部修复工具 - 使用 GFPGAN
用法：python fix_faces_gfpgan.py <图片路径或目录> -o <输出目录>
"""
import os
import sys
import glob
import argparse
import cv2
import numpy as np
from PIL import Image

try:
    from gfpgan import GFPGANer
    HAS_GFPGAN = True
except ImportError:
    HAS_GFPGAN = False
    print("\n❌ 未安装 GFPGAN")
    print("请运行: pip install gfpgan")
    sys.exit(1)

# ==================== 配置 ====================
OUTPUT_DIR = "output/fixed_faces"
MODEL_PATH = "../models/gfpgan/GFPGANv1.4.pth"

# ==================== 函数 ====================

def get_image_files(path):
    if os.path.isfile(path):
        return [path]
    
    if os.path.isdir(path):
        extensions = [".png", ".jpg", ".jpeg", ".webp", ".bmp"]
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(path, f"*{ext}")))
            files.extend(glob.glob(os.path.join(path, f"*{ext.upper()}")))
        return sorted(files)
    
    files = glob.glob(path)
    return sorted(files) if files else []

def setup_restorer():
    """初始化 GFPGAN"""
    print("🔧 初始化 GFPGAN...")
    
    # 检查模型
    abs_model_path = os.path.abspath(MODEL_PATH)
    if not os.path.exists(abs_model_path):
        print(f"❌ 模型不存在: {abs_model_path}")
        print("请下载模型到: E:\\SD_OpenVINO\\models\\gfpgan\\GFPGANv1.4.pth")
        sys.exit(1)
    
    print(f"✅ 找到模型: {abs_model_path}")
    
    try:
        restorer = GFPGANer(
            model_path=abs_model_path,
            upscale=1,
            arch="clean",
            channel_multiplier=2,
            bg_upsampler=None
        )
        print("✅ GFPGAN 初始化成功")
        return restorer
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)

def fix_image(restorer, img_path, output_path):
    """修复单张图片"""
    try:
        # 读取图片
        img = cv2.imread(img_path, cv2.IMREAD_COLOR)
        if img is None:
            print(f"  ❌ 无法读取图片")
            return False
        
        h, w = img.shape[:2]
        print(f"  📐 尺寸: {w}x{h}")
        
        # GFPGAN 修复
        _, _, restored = restorer.enhance(
            img,
            has_aligned=False,
            only_center_face=False,
            paste_back=True,
            weight=0.5
        )
        
        if restored is None:
            print(f"  ⚠️ 未检测到人脸，复制原图")
            import shutil
            shutil.copy2(img_path, output_path)
            return True
        
        # 保存
        cv2.imwrite(output_path, restored)
        print(f"  ✅ 修复完成")
        return True
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        # 失败时复制原图
        try:
            import shutil
            shutil.copy2(img_path, output_path)
            print(f"  📋 已复制原图")
            return True
        except:
            return False

def main():
    parser = argparse.ArgumentParser(description="脸部修复工具 - GFPGAN")
    parser.add_argument("path", help="图片路径或目录")
    parser.add_argument("-o", "--output", help="输出路径", default=None)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"❌ 路径不存在: {args.path}")
        sys.exit(1)
    
    files = get_image_files(args.path)
    if not files:
        print(f"❌ 未找到图片: {args.path}")
        sys.exit(1)
    
    print(f"\n📂 找到 {len(files)} 张图片")
    
    if args.output:
        output_dir = args.output
    else:
        output_dir = OUTPUT_DIR
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"📂 输出: {output_dir}")
    
    restorer = setup_restorer()
    
    print("\n" + "="*50)
    print("🔧 开始修复...")
    print("="*50)
    
    success = 0
    failed = 0
    
    for i, img_path in enumerate(files):
        print(f"\n📄 [{i+1}/{len(files)}] {os.path.basename(img_path)}")
        
        base_name = os.path.basename(img_path)
        output_path = os.path.join(output_dir, base_name)
        
        if fix_image(restorer, img_path, output_path):
            success += 1
        else:
            failed += 1
    
    print("\n" + "="*50)
    print(f"✅ 成功: {success} 张")
    print(f"❌ 失败: {failed} 张")
    print(f"📂 输出: {output_dir}")
    print("="*50)

if __name__ == "__main__":
    main()