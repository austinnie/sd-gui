# ==================== 📖 风格提示词总管（默认使用新版，兼容旧版） ====================
import os
import glob
import sys

# 找到当前目录下的 tools 根目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 定义两个提示词目录
PROMPTS_DIR_NEW = os.path.join(CURRENT_DIR, "prompts_new")
PROMPTS_DIR_OLD = os.path.join(CURRENT_DIR, "prompts")

STYLE_PROMPTS = {}

# ==================== 核心加载函数 ====================
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

# ==================== 智能加载逻辑 ====================

# 1. 检查命令行参数是否包含 --use_old_prompts
use_old_prompts = "--use-old" in sys.argv or "--use_old" in sys.argv

# 2. 决定加载顺序
if use_old_prompts:
    print("\n🔓 [提示] 检测到 --use-old 参数，优先加载旧版提示词库...\n")
    
    # 优先加载旧的
    old_styles = load_prompts_from_dir(PROMPTS_DIR_OLD)
    STYLE_PROMPTS.update(old_styles)
    print(f"✅ 已加载旧版提示词: {len(old_styles)} 个")
    
    # 补充加载新的（如果有同名，旧的会保留）
    new_styles = load_prompts_from_dir(PROMPTS_DIR_NEW)
    STYLE_PROMPTS.update(new_styles)
    print(f"✅ 补充加载新版提示词: {len(new_styles)} 个")

else:
    # 默认策略：只加载新版 (prompts_new)
    print("\n🛡️ [安全模式] 默认只加载安全的新版提示词库 (prompts_new)...\n")
    
    new_styles = load_prompts_from_dir(PROMPTS_DIR_NEW)
    STYLE_PROMPTS.update(new_styles)
    print(f"✅ 已加载新版提示词: {len(new_styles)} 个")
    
    # 仅当新版目录为空时，才作为降级方案尝试加载旧版
    if not STYLE_PROMPTS:
        print("⚠️ 检测到新版目录为空或加载失败，降级尝试加载旧版提示词...")
        old_styles = load_prompts_from_dir(PROMPTS_DIR_OLD)
        STYLE_PROMPTS.update(old_styles)
        print(f"✅ 加载旧版提示词: {len(old_styles)} 个")

# ==================== 最终校验 ====================
if not STYLE_PROMPTS:
    print("⚠️ 警告：没有找到任何风格配置！请确保 prompts_new 文件夹里有 .py 文件。")
else:
    print(f"\n🎯 系统最终合并加载了 {len(STYLE_PROMPTS)} 个可用风格。")