#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量修复 Step 文件中的错误
- 修复 error_var 未定义问题（改为 e）
- 修复编码问题（中文乱码）
- 修复 continue 在循环外的问题

使用方法: python scripts/fix_step_errors.py
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
    """修复单个 Step 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 1. 修复 error_var 未定义 -> 改为 e
    content = re.sub(
        r'print\(f"      ❌ 失败: \{error_var\}"\)',
        'print(f"      ❌ 失败: {e}")',
        content
    )
    
    # 2. 修复中文乱码的打印语句
    content = re.sub(
        r'print\(f"      笶・螟ｱ雍･: \{error_var\}"\)',
        'print(f"      ❌ 失败: {e}")',
        content
    )
    
    # 3. 修复中文乱码的打印语句（第二种变体）
    content = re.sub(
        r'print\(f"      笶・螟ｱ雍･: \{e\}"\)',
        'print(f"      ❌ 失败: {e}")',
        content
    )
    
    # 4. 修复中文乱码的注释
    content = re.sub(
        r'# 笨・扈ｧ扈ｭ荳倶ｸ荳�莉ｻ蜉｡',
        '# 继续下一个任务（已在循环中）',
        content
    )
    
    # 5. 检查并修复 continue 在循环外的问题
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 检查是否在 except 块中
        if 'except Exception as e:' in line:
            except_indent = len(re.match(r'^(\s*)', line).group(1))
            j = i + 1
            block_lines = []
            
            # 收集 except 块内容
            while j < len(lines):
                if lines[j].strip() and len(re.match(r'^(\s*)', lines[j]).group(1)) <= except_indent:
                    break
                block_lines.append(lines[j])
                j += 1
            
            # 检查这个 except 块是否在 for 循环内
            in_for = False
            for k in range(i - 1, max(0, i - 30), -1):
                if 'for ' in lines[k] and ' in enumerate(' in lines[k]:
                    in_for = True
                    break
            
            # 如果不在 for 循环内，移除 continue
            if not in_for:
                new_block = []
                for bline in block_lines:
                    if 'continue' in bline and not '#' in bline:
                        indent_match = re.match(r'^(\s*)', bline)
                        indent = indent_match.group(1) if indent_match else ''
                        new_block.append(f'{indent}# continue (已移除，不在循环中)')
                    else:
                        new_block.append(bline)
                block_lines = new_block
            
            new_lines.append(line)
            new_lines.extend(block_lines)
            i = j
            continue
        
        new_lines.append(line)
        i += 1
    
    content = '\n'.join(new_lines)
    
    # 6. 额外修复：确保 except 块中的 continue 在循环内是有效的
    # 这个比较复杂，需要分析代码结构，暂时跳过
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """主函数"""
    print("=" * 60)
    print("🔧 批量修复 Step 文件错误")
    print("=" * 60)
    print(f"📁 目录: {STEPS_DIR}")
    print()
    
    if not STEPS_DIR.exists():
        print(f"❌ 目录不存在: {STEPS_DIR}")
        return
    
    step_files = [
        f for f in STEPS_DIR.iterdir()
        if f.suffix == '.py' and f.name not in ['__init__.py', 'controlnet_mixin.py']
    ]
    
    print(f"📋 找到 {len(step_files)} 个 Step 文件\n")
    
    fixed = []
    for filepath in sorted(step_files):
        print(f"📄 处理: {filepath.name}")
        if fix_step_file(filepath):
            fixed.append(filepath.name)
            print(f"   ✅ 已修复")
        else:
            print(f"   ⏭️  无需修改")
    
    print("=" * 60)
    print(f"✅ 共修复 {len(fixed)} 个文件")
    
    # 验证
    print("\n🔍 验证结果:")
    
    # 检查是否还有 error_var
    error_var_files = []
    for f in step_files:
        with open(f, 'r', encoding='utf-8') as fp:
            if 'error_var' in fp.read():
                error_var_files.append(f.name)
    
    if error_var_files:
        print(f"   ⚠️ 还有 error_var: {', '.join(error_var_files)}")
    else:
        print("   ✅ 没有 error_var 了")
    
    # 检查是否还有乱码
    garbled_files = []
    for f in step_files:
        with open(f, 'r', encoding='utf-8') as fp:
            if '笶・' in fp.read():
                garbled_files.append(f.name)
    
    if garbled_files:
        print(f"   ⚠️ 还有乱码: {', '.join(garbled_files)}")
    else:
        print("   ✅ 没有乱码了")
    
    print("=" * 60)
    print("\n💡 下一步:")
    print("   1. 检查修改: git diff core/pipeline/steps/")
    print("   2. 测试流水线功能")
    print("   3. 提交: git add core/pipeline/steps/ && git commit -m 'fix: 修复Step文件错误'")


if __name__ == "__main__":
    main()