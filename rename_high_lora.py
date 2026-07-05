#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LoRA 高分文件批量重命名工具
读取 high_sex_lora_list.txt，将 test_lora 目录下的对应 LoRA 文件重命名为 01_xxx.safetensors
"""

import os
import re
import shutil

# ==================== 配置 ====================
LORA_LIST_FILE = r"E:\SD_OpenVINO\v8_universal_generator\output\high_sex_lora_list.txt"
TARGET_DIR = r"E:\SD_OpenVINO\models\test_lora"
# ===============================================

def clean_lora_name(raw_name):
    """
    从高分名单中提取纯净的 LoRA 文件名关键词
    去掉序号、括号、评分，并过滤掉不可用于文件名的字符
    """
    name = raw_name.strip()
    if '. ' in name:
        name = name.split('. ', 1)[1]
    # 去掉评分信息
    name = re.sub(r'\s*\([^)]*\)', '', name)
    # 将非法文件名字符替换为下划线
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    return name.strip()

def load_high_score_list(file_path):
    """读取高分列表，返回排名和对应的纯净名字"""
    if not os.path.exists(file_path):
        print(f"❌ 找不到高分列表文件: {file_path}")
        return []
    
    result = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        if not line.strip() or line.startswith("==="):
            continue
        clean_name = clean_lora_name(line)
        if clean_name:
            result.append(clean_name)
    
    return result

def rename_lora_files(target_dir, name_list):
    """执行重命名操作"""
    if not os.path.exists(target_dir):
        print(f"❌ 目标目录不存在: {target_dir}")
        return
    
    # 扫描当前目录下所有 .safetensors 文件
    files = [f for f in os.listdir(target_dir) if f.endswith('.safetensors')]
    
    renamed_count = 0
    skipped_count = 0
    
    print(f"📂 目标目录: {target_dir}")
    print(f"📋 准备将 {len(name_list)} 个 LoRA 按顺序重命名...")
    print("-" * 50)
    
    for index, target_name in enumerate(name_list, 1):
        # 构造目标文件名
        new_filename = f"{index:02d}_{target_name}.safetensors"
        new_path = os.path.join(target_dir, new_filename)
        
        # 检查目标文件是否已存在（防止覆盖）
        if os.path.exists(new_path):
            print(f"⚠️ 目标文件已存在，跳过: {new_filename}")
            skipped_count += 1
            continue
        
        # 在目录中寻找匹配的源文件（只要文件名包含目标关键词）
        found = False
        for old_filename in files:
            # 如果源文件已经被重命名过，跳过它
            if old_filename.startswith(f"{index:02d}_"):
                found = True
                break
            # 如果文件名包含目标关键词（且尚未被重命名）
            if target_name in old_filename:
                old_path = os.path.join(target_dir, old_filename)
                try:
                    os.rename(old_path, new_path)
                    print(f"✅ [{index:02d}] 重命名: {old_filename} -> {new_filename}")
                    renamed_count += 1
                    found = True
                    # 从扫描列表中移除已处理的文件，避免重复匹配
                    files.remove(old_filename)
                    break
                except Exception as e:
                    print(f"❌ 重命名失败: {old_filename} -> {new_filename} ({e})")
        
        if not found:
            print(f"⚠️ 未找到匹配的文件: {target_name}")
            skipped_count += 1
    
    print("-" * 50)
    print(f"✅ 重命名完成！")
    print(f"   - 成功重命名: {renamed_count} 个")
    print(f"   - 跳过/未找到: {skipped_count} 个")
    print(f"   - 请前往目录查看结果: {target_dir}")

def main():
    print("=" * 60)
    print("🎯 LoRA 高分文件批量重命名工具")
    print("=" * 60)
    
    name_list = load_high_score_list(LORA_LIST_FILE)
    if not name_list:
        print("❌ 没有可用的重命名列表，退出。")
        return
    
    print(f"📋 即将按以下顺序重命名:")
    for i, name in enumerate(name_list, 1):
        print(f"   {i:02d}. {name}")
    
    confirm = input(f"\n⚠️ 确认将 {TARGET_DIR} 下的对应文件重命名为 01~{len(name_list)} 格式？(y/N): ")
    if confirm.lower() != 'y':
        print("❌ 操作已取消。")
        return
    
    rename_lora_files(TARGET_DIR, name_list)

if __name__ == "__main__":
    main()