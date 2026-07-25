from utils.logger import get_logger

logger = get_logger(__name__)

# utils/controlnet/types.py
"""
ControlNet 类型配置
"""

CONTROLNET_TYPES = {
    # 姿态/骨架类
    "openpose": {
        "name": "OpenPose (姿态)",
        "model_id": "lllyasviel/sd-controlnet-openpose",
        "description": "锁定人体姿态骨架",
        "needs_preprocessor": True,
        "preprocessor": "openpose"
    },
    "openpose_full": {
        "name": "OpenPose Full (完整姿态)",
        "model_id": "lllyasviel/control_v11p_sd15_openpose",
        "description": "全身姿态+手指+面部",
        "needs_preprocessor": True,
        "preprocessor": "openpose_full"
    },
    "dwpose": {
        "name": "DWPose (增强姿态)",
        "model_id": "lllyasviel/sd-controlnet-openpose",
        "description": "更精准的姿态检测",
        "needs_preprocessor": True,
        "preprocessor": "dwpose"
    },
    # 边缘/轮廓类
    "canny": {
        "name": "Canny (边缘)",
        "model_id": "lllyasviel/sd-controlnet-canny",
        "description": "Canny 边缘检测",
        "needs_preprocessor": True,
        "preprocessor": "canny"
    },
    "hed": {
        "name": "HED (软边缘)",
        "model_id": "lllyasviel/sd-controlnet-hed",
        "description": "HED 软边缘检测",
        "needs_preprocessor": True,
        "preprocessor": "hed"
    },
    "lineart": {
        "name": "Lineart (线稿)",
        "model_id": "lllyasviel/control_v11p_sd15_lineart",
        "description": "线稿提取",
        "needs_preprocessor": True,
        "preprocessor": "lineart"
    },
    "scribble": {
        "name": "Scribble (涂鸦)",
        "model_id": "lllyasviel/sd-controlnet-scribble",
        "description": "涂鸦/草图控制",
        "needs_preprocessor": True,
        "preprocessor": "scribble"
    },
    # 深度/空间类
    "depth": {
        "name": "Depth (深度)",
        "model_id": "lllyasviel/sd-controlnet-depth",
        "description": "深度图控制",
        "needs_preprocessor": True,
        "preprocessor": "depth"
    },
    "midas": {
        "name": "Midas (深度)",
        "model_id": "lllyasviel/control_v11f1p_sd15_depth",
        "description": "Midas 深度图",
        "needs_preprocessor": True,
        "preprocessor": "midas"
    },
    "normal": {
        "name": "Normal (法线)",
        "model_id": "lllyasviel/sd-controlnet-normal",
        "description": "法线图控制",
        "needs_preprocessor": True,
        "preprocessor": "normal"
    },
    # 风格/参考类
    "reference": {
        "name": "Reference (风格)",
        "model_id": "lllyasviel/control_v11u_sd15_reference",
        "description": "锁定风格/构图，不锁动作",
        "needs_preprocessor": False,
        "preprocessor": None
    },
    # 其他
    "mlsd": {
        "name": "MLSD (直线)",
        "model_id": "lllyasviel/sd-controlnet-mlsd",
        "description": "直线检测(建筑)",
        "needs_preprocessor": True,
        "preprocessor": "mlsd"
    },
    "seg": {
        "name": "Seg (语义分割)",
        "model_id": "lllyasviel/sd-controlnet-seg",
        "description": "语义分割控制",
        "needs_preprocessor": True,
        "preprocessor": "seg"
    },
    "tile": {
        "name": "Tile (图块)",
        "model_id": "lllyasviel/control_v11f1e_sd15_tile",
        "description": "图块/放大控制",
        "needs_preprocessor": False,
        "preprocessor": None
    },
}


def get_controlnet_types():
    """获取所有 ControlNet 类型列表"""
    return list(CONTROLNET_TYPES.keys())


def get_controlnet_display_names():
    """获取 ControlNet 显示名称列表（用于 UI）"""
    return [f"{key} ({info['name']})" for key, info in CONTROLNET_TYPES.items()]


def get_controlnet_info(controlnet_type):
    """获取 ControlNet 类型信息"""
    return CONTROLNET_TYPES.get(controlnet_type, CONTROLNET_TYPES["openpose"])


def is_controlnet_available():
    """检查 ControlNet 是否可用"""
    try:
        import controlnet_aux
        return True
    except ImportError:
        logger.info(f"⚠️ controlnet_aux 未安装，ControlNet 功能不可用")
        return False
    except Exception as e:
        logger.info(f"⚠️ 检查 ControlNet 可用性失败: {e}")
        return False