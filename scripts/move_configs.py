#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一键迁移配置文件到 configs/ 目录 (Windows 兼容版)
自动更新所有引用
"""

import os
import re
import shutil
import sys
from pathlib import Path

# 颜色输出
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

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
CONFIGS_DIR = PROJECT_ROOT / "configs"

# 需要移动的配置文件
CONFIG_FILES = [
    "grid_config.json",
    "gui_config.json",
    "janus_config.json",
    "nsfw_config.json",
    "pipelines_config.json",
    "scene_patterns.json",
    "scene_patterns_template.json",
]

# 需要更新引用的文件 (文件路径, 旧字符串, 新字符串)
FILE_REPLACEMENTS = [
    # config/app_config.py
    (
        "config/app_config.py",
        '"gui_config.json"',
        '"configs/gui_config.json"'
    ),
    (
        "config/app_config.py",
        "'gui_config.json'",
        "'configs/gui_config.json'"
    ),
    
    # config/config_manager.py
    (
        "config/config_manager.py",
        "'gui_config.json'",
        "'configs/gui_config.json'"
    ),
    (
        "config/config_manager.py",
        "'nsfw_config.json'",
        "'configs/nsfw_config.json'"
    ),
    (
        "config/config_manager.py",
        "'scene_patterns.json'",
        "'configs/scene_patterns.json'"
    ),
    
    # config/janus_config.py
    (
        "config/janus_config.py",
        '"janus_config.json"',
        '"configs/janus_config.json"'
    ),
    
    # gui/scene_manager.py
    (
        "gui/scene_manager.py",
        'config_path: str = "scene_patterns.json"',
        'config_path: str = "configs/scene_patterns.json"'
    ),
    
    # gui/tabs/pipeline_tab.py
    (
        "gui/tabs/pipeline_tab.py",
        '"pipelines_config.json"',
        '"configs/pipelines_config.json"'
    ),
]

# 需要更新 code_collect.py 和 code_package.py 的排除列表
EXCLUDE_UPDATE_FILES = [
    "code_collect.py",
    "code_package.py",
]


def backup_file(filepath: Path) -> bool:
    """备份文件"""
    if not filepath.exists():
        return False
    backup_path = filepath.with_suffix(filepath.suffix + ".backup")
    shutil.copy2(filepath, backup_path)
    print(f"   📦 已备份: {backup_path.name}")
    return True


def move_configs():
    """移动配置文件到 configs/ 目录 (Windows 兼容)"""
    print_bold("\n📁 步骤 1: 创建 configs/ 目录并移动配置文件")
    print("-" * 50)
    
    # 创建 configs 目录
    CONFIGS_DIR.mkdir(exist_ok=True)
    print_green(f"   ✅ 创建目录: {CONFIGS_DIR}")
    
    moved_count = 0
    for filename in CONFIG_FILES:
        src = PROJECT_ROOT / filename
        dst = CONFIGS_DIR / filename
        
        if src.exists():
            shutil.move(str(src), str(dst))
            print_green(f"   ✅ 移动: {filename} -> configs/{filename}")
            moved_count += 1
        else:
            print_yellow(f"   ⚠️ 跳过: {filename} (不存在)")
    
    print_green(f"\n   ✅ 共移动 {moved_count} 个配置文件")


def update_file_references():
    """更新文件中的路径引用"""
    print_bold("\n📝 步骤 2: 更新文件中的路径引用")
    print("-" * 50)
    
    updated = 0
    for filepath_str, old_str, new_str in FILE_REPLACEMENTS:
        filepath = PROJECT_ROOT / filepath_str
        
        if not filepath.exists():
            print_yellow(f"   ⚠️ 跳过: {filepath_str} (不存在)")
            continue
        
        # 备份
        backup_file(filepath)
        
        # 读取并替换
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = content.replace(old_str, new_str)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print_green(f"   ✅ 更新: {filepath_str}")
            print(f"      {old_str} -> {new_str}")
            updated += 1
        else:
            print_yellow(f"   ⏭️ 无变化: {filepath_str}")
    
    return updated


def update_exclude_lists():
    """更新 code_collect.py 和 code_package.py 的排除列表"""
    print_bold("\n🚫 步骤 3: 更新工具脚本的排除列表")
    print("-" * 50)
    
    updated = 0
    for filename in EXCLUDE_UPDATE_FILES:
        filepath = PROJECT_ROOT / filename
        if not filepath.exists():
            continue
        
        backup_file(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加 configs 到排除列表
        if 'EXCLUDE_DIRS = [' in content:
            if 'configs' not in content:
                # 在列表中添加 configs
                pattern = r'(EXCLUDE_DIRS = \[[^\]]*)'
                replacement = r'\1\n    "configs",'
                new_content = re.sub(pattern, replacement, content)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print_green(f"   ✅ 更新: {filename} (添加 configs 到排除列表)")
                    updated += 1
                else:
                    print_yellow(f"   ⏭️ 无变化: {filename}")
            else:
                print_yellow(f"   ⏭️ 已包含: {filename}")
        else:
            print_yellow(f"   ⚠️ 未找到 EXCLUDE_DIRS: {filename}")
    
    return updated


def create_init_file():
    """在 configs/ 目录创建 __init__.py（如果需要）"""
    init_file = CONFIGS_DIR / "__init__.py"
    if not init_file.exists():
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('"""配置文件目录"""\n')
        print_green(f"   ✅ 创建: configs/__init__.py")


def verify_migration():
    """验证迁移结果"""
    print_bold("\n🔍 步骤 4: 验证迁移结果")
    print("-" * 50)
    
    # 检查配置文件是否已移动
    all_moved = True
    for filename in CONFIG_FILES:
        old_path = PROJECT_ROOT / filename
        new_path = CONFIGS_DIR / filename
        
        if old_path.exists():
            print_red(f"   ❌ 旧文件仍存在: {filename}")
            all_moved = False
        elif new_path.exists():
            print_green(f"   ✅ 已迁移: configs/{filename}")
        else:
            print_yellow(f"   ⚠️ 文件不存在: {filename}")
    
    # 检查是否还有 JSON 文件残留
    remaining_json = list(PROJECT_ROOT.glob("*.json"))
    if remaining_json:
        # 排除 .backup 文件
        remaining_json = [f for f in remaining_json if not f.name.endswith('.backup')]
        if remaining_json:
            print_yellow(f"\n   ⚠️ 根目录仍有 JSON 文件: {len(remaining_json)} 个")
            for f in remaining_json:
                print(f"      - {f.name}")
        else:
            print_green(f"\n   ✅ 根目录已无 JSON 文件")
    else:
        print_green(f"\n   ✅ 根目录已无 JSON 文件")
    
    return all_moved


def print_summary(updated_files, updated_excludes):
    """打印汇总"""
    print("\n" + "=" * 60)
    print_bold("📊 迁移完成!")
    print("=" * 60)
    print(f"\n   📁 配置文件已移至: configs/")
    print(f"   📝 已更新 {updated_files} 个文件的引用")
    print(f"   📝 已更新 {updated_excludes} 个工具脚本")
    print("\n" + "=" * 60)
    
    print_bold("\n💡 建议:")
    print("   1. 运行 python main.py 测试是否正常")
    print("   2. 检查所有功能是否正常")
    print("   3. 确认无误后提交:")
    print("      git add -A && git commit -m 'refactor: 移动配置文件到 configs/ 目录'")


def main():
    """主函数"""
    print_bold("=" * 60)
    print("  🔧 一键迁移配置文件到 configs/ 目录 (Windows 版)")
    print("=" * 60)
    print(f"\n📂 项目根目录: {PROJECT_ROOT}")
    
    # 确认
    print("\n⚠️ 将执行以下操作:")
    print("   1. 创建 configs/ 目录")
    print("   2. 移动 7 个配置文件到 configs/")
    print("   3. 更新 6 个文件的路径引用")
    print("   4. 更新工具脚本的排除列表")
    print("\n   涉及的文件:")
    for f in CONFIG_FILES:
        print(f"      - {f}")
    
    response = input("\n是否继续? (y/n): ")
    if response.lower() != 'y':
        print("\n❌ 已取消")
        return
    
    try:
        # 1. 移动配置文件
        move_configs()
        
        # 2. 更新文件引用
        updated_files = update_file_references()
        
        # 3. 更新排除列表
        updated_excludes = update_exclude_lists()
        
        # 4. 创建 __init__.py
        create_init_file()
        
        # 5. 验证
        verify_migration()
        
        # 6. 打印汇总
        print_summary(updated_files, updated_excludes)
        
    except Exception as e:
        print_red(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()