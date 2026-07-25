# utils/controlnet/preprocess.py
"""
ControlNet 图片预处理
支持中文路径（通过 PIL 读取）
"""

import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple, Union

from .types import get_controlnet_info
from .config import CONTROLNET_PREPROCESS_MODE


from utils.logger import get_logger

logger = get_logger(__name__)


def preprocess_image_for_controlnet(
    image_input: Union[str, Image.Image],
    controlnet_type: str = "openpose",
    output_size: Tuple[int, int] = (512, 512)
) -> Optional[Image.Image]:
    """
    根据 ControlNet 类型预处理图片
    支持中文路径（通过 PIL 读取）
    
    参数:
        image_input: 图片路径 (str) 或 PIL Image
        controlnet_type: ControlNet 类型
        output_size: 输出尺寸 (width, height)
    
    返回:
        处理后的 PIL Image
    """
    try:
        from controlnet_aux import (
            OpenposeDetector,
            CannyDetector,
            HEDdetector,
            LineartDetector,
            MLSDdetector,
            MidasDetector,
            NormalBaeDetector,
            PidiNetDetector,
            ZoeDetector,
            DWposeDetector,
        )
    except ImportError:
        logger.info(f"⚠️ controlnet_aux 未安装，请运行: pip install controlnet-aux")
        return None
    
    # ===== ✅ 支持两种输入方式：路径字符串 或 PIL Image =====
    try:
        if isinstance(image_input, str):
            # 如果是路径，用 PIL 读取（支持中文）
            pil_image = Image.open(image_input).convert('RGB')
            logger.debug(f"   📁 从路径读取: {image_input[:50]}...")
        elif isinstance(image_input, Image.Image):
            pil_image = image_input.convert('RGB')
            logger.debug(f"   📁 从 PIL Image 读取")
        else:
            logger.info(f"   ⚠️ 不支持的输入类型: {type(image_input)}")
            return None
        
        # 转为 numpy 数组（OpenCV 格式）
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
    except Exception as e:
        logger.info(f"   ⚠️ 读取图片失败: {e}")
        return None
    
    info = get_controlnet_info(controlnet_type)
    preprocessor = info.get("preprocessor")
    
    if preprocessor is None:
        # 不需要预处理，直接返回
        return pil_image.resize(output_size, Image.Resampling.LANCZOS)
    
    try:
        # ===== 各种预处理 =====
        if preprocessor == "openpose":
            detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
            result = _preprocess_openpose(detector, image, output_size)
            
        elif preprocessor == "openpose_full":
            detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
            result = detector(image, output_type="pil", include_hands=True, include_face=True)
            
        elif preprocessor == "dwpose":
            result = _preprocess_dwpose(image, output_size)
            
        elif preprocessor == "canny":
            detector = CannyDetector()
            result = detector(image, output_type="pil")
            
        elif preprocessor == "hed":
            result = _preprocess_hed(image, output_size)
            
        elif preprocessor == "lineart":
            result = _preprocess_lineart(image, output_size)
            
        elif preprocessor == "scribble":
            detector = HEDdetector.from_pretrained("lllyasviel/ControlNet")
            result = detector(image, output_type="pil", scribble=True)
            
        elif preprocessor == "depth":
            detector = MidasDetector.from_pretrained("lllyasviel/ControlNet")
            result = detector(image, output_type="pil")
            
        elif preprocessor == "midas":
            detector = MidasDetector.from_pretrained("lllyasviel/ControlNet")
            result = detector(image, output_type="pil")
            
        elif preprocessor == "normal":
            detector = NormalBaeDetector.from_pretrained("lllyasviel/ControlNet")
            result = detector(image, output_type="pil")
            
        elif preprocessor == "mlsd":
            detector = MLSDdetector.from_pretrained("lllyasviel/ControlNet")
            result = detector(image, output_type="pil")
            
        elif preprocessor == "seg":
            from controlnet_aux import SamDetector
            detector = SamDetector.from_pretrained("ybelkada/segment-anything", subfolder="checkpoints")
            result = detector(image, output_type="pil")
            
        else:
            result = pil_image
            
        if result and output_size and output_size[0] > 0:
            result = result.resize(output_size, Image.Resampling.LANCZOS)
        return result
        
    except Exception as e:
        logger.info(f"⚠️ 预处理失败 ({preprocessor}): {e}")
        return None


