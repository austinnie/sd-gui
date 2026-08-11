# tools/config.py
# ==================== 📋 全局配置中心 ====================
import os
import sys
import json
import re  # 🆕 添加 re 模块导入
from pathlib import Path

# ✅ 核心修复：把当前脚本所在目录（tools）加入 Python 系统路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # tools/
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# ==================== 基础路径 ====================
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)  # v8_universal_generator/

# 🆕 添加 CONFIG_FILE 定义（用于自动更新配置）
CONFIG_FILE = os.path.join(CURRENT_DIR, "config.py")  # tools/config.py 自身

# ==================== 📚 加载模型索引 ====================
# 索引文件在 scripts/ 目录下（和 model_index.py 在一起）
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
INDEX_FILE = os.path.join(SCRIPTS_DIR, "models_index.json")

def load_model_index():
    """加载模型索引文件，如果不存在则自动生成"""
    if not os.path.exists(INDEX_FILE):
        print("⚠️ 模型索引不存在，正在自动生成...")
        try:
            import subprocess
            # 在 scripts 目录下运行 model_index.py
            model_index_script = os.path.join(SCRIPTS_DIR, "model_index.py")
            if os.path.exists(model_index_script):
                subprocess.run(
                    [sys.executable, model_index_script],
                    capture_output=True,
                    text=True,
                    cwd=SCRIPTS_DIR
                )
            else:
                print(f"⚠️ 找不到 model_index.py: {model_index_script}")
                return {"models": [], "default": None}
        except Exception as e:
            print(f"⚠️ 自动生成索引失败: {e}")
            return {"models": [], "default": None}
    
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 加载索引失败: {e}")
        return {"models": [], "default": None}

MODEL_INDEX = load_model_index()
AVAILABLE_MODELS = MODEL_INDEX.get("models", [])

# ==================== 🔵 模型选择配置 ====================
# 🆕 模型类型: "sd15" | "sdxl"（由 switch_model.py 自动管理）
MODEL_TYPE = "sdxl"


# 模式: "legacy" | "smart" | "manual"
#   legacy: 使用原有的 ACTIVE_MODEL 方式（完全兼容旧代码）
#   smart:  使用索引推荐的模型（自动选择最佳）
#   manual: 手动指定模型名称
MODEL_SELECTION_MODE = "smart"  # 默认使用智能模式

# 手动指定模型名称（当 MODE="manual" 时生效）
MANUAL_MODEL_NAME = None  # 例如 "DreamShaper_8"

# ==================== 保留原有配置（完全兼容） ====================
# 核心开关：True=使用 OpenVINO 模型，False=使用普通模型
USE_OPENVINO_MODEL = False  
ACTIVE_MODEL = 0  # 仅在 legacy 模式下使用

# ==================== 🔴 智能模型选择 ====================
# tools/config.py
# 替换原有的 resolve_model_path 函数

