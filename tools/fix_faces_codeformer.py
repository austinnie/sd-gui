#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
脸部修复工具 - 使用 CodeFormer
用法：python fix_faces.py <图片路径或目录> -o <输出目录>
"""
import os
import sys
import glob
import argparse
import numpy as np
from PIL import Image
import io

try:
    from codeformer import CodeFormer
    HAS_CODEFORMER = True
except ImportError:
    HAS_CODEFORMER = False
    print("\n❌ 未安装 CodeFormer")
    print("请运行: pip install codeformer")
    sys.exit(1)

# ==================== 配置 ====================
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

def setup_restorer(fidelity=0.7):
    """初始化 CodeFormer"""
    print("🔧 初始化 CodeFormer...")
    
    try:
        restorer = CodeFormer(
            fidelity_weight=fidelity,
            upscale=1,
            bg_enhance=False,
            face_enhance=False
        )
        print(f"✅ CodeFormer 初始化成功 (fidelity={fidelity})")
        return restorer
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)

def fix_image(restorer, img_path, output_path):
    """修复单张图片"""
    try:
        # 读取图片
        img = Image.open(img_path).convert('RGB')
        print(f"  📐 尺寸: {img.size}")
        
        # 转为 numpy array
        img_array = np.array(img)
        
        # 使用 upscale_image 方法
        result = restorer.upscale_image(img_array)
        
        # 检查结果类型
        if result is None:
            print(f"  ⚠️ 处理失败，复制原图")
            img.save(output_path)
            return True
        
        # 如果返回的是 bytes（JPEG 格式），用 PIL 读取
        if isinstance(result, bytes):
            print(f"  📋 返回 bytes 格式")
            result_img = Image.open(io.BytesIO(result))
        elif isinstance(result, np.ndarray):
            result_img = Image.fromarray(result)
        else:
            print(f"  ⚠️ 未知返回类型: {type(result)}，复制原图")
            img.save(output_path)
            return True
        
        # 保存
        result_img.save(output_path, quality=95)
        print(f"  ✅ 修复完成")
        return True
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        # 失败时复制原图
        try:
            img = Image.open(img_path).convert('RGB')
            img.save(output_path)
            print(f"  📋 已复制原图")
            return True
        except:
            return False

def main():
    parser = argparse.ArgumentParser(description="脸部修复工具 - CodeFormer")
    parser.add_argument("path", help="图片路径或目录")
    parser.add_argument("-o", "--output", help="输出路径", default=None)
    parser.add_argument("-f", "--fidelity", type=float, default=0.7, help="修复强度 (0-1), 默认0.7")
    
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
    
    restorer = setup_restorer(args.fidelity)
    
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