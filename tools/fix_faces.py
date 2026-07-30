#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
脸部修复工具 - 使用 CodeFormer（更轻量，不卡编译）
"""
import os
import sys
import glob
import argparse
from PIL import Image

try:
    from codeformer import CodeFormer
    HAS_CODEFORMER = True
except ImportError:
    HAS_CODEFORMER = False
    print("\n❌ 未安装 CodeFormer")
    print("请运行: pip install codeformer -i https://pypi.tuna.tsinghua.edu.cn/simple")
    print("\n如果还是不行，使用在线工具：")
    print("  - Remini (手机App)")
    print("  - Upscayl (免费桌面软件)")
    sys.exit(1)

# ==================== 配置 ====================
MODEL_PATH = "../models/codeformer/CodeFormer.pth"
OUTPUT_DIR = "output/fixed_faces"

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
    print("🔧 初始化 CodeFormer...")
    # 如果模型不存在，会在线下载
    restorer = CodeFormer(
        model_path=MODEL_PATH,
        fidelity=0.7,
        device='cpu'
    )
    return restorer

def fix_image(restorer, img_path, output_path):
    try:
        img = Image.open(img_path).convert('RGB')
        print(f"  📐 尺寸: {img.size}")
        
        # CodeFormer 直接接受 PIL Image
        result = restorer.enhance(img)
        
        if result is None:
            print(f"  ⚠️ 未检测到人脸，复制原图")
            img.save(output_path)
            return True
        
        result.save(output_path, quality=95)
        return True
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="脸部修复工具 - 使用 CodeFormer"
    )
    parser.add_argument("path", help="图片路径或目录")
    parser.add_argument("-o", "--output", help="输出路径")
    
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