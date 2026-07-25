# services/cache_config.py
"""统一缓存配置 - 所有模块共享"""

import os

from utils.logger import get_logger, info, warning, error, debug

logger = get_logger(__name__)
# ===== 缓存根目录 =====
CACHE_ROOT = r"E:\hf_cache\.cache"
os.makedirs(CACHE_ROOT, exist_ok=True)

# ===== 设置环境变量 =====
os.environ["HF_HOME"] = CACHE_ROOT
os.environ["HF_HUB_CACHE"] = os.path.join(CACHE_ROOT, "hub")
os.environ["U2NET_HOME"] = os.path.join(CACHE_ROOT, "u2net")
os.environ["DEEPFACE_HOME"] = os.path.join(CACHE_ROOT, "deepface")
os.environ["TRANSFORMERS_CACHE"] = os.path.join(CACHE_ROOT, "hub")
os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(CACHE_ROOT, "hub")
os.environ["CLIP_INTERROGATOR_CACHE"] = os.path.join(CACHE_ROOT, "clip_interrogator")
CONTROLNET_AUX_HOME = os.path.join(CACHE_ROOT, "controlnet_aux")  # ✅ 新增

# ===== 路径常量 =====
HF_HUB_CACHE = os.environ["HF_HUB_CACHE"]
U2NET_HOME = os.environ["U2NET_HOME"]
DEEPFACE_HOME = os.environ["DEEPFACE_HOME"]

# ===== 确保目录存在 =====
for path in [HF_HUB_CACHE, U2NET_HOME, DEEPFACE_HOME]:
    os.makedirs(path, exist_ok=True)

# ===== 打印状态（只在首次加载时） =====
if not hasattr(os.environ, "_CACHE_CONFIG_LOADED"):
    logger.info(f"📁 缓存目录: {CACHE_ROOT}")
    logger.info(f"   HF_HUB_CACHE: {HF_HUB_CACHE}")
    logger.info(f"   U2NET_HOME: {U2NET_HOME}")
    logger.info(f"   DEEPFACE_HOME: {DEEPFACE_HOME}")
    os.environ["_CACHE_CONFIG_LOADED"] = "1"