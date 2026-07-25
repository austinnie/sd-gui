# scripts/fix_logger_imports.py
"""
修复 logger 导入，移除 warning 别名
"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 1. 移除 warning 导入
    content = re.sub(
        r'from utils\.logger import get_logger, info, warning, error, debug',
        'from utils.logger import get_logger',
        content
    )
    content = re.sub(
        r'from utils\.logger import get_logger, info, warning, error',
        'from utils.logger import get_logger',
        content
    )
    content = re.sub(
        r'from utils\.logger import get_logger, info, warning',
        'from utils.logger import get_logger',
        content
    )
    
    # 2. 添加 logger 初始化 (如果还没有)
    if 'logger = get_logger' not in content and 'from utils.logger import get_logger' in content:
        lines = content.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(line)
            if 'from utils.logger import get_logger' in line:
                new_lines.append('')
                new_lines.append('logger = get_logger(__name__)')
        content = '\n'.join(new_lines)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# 扫描所有 Python 文件
for py_file in PROJECT_ROOT.rglob("*.py"):
    if "venv" not in str(py_file) and "__pycache__" not in str(py_file):
        if fix_file(py_file):
            print(f"✅ 修复: {py_file.relative_to(PROJECT_ROOT)}")