def _preprocess_openpose(detector, image, output_size):
    """OpenPose 预处理 - 支持多种模式"""
    mode = CONTROLNET_PREPROCESS_MODE
    
    if mode == "pil":
        logger.debug(f"   📌 OpenPose 模式: PIL (原图+骨架)")
        return detector(image, output_type="pil")
    
    elif mode == "skeleton":
        logger.debug(f"   📌 OpenPose 模式: Skeleton (纯骨架)")
        try:
            result_pil = detector(image, output_type="pil", include_hands=False, include_face=False)
            result_np = np.array(result_pil)
            
            # 只保留最大连通区域（主体骨架）
            gray = cv2.cvtColor(result_np, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
            
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(thresh, connectivity=8)
            if num_labels > 1:
                areas = stats[1:, cv2.CC_STAT_AREA]
                if len(areas) > 0:
                    max_area_idx = np.argmax(areas) + 1
                    filtered = np.zeros_like(thresh)
                    filtered[labels == max_area_idx] = 255
                    thresh = filtered
            
            skeleton = np.zeros_like(result_np)
            skeleton[thresh > 0] = [255, 255, 255]
            
            kernel = np.ones((2, 2), np.uint8)
            skeleton = cv2.morphologyEx(skeleton, cv2.MORPH_CLOSE, kernel)
            
            return Image.fromarray(skeleton).convert('RGB')
            
        except Exception as e:
            logger.info(f"   ⚠️ 骨架提取失败: {e}，回退到 pil 模式")
            return detector(image, output_type="pil")
    
    return detector(image, output_type="pil")


def _preprocess_dwpose(image, output_size):
    """DWPose 预处理"""
    try:
        from controlnet_aux import DWposeDetector
        
        target_w, target_h = output_size if output_size and output_size[0] > 0 else (512, 512)
        max_dim = max(target_w, target_h)
        
        detector = DWposeDetector.from_pretrained("lllyasviel/ControlNet")
        
        try:
            result = detector(
                image,
                output_type="pil",
                detect_resolution=max_dim,
                image_resolution=max_dim,
                max_people=1
            )
            logger.debug(f"   ✅ DWPose 使用 max_people=1")
        except TypeError:
            logger.debug(f"   ℹ️ DWPose 版本不支持 max_people，使用默认行为")
            result = detector(
                image,
                output_type="pil",
                detect_resolution=max_dim,
                image_resolution=max_dim
            )
        
        if result:
            result = result.resize((target_w, target_h), Image.Resampling.LANCZOS)
        return result
        
    except Exception as e:
        logger.info(f"   ⚠️ DWPose 失败: {e}，回退到 OpenPose")
        from controlnet_aux import OpenposeDetector
        detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
        result = detector(image, output_type="pil", include_hands=False, include_face=False)
        if result and output_size and output_size[0] > 0:
            result = result.resize(output_size, Image.Resampling.LANCZOS)
        return result


def _preprocess_hed(image, output_size):
    """HED 预处理"""
    try:
        from controlnet_aux import HEDdetector
        import os
        from pathlib import Path
        
        cache_dir = os.environ.get("HF_HOME", os.path.expanduser("~/.cache"))
        local_model_path = Path(cache_dir) / "controlnet_aux" / "ControlNetHED.pth"
        
        if local_model_path.exists():
            logger.debug(f"   📁 使用本地 HED 模型: {local_model_path}")
            detector = HEDdetector()
        else:
            logger.debug(f"   ⚠️ 本地 HED 模型不存在，尝试下载...")
            detector = HEDdetector.from_pretrained("lllyasviel/ControlNet")
        
        result = detector(image, output_type="pil")
        if result:
            result = result.resize(output_size, Image.Resampling.LANCZOS)
        return result
        
    except Exception as e:
        logger.info(f"   ⚠️ HED 预处理失败: {e}，使用 Canny 替代")
        from controlnet_aux import CannyDetector
        detector = CannyDetector()
        result = detector(image, output_type="pil")
        if result:
            result = result.resize(output_size, Image.Resampling.LANCZOS)
        return result


def _preprocess_lineart(image, output_size):
    """Lineart 预处理"""
    try:
        from controlnet_aux import LineartDetector
        import os
        from pathlib import Path
        
        cache_dir = os.environ.get("HF_HOME", os.path.expanduser("~/.cache"))
        local_model_path = Path(cache_dir) / "controlnet_aux" / "sk_model.pth"
        
        if local_model_path.exists():
            logger.debug(f"   📁 使用本地 Lineart 模型: {local_model_path}")
            try:
                detector = LineartDetector()
                result = detector(image, output_type="pil")
            except Exception as e2:
                logger.info(f"   ⚠️ Lineart 加载失败: {e2}，使用 Canny 替代")
                from controlnet_aux import CannyDetector
                detector = CannyDetector()
                result = detector(image, output_type="pil")
        else:
            logger.debug(f"   ⚠️ 本地 Lineart 模型不存在，尝试下载...")
            detector = LineartDetector.from_pretrained("lllyasviel/ControlNet")
            result = detector(image, output_type="pil")
        
        if result:
            result = result.resize(output_size, Image.Resampling.LANCZOS)
        return result
        
    except Exception as e:
        logger.info(f"   ⚠️ Lineart 预处理失败: {e}，使用 Canny 替代")
        from controlnet_aux import CannyDetector
        detector = CannyDetector()
        result = detector(image, output_type="pil")
        if result:
            result = result.resize(output_size, Image.Resampling.LANCZOS)
        return result


# 别名，兼容旧代码
extract_pose = preprocess_image_for_controlnet