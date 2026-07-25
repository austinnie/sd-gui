#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量将 print() 替换为 logging 调用
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 需要处理的目录
TARGET_DIRS = [
    "core",
    "gui",
    "utils",
    "config",
    "generators",
    "services",
]

# 排除的文件模式
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".pyc",
    "venv",
    "env",
    "logs",
]

# 需要添加 logger 导入的文件
FILES_NEED_LOGGER = set()

# 替换规则
REPLACEMENTS = [
    # print("xxx") -> logger.info("xxx")
    (r'print\(f?"([^"]*)"\)', r'logger.info(f"\1")'),
    (r"print\(f?'([^']*)'\)", r"logger.info(f'\1')"),
    # print("xxx", file=sys.stderr) -> logger.error("xxx")
    (r'print\(f?"([^"]*)",\s*file=sys\.stderr\)', r'logger.error(f"\1")'),
    (r"print\(f?'([^']*)',\s*file=sys\.stderr\)", r"logger.error(f'\1')"),
    # print("xxx", "yyy") -> logger.info(f"xxx yyy")
    (r'print\(([^,)]+),\s*([^,)]+)\)', r'logger.info(f"\1 \2")'),
]


def should_skip_file(filepath: Path) -> bool:
    """检查是否应该跳过该文件"""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in str(filepath):
            return True
    return False


def add_logger_import(content: str, filepath: Path) -> str:
    """添加 logger 导入"""
    if 'from utils.logger import' in content:
        return content
    
    # 在现有导入之后添加
    lines = content.split('\n')
    new_lines = []
    import_section = False
    added = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        if line.startswith('import ') or line.startswith('from '):
            import_section = True
        elif import_section and not line.startswith((' ', '\t')) and line.strip():
            # 导入节结束
            if not added:
                new_lines.insert(i, 'from utils.logger import get_logger, info, warning, error, debug')
                added = True
            import_section = False
    
    if not added:
        # 在文件顶部添加
        new_lines.insert(0, 'from utils.logger import get_logger, info, warning, error, debug')
        new_lines.insert(1, '')
    
    return '\n'.join(new_lines)


def add_logger_init(content: str) -> str:
    """添加 logger = get_logger(__name__)"""
    if 'logger = get_logger' in content:
        return content
    
    # 在导入之后添加
    lines = content.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        if 'from utils.logger import' in line:
            # 在下一行添加 logger 初始化
            new_lines.append('')
            new_lines.append('logger = get_logger(__name__)')
    
    return '\n'.join(new_lines)


def process_file(filepath: Path) -> bool:
    """处理单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return False
    
    original = content
    
    # 1. 替换 print 语句
    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)
    
    # 2. 添加 logger 导入
    if 'logger.' in content and 'from utils.logger import' not in content:
        content = add_logger_import(content, filepath)
        content = add_logger_init(content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False


def main():
    print("=" * 60)
    print("  🔧 批量替换 print() 为 logging")
    print("=" * 60)
    
    processed = 0
    modified = 0
    
    for target_dir in TARGET_DIRS:
        dir_path = PROJECT_ROOT / target_dir
        if not dir_path.exists():
            continue
        
        for py_file in dir_path.rglob("*.py"):
            if should_skip_file(py_file):
                continue
            
            processed += 1
            if process_file(py_file):
                modified += 1
                print(f"   ✅ 已处理: {py_file.relative_to(PROJECT_ROOT)}")
    
    print("\n" + "=" * 60)
    print(f"✅ 完成! 处理 {processed} 个文件, 修改 {modified} 个文件")
    print("=" * 60)
    
    print("\n📝 下一步:")
    print("   1. 检查修改: git diff")
    print("   2. 测试程序: python main.py")
    print("   3. 提交: git add -A && git commit -m 'refactor: 统一日志系统'")


if __name__ == "__main__":
    main()