def resolve_model_path():
    """根据配置决定最终使用的模型路径（智能版）"""
    
    # ---------- 1. 从索引中智能查找 ----------
    try:
        import sys
        import json
        
        # 加载索引
        index_file = os.path.join(SCRIPTS_DIR, "models_index.json")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            
            models = index_data.get("models", [])
            
            # 获取当前配置的模型类型
            current_type = MODEL_TYPE if 'MODEL_TYPE' in globals() else "sd15"
            
            # 查找该类型的模型
            type_models = [m for m in models if m.get("model_type") == current_type]
            
            if type_models:
                # 优先使用默认模型
                default_name = index_data.get("default")
                if default_name:
                    for m in type_models:
                        if m["name"] == default_name:
                            # 解析路径
                            if "path" in m and m["path"]:
                                abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, m["path"]))
                                if os.path.exists(abs_path):
                                    print(f"🤖 智能加载: {m.get('model_type_icon', '')} {m['name']}")
                                    return abs_path
                            if "absolute_path" in m and m["absolute_path"]:
                                if os.path.exists(m["absolute_path"]):
                                    print(f"🤖 智能加载: {m.get('model_type_icon', '')} {m['name']}")
                                    return m["absolute_path"]
                
                # 使用该类型第一个模型
                m = type_models[0]
                if "path" in m and m["path"]:
                    abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, m["path"]))
                    if os.path.exists(abs_path):
                        print(f"🤖 智能加载: {m.get('model_type_icon', '')} {m['name']}")
                        return abs_path
                if "absolute_path" in m and m["absolute_path"]:
                    if os.path.exists(m["absolute_path"]):
                        print(f"🤖 智能加载: {m.get('model_type_icon', '')} {m['name']}")
                        return m["absolute_path"]
            
            # 如果当前类型没有模型，尝试其他类型
            for model_type in ["sdxl", "sd15"]:
                if model_type != current_type:
                    type_models = [m for m in models if m.get("model_type") == model_type]
                    if type_models:
                        m = type_models[0]
                        if "path" in m and m["path"]:
                            abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, m["path"]))
                            if os.path.exists(abs_path):
                                print(f"⚠️ {current_type} 无可用模型，自动使用 {model_type}: {m['name']}")
                                # 自动更新 config.py
                                try:
                                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                                        content = f.read()

                                    # ✅ 正确写法
                                    content = re.sub(r'MODEL_TYPE = ".*?"', f'MODEL_TYPE = "{model_type}"', content)
                                    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                                        f.write(content)
                                except:
                                    pass
                                return abs_path
    except Exception as e:
        print(f"⚠️ 智能加载失败: {e}")
    
    # ---------- 2. OpenVINO 模式 ----------
    if USE_OPENVINO_MODEL:
        ov_path = os.path.normpath(os.path.join(PROJECT_ROOT, "models", "sd-v1-5", "official_ov"))
        if os.path.exists(ov_path):
            return ov_path
        print("⚠️ 未找到 OpenVINO 模型，回退到普通模型")
    
    # ---------- 3. legacy 模式 ----------
    SD_MODEL_PATH_0 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/aiiiii01_v10.safetensors") 
    SD_MODEL_PATH_1 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/anytimeRealistic_v10.safetensors")
    SD_MODEL_PATH_2 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/henmixreal_v10_henmixrealV10.safetensors")
    SD_MODEL_PATH_3 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/sd-v1-5-tiny.safetensors")
    
    if ACTIVE_MODEL == 0:
        return SD_MODEL_PATH_0
    elif ACTIVE_MODEL == 1:
        return SD_MODEL_PATH_1
    elif ACTIVE_MODEL == 2:
        return SD_MODEL_PATH_2
    elif ACTIVE_MODEL == 3:
        return SD_MODEL_PATH_3
    
    # 最终回退
    return SD_MODEL_PATH_0 if os.path.exists(SD_MODEL_PATH_0) else SD_MODEL_PATH_1
    
    
# tools/config.py

def resolve_model_path_from_index(model_entry):
    """从索引条目解析实际模型路径（支持 SD1.5 + SDXL）"""
    if not model_entry:
        return None
    
    # 1. 如果有相对路径，基于项目根目录解析
    if "path" in model_entry and model_entry["path"]:
        abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, model_entry["path"]))
        if os.path.exists(abs_path):
            return abs_path
    
    # 2. 如果有绝对路径
    if "absolute_path" in model_entry and model_entry["absolute_path"]:
        if os.path.exists(model_entry["absolute_path"]):
            return model_entry["absolute_path"]
    
    # 3. 如果有 path 且是绝对路径
    if "path" in model_entry and model_entry["path"]:
        if os.path.exists(model_entry["path"]):
            return model_entry["path"]
    
    # 4. 回退：根据模型类型在对应目录中查找文件名
    if "filename" in model_entry:
        model_type = model_entry.get("model_type", "sd15")
        
        # 4a. 尝试在索引记录的 model_dirs 中查找（支持多类型）
        model_dirs = MODEL_INDEX.get("model_dirs", {})
        if model_type in model_dirs:
            fallback_path = os.path.join(model_dirs[model_type], model_entry["filename"])
            if os.path.exists(fallback_path):
                return fallback_path
        
        # 4b. 尝试在索引记录的 model_dirs_relative 中查找
        model_dirs_rel = MODEL_INDEX.get("model_dirs_relative", {})
        if model_type in model_dirs_rel:
            fallback_path = os.path.normpath(os.path.join(PROJECT_ROOT, model_dirs_rel[model_type], model_entry["filename"]))
            if os.path.exists(fallback_path):
                return fallback_path
        
        # 4c. 尝试在项目根目录的 models/{model_type} 目录查找
        fallback_path = os.path.join(PROJECT_ROOT, "models", model_type, model_entry["filename"])
        if os.path.exists(fallback_path):
            return fallback_path
        
        # 4d. 尝试在 SD_ROOT/models/{model_type} 目录查找
        SD_ROOT = os.path.dirname(PROJECT_ROOT)
        fallback_path = os.path.join(SD_ROOT, "models", model_type, model_entry["filename"])
        if os.path.exists(fallback_path):
            return fallback_path
    
    # 5. 最后回退：使用绝对路径（如果存在）
    if "absolute_path" in model_entry:
        return model_entry["absolute_path"]
    
    return None
    
