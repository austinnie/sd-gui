# tools/config.py
# ==================== 📋 全局配置中心 ====================
import os
import sys
import json
from pathlib import Path

# ✅ 核心修复：把当前脚本所在目录（tools）加入 Python 系统路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # tools/
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# ==================== 基础路径 ====================
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)  # v8_universal_generator/

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
def resolve_model_path():
    """根据配置决定最终使用的模型路径（增强版）"""
    
    # ---------- 1. OpenVINO 模式（优先） ----------
    if USE_OPENVINO_MODEL:
        ov_path = os.path.normpath(os.path.join(PROJECT_ROOT, "models", "sd-v1-5", "official_ov"))
        if os.path.exists(ov_path):
            return ov_path
        
        # 尝试从索引中查找 OpenVINO 模型
        for m in AVAILABLE_MODELS:
            if m.get("is_ov"):
                ov_abs_path = resolve_model_path_from_index(m)
                if ov_abs_path:
                    return ov_abs_path
        print("⚠️ 未找到 OpenVINO 模型，回退到普通模型")
    
    # ---------- 2. manual 模式 ----------
    if MODEL_SELECTION_MODE == "manual" and MANUAL_MODEL_NAME:
        for m in AVAILABLE_MODELS:
            if MANUAL_MODEL_NAME.lower() in m["name"].lower():
                return resolve_model_path_from_index(m)
        print(f"⚠️ 未找到模型: {MANUAL_MODEL_NAME}，使用默认模型")
    
    # ---------- 3. smart 模式 ----------
    if MODEL_SELECTION_MODE == "smart":
        if AVAILABLE_MODELS:
            # 使用索引推荐的默认模型
            default_name = MODEL_INDEX.get("default")
            if default_name:
                for m in AVAILABLE_MODELS:
                    if m["name"] == default_name:
                        abs_path = resolve_model_path_from_index(m)
                        if abs_path:
                            print(f"🤖 智能推荐: {m['name']} ({m['size_gb']}GB, 标签: {', '.join(m['tags'])})")
                            return abs_path
            # 回退：使用第一个模型
            first_path = resolve_model_path_from_index(AVAILABLE_MODELS[0])
            if first_path:
                return first_path
    
    # ---------- 4. legacy 模式（完全兼容旧代码） ----------
    # 使用原有的路径配置
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
    else:
        # 默认使用第一个
        return SD_MODEL_PATH_0

def resolve_model_path_from_index(model_entry):
    """从索引条目解析实际模型路径"""
    # 1. 如果有相对路径，基于项目根目录解析
    if "path" in model_entry and model_entry["path"]:
        # 相对路径（如 ../models/sd-v1-5/xxx.safetensors）
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
    
    # 4. 回退：在模型目录中查找文件名
    if "filename" in model_entry:
        # 尝试在 models_dir_relative 中查找
        models_dir_rel = MODEL_INDEX.get("models_dir_relative", "")
        if models_dir_rel:
            fallback_path = os.path.normpath(os.path.join(PROJECT_ROOT, models_dir_rel, model_entry["filename"]))
            if os.path.exists(fallback_path):
                return fallback_path
        
        # 尝试在 models_dir 中查找
        models_dir = MODEL_INDEX.get("models_dir", "")
        if models_dir:
            fallback_path = os.path.join(models_dir, model_entry["filename"])
            if os.path.exists(fallback_path):
                return fallback_path
        
        # 尝试在项目根目录的 models 目录查找
        fallback_path = os.path.join(PROJECT_ROOT, "models", "sd-v1-5", model_entry["filename"])
        if os.path.exists(fallback_path):
            return fallback_path
    
    # 5. 最后回退：使用绝对路径（如果存在）
    if "absolute_path" in model_entry:
        return model_entry["absolute_path"]
    
    return None

SD_MODEL_PATH = resolve_model_path()

# ==================== 🤖 LoRA 模型选择开关 ====================

# ==================== 📚 加载 LoRA 索引 ====================
LORA_INDEX_FILE = os.path.join(SCRIPTS_DIR, "lora_index.json")

def load_lora_index():
    """加载 LoRA 索引文件"""
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


# 多 LoRA 配置模式（完全保留原有配置）
LORA_ACTIVE_INDICES = [1]  # 例如 [0] 启用第一个，[0, 1] 同时启用前两个

# 来源链接（仅供备忘）
LORA_PATHS = [
    os.path.join(PROJECT_ROOT, "models", "sd15-lora", "AMechaSSS.safetensors"),          # [0]
    os.path.join(PROJECT_ROOT, "models", "sd15-lora", "MechaGirlFigure_v1.safetensors"), # [1]
    os.path.join(PROJECT_ROOT, "models", "sd15-lora", "mecha_offset.safetensors"),       # [2]
    os.path.join(PROJECT_ROOT, "models", "sd15-lora", "Mechav2_1.0.safetensors"),        # [3]
    os.path.join(PROJECT_ROOT, "models", "sd15-lora", "MechaGirl_v1.safetensors"),       # [4]
    os.path.join(PROJECT_ROOT, "models", "sd15-lora", "mecha_girl.safetensors")          # [5]
]

LORA_WEIGHTS = [0.8, 0.7, 0.8, 0.7, 0.8, 0.7]

FINAL_LORA_LIST = []
if LORA_ACTIVE_INDICES:
    for idx in LORA_ACTIVE_INDICES:
        if 0 <= idx < len(LORA_PATHS):
            FINAL_LORA_LIST.append({
                "path": LORA_PATHS[idx],
                "weight": LORA_WEIGHTS[idx] if idx < len(LORA_WEIGHTS) else 0.8
            })

# ==================== 📝 自动图片鉴赏配置 ====================
AI_APPRECIATION_ENGINE = "llm"  # tag / blip / combined / llm / prompt

# ==================== ⚙️ 生成与图像处理参数 ====================
STEPS = 25
MAX_LIMIT = 576
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