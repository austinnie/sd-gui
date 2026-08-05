# tools/config.py
# ==================== 📋 全局配置中心 ====================
import os
import sys

# ✅ 核心修复：把当前脚本所在目录（tools）加入 Python 系统路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# ==================== 模型配置 ====================
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

# 模型路径配置
SD_MODEL_PATH_0 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/aiiiiii01_v10.safetensors")
SD_MODEL_PATH_1 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/anytimeRealistic_v10.safetensors")
SD_MODEL_PATH_2 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/henmixreal_v10_henmixrealV10.safetensors")
SD_MODEL_PATH_3 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/sd-v1-5-tiny.safetensors")

ACTIVE_MODEL = 0
STEPS = 25
MAX_LIMIT = 576
INPUT_IMAGE_NAME = "input"
DEFAULT_STRENGTH = 0.35

if ACTIVE_MODEL == 0:
    SD_MODEL_PATH = SD_MODEL_PATH_0
elif ACTIVE_MODEL == 1:
    SD_MODEL_PATH = SD_MODEL_PATH_1
elif ACTIVE_MODEL == 2:
    SD_MODEL_PATH = SD_MODEL_PATH_2
elif ACTIVE_MODEL == 3:
    SD_MODEL_PATH = SD_MODEL_PATH_3
else:
    SD_MODEL_PATH = SD_MODEL_PATH_0

# ==================== 消除AI痕迹配置 ====================
# 总开关
REMOVE_AI_TRACES = True

# 各功能开关
AI_CLEAR_METADATA = True   # 清除元数据（转换为JPG）
AI_INJECT_EXIF = True      # 注入EXIF信息
AI_REALISTIC = True        # 照片真实化

# 参数配置
AI_CAMERA = "sony_a7iv"    # 相机预设: sony_a7iv, canon_r5, nikon_z8, iphone_15
AI_STRENGTH = "medium"     # 强度: light / medium / strong
AI_STYLE = "portrait"      # 风格: portrait, landscape, street, night

# 是否随机化参数（让每张照片的EXIF略有不同）
AI_RANDOMIZE = True

# 图像指纹混淆
AI_FINGERPRINT_OBFUSCATION = True   # 图像指纹混淆
AI_DISTORTION_STRENGTH = 0.002      # 扭曲强度 (0.001-0.005)

# 紫边模拟
AI_CHROMATIC_ABERRATION = True      # 紫边/色散模拟（真实镜头特征）
AI_CHROMATIC_STRENGTH = 0.3         # 紫边强度 (0.1-0.8)

# 真实噪点
AI_REALISTIC_NOISE = True           # 真实噪点（基于ISO的噪声模型）
AI_NOISE_ISO_BASE = 400             # 噪点ISO基准值 (200-1600)
AI_NOISE_RANDOMIZE = True           # 随机化ISO值（每张照片不同）

# 轻微裁剪
AI_MINOR_CROP = True                # 轻微裁剪（改变构图，破坏像素排列）
AI_CROP_PERCENT = 0.015             # 裁剪比例 (0.005-0.03，即0.5%-3%)

# 风格自动检测
AUTO_DETECT_STYLE = True            # 自动检测素描/线稿风格

# 素描/线稿类风格关键词（检测到则跳过相机相关处理）
SKETCH_KEYWORDS = [
    "sketch", "pencil", "lineart", "baimiao", "ink", "wash",
    "draft", "monochrome", "black and white", "drawing",
    "charcoal", "graphite", "outline", "contour", "tiger_sketch",
    "素描", "线稿", "白描", "水墨", "铅笔", "炭笔", "速写"
]