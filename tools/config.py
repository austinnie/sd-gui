# tools/config.py
# ==================== 📋 全局配置中心 ====================
import os
import sys

# ✅ 核心修复：把当前脚本所在目录（tools）加入 Python 系统路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# ==================== 基础路径 ====================
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

# ==================== 🔵 模型选择主开关 ====================
# 核心开关：True=使用 OpenVINO 模型，False=使用普通模型
USE_OPENVINO_MODEL = False  
ACTIVE_MODEL = 1


# ==================== 🔴 终极物理隔离：决定最终路径 ====================
#OpenVINO模型下载和转换方法
#huggingface-cli download runwayml/stable-diffusion-v1-5 --local-dir D:\SD_OpenVINO\models\sd-v1-5\official
#optimum-cli export openvino --model D:/SD_OpenVINO/models/sd-v1-5/official --task text-to-image D:/SD_OpenVINO/models/sd-v1-5/official_ov 
# ==================== 🔴 终极物理隔离：决定最终路径 ====================
if USE_OPENVINO_MODEL:
    # 【分支 A：仅当开启 OpenVINO 时】   
    # 使用 os.path.normpath 把混合斜杠清洗为标准反斜杠，彻底解决目录不可识别问题
    SD_OV_MODEL_PATH = os.path.normpath(os.path.join(PROJECT_ROOT, "models", "sd-v1-5", "official_ov"))
    SD_MODEL_PATH = SD_OV_MODEL_PATH
    
else:
    # 【分支 B：普通模型（无论你怎么改，这里的 0~3 必须在 else 内部定义）】
    SD_MODEL_PATH_0 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/aiiiiii01_v10.safetensors") 
    SD_MODEL_PATH_1 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/anytimeRealistic_v10.safetensors")
    SD_MODEL_PATH_2 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/henmixreal_v10_henmixrealV10.safetensors")
    SD_MODEL_PATH_3 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/sd-v1-5-tiny.safetensors")

    if ACTIVE_MODEL == 0:
        SD_MODEL_PATH = SD_MODEL_PATH_0
    elif ACTIVE_MODEL == 1:
        SD_MODEL_PATH = SD_MODEL_PATH_1
    elif ACTIVE_MODEL == 2:
        SD_MODEL_PATH = SD_MODEL_PATH_2
    elif ACTIVE_MODEL == 3:
        SD_MODEL_PATH = SD_MODEL_PATH_3
    else:
        SD_MODEL_PATH_0 = os.path.join(PROJECT_ROOT, "models/sd-v1-5/official/v1-5-pruned-emaonly.safetensors")
        SD_MODEL_PATH = SD_MODEL_PATH_0
# ==================================================================


# ==================== 🤖 LoRA 模型选择开关 ====================
# 多 LoRA 配置模式：
# 你可以在此定义多个 LoRA，并决定同时启用哪几个。

# 默认启用哪些 LoRA（填入上面的索引号，如 [0, 1] 表示同时启用 0号和1号）
LORA_ACTIVE_INDICES = [1]  # 例如 [0] 启用第一个，[0, 1] 同时启用前两个

# 来源链接（仅供备忘）
# [0] Mecha Musume A: https://civitai.com/models/15464/a-mecha-musume-a                                  #AMechaSSS.safetensors 素体机娘
# [1] Mecha Girl Figure: https://civitai.com/models/93394/mechagirlfigure                                #MechaGirlFigure_v1.safetensors
# [2] Mecha Musume Gundam Slider: https://civitai.com/models/78090/mecha-musume-gundam-mecha-slider-lora #mecha_offset.safetensors
# [3] Mecha Style: https://civitai.com/models/65851/mecha-style                                          #Mechav2_1.0.safetensors
# [4] Mecha Girl: https://civitai.com/models/85652/mechagirl                                             #MechaGirl_v1 .safetensors
# [5] Mecha Girl (227168): https://civitai.com/models/227168/mecha-girl                                  #mecha_girl.safetensors

LORA_PATHS = [
    os.path.join(PROJECT_ROOT, "models", "sd15-lora", "AMechaSSS.safetensors"),          # [0] 对应 Civitai 15464 (Mecha Musume A)
    os.path.join(PROJECT_ROOT, "models", "sd15-lora", "MechaGirlFigure_v1.safetensors"), # [1] 对应 Civitai 93394 (Mecha Girl Figure)
    os.path.join(PROJECT_ROOT, "models", "sd15-lora", "mecha_offset.safetensors"),       # [2] 对应 Civitai 78090 (Gundam Slider)
    os.path.join(PROJECT_ROOT, "models", "sd15-lora", "Mechav2_1.0.safetensors"),        # [3] 对应 Civitai 65851 (Mecha Style)
    os.path.join(PROJECT_ROOT, "models", "sd15-lora", "MechaGirl_v1.safetensors"),       # [4] 对应 Civitai 85652 (Mecha Girl)
    os.path.join(PROJECT_ROOT, "models", "sd15-lora", "mecha_girl.safetensors")          # [5] 对应 Civitai 227168 (Mecha Girl 227168)
]

