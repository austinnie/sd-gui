#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
严格区分架构的 LoRA 同步脚本
防止跨架构误复制
"""

import os
import shutil

# ==================== 配置 ====================
TEST_LORA_DIR = r"E:\SD_OpenVINO\models\test_lora"
SD15_DIR = r"E:\SD_OpenVINO\models\sd15-lora"
SDXL_DIR = r"E:\SD_OpenVINO\models\sdxl-lora"
# ===============================================

def get_lora_list_by_architecture():
    """
    扫描 test_lora 目录，根据文件大小或命名规则判断架构
    """
    if not os.path.exists(TEST_LORA_DIR):
        print(f"❌ 找不到源目录: {TEST_LORA_DIR}")
        return [], [], []

    files = [f for f in os.listdir(TEST_LORA_DIR) if f.endswith('.safetensors')]
    
    sd15_list = []
    sdxl_list = []
    unknown_list = []
    
    for f in files:
        path = os.path.join(TEST_LORA_DIR, f)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        
        # 判断逻辑：SD 1.5 的 LoRA 通常小于 200MB，SDXL 通常大于 200MB
        if size_mb < 200:
            sd15_list.append(f)
        elif size_mb >= 200:
            sdxl_list.append(f)
        else:
            unknown_list.append(f)
    
    return sd15_list, sdxl_list, unknown_list

def sync_directory(target_dir, source_list, arch_name):
    """
    将 source_list 中的文件复制到 target_dir
    如果目标目录里没有该文件，则复制；如果有则跳过
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        print(f"📁 创建目录: {target_dir}")

    copied = 0
    skipped = 0
    
    print(f"\n📁 正在同步 {arch_name} 模型到: {target_dir}")
    
    for filename in source_list:
        src_path = os.path.join(TEST_LORA_DIR, filename)
        dst_path = os.path.join(target_dir, filename)
        
        if os.path.exists(dst_path):
            skipped += 1
            continue
        
        try:
            shutil.copy2(src_path, dst_path)
            copied += 1
            print(f"   ✅ 复制: {filename}")
        except Exception as e:
            print(f"   ❌ 复制失败 {filename}: {e}")
    
    print(f"   📊 结果: 复制了 {copied} 个，已存在跳过 {skipped} 个")
    return copied, skipped

def main():
    print("=" * 60)
    print("🎯 严格区分架构的 LoRA 同步脚本")
    print("=" * 60)
    
    # 获取架构分类列表
    sd15_list, sdxl_list, unknown_list = get_lora_list_by_architecture()
    
    print(f"✅ test_lora 目录分析完成:")
    print(f"   - SD 1.5 架构模型: {len(sd15_list)} 个")
    print(f"   - SDXL 架构模型: {len(sdxl_list)} 个")
    if unknown_list:
        print(f"   ⚠️ 无法判断架构: {len(unknown_list)} 个 (请检查文件大小)")
    
    # 分别同步到对应目录
    sync_directory(SD15_DIR, sd15_list, "SD 1.5")
    sync_directory(SDXL_DIR, sdxl_list, "SDXL")
    
    print("\n" + "=" * 60)
    print("✅ 同步完成！")
    print(f"📁 SD 1.5 目录: {SD15_DIR}")
    print(f"📁 SDXL 目录: {SDXL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()