# ==================== 📋 全局配置中心 ====================
import os
import sys
from .ai_clean_config import *

# ✅ 核心修复：把当前脚本所在目录（tools）加入 Python 系统路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# 模型根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

# 模型路径配置
SD_MODEL_PATH_1 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/anytimeRealistic_v10.safetensors")
SD_MODEL_PATH_2 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/henmixreal_v10_henmixrealV10.safetensors")
SD_MODEL_PATH_3 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/sd-v1-5-tiny.safetensors")

ACTIVE_MODEL = 1

# 👇 统一核心参数（所有工具都从这里读）
STEPS = 25
MAX_LIMIT = 576
NEGATIVE_PROMPT_BASE = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, logo, brand"
INPUT_IMAGE_NAME = "input"  # 👈 统一原图文件名

# 👇 统一默认强度（各别特殊脚本可以在内部单独覆盖）
DEFAULT_STRENGTH = 0.35

if ACTIVE_MODEL == 1:
    SD_MODEL_PATH = SD_MODEL_PATH_1
elif ACTIVE_MODEL == 2:
    SD_MODEL_PATH = SD_MODEL_PATH_2
elif ACTIVE_MODEL == 3:
    SD_MODEL_PATH = SD_MODEL_PATH_3
else:
    SD_MODEL_PATH = SD_MODEL_PATH_1