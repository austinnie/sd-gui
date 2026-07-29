# ==================== 📖 风格提示词总管 ====================
import os
import glob

# 找到当前目录下的 prompts 子文件夹
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(CURRENT_DIR, "prompts")

STYLE_PROMPTS = {}

# 自动扫描 prompts 目录下的所有 .py 文件并加载
if os.path.exists(PROMPTS_DIR):
    for filepath in glob.glob(os.path.join(PROMPTS_DIR, "*.py")):
        # 获取文件名（不带扩展名）
        basename = os.path.basename(filepath)
        if basename == "__init__.py":
            continue
        
        # 动态执行文件里的代码
        with open(filepath, 'r', encoding='utf-8') as f:
            file_code = f.read()
        
        # 创建一个临时命名空间来执行
        local_ns = {}
        exec(file_code, {}, local_ns)
        
        # 提取 STYLE 变量并合并到主字典
        if 'STYLE' in local_ns:
            STYLE_PROMPTS.update(local_ns['STYLE'])
        elif 'styles' in local_ns:
            STYLE_PROMPTS.update(local_ns['styles'])

# 如果没有任何配置，给个默认提示
if not STYLE_PROMPTS:
    print("⚠️ 警告：没有找到任何风格配置！请确保 prompts 文件夹里有 .py 文件。")