#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量修复所有 Step 文件中的 _setup_controlnet 调用
添加 context 参数

使用方法: python scripts/fix_setup_controlnet_context.py
"""

import os
import re
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

STEPS_DIR = project_root / "core" / "pipeline" / "steps"


def fix_step_file(filepath: Path) -> bool:
    """修复单个 Step 文件中的 _setup_controlnet 调用"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 1. 修复 _setup_controlnet( 调用，添加 context
    # 匹配: self._setup_controlnet(config, model_path, image_path, init_image)
    # 替换为: self._setup_controlnet(config, model_path, image_path, init_image, context)
    pattern1 = r'self\._setup_controlnet\(\s*config\s*,\s*model_path\s*,\s*image_path\s*,\s*init_image\s*\)'
    replacement1 = r'self._setup_controlnet(config, model_path, image_path, init_image, context)'
    content = re.sub(pattern1, replacement1, content)
    
    # 2. 修复其他可能的格式（带换行）
    pattern2 = r'self\._setup_controlnet\(\s*config\s*,\s*model_path\s*,\s*image_path\s*,\s*init_image\s*,\s*\)'
    replacement2 = r'self._setup_controlnet(config, model_path, image_path, init_image, context)'
    content = re.sub(pattern2, replacement2, content)
    
    # 3. 检查是否还有没修复的
    if 'self._setup_controlnet' in content:
        # 检查是否已经传入 context
        if 'self._setup_controlnet' in content and 'context' not in content.split('self._setup_controlnet')[1].split(')')[0]:
            # 手动修复：找到 _setup_controlnet 调用并添加 context
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if 'self._setup_controlnet' in line and 'context' not in line:
                    # 添加 context 参数
                    line = re.sub(
                        r'self\._setup_controlnet\(([^)]*)\)',
                        r'self._setup_controlnet(\1, context)',
                        line
                    )
                new_lines.append(line)
            content = '\n'.join(new_lines)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def check_step_files():
    """检查哪些文件需要修复"""
    step_files = [
        f for f in STEPS_DIR.iterdir()
        if f.suffix == '.py' and f.name not in ['__init__.py', 'controlnet_mixin.py']
    ]
    
    needs_fix = []
    already_fixed = []
    
    for filepath in step_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '_setup_controlnet' in content:
            if 'context' in content.split('_setup_controlnet')[1].split(')')[0] if '_setup_controlnet' in content else '':
                already_fixed.append(filepath.name)
            else:
                needs_fix.append(filepath.name)
    
    return needs_fix, already_fixed


def main():
    """主函数"""
    print("=" * 60)
    print("🔧 批量修复 _setup_controlnet 调用 (添加 context)")
    print("=" * 60)
    print(f"📁 目录: {STEPS_DIR}")
    print()
    
    if not STEPS_DIR.exists():
        print(f"❌ 目录不存在: {STEPS_DIR}")
        return
    
    # 检查哪些文件需要修复
    needs_fix, already_fixed = check_step_files()
    
    print(f"📋 已修复: {len(already_fixed)} 个文件")
    print(f"📋 需要修复: {len(needs_fix)} 个文件")
    print()
    
    if not needs_fix:
        print("✅ 所有文件都已修复！")
        return
    
    print("需要修复的文件:")
    for name in needs_fix:
        print(f"   📄 {name}")
    print()
    
    # 执行修复
    fixed = []
    for filename in needs_fix:
        filepath = STEPS_DIR / filename
        if fix_step_file(filepath):
            fixed.append(filename)
            print(f"✅ 修复: {filename}")
        else:
            print(f"⏭️  跳过: {filename}")
    
    print("=" * 60)
    print(f"✅ 共修复 {len(fixed)} 个文件")
    
    # 验证
    print("\n🔍 验证结果:")
    still_needs, _ = check_step_files()
    if still_needs:
        print(f"   ⚠️ 还有 {len(still_needs)} 个文件需要修复: {', '.join(still_needs)}")
    else:
        print("   ✅ 所有文件都已修复！")
    
    print("=" * 60)
    print("\n💡 下一步:")
    print("   1. 检查修改: git diff core/pipeline/steps/")
    print("   2. 测试流水线功能")
    print("   3. 提交: git add core/pipeline/steps/ && git commit -m 'fix: 所有Step的_setup_controlnet添加context参数'")


if __name__ == "__main__":
    main()