SD_MODEL_PATH = resolve_model_path()

# ==================== 🤖 LoRA 模型选择开关 ====================

# ==================== 📚 加载 LoRA 索引 ====================
# tools/config.py
# 在 LoRA 配置部分添加

# ==================== 📚 加载 LoRA 索引 ====================
LORA_INDEX_FILE = os.path.join(SCRIPTS_DIR, "lora_index.json")

def load_lora_index():
    """加载 LoRA 索引文件（支持多类型）"""
    if not os.path.exists(LORA_INDEX_FILE):
        print("⚠️ LoRA 索引不存在，正在自动生成...")
        try:
            import subprocess
            lora_index_script = os.path.join(SCRIPTS_DIR, "lora_index.py")
            if os.path.exists(lora_index_script):
                subprocess.run(
                    [sys.executable, lora_index_script],
                    capture_output=True,
                    text=True,
                    cwd=SCRIPTS_DIR
                )
            else:
                print(f"⚠️ 找不到 lora_index.py: {lora_index_script}")
                return {"loras": [], "default": None}
        except Exception as e:
            print(f"⚠️ 自动生成 LoRA 索引失败: {e}")
            return {"loras": [], "default": None}
    
    try:
        with open(LORA_INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 加载 LoRA 索引失败: {e}")
        return {"loras": [], "default": None}

LORA_INDEX = load_lora_index()
AVAILABLE_LORAS = LORA_INDEX.get("loras", [])

# ==================== 🆕 LoRA 类型配置 ====================

# 多 LoRA 配置模式（完全保留原有配置）
LORA_ACTIVE_INDICES = [1]  # 例如 [0] 启用第一个，[0, 1] 同时启用前两个

# ==================== 🔄 根据类型获取 LoRA 路径 ====================
def get_lora_list():
    """根据 MODEL_TYPE 从索引中获取对应的 LoRA 列表"""
    lora_list = []
    
    if not LORA_ACTIVE_INDICES:
        return lora_list
    
    # ✅ 直接用全局 MODEL_TYPE
    model_type = MODEL_TYPE
    
    # 从索引中获取该类型的 LoRA
    type_loras = [l for l in AVAILABLE_LORAS if l.get("lora_type") == model_type]
    
    if not type_loras:
        print(f"⚠️ 没有找到 {model_type} 类型的 LoRA")
        return lora_list
    
    for idx in LORA_ACTIVE_INDICES:
        if 0 <= idx < len(type_loras):
            lora = type_loras[idx]
            # 解析绝对路径
            lora_path = lora.get("absolute_path")
            if not lora_path or not os.path.exists(lora_path):
                rel_path = lora.get("path")
                if rel_path:
                    lora_path = os.path.normpath(os.path.join(PROJECT_ROOT, rel_path))
            
            if lora_path and os.path.exists(lora_path):
                lora_list.append({
                    "path": lora_path,
                    "weight": 0.8,
                    "name": lora.get("name", f"lora_{idx}"),
                })
            else:
                print(f"⚠️ LoRA 文件不存在: {lora.get('name', 'unknown')}")
    
    return lora_list
    
    
# 向后兼容：保留 FINAL_LORA_LIST
FINAL_LORA_LIST = get_lora_list()

# ==================== 📝 自动图片鉴赏配置 ====================
AI_APPRECIATION_ENGINE = "llm"  # tag / blip / combined / llm / prompt

# ==================== ⚙️ 生成与图像处理参数 ====================
STEPS = 25
MAX_LIMIT = 768
INPUT_IMAGE_NAME = "input"
DEFAULT_STRENGTH = 0.35

# ==================== 📷 消除AI痕迹配置 ====================
REMOVE_AI_TRACES = True
AI_CLEAR_METADATA = True
AI_REALISTIC = True
AI_CAMERA = "sony_a7iv"
AI_STRENGTH = "light"
AI_STYLE = "portrait"
AI_RANDOMIZE = True
AI_INJECT_EXIF = False
AI_REALISTIC_NOISE = False
AI_NOISE_ISO_BASE = 100
AI_NOISE_RANDOMIZE = True
AI_CHROMATIC_ABERRATION = True
AI_CHROMATIC_STRENGTH = 0.05
AI_FINGERPRINT_OBFUSCATION = False
AI_DISTORTION_STRENGTH = 0.0005
AI_MINOR_CROP = True
AI_CROP_PERCENT = 0.005
AUTO_DETECT_STYLE = True

SKETCH_KEYWORDS = [
    "sketch", "pencil", "lineart", "baimiao", "ink", "wash",
    "draft", "monochrome", "black and white", "drawing",
    "charcoal", "graphite", "outline", "contour", "tiger_sketch",
    "素描", "线稿", "白描", "水墨", "铅笔", "炭笔", "速写"
]

# ==================== 📊 启动信息 ====================
def get_model_info():
    """获取当前模型信息"""
    for m in AVAILABLE_MODELS:
        # 检查路径匹配
        if "absolute_path" in m and m["absolute_path"] == SD_MODEL_PATH:
            return m
        if "path" in m:
            abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, m["path"]))
            if abs_path == SD_MODEL_PATH:
                return m
        if m.get("filename") and m["filename"] in SD_MODEL_PATH:
            return m
    return None

