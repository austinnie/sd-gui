#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量更新 controlnet_helper 导入为 controlnet 模块
"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 需要修改的文件及其替换规则
FILE_REPLACEMENTS = {
    "core/pipeline/runner.py": [
        (r'from utils\.controlnet_helper import get_controlnet_info',
         'from utils.controlnet import get_controlnet_info'),
    ],
    "core/pipeline/steps/controlnet_mixin.py": [
        (r'from utils\.controlnet_helper import get_controlnet_info, preprocess_image_for_controlnet',
         'from utils.controlnet import get_controlnet_info, preprocess_image_for_controlnet'),
    ],
    "core/pipeline/steps/sketch_step.py": [
        (r'from utils\.controlnet_helper import get_controlnet_info',
         'from utils.controlnet import get_controlnet_info'),
        (r'from utils\.controlnet_helper import preprocess_image_for_controlnet',
         'from utils.controlnet import preprocess_image_for_controlnet'),
    ],
    "gui/chat/controlnet_manager.py": [
        (r'from utils\.controlnet_helper import get_controlnet_info',
         'from utils.controlnet import get_controlnet_info'),
    ],
    "gui/chat/handlers/image_to_image.py": [
        (r'from utils\.controlnet_helper import preprocess_image_for_controlnet',
         'from utils.controlnet import preprocess_image_for_controlnet'),
    ],
    "gui/chat/ui/toolbar.py": [
        (r'from utils\.controlnet_helper import get_controlnet_display_names',
         'from utils.controlnet import get_controlnet_display_names'),
    ],
    "gui/reloader.py": [
        (r'"utils\.controlnet_helper",',
         '"utils.controlnet",'),
    ],
    "gui/tabs/img2img/controlnet.py": [
        (r'from utils\.controlnet_helper import controlnet_config',
         'from utils.controlnet import controlnet_config'),
        (r'from utils\.controlnet_helper import get_recommended_multi_controlnet_combos',
         'from utils.controlnet import get_recommended_multi_controlnet_combos'),
    ],
    "gui/tabs/img2img/generator.py": [
        (r'from utils\.controlnet_helper import get_recommended_multi_controlnet_combos',
         'from utils.controlnet import get_recommended_multi_controlnet_combos'),
        (r'from utils\.controlnet_helper import preprocess_image_for_controlnet',
         'from utils.controlnet import preprocess_image_for_controlnet'),
        (r'from utils\.controlnet_helper import process_with_multi_controlnet',
         'from utils.controlnet import process_with_multi_controlnet'),
    ],
    "gui/tabs/img2img/tab.py": [
        (r'from utils\.controlnet_helper import get_recommended_multi_controlnet_combos',
         'from utils.controlnet import get_recommended_multi_controlnet_combos'),
    ],
    "gui/tabs/img2img/ui.py": [
        (r'from utils\.controlnet_helper import get_recommended_multi_controlnet_combos',
         'from utils.controlnet import get_recommended_multi_controlnet_combos'),
    ],
}

# 还需要在 controlnet_mixin.py 中添加 from utils.controlnet import preprocess_image_for_controlnet
# 因为原文件可能没有导入，但在代码中使用了

def update_file(filepath: Path, replacements: list) -> bool:
    """更新单个文件"""
    if not filepath.exists():
        print(f"   ⚠️ 文件不存在: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        # 备份
        backup_path = filepath.with_suffix(filepath.suffix + ".backup")
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original)
        print(f"   📦 已备份: {backup_path.name}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ 更新: {filepath}")
        return True
    else:
        print(f"   ⏭️ 无变化: {filepath}")
        return False


def update_controlnet_mixin():
    """单独处理 controlnet_mixin.py，需要添加 from utils.controlnet import preprocess_image_for_controlnet"""
    filepath = PROJECT_ROOT / "core/pipeline/steps/controlnet_mixin.py"
    if not filepath.exists():
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 检查是否已经导入
    if 'from utils.controlnet import' in content:
        print(f"   ⏭️ 已更新: {filepath}")
        return False
    
    # 添加导入
    import_pattern = r'(from utils\.controlnet_helper import get_controlnet_info, preprocess_image_for_controlnet)'
    replacement = 'from utils.controlnet import get_controlnet_info, preprocess_image_for_controlnet'
    content = re.sub(import_pattern, replacement, content)
    
    if content != original:
        backup_path = filepath.with_suffix(filepath.suffix + ".backup")
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original)
        print(f"   📦 已备份: {backup_path.name}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ 更新: {filepath}")
        return True
    
    return False


def main():
    print("=" * 60)
    print("  🔧 批量更新 controlnet_helper → controlnet 导入")
    print("=" * 60)
    
    updated_count = 0
    
    for filepath_str, replacements in FILE_REPLACEMENTS.items():
        filepath = PROJECT_ROOT / filepath_str
        if update_file(filepath, replacements):
            updated_count += 1
    
    # 单独处理 controlnet_mixin.py
    if update_controlnet_mixin():
        updated_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ 完成！共更新 {updated_count} 个文件")
    print("=" * 60)
    
    print("\n📝 下一步:")
    print("   1. 运行 python main.py 测试")
    print("   2. 确认无误后删除 utils/controlnet_helper.py")
    print("   3. git add -A && git commit -m 'refactor: 拆分 controlnet_helper 为 controlnet 模块'")


if __name__ == "__main__":
    main()