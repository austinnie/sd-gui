# scripts/migrate_to_new_controlnet.py
"""
一键迁移：从 controlnet_helper 迁移到新的 controlnet 模块
运行方式：python scripts/migrate_to_new_controlnet.py
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
    "gui/reloader.py": [
        (r'"utils\.controlnet_helper",',
         '"utils.controlnet",'),
    ],
}

def migrate_files():
    """执行迁移"""
    print("=" * 60)
    print("🔄 迁移 ControlNet 导入：controlnet_helper → controlnet")
    print("=" * 60)

    modified = 0
    for filepath_str, rules in FILE_REPLACEMENTS.items():
        filepath = PROJECT_ROOT / filepath_str
        if not filepath.exists():
            print(f"   ⚠️ 文件不存在: {filepath_str}")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content
        for pattern, replacement in rules:
            content = re.sub(pattern, replacement, content)

        if content != original:
            # 备份
            backup = filepath.with_suffix(filepath.suffix + ".backup")
            with open(backup, 'w', encoding='utf-8') as f:
                f.write(original)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✅ 已更新: {filepath_str}")
            modified += 1
        else:
            print(f"   ⏭️ 无变化: {filepath_str}")

    print("=" * 60)
    print(f"✅ 迁移完成！共修改 {modified} 个文件")
    print("=" * 60)

    # 验证
    print("\n🔍 验证：检查是否还有 controlnet_helper 引用...")
    remaining = []
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "controlnet_helper" in content:
                remaining.append(py_file.relative_to(PROJECT_ROOT))

    if remaining:
        print(f"   ⚠️ 仍有 {len(remaining)} 个文件引用 controlnet_helper:")
        for f in remaining:
            print(f"      - {f}")
    else:
        print("   ✅ 没有发现 controlnet_helper 引用")

    print("\n💡 下一步:")
    print("   1. 确认迁移无误后，删除 utils/controlnet_helper.py")
    print("   2. 运行 python main.py 测试功能")
    print("   3. 提交更改: git add -A && git commit -m 'refactor: 统一迁移到新的 controlnet 模块'")

if __name__ == "__main__":
    migrate_files()