model_info = get_model_info()


# ==================== 🎨 采样器与步数配置 (智能联动) ====================
# 支持的采样器列表 (大小写不敏感):
# - Euler (你当前默认)
# - EulerAncestral / Euler a
# - DPM++ 2M
# - DPM++ 2M Karras (强烈推荐，用于人像/图生图)
# - DPM++ SDE Karras
# - DDIM
# - PNDM
# - LMS
# - Heun
# - UniPC

# ✨ 在此处修改，控制全局采样器
SCHEDULER_TYPE = "DPM++ 2M Karras"  # 建议改为 DPM++ 2M Karras

# 📊 采样器自适应步数词典 (根据选择的采样器，智能推荐最佳步数)
# 步数如果太小，有些采样器效果会差；步数太大，时间浪费。
SCHEDULER_STEPS_MAP = {
    "Euler": 25,              # 默认安全值
    "EulerAncestral": 25,     # 类似 Euler
    "DPM++ 2M": 20,           # 20 步足够
    "DPM++ 2M Karras": 20,    # 20 步已经神级效果
    "DPM++ SDE Karras": 25,
    "DDIM": 40,               # DDIM 需要步数多一点
    "PNDM": 40,
    "LMS": 35,
    "Heun": 30,
    "UniPC": 20,
}

# 🎯 解析实际使用的采样器名称 (处理别名)
def get_final_scheduler_name(input_name):
    name = input_name.strip().lower()
    if name in ["euler a", "euler_ancestral", "eulerancestral"]:
        return "EulerAncestral"
    if name in ["dpm++ 2m karras", "dpmpp_2m_karras"]:
        return "DPM++ 2M Karras"
    if name in ["dpm++ 2m", "dpmpp_2m"]:
        return "DPM++ 2M"
    if name in ["dpm++ sde karras", "dpmpp_sde_karras"]:
        return "DPM++ SDE Karras"
    # 其他原样返回（首字母大写，保持库的兼容）
    return name.capitalize()

# 计算出最终使用的采样器类型和步数
FINAL_SCHEDULER = get_final_scheduler_name(SCHEDULER_TYPE)
FINAL_STEPS = SCHEDULER_STEPS_MAP.get(FINAL_SCHEDULER, STEPS)  # 如果没配置，使用原 STEPS

print(f"🎨 采样器类型: {FINAL_SCHEDULER}")
print(f"🔄 推荐步数: {FINAL_STEPS}")

print(f"""
╔═══════════════════════════════════════════════╗
║  📦 模型配置信息                              ║
╠═══════════════════════════════════════════════╣
║  模式: {MODEL_SELECTION_MODE}                                  
║  模型: {os.path.basename(SD_MODEL_PATH) if SD_MODEL_PATH else '未设置'}      
║  大小: {model_info['size_gb'] if model_info else '未知'} GB
║  标签: {', '.join(model_info['tags']) if model_info else '无'}
║  OpenVINO: {USE_OPENVINO_MODEL}              
║  可用模型: {len(AVAILABLE_MODELS)} 个         
║  LoRA 激活: {len(FINAL_LORA_LIST)} 个         
╚═══════════════════════════════════════════════╝
""")