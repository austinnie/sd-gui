# ==================== 📖 风格提示词总管 ====================
import os
import glob

# 找到当前目录下的 prompts 子文件夹
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 定义两个提示词目录（旧版和新版）
PROMPTS_DIR_OLD = os.path.join(CURRENT_DIR, "prompts")
PROMPTS_DIR_NEW = os.path.join(CURRENT_DIR, "prompts_new")

STYLE_PROMPTS = {}

# ==================== 1. 加载旧版目录 (prompts) ====================
def load_prompts_from_dir(directory_path):
    if not os.path.exists(directory_path):
        return {}
    
    local_styles = {}
    for filepath in glob.glob(os.path.join(directory_path, "*.py")):
        basename = os.path.basename(filepath)
        if basename == "__init__.py":
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                file_code = f.read()
            
            local_ns = {}
            exec(file_code, {}, local_ns)
            
            if 'STYLE' in local_ns:
                local_styles.update(local_ns['STYLE'])
            elif 'styles' in local_ns:
                local_styles.update(local_ns['styles'])
        except Exception as e:
            print(f"⚠️ 警告：加载 {filepath} 时出错：{e}")
    
    return local_styles

# ==================== 2. 执行加载 ====================
# 先加载旧的
old_styles = load_prompts_from_dir(PROMPTS_DIR_OLD)
STYLE_PROMPTS.update(old_styles)
print(f"✅ 已加载旧版提示词: {len(old_styles)} 个")

# 后加载新的（如果有重名的，新的会覆盖旧的）
new_styles = load_prompts_from_dir(PROMPTS_DIR_NEW)
STYLE_PROMPTS.update(new_styles)
print(f"✅ 已加载新版提示词: {len(new_styles)} 个")

# ==================== 3. 最终校验 ====================
if not STYLE_PROMPTS:
    print("⚠️ 警告：没有找到任何风格配置！请确保 prompts 或 prompts_new 文件夹里有 .py 文件。")
else:
    print(f"🎯 系统共加载了 {len(STYLE_PROMPTS)} 个风格。")