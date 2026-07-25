#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复移动到 scripts/ 目录后的路径问题
"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 需要修复的文件
FIXES = {
    "code_collect.py": [
        (r"os\.path\.dirname\(os\.path\.abspath\(__file__\)\)",
         "os.path.dirname(os.path.dirname(os.path.abspath(__file__)))"),
    ],
    "env_check.py": [
        (r'"gui_config.json"', '"data/configs/gui_config.json"'),
        (r'"scene_patterns.json"', '"data/configs/scene_patterns.json"'),
        (r'"pipelines_config.json"', '"data/configs/pipelines_config.json"'),
    ],
    "env_setup.py": [
        (r"project_dir = Path\(__file__\)\.parent\.absolute\(\)",
         "project_dir = Path(__file__).parent.parent.absolute()"),
    ],
    "lora_info_gui.py": [
        (r"os\.path\.dirname\(os\.path\.abspath\(__file__\)\)",
         "os.path.dirname(os.path.dirname(os.path.abspath(__file__)))"),
    ],
    "test_pipeline_controlnet_steps.py": [
        (r"os\.path\.dirname\(os\.path\.abspath\(__file__\)\)",
         "os.path.dirname(os.path.dirname(os.path.abspath(__file__)))"),
    ],
}

def fix_file(filename):
    filepath = PROJECT_ROOT / "scripts" / filename
    if not filepath.exists():
        print(f"⚠️ 文件不存在: {filename}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for pattern, replacement in FIXES.get(filename, []):
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 修复: {filename}")
        return True
    else:
        print(f"⏭️ 无需修改: {filename}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 修复脚本路径")
    print("=" * 50)
    
    for filename in FIXES.keys():
        fix_file(filename)
    
    print("\n✅ 完成!")