#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量给所有 Pipeline Step 添加取消检查
使用方法: python scripts/add_cancel_check_to_steps.py
"""

import os
import re
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

STEPS_DIR = project_root / "core" / "pipeline" / "steps"


def add_cancel_check_to_step(filepath: Path) -> bool:
    """给单个 Step 文件添加取消检查"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经添加了取消检查
    if 'context.is_cancelled()' in content:
        print(f"   ⏭️ 跳过 {filepath.name} (已有取消检查)")
        return False
    
    # 检查是否在 execute 方法中有 for 循环
    if 'def execute(self, context: StepContext) -> StepResult:' not in content:
        print(f"   ⚠️ 跳过 {filepath.name} (没有 execute 方法)")
        return False
    
    # 检查是否有 for 循环
    if 'for ' not in content or 'enumerate' not in content:
        print(f"   ⚠️ 跳过 {filepath.name} (没有 for 循环)")
        return False
    
    # 逐行处理
    lines = content.split('\n')
    new_lines = []
    i = 0
    modified = False
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # 查找 for idx, job in enumerate(...) 循环
        # 匹配多种格式:
        # for idx, job in enumerate(jobs):
        # for idx, job in enumerate(prompts):
        # for idx, job in enumerate(all_jobs):
        for_match = re.match(r'^(\s*)for\s+(\w+)\s*,\s*(\w+)\s+in\s+enumerate\(([^)]+)\)\s*:', line)
        if for_match:
            indent = for_match.group(1)
            idx_var = for_match.group(2)      # 通常是 idx
            item_var = for_match.group(3)     # 通常是 job
            list_var = for_match.group(4)     # 通常是 jobs, prompts, all_jobs
            
            # 检查是否已经有取消检查（防止重复插入）
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            if 'context.is_cancelled()' in next_line:
                i += 1
                continue
            
            # 插入取消检查
            cancel_check = f'''{indent}    # ✅ 检查取消
{indent}    if context.is_cancelled():
{indent}        print(f"   ⏹️ 用户取消，已生成 {{{idx_var}}}/{{{len(list_var)}}} 张")
{indent}        return StepResult(
{indent}            status=StepStatus.FAILED,
{indent}            error="用户取消",
{indent}            output_path=output_dir,
{indent}            metadata={{
{indent}                "output_count": {idx_var},
{indent}                "output_dir": output_dir,
{indent}                "success_count": success_count,
{indent}                "cancelled": True,
{indent}            }}
{indent}        )'''
            
            new_lines.append(cancel_check)
            modified = True
            print(f"   ✅ 已添加取消检查: {filepath.name} (for 循环: {list_var})")
        
        i += 1
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        return True
    
    return False


def add_cancel_check_to_exception(filepath: Path) -> bool:
    """在 except 块中也添加取消检查"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经处理了取消异常
    if '"取消" in error_msg' in content or '"cancelled" in error_msg' in content:
        return False
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    modified = False
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # 查找 except Exception as e:
        if re.match(r'^(\s*)except\s+Exception\s+as\s+(\w+)\s*:', line):
            indent = re.match(r'^(\s*)', line).group(1)
            error_var = re.match(r'^(\s*)except\s+Exception\s+as\s+(\w+)\s*:', line).group(2)
            
            # 检查下一行是否已经有取消处理
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            if '取消' in next_line or 'cancelled' in next_line:
                i += 1
                continue
            
            # 插入取消异常处理
            cancel_check = f'''{indent}    error_msg = str({error_var})
{indent}    if "取消" in error_msg or "cancelled" in error_msg.lower():
{indent}        print(f"      ⏹️ 生成被取消")
{indent}        return StepResult(
{indent}            status=StepStatus.FAILED,
{indent}            error="用户取消",
{indent}            output_path=output_dir,
{indent}            metadata={{
{indent}                "output_count": idx,
{indent}                "output_dir": output_dir,
{indent}                "success_count": success_count,
{indent}                "cancelled": True,
{indent}            }}
{indent}        )
{indent}    print(f"      ❌ 失败: {{error_var}}")
{indent}    import traceback
{indent}    traceback.print_exc()
{indent}    continue'''
            
            # 检查原有的 except 块内容，替换掉简单的 print 和 continue
            j = i + 1
            while j < len(lines) and lines[j].strip() and lines[j].startswith(indent + '    '):
                j += 1
            
            # 删除旧的 except 块内容（从下一行到下一个同级别代码）
            del new_lines[i+1:]
            new_lines.append(cancel_check)
            
            # 跳过已被替换的行
            i = j - 1
            modified = True
            print(f"   ✅ 已添加取消异常处理: {filepath.name}")
        
        i += 1
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        return True
    
    return False


def main():
    """主函数"""
    print("=" * 60)
    print("🔧 批量添加取消检查到所有 Pipeline Step")
    print("=" * 60)
    print(f"📁 目录: {STEPS_DIR}")
    print()
    
    if not STEPS_DIR.exists():
        print(f"❌ 目录不存在: {STEPS_DIR}")
        return
    
    # 获取所有 Step 文件
    step_files = [
        f for f in STEPS_DIR.iterdir()
        if f.suffix == '.py'
        and f.name != '__init__.py'
        and f.name != 'controlnet_mixin.py'
    ]
    
    print(f"📋 找到 {len(step_files)} 个 Step 文件\n")
    
    modified_count = 0
    
    for filepath in sorted(step_files):
        print(f"📄 处理: {filepath.name}")
        
        # 1. 添加 for 循环中的取消检查
        if add_cancel_check_to_step(filepath):
            modified_count += 1
        
        # 2. 添加 except 块中的取消检查
        if add_cancel_check_to_exception(filepath):
            modified_count += 1
        
        print()
    
    print("=" * 60)
    print(f"✅ 完成！共修改 {modified_count} 个 Step 文件")
    print("=" * 60)
    
    # 验证
    print("\n🔍 验证修改结果:")
    verified = []
    for filepath in step_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'context.is_cancelled()' in content:
                verified.append(filepath.name)
    
    print(f"   ✅ 已添加取消检查: {len(verified)}/{len(step_files)} 个文件")
    if len(verified) < len(step_files):
        missing = set(f.name for f in step_files) - set(verified)
        print(f"   ⚠️ 未添加: {', '.join(missing)}")
    
    print("\n💡 下一步:")
    print("   1. 检查修改是否正确: git diff core/pipeline/steps/")
    print("   2. 测试流水线取消功能")
    print("   3. 提交修改: git add core/pipeline/steps/ && git commit -m 'feat: 所有Step支持取消'")


if __name__ == "__main__":
    main()