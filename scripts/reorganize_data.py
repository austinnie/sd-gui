#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
整理项目数据目录结构
- configs/ → data/configs/
- grid_configs/ → data/configs/grid_configs/
- templates/ → data/templates/
- 更新所有代码中的路径引用
"""

import os
import re
import shutil
import sys
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_green(msg): print(f"{Colors.GREEN}{msg}{Colors.RESET}")
def print_red(msg): print(f"{Colors.RED}{msg}{Colors.RESET}")
def print_yellow(msg): print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
def print_cyan(msg): print(f"{Colors.CYAN}{msg}{Colors.RESET}")
def print_bold(msg): print(f"{Colors.BOLD}{msg}{Colors.RESET}")

PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 目录映射: (源目录, 目标目录)
DIR_MOVES = [
    ("configs", "data/configs"),
    ("grid_configs", "data/configs/grid_configs"),
    ("templates", "data/templates"),
]

# 需要更新的文件路径替换
FILE_REPLACEMENTS = [
    # config/config_manager.py
    ("config/config_manager.py", "'configs/gui_config.json'", "'data/configs/gui_config.json'"),
    ("config/config_manager.py", "'configs/nsfw_config.json'", "'data/configs/nsfw_config.json'"),
    ("config/config_manager.py", "'configs/scene_patterns.json'", "'data/configs/scene_patterns.json'"),
    
    # config/app_config.py
    ("config/app_config.py", '"configs/gui_config.json"', '"data/configs/gui_config.json"'),
    
    # config/janus_config.py
    ("config/janus_config.py", '"configs/janus_config.json"', '"data/configs/janus_config.json"'),
    
    # gui/scene_manager.py
    ("gui/scene_manager.py", '"configs/scene_patterns.json"', '"data/configs/scene_patterns.json"'),
    
    # gui/tabs/pipeline_tab.py
    ("gui/tabs/pipeline_tab.py", '"configs/pipelines_config.json"', '"data/configs/pipelines_config.json"'),
    
    # core/config_loader.py
    ("core/config_loader.py", '"templates/persons.json"', '"data/templates/persons.json"'),
    ("core/config_loader.py", '"templates/relationships.json"', '"data/templates/relationships.json"'),
    ("core/config_loader.py", '"templates/prompt_templates.json"', '"data/templates/prompt_templates.json"'),
    
    # config/config_manager.py (templates)
    ("config/config_manager.py", "'templates/persons.json'", "'data/templates/persons.json'"),
    ("config/config_manager.py", "'templates/relationships.json'", "'data/templates/relationships.json'"),
    ("config/config_manager.py", "'templates/prompt_templates.json'", "'data/templates/prompt_templates.json'"),
    
    # gui/tabs/grid_test_tab.py
    ("gui/tabs/grid_test_tab.py", 'config_dir = "data/configs/grid_configs"', 'config_dir = "data/configs/grid_configs"'),
]

# 需要更新的代码模式
PATTERN_REPLACEMENTS = [
    # core/person_builder.py
    (r'templates_path = os\.path\.join\(os\.path\.dirname\(os\.path\.dirname\(__file__\)\), "templates"\)',
     'templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "templates")'),
    
    # gui/tabs/grid_test_tab.py - config_dir 路径
    (r'os\.path\.join\(os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\), "grid_configs"\)',
     'os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "configs", "grid_configs")'),
    
    # gui/tabs/grid_test_tab.py - config_dir 变量
    (r'config_dir = "data/configs/grid_configs"',
     'config_dir = "data/configs/grid_configs"'),
    
    # gui/tabs/grid_test_tab.py - 输出目录
    (r'output_dir = "data/configs/grid_configs"',
     'output_dir = "data/configs/grid_configs"'),
]


def backup_file(filepath: Path) -> bool:
    if not filepath.exists():
        return False
    backup_path = filepath.with_suffix(filepath.suffix + ".backup")
    shutil.copy2(filepath, backup_path)
    print(f"   📦 已备份: {backup_path.name}")
    return True


def create_directories():
    """创建目标目录"""
    print_bold("\n📁 步骤 1: 创建目标目录")
    print("-" * 50)
    
    for src, dst in DIR_MOVES:
        dst_path = PROJECT_ROOT / dst
        dst_path.mkdir(parents=True, exist_ok=True)
        print_green(f"   ✅ 创建: {dst}")


def move_directories():
    """移动目录"""
    print_bold("\n📁 步骤 2: 移动目录")
    print("-" * 50)
    
    for src, dst in DIR_MOVES:
        src_path = PROJECT_ROOT / src
        dst_path = PROJECT_ROOT / dst
        
        if not src_path.exists():
            print_yellow(f"   ⚠️ 跳过: {src} (不存在)")
            continue
        
        # 如果目标已存在，先合并
        if dst_path.exists():
            # 移动所有内容到目标
            for item in src_path.iterdir():
                target = dst_path / item.name
                if target.exists():
                    # 如果是目录，递归合并
                    if item.is_dir():
                        shutil.copytree(item, target, dirs_exist_ok=True)
                        shutil.rmtree(item)
                    else:
                        shutil.move(str(item), str(target))
                else:
                    shutil.move(str(item), str(target))
            # 删除空目录
            if src_path.exists() and not any(src_path.iterdir()):
                src_path.rmdir()
            print_green(f"   ✅ 合并: {src} -> {dst}")
        else:
            shutil.move(str(src_path), str(dst_path))
            print_green(f"   ✅ 移动: {src} -> {dst}")


def update_file_references():
    """更新文件中的路径引用"""
    print_bold("\n📝 步骤 3: 更新文件中的路径引用")
    print("-" * 50)
    
    updated = 0
    for filepath_str, old_str, new_str in FILE_REPLACEMENTS:
        filepath = PROJECT_ROOT / filepath_str
        
        if not filepath.exists():
            print_yellow(f"   ⚠️ 跳过: {filepath_str} (不存在)")
            continue
        
        backup_file(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = content.replace(old_str, new_str)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print_green(f"   ✅ 更新: {filepath_str}")
            updated += 1
        else:
            print_yellow(f"   ⏭️ 无变化: {filepath_str}")
    
    return updated


def update_pattern_references():
    """使用正则更新代码模式"""
    print_bold("\n🔄 步骤 4: 更新代码模式")
    print("-" * 50)
    
    updated = 0
    for pattern, replacement in PATTERN_REPLACEMENTS:
        for py_file in PROJECT_ROOT.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                continue
            
            new_content = re.sub(pattern, replacement, content)
            
            if new_content != content:
                backup_file(py_file)
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                rel_path = py_file.relative_to(PROJECT_ROOT)
                print_green(f"   ✅ 更新: {rel_path}")
                updated += 1
    
    return updated


def update_code_collect_exclude():
    """更新 code_collect.py 的排除列表"""
    print_bold("\n🚫 步骤 5: 更新 code_collect.py 排除列表")
    print("-" * 50)
    
    filepath = PROJECT_ROOT / "code_collect.py"
    if not filepath.exists():
        print_yellow("   ⚠️ code_collect.py 不存在")
        return False
    
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加 data 到排除列表
    if 'EXCLUDE_DIRS = [' in content:
        if 'data' not in content:
            pattern = r'(EXCLUDE_DIRS = \[[^\]]*)'
            replacement = r'\1\n    "data",'
            new_content = re.sub(pattern, replacement, content)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print_green("   ✅ 更新: code_collect.py (添加 data 到排除列表)")
                return True
            else:
                print_yellow("   ⏭️ 无变化: code_collect.py")
        else:
            print_yellow("   ⏭️ 已包含: code_collect.py")
    else:
        print_yellow("   ⚠️ 未找到 EXCLUDE_DIRS: code_collect.py")
    
    return False


def verify_migration():
    """验证迁移结果"""
    print_bold("\n🔍 步骤 6: 验证迁移结果")
    print("-" * 50)
    
    # 检查旧目录是否已清理
    for src, _ in DIR_MOVES:
        old_path = PROJECT_ROOT / src
        if old_path.exists():
            print_red(f"   ❌ 旧目录仍存在: {src}")
        else:
            print_green(f"   ✅ 已清理: {src}")
    
    # 检查新目录是否创建
    for _, dst in DIR_MOVES:
        new_path = PROJECT_ROOT / dst
        if new_path.exists():
            print_green(f"   ✅ 已创建: {dst}")
        else:
            print_red(f"   ❌ 目录不存在: {dst}")


def print_summary(updated_files, updated_patterns):
    """打印汇总"""
    print("\n" + "=" * 60)
    print_bold("📊 数据目录整理完成!")
    print("=" * 60)
    print("\n   📁 新目录结构:")
    print("   ├── config/          ← 代码配置模块 (保留)")
    print("   ├── data/            ← 🆕 统一数据目录")
    print("   │   ├── configs/     ← 配置文件")
    print("   │   └── templates/   ← 模板数据")
    print("   ├── scripts/         ← 工具脚本")
    print("   └── output/          ← 输出目录")
    print(f"\n   📝 已更新 {updated_files} 个文件的引用")
    print(f"   📝 已更新 {updated_patterns} 个代码模式")
    print("\n" + "=" * 60)
    
    print_bold("\n💡 建议:")
    print("   1. 运行 python main.py 测试")
    print("   2. 确认无误后提交:")
    print("      git add -A && git commit -m 'refactor: 统一数据目录到 data/'")


def main():
    print_bold("=" * 60)
    print("  🔧 整理数据目录结构")
    print("=" * 60)
    print(f"\n📂 项目根目录: {PROJECT_ROOT}")
    
    print("\n将执行以下操作:")
    for src, dst in DIR_MOVES:
        print(f"   📁 {src}/ -> {dst}/")
    
    print("\n   涉及的文件:")
    for f, _, _ in FILE_REPLACEMENTS:
        print(f"      - {f}")
    
    response = input("\n是否继续? (y/n): ")
    if response.lower() != 'y':
        print("\n❌ 已取消")
        return
    
    try:
        create_directories()
        move_directories()
        updated_files = update_file_references()
        updated_patterns = update_pattern_references()
        update_code_collect_exclude()
        verify_migration()
        print_summary(updated_files, updated_patterns)
        
    except Exception as e:
        print_red(f"\n❌ 整理失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()