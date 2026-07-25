#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提示词模板自动拆分脚本
从旧的 prompt_templates.json 拆分成按分类的小文件
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path


def ensure_dir(path):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def backup_file(filepath):
    """备份文件"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        print(f"📦 已备份: {backup_path}")
        return backup_path
    return None


def split_templates():
    """拆分模板"""
    
    # ===== 配置 =====
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_file = os.path.join(project_root, "templates", "prompt_templates.json")
    output_dir = os.path.join(project_root, "templates", "prompts")
    
    # ===== 检查源文件 =====
    if not os.path.exists(source_file):
        print(f"❌ 源文件不存在: {source_file}")
        return False
    
    # ===== 备份源文件 =====
    backup_file(source_file)
    
    # ===== 读取源文件 =====
    print(f"📖 读取: {source_file}")
    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # ===== 准备输出目录 =====
    ensure_dir(output_dir)
    print(f"📁 输出目录: {output_dir}")
    
    # ===== 提取每个分类 =====
    categories = {}
    category_configs = []
    
    for category_name, category_data in data.items():
        print(f"\n📂 处理分类: {category_name}")
        
        # 提取模板列表
        if isinstance(category_data, dict):
            icon = category_data.get("icon", "📁")
            priority = category_data.get("priority", 99)
            templates = category_data.get("templates", [])
        elif isinstance(category_data, list):
            icon = "📁"
            priority = 99
            templates = category_data
        else:
            print(f"   ⚠️ 跳过 {category_name}: 格式未知")
            continue
        
        print(f"   📊 {len(templates)} 个模板, 图标: {icon}, 优先级: {priority}")
        
        # 保存分类信息
        category_id = _generate_id(category_name)
        categories[category_id] = {
            "name": category_name,
            "icon": icon,
            "priority": priority,
            "templates": templates
        }
        
        # 写入分类文件
        output_file = os.path.join(output_dir, f"{category_id}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "name": category_name,
                "icon": icon,
                "priority": priority,
                "templates": templates
            }, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 已保存: {os.path.basename(output_file)}")
        
        # 收集分类配置
        category_configs.append({
            "id": category_id,
            "name": category_name,
            "icon": icon,
            "priority": priority,
            "file": f"{category_id}.json"
        })
    
    # ===== 写入 categories.json =====
    categories_file = os.path.join(output_dir, "categories.json")
    with open(categories_file, 'w', encoding='utf-8') as f:
        json.dump({
            "version": "2.0",
            "created": datetime.now().isoformat(),
            "description": "提示词模板分类",
            "categories": category_configs
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已生成分类配置: {categories_file}")
    
    # ===== 生成统计报告 =====
    total = sum(len(c["templates"]) for c in categories.values())
    print("\n" + "=" * 50)
    print("📊 拆分完成统计:")
    print(f"   分类数: {len(categories)}")
    print(f"   模板总数: {total}")
    print("=" * 50)
    
    for cfg in category_configs:
        count = len(categories[cfg["id"]]["templates"])
        print(f"   {cfg['icon']} {cfg['name']}: {count} 个")
    
    # ===== 生成迁移提示 =====
    print("\n" + "=" * 50)
    print("📝 后续步骤:")
    print("1. 检查拆分后的文件是否完整")
    print(f"   目录: {output_dir}")
    print("2. 修改 txt2img_tab.py 使用新的服务")
    print("3. 测试无误后删除旧的 prompt_templates.json")
    print("=" * 50)
    
    return True


def _generate_id(name: str) -> str:
    """生成分类 ID"""
    # 中文转拼音映射
    mapping = {
        "美女": "beauty",
        "帅哥": "handsome",
        "风景": "landscape",
        "动物": "animal",
        "植物": "plant",
        "艺术": "art",
        "时尚": "fashion",
        "奇幻": "fantasy",
        "情侣": "couple",
        "私密": "intimate",
        "动漫": "anime",
        "女神": "goddess",
        "古典": "classic",
        "现代": "modern",
        "自然": "nature",
    }
    
    if name in mapping:
        return mapping[name]
    
    # 简单处理：取前几个字符
    result = ""
    for char in name:
        if '\u4e00' <= char <= '\u9fff':  # 中文字符
            continue
        result += char
    return result.lower() or "unknown"


def verify_split():
    """验证拆分结果"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "templates", "prompts")
    categories_file = os.path.join(output_dir, "categories.json")
    
    if not os.path.exists(categories_file):
        print("❌ categories.json 不存在")
        return False
    
    with open(categories_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("\n📊 验证结果:")
    total = 0
    for cat in config.get("categories", []):
        file_path = os.path.join(output_dir, cat["file"])
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            count = len(data.get("templates", []))
            total += count
            print(f"   ✅ {cat['icon']} {cat['name']}: {count} 个模板")
        else:
            print(f"   ❌ {cat['name']}: 文件缺失")
    
    print(f"\n   📊 总计: {total} 个模板")
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("🔧 提示词模板自动拆分工具")
    print("=" * 50)
    
    # 执行拆分
    if split_templates():
        print("\n✅ 拆分完成！")
        
        # 验证
        verify_split()
        
        print("\n💡 提示:")
        print("   • 拆分后的文件在 templates/prompts/ 目录")
        print("   • 原文件已备份: templates/prompt_templates.json.backup_*")
        print("   • 确认无误后可删除原文件")
    else:
        print("\n❌ 拆分失败，请检查错误信息")