# 每个 LoRA 对应的权重（索引和上面 LORA_PATHS 一一对应）
LORA_WEIGHTS = [
    0.8,  # [0] 权重
    0.7,  # [1] 权重
    0.8,  # [2] 权重
    0.7,  # [3] 权重
    0.8,  # [4] 权重
    0.7   # [5] 权重
]

# 以下代码根据设定自动生成最终需要加载的 LoRA 列表，无需改动
FINAL_LORA_LIST = []
if LORA_ACTIVE_INDICES:
    for idx in LORA_ACTIVE_INDICES:
        if 0 <= idx < len(LORA_PATHS):
            FINAL_LORA_LIST.append({
                "path": LORA_PATHS[idx],
                "weight": LORA_WEIGHTS[idx] if idx < len(LORA_WEIGHTS) else 0.8
            })


# ==================== 📝 自动图片鉴赏配置 ====================
# 选择图片鉴赏后端引擎：
#   "tag"       -> 快速标签模式，提取画面元素关键词。
#   "blip"      -> 轻量级 BLIP-large 看图写话。
#   "combined"  -> 组合模式：BLIP 描述 + CLIP 精准标签。
#   "llm"       -> (最推荐) 本地 LLM (Ollama) 增强鉴赏模式。
#   "prompt"    -> (极速) 仅使用提示词降级，无需任何模型。
AI_APPRECIATION_ENGINE = "llm"  # 可根据需要改为 "combined", "blip" 等
# ================================================================

# ==================== ⚙️ 生成与图像处理参数 ====================
STEPS = 25
MAX_LIMIT = 576
INPUT_IMAGE_NAME = "input"
DEFAULT_STRENGTH = 0.35


# ==================== 📷 消除AI痕迹配置 ====================
# 总开关
REMOVE_AI_TRACES = True

# ==================== 1. 元数据清理 ====================
AI_CLEAR_METADATA = True       # 清除元数据并转换为 JPG (防止平台查AI)


# ==================== 2. 照片真实化处理 ====================
AI_REALISTIC = True            # 照片真实化（添加暗角、锐化、光影、微噪点）
# 真实化参数
AI_CAMERA = "sony_a7iv"        # 相机预设: sony_a7iv, canon_r5, nikon_z8, iphone_15
AI_STRENGTH = "light"          # 真实化强度: light / medium / strong
AI_STYLE = "portrait"          # 照片风格: portrait, landscape, street, night
AI_RANDOMIZE = True            # 是否随机化相机参数（让每张照片参数不同）


# ==================== 3. EXIF 元数据注入 ====================
AI_INJECT_EXIF = False         # 注入相机 EXIF 元数据（需要安装 exiftool）


# ==================== 4. 真实镜头噪点模拟 ====================
AI_REALISTIC_NOISE = False     # 添加基于 ISO 的真实噪点
# 噪点参数
AI_NOISE_ISO_BASE = 100        # 基准 ISO 值 (100-1600)
AI_NOISE_RANDOMIZE = True      # 随机化 ISO（每张照片 ISO 不同）


# ==================== 5. 镜头紫边/色散模拟 ====================
AI_CHROMATIC_ABERRATION = True # 模拟真实镜头的紫边/色散
AI_CHROMATIC_STRENGTH = 0.05   # 紫边强度 (0.05 - 0.8)，0.05 为极轻微保留质感


# ==================== 6. 图像细微变形 (改变 AI 像素排列) ====================
AI_FINGERPRINT_OBFUSCATION = False # 整体图像指纹混淆 (如果打开，包含扭曲、紫边、噪点、裁剪)
AI_DISTORTION_STRENGTH = 0.0005    # 【主要指纹混淆手段】微小扭曲强度 (0.0001-0.005)


# ==================== 7. 轻微裁剪 (破坏 AI 边缘像素规律) ====================
AI_MINOR_CROP = True           # 在图片边缘进行微小裁剪并缩放回原尺寸
AI_CROP_PERCENT = 0.005        # 裁剪比例 (0.005 - 0.03，0.005 为 0.5% 几乎无损)


# ==================== 8. 风格自动检测 ====================
AUTO_DETECT_STYLE = True       # 自动检测素描/线稿风格
# 素描/线稿类风格关键词（检测到则跳过相机相关处理）
SKETCH_KEYWORDS = [
    "sketch", "pencil", "lineart", "baimiao", "ink", "wash",
    "draft", "monochrome", "black and white", "drawing",
    "charcoal", "graphite", "outline", "contour", "tiger_sketch",
    "素描", "线稿", "白描", "水墨", "铅笔", "炭笔", "速写"
]