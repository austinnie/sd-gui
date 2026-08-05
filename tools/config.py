# tools/config.py
# ==================== 📋 全局配置中心 ====================
import os
import sys

# ✅ 核心修复：把当前脚本所在目录（tools）加入 Python 系统路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# ✅ 加载 ai_clean_config（放在前面，但不要污染命名空间）
# 使用显式导入，避免命名冲突
try:
    from ai_clean_config import (
        REMOVE_AI_TRACES,
        AI_CLEAR_METADATA,
        AI_INJECT_EXIF,
        AI_REALISTIC,
        AI_CAMERA,
        AI_STRENGTH,
        AI_STYLE,
        AI_RANDOMIZE,
        AI_FINGERPRINT_OBFUSCATION,
        AI_DISTORTION_STRENGTH,
        AI_CHROMATIC_ABERRATION,
        AI_CHROMATIC_STRENGTH,
        AI_REALISTIC_NOISE,
        AI_NOISE_ISO_BASE,
        AI_NOISE_RANDOMIZE,
        AI_MINOR_CROP,
        AI_CROP_PERCENT,
    )
except ImportError:
    print("⚠️ 警告：无法加载 ai_clean_config.py，使用默认配置")
    REMOVE_AI_TRACES = True
    AI_CLEAR_METADATA = True
    AI_INJECT_EXIF = True
    AI_REALISTIC = True
    AI_CAMERA = "sony_a7iv"
    AI_STRENGTH = "medium"
    AI_STYLE = "portrait"
    AI_RANDOMIZE = True
    AI_FINGERPRINT_OBFUSCATION = True
    AI_DISTORTION_STRENGTH = 0.002
    AI_CHROMATIC_ABERRATION = True
    AI_CHROMATIC_STRENGTH = 0.3
    AI_REALISTIC_NOISE = True
    AI_NOISE_ISO_BASE = 400
    AI_NOISE_RANDOMIZE = True
    AI_MINOR_CROP = True
    AI_CROP_PERCENT = 0.015

# 模型根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

# 模型路径配置
SD_MODEL_PATH_0 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/aiiiiii01_v10.safetensors")
SD_MODEL_PATH_1 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/anytimeRealistic_v10.safetensors")
SD_MODEL_PATH_2 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/henmixreal_v10_henmixrealV10.safetensors")
SD_MODEL_PATH_3 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/sd-v1-5-tiny.safetensors")

ACTIVE_MODEL = 0

# 👇 统一核心参数（所有工具都从这里读）
STEPS = 25
MAX_LIMIT = 576
NEGATIVE_PROMPT_BASE = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, logo, brand"
INPUT_IMAGE_NAME = "input"  # 👈 统一原图文件名

# 👇 统一默认强度（各别特殊脚本可以在内部单独覆盖）
DEFAULT_STRENGTH = 0.35

if ACTIVE_MODEL == 0:
    SD_MODEL_PATH = SD_MODEL_PATH_0
if ACTIVE_MODEL == 1:
    SD_MODEL_PATH = SD_MODEL_PATH_1
elif ACTIVE_MODEL == 2:
    SD_MODEL_PATH = SD_MODEL_PATH_2
elif ACTIVE_MODEL == 3:
    SD_MODEL_PATH = SD_MODEL_PATH_3
else:
    SD_MODEL_PATH = SD_MODEL_PATH_0

# 显式导出所有变量（供 generate.py 的 from config import * 使用）
__all__ = [
    'SD_MODEL_PATH', 'STEPS', 'MAX_LIMIT', 'INPUT_IMAGE_NAME',
    'NEGATIVE_PROMPT_BASE', 'DEFAULT_STRENGTH',
    'REMOVE_AI_TRACES', 'AI_CLEAR_METADATA', 'AI_INJECT_EXIF', 'AI_REALISTIC',
    'AI_CAMERA', 'AI_STRENGTH', 'AI_STYLE', 'AI_RANDOMIZE',
    'AI_FINGERPRINT_OBFUSCATION', 'AI_DISTORTION_STRENGTH',
    'AI_CHROMATIC_ABERRATION', 'AI_CHROMATIC_STRENGTH',
    'AI_REALISTIC_NOISE', 'AI_NOISE_ISO_BASE', 'AI_NOISE_RANDOMIZE',
    'AI_MINOR_CROP', 'AI_CROP_PERCENT'
]