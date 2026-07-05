#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
根据 high_sex_lora_list.txt 同时过滤 sd15-lora 和 sdxl-lora 目录
只保留高分 LoRA，删除未上榜的 LoRA
"""

import os
import re

# ==================== 配置 ====================
LORA_LIST_FILE = "output/high_sex_lora_list.txt"
MODELS_ROOT = r"E:\SD_OpenVINO\models"

# 需要清理的两个子目录
TARGET_SUBDIRS = [
    "sd15-lora",
    "sdxl-lora"
]
# ===============================================

def clean_lora_name(raw_name):
    """
    从高分名单中提取纯净的 LoRA 文件名关键词
    去掉序号、括号、评分
    """
    name = raw_name.strip()
    if '. ' in name:
        name = name.split('. ', 1)[1]
    name = re.sub(r'\s*\([^)]*\)', '', name)
    return name.strip()

def get_score_list(file_path):
    """读取高分列表，返回一个纯净名字的集合"""
    if not os.path.exists(file_path):
        print(f"❌ 找不到高分列表文件: {file_path}")
        return set()
    
    keep_names = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        if not line.strip() or line.startswith("==="):
            continue
        clean_name = clean_lora_name(line)
        if clean_name:
            keep_names.add(clean_name)
    
    print(f"✅ 共找到 {len(keep_names)} 个需要保留的 LoRA 名称关键词")
    return keep_names

def filter_directory(target_dir, keep_names):
    """过滤单个目录，返回 (保留数量, 删除数量, 删除列表)"""
    if not os.path.exists(target_dir):
        return 0, 0, []
    
    files = [f for f in os.listdir(target_dir) if f.endswith('.safetensors')]
    to_delete = []
    to_keep = []
    
    for filename in files:
        kept = False
        for name in keep_names:
            # 如果文件名包含名单中的关键词
            if name in filename:
                kept = True
                break
        if kept:
            to_keep.append(filename)
        else:
            to_delete.append(filename)
    
    return len(to_keep), len(to_delete), to_delete

def main():
    print("=" * 60)
    print("🎯 LoRA 高分筛选工具 (双目录版)")
    print("=" * 60)
    
    keep_names = get_score_list(LORA_LIST_FILE)
    if not keep_names:
        print("❌ 没有可用的保留名单，退出。")
        return
    
    all_to_delete = {}
    total_keep = 0
    total_del = 0
    
    # 遍历两个目录，收集删除列表
    for subdir in TARGET_SUBDIRS:
        target_dir = os.path.join(MODELS_ROOT, subdir)
        if not os.path.exists(target_dir):
            print(f"⚠️ 目录不存在: {subdir}，跳过")
            continue
            
        keep_count, del_count, del_list = filter_directory(target_dir, keep_names)
        total_keep += keep_count
        total_del += del_count
        if del_count > 0:
            all_to_delete[subdir] = del_list
        print(f"\n📁 {subdir}:")
        print(f"   ✅ 保留: {keep_count} 个")
        print(f"   ❌ 删除: {del_count} 个")
    
    print(f"\n📊 总计:")
    print(f"   ✅ 保留: {total_keep} 个 LoRA")
    print(f"   ❌ 删除: {total_del} 个 LoRA")
    
    if total_del == 0:
        print("🎉 所有文件都已匹配，无需删除。")
        return
    
    # 显示预览并确认
    print("\n⚠️ 预览将被删除的文件:")
    for subdir, del_list in all_to_delete.items():
        print(f"   📁 {subdir} 的删除列表 ({len(del_list)} 个):")
        for f in del_list[:10]:
            print(f"      - {f}")
        if len(del_list) > 10:
            print(f"      ... 还有 {len(del_list) - 10} 个文件")
    
    confirm = input("\n⚠️ 确认删除以上文件？(y/N): ")
    if confirm.lower() != 'y':
        print("❌ 操作已取消。")
        return
    
    # 执行删除
    deleted_count = 0
    for subdir, del_list in all_to_delete.items():
        target_dir = os.path.join(MODELS_ROOT, subdir)
        for filename in del_list:
            full_path = os.path.join(target_dir, filename)
            try:
                os.remove(full_path)
                deleted_count += 1
                print(f"   🗑️ 已删除: {subdir}/{filename}")
            except Exception as e:
                print(f"   ❌ 删除失败: {subdir}/{filename} ({e})")
    
    print(f"\n✅ 清理完成！共删除了 {deleted_count} 个文件。")

if __name__ == "__main__":
    main()