# utils/controlnet_helper.py

"""
ControlNet 辅助函数 - 支持多种 ControlNet 类型
"""

import os
import torch
import gc
import random
from datetime import datetime
from PIL import Image
from diffusers import ControlNetModel, StableDiffusionControlNetPipeline, EulerDiscreteScheduler
import cv2
import numpy as np

# ============================================================
# ControlNet 类型配置
# ============================================================

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

def is_controlnet_available():
    """✅ 检查 ControlNet 是否可用"""
    try:
        import controlnet_aux
        return True
    except ImportError:
        print("⚠️ controlnet_aux 未安装，ControlNet 功能不可用")
        return False
    except Exception as e:
        print(f"⚠️ 检查 ControlNet 可用性失败: {e}")
        return False

def get_controlnet_types():
    """获取所有 ControlNet 类型列表"""
    return list(CONTROLNET_TYPES.keys())


def get_controlnet_display_names():
    """获取 ControlNet 显示名称列表（用于 UI）"""
    return [f"{key} ({info['name']})" for key, info in CONTROLNET_TYPES.items()]


def get_controlnet_info(controlnet_type):
    """获取 ControlNet 类型信息"""
    return CONTROLNET_TYPES.get(controlnet_type, CONTROLNET_TYPES["openpose"])

# ============================================================
# ✅ ControlNet 预处理模式配置
# ============================================================
# 可选值:
#   "pil"          - 使用 pil 输出（原图 + 骨架叠加）- 简单直接
#   "skeleton"     - 提取纯骨架图（黑白线条）- 需要额外处理
#   "np"           - 使用 numpy 数组输出
#   "auto"         - 自动选择最佳模式
CONTROLNET_PREPROCESS_MODE = "skeleton"  # ← 修改这里切换模式
# ============================================================

def preprocess_image_for_controlnet(image_path, controlnet_type="openpose", output_size=(512, 512)):
    """
    根据 ControlNet 类型预处理图片
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
        print("⚠️ controlnet_aux 未安装，请运行: pip install controlnet-aux")
        return None
    
    # 读取图片
    image = cv2.imread(image_path)
    if image is None:
        return None
    
    info = get_controlnet_info(controlnet_type)
    preprocessor = info.get("preprocessor")
    
    if preprocessor is None:
        pil_image = Image.open(image_path).convert('RGB')
        return pil_image.resize(output_size, Image.Resampling.LANCZOS)
    
    try:
        if preprocessor == "openpose":
            detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
            result = _preprocess_openpose(detector, image, output_size)
        elif preprocessor == "openpose_full":
            detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
            result = detector(image, output_type="pil", include_hands=True, include_face=True)


        elif preprocessor == "dwpose":
            # ✅ DWPose 兼容性修复
            try:
                from controlnet_aux import DWposeDetector
                detector = DWposeDetector.from_pretrained("lllyasviel/ControlNet")
                
                target_w, target_h = output_size if output_size and output_size[0] > 0 else (512, 512)
                max_dim = max(target_w, target_h)
                
                # ✅ 尝试使用 max_people=1，如果不支持则忽略
                try:
                    result = detector(
                        image, 
                        output_type="pil",
                        detect_resolution=max_dim,
                        image_resolution=max_dim,
                        max_people=1
                    )
                    print("   ✅ DWPose 使用 max_people=1")
                except TypeError:
                    # 版本不支持 max_people，去掉该参数重试
                    print("   ℹ️ DWPose 版本不支持 max_people，使用默认行为")
                    result = detector(
                        image, 
                        output_type="pil",
                        detect_resolution=max_dim,
                        image_resolution=max_dim
                    )
                
                if result:
                    result = result.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    
            except Exception as e:
                print(f"   ⚠️ DWPose 失败: {e}，回退到 OpenPose")
                from controlnet_aux import OpenposeDetector
                detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
                result = detector(image, output_type="pil", include_hands=False, include_face=False)
                if result and output_size and output_size[0] > 0:
                    result = result.resize(output_size, Image.Resampling.LANCZOS)
                
        elif preprocessor == "canny":
            detector = CannyDetector()
            result = detector(image, output_type="pil")
        elif preprocessor == "hed":
            try:
                from controlnet_aux import HEDdetector
                import os
                from pathlib import Path
                
                # 设置环境变量让 controlnet_aux 使用本地缓存
                cache_dir = os.environ.get("HF_HOME", os.path.expanduser("~/.cache"))
                local_model_path = Path(cache_dir) / "controlnet_aux" / "ControlNetHED.pth"
                
                if local_model_path.exists():
                    print(f"   📁 使用本地 HED 模型: {local_model_path}")
                    # 直接使用 HEDdetector，它会在缓存目录中查找
                    # 但需要确保文件名正确
                    detector = HEDdetector()
                    # 或者尝试用 from_pretrained 指定本地路径
                    # detector = HEDdetector.from_pretrained(str(local_model_path.parent))
                else:
                    print("   ⚠️ 本地 HED 模型不存在，尝试下载...")
                    detector = HEDdetector.from_pretrained("lllyasviel/ControlNet")
                
                result = detector(image, output_type="pil")
                
            except Exception as e:
                print(f"   ⚠️ HED 预处理失败: {e}")
                # 备用方案：使用 Canny 替代
                print("   🔄 使用 Canny 作为替代...")
                from controlnet_aux import CannyDetector
                detector = CannyDetector()
                result = detector(image, output_type="pil")
        elif preprocessor == "lineart":
            try:
                from controlnet_aux import LineartDetector
                import os
                from pathlib import Path
                
                cache_dir = os.environ.get("HF_HOME", os.path.expanduser("~/.cache"))
                local_model_path = Path(cache_dir) / "controlnet_aux" / "sk_model.pth"
                
                if local_model_path.exists():
                    print(f"   📁 使用本地 Lineart 模型: {local_model_path}")
                    # 尝试直接使用 LineartDetector
                    try:
                        # 有些版本支持直接传入模型路径
                        detector = LineartDetector()
                        result = detector(image, output_type="pil")
                    except Exception as e2:
                        print(f"   ⚠️ Lineart 加载失败: {e2}")
                        print("   🔄 使用 Canny 作为替代...")
                        from controlnet_aux import CannyDetector
                        detector = CannyDetector()
                        result = detector(image, output_type="pil")
                else:
                    print("   ⚠️ 本地 Lineart 模型不存在，尝试下载...")
                    detector = LineartDetector.from_pretrained("lllyasviel/ControlNet")
                    result = detector(image, output_type="pil")
                
                if result:
                    result = result.resize(output_size, Image.Resampling.LANCZOS)
                
            except Exception as e:
                print(f"   ⚠️ Lineart 预处理失败: {e}")
                print("   🔄 使用 Canny 作为替代...")
                from controlnet_aux import CannyDetector
                detector = CannyDetector()
                result = detector(image, output_type="pil")
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
            result = Image.open(image_path).convert('RGB')
        
        if result:
            return result.resize(output_size, Image.Resampling.LANCZOS)
        return None
        
    except Exception as e:
        print(f"⚠️ 预处理失败 ({preprocessor}): {e}")
        return None


def _preprocess_openpose(detector, image, output_size):
    """
    OpenPose 预处理 - 支持多种模式
    模式由 CONTROLNET_PREPROCESS_MODE 控制
    """
    mode = CONTROLNET_PREPROCESS_MODE
    
    if mode == "pil":
        # ===== 模式1: pil 输出（原图 + 骨架叠加）- 推荐 =====
        print("   📌 OpenPose 模式: PIL (原图+骨架)")
        result = detector(image, output_type="pil")
        return result
        
    elif mode == "skeleton":
        # ===== 模式2: 提取纯骨架图（黑白线条）- 【新增多人过滤】 =====
        print("   📌 OpenPose 模式: Skeleton (纯骨架)")
        try:
            # ✅ 使用 include_hands=False, include_face=False 减少杂散点
            result_pil = detector(image, output_type="pil", include_hands=False, include_face=False)
            result_np = np.array(result_pil)
            
            # ✅ 【关键】只保留最大连通区域（即主体骨架）
            gray = cv2.cvtColor(result_np, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
            
            # 找连通域，只保留最大的那个
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(thresh, connectivity=8)
            if num_labels > 1:
                # 面积最大的连通域（排除背景）
                areas = stats[1:, cv2.CC_STAT_AREA]
                if len(areas) > 0:
                    max_area_idx = np.argmax(areas) + 1  # +1 因为背景是0
                    # 只保留最大连通域
                    filtered = np.zeros_like(thresh)
                    filtered[labels == max_area_idx] = 255
                    thresh = filtered
            
            # 生成纯白骨架图
            skeleton = np.zeros_like(result_np)
            skeleton[thresh > 0] = [255, 255, 255]
            
            # 形态学闭运算连接断点
            kernel = np.ones((2, 2), np.uint8)
            skeleton = cv2.morphologyEx(skeleton, cv2.MORPH_CLOSE, kernel)
            
            debug_path = f"debug_skeleton_{datetime.now().strftime('%H%M%S')}.png"
            Image.fromarray(skeleton).save(debug_path)
            print(f"   📸 骨架图已保存: {debug_path}")
               
            return Image.fromarray(skeleton).convert('RGB')
            
        except Exception as e:
            print(f"   ⚠️ 骨架提取失败: {e}，回退到 pil 模式")
            return detector(image, output_type="pil")
    
    # 默认返回 pil 模式
    return detector(image, output_type="pil")
            
def get_controlnet_pipeline(model_path, controlnet_type="openpose", controlnet_model_path=None, device="cpu"):
    """
    加载 ControlNet Pipeline
    
    参数:
        model_path: 主模型路径
        controlnet_type: ControlNet 类型
        controlnet_model_path: 自定义 ControlNet 路径
        device: 设备
    """
    import torch  # ✅ 添加
    import os     # ✅ 确保也有
    try:
        info = get_controlnet_info(controlnet_type)
        model_id = info["model_id"]
        
        # 1. 加载 ControlNet 模型
        if controlnet_model_path and os.path.exists(controlnet_model_path):
            controlnet = ControlNetModel.from_single_file(
                controlnet_model_path,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            print(f"📦 加载 ControlNet (本地): {os.path.basename(controlnet_model_path)}")
        else:
            controlnet = ControlNetModel.from_pretrained(
                model_id,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            print(f"📦 加载 ControlNet: {info['name']}")
        
        # 2. 加载主模型
        pipe = StableDiffusionControlNetPipeline.from_single_file(
            model_path,
            controlnet=controlnet,
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
            use_safetensors=True,
            low_cpu_mem_usage=True
        )
        
        # 3. 优化配置
        pipe.to(device)
        pipe.enable_vae_slicing()
        pipe.enable_attention_slicing()
        if hasattr(pipe.vae, 'enable_tiling'):
            pipe.vae.enable_tiling()
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        
        print(f"✅ ControlNet Pipeline 加载完成: {info['name']}")
        print(f"   📝 {info['description']}")
        return pipe
        
    except Exception as e:
        print(f"❌ ControlNet Pipeline 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_with_controlnet(selected_images, prompt, negative, steps, cfg, strength, 
                            seed, app, params, progress_callback, status_callback,
                            controlnet_type="openpose"):
    """
    使用 ControlNet 处理图生图
    
    参数:
        controlnet_type: ControlNet 类型 (openpose, canny, depth, reference, etc.)
    """

    print("=" * 60)
    print("🔍 [ControlNet 调试] process_with_controlnet 被调用")
    print(f"   selected_images: {len(selected_images)} 张")
    print(f"   prompt: {prompt[:50]}...")
    print(f"   controlnet_type: {controlnet_type}")
    print("=" * 60)
    
    if not selected_images:
        return False, []
    
    # 获取模型路径
    model_name = app.model_var.get()
    model_path = app._get_model_path(model_name)
    if not model_path:
        status_callback("❌ 找不到模型文件")
        return False, []
    
    info = get_controlnet_info(controlnet_type)
    
    # 加载 ControlNet Pipeline
    status_callback(f"📦 加载 ControlNet ({info['name']})...")
    pipe = get_controlnet_pipeline(model_path, controlnet_type=controlnet_type)
    if pipe is None:
        status_callback(f"❌ ControlNet Pipeline 加载失败")
        return False, []
    
    # ===== ✅ ControlNet 强度映射（按类型区分） =====
    CONTROLNET_STRENGTH_MAP = {
        # 姿态/骨架类（高强度锁定动作）
        "openpose": 0.85,
        "openpose_full": 0.85,
        "dwpose": 0.90,
        
        # 边缘/轮廓类（中高强度，给模型一些自由）
        "canny": 0.70,
        "hed": 0.75,
        "lineart": 0.70,
        "scribble": 0.70,
        
        # 深度/空间类（高强度保持结构）
        "depth": 0.80,
        "midas": 0.80,
        "normal": 0.80,
        
        # 风格/参考类（低强度，避免过度复制）
        "reference": 0.55,
        
        # 其他
        "mlsd": 0.80,
        "seg": 0.85,
        "tile": 0.90,
    }
    
    generated_images = []
    total = len(selected_images)
    
    for img_idx, image_path in enumerate(selected_images):
        if hasattr(app, 'txt2img_tab') and app.txt2img_tab.cancel_generation:
            break
        
        # 加载原图
        init_image = Image.open(image_path).convert('RGB')
        w, h = init_image.size
        
        # 对齐尺寸
        new_w = ((w + 31) // 64) * 64
        new_h = ((h + 31) // 64) * 64
        if new_w != w or new_h != h:
            init_image = init_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 限制最大尺寸
        max_size = 1024
        if max(new_w, new_h) > max_size:
            scale = max_size / max(new_w, new_h)
            new_w = int(new_w * scale)
            new_h = int(new_h * scale)
            new_w = ((new_w + 31) // 64) * 64
            new_h = ((new_h + 31) // 64) * 64
            init_image = init_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # ============================================================
        # 根据类型决定 control_image
        # ============================================================
        if controlnet_type == "reference":
            # Reference 模式：用原图作为控制图
            status_callback(f"🎨 使用 Reference ControlNet {img_idx+1}/{len(selected_images)}...")
            control_image = init_image.copy()
        else:
            # 其他模式：预处理图片
            status_callback(f"🔄 预处理图片 {img_idx+1}/{len(selected_images)} ({info['name']})...")
            control_image = preprocess_image_for_controlnet(
                image_path, 
                controlnet_type=controlnet_type,
                output_size=(new_w, new_h)
            )
            
            if control_image is None:
                status_callback("⚠️ 预处理失败，跳过该图片")
                continue
        
        # ===== ✅ 根据类型获取 ControlNet 强度 =====
        conditioning_scale = CONTROLNET_STRENGTH_MAP.get(controlnet_type, 0.80)
        print(f"   🎛️ ControlNet 强度: {conditioning_scale:.2f} ({controlnet_type})")
        
        status_callback(f"🎨 生成中 {img_idx+1}/{len(selected_images)}...")
        
        # 生成种子
        current_seed = seed if seed != -1 else random.randint(1, 2**32 - 1)
        generator = torch.Generator("cpu").manual_seed(current_seed + img_idx)
        
        try:
            result = pipe(
                prompt=prompt,
                negative_prompt=negative + ", multiple people, two people, group, crowd, couple",
                image=init_image,
                control_image=control_image,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
                controlnet_conditioning_scale=conditioning_scale,
                num_images_per_prompt=1,
            )
            
            image = result.images[0]
            
            # 保存图片
            from config.app_config import app_config
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_controlnet_{controlnet_type}_img{img_idx+1}.png"
            filepath = os.path.join(output_dir, filename)
            image.save(filepath)
            
            # 添加到预览
            app.root.after(0, lambda fp=filepath, img=image: app.add_to_preview(fp, img))
            
            # 后处理
            from utils.image_post_processor import post_process_image
            final_path = post_process_image(filepath, params, prompt=prompt, log_prefix="[ControlNet]")
            if final_path != filepath:
                try:
                    os.remove(filepath)
                except:
                    pass
            
            generated_images.append(final_path)
            progress_callback((img_idx + 1) / total, f"✅ 完成 {img_idx+1}/{len(selected_images)}")
            
            # 清理内存
            del result
            gc.collect()
            
        except Exception as e:
            status_callback(f"❌ ControlNet 生成失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 释放 Pipeline
    if pipe:
        del pipe
        gc.collect()
    
    return True, generated_images


# ============================================================
# 🆕 多层 ControlNet 支持
# ============================================================

def get_multi_controlnet_pipeline(model_path, controlnet_types=None, device="cpu"):
    """
    加载多层 ControlNet Pipeline
    
    参数:
        model_path: 主模型路径
        controlnet_types: ControlNet 类型列表，如 ["openpose", "canny", "depth"]
                        默认使用 ["openpose", "canny", "depth"]
        device: 设备
    
    返回:
        pipe, controlnet_list
    """
    if controlnet_types is None:
        controlnet_types = ["openpose", "canny", "depth"]
    
    try:
        from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
        from diffusers import EulerDiscreteScheduler
        
        # 1. 加载多个 ControlNet 模型
        controlnets = []
        print(f"\n📦 加载多层 ControlNet ({len(controlnet_types)} 层)...")
        
        for ctype in controlnet_types:
            info = get_controlnet_info(ctype)
            print(f"   📦 {info['name']}...")
            
            cn = ControlNetModel.from_pretrained(
                info["model_id"],
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            controlnets.append(cn)
            print(f"      ✅ 加载完成")
        
        # 2. 加载主模型
        print(f"   📦 加载主模型...")
        pipe = StableDiffusionControlNetPipeline.from_single_file(
            model_path,
            controlnet=controlnets,  # 传入列表
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
            use_safetensors=True,
            low_cpu_mem_usage=True
        )
        
        # 3. 优化配置
        pipe.to(device)
        pipe.enable_vae_slicing()
        pipe.enable_attention_slicing()
        if hasattr(pipe.vae, 'enable_tiling'):
            pipe.vae.enable_tiling()
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        
        print(f"   ✅ 多层 ControlNet Pipeline 加载完成")
        return pipe, controlnets
        
    except Exception as e:
        print(f"❌ 多层 ControlNet Pipeline 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def process_with_multi_controlnet(
    selected_images, prompt, negative, steps, cfg, strength, 
    seed, app, params, progress_callback, status_callback,
    controlnet_types=None,
    conditioning_scales=None
):
    """
    使用多层 ControlNet 处理图生图
    
    参数:
        controlnet_types: ControlNet 类型列表
        conditioning_scales: 每层的控制强度列表（0-1）
    """
    if controlnet_types is None:
        controlnet_types = ["openpose", "canny", "depth"]
    
    # 自动生成 conditioning_scales
    if conditioning_scales is None:
        if len(controlnet_types) == 1:
            conditioning_scales = [0.6]
        elif len(controlnet_types) == 2:
            conditioning_scales = [0.6, 0.5]
        elif len(controlnet_types) == 3:
            conditioning_scales = [0.6, 0.5, 0.4]
        else:
            conditioning_scales = [0.5] * len(controlnet_types)
    
    print("=" * 60)
    print("🔍 [多层 ControlNet 调试] process_with_multi_controlnet 被调用")
    print(f"   selected_images: {len(selected_images)} 张")
    print(f"   controlnet_types: {controlnet_types}")
    print(f"   conditioning_scales: {conditioning_scales}")
    print("=" * 60)
    
    if not selected_images:
        return False, []
    
    model_name = app.model_var.get()
    model_path = app._get_model_path(model_name)
    if not model_path:
        status_callback("❌ 找不到模型文件")
        return False, []
    
    status_callback(f"📦 加载多层 ControlNet ({len(controlnet_types)} 层)...")
    pipe, controlnets = get_multi_controlnet_pipeline(model_path, controlnet_types)
    if pipe is None:
        status_callback("❌ ControlNet Pipeline 加载失败")
        return False, []
    
    generated_images = []
    total = len(selected_images)
    
    for img_idx, image_path in enumerate(selected_images):
        if hasattr(app, 'txt2img_tab') and app.txt2img_tab.cancel_generation:
            break
        
        init_image = Image.open(image_path).convert('RGB')
        w, h = init_image.size
        
        new_w = ((w + 31) // 64) * 64
        new_h = ((h + 31) // 64) * 64
        if new_w != w or new_h != h:
            init_image = init_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        max_size = 1024
        if max(new_w, new_h) > max_size:
            scale = max_size / max(new_w, new_h)
            new_w = int(new_w * scale)
            new_h = int(new_h * scale)
            new_w = ((new_w + 31) // 64) * 64
            new_h = ((new_h + 31) // 64) * 64
            init_image = init_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        status_callback(f"🔄 预处理图片 {img_idx+1}/{total}...")
        control_images = []
        
        for ctype in controlnet_types:
            info = get_controlnet_info(ctype)
            print(f"   🎨 生成 {info['name']} 控制图...")
            
            control_img = preprocess_image_for_controlnet(
                image_path,
                controlnet_type=ctype,
                output_size=(new_w, new_h)
            )
            if control_img is not None:
                control_images.append(control_img)
                print(f"      ✅ {ctype} 控制图已生成")
            else:
                print(f"      ⚠️ {ctype} 控制图生成失败，使用原图")
                control_images.append(init_image.copy())
        
        if not control_images:
            status_callback("⚠️ 所有控制图生成失败，跳过")
            continue
        
        status_callback(f"🎨 生成中 {img_idx+1}/{total} (多层 ControlNet)...")
        
        current_seed = seed if seed != -1 else random.randint(1, 2**32 - 1)
        generator = torch.Generator("cpu").manual_seed(current_seed + img_idx)
        
        try:
            negative_full = negative + ", multiple people, two people, group, crowd, couple"
            
            # ✅ 修复：统一使用列表格式（兼容多层 ControlNet）
            num_controls = len(control_images)
            
            # 打印调试信息
            print(f"   🔧 调用多层 ControlNet: {num_controls} 层")
            print(f"   📷 image 类型: {type([init_image] * num_controls)}")
            print(f"   🖼️ control_image 类型: {type(control_images)}")
            
            # ✅ 始终使用列表格式
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_full,
                image=[init_image] * num_controls,      # ✅ 始终是列表
                control_image=control_images,            # ✅ 始终是列表
                controlnet_conditioning_scale=conditioning_scales,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
                num_images_per_prompt=1,
            )
            
            image = result.images[0]
            
            from config.app_config import app_config
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            types_str = "_".join(controlnet_types)
            filename = f"{timestamp}_multi_controlnet_{types_str}_img{img_idx+1}.png"
            filepath = os.path.join(output_dir, filename)
            image.save(filepath)
            
            app.root.after(0, lambda fp=filepath, img=image: app.add_to_preview(fp, img))
            
            from utils.image_post_processor import post_process_image
            final_path = post_process_image(filepath, params, prompt=prompt, log_prefix="[Multi-ControlNet]")
            if final_path != filepath:
                try:
                    os.remove(filepath)
                except:
                    pass
            
            generated_images.append(final_path)
            progress_callback((img_idx + 1) / total, f"✅ 完成 {img_idx+1}/{total}")
            
            del result
            gc.collect()
            
        except Exception as e:
            status_callback(f"❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if pipe:
        del pipe
        gc.collect()
    
    return True, generated_images

# ============================================================
# 便捷函数：获取推荐的多层组合
# ============================================================

def get_recommended_multi_controlnet_combos():
    """
    获取推荐的多层 ControlNet 组合
    
    返回:
        字典，key 为组合名称，value 为 (类型列表, 权重列表)
    """
    return {
        # ============================================================
        # ⭐ 单层（最稳定，速度最快）
        # ============================================================
        "仅姿态 (换装)": {
            "types": ["openpose"],
            "scales": [0.6],
            "description": "换衣服专用：只锁姿态，自由度最高"
        },
        "仅姿态 (强锁)": {
            "types": ["openpose"],
            "scales": [0.85],
            "description": "强锁姿态，适合保持原姿势"
        },
        "仅边缘 (换装)": {
            "types": ["canny"],
            "scales": [0.5],
            "description": "换衣服专用：只锁轮廓"
        },
        "仅边缘 (强锁)": {
            "types": ["canny"],
            "scales": [0.7],
            "description": "强锁轮廓，适合保持构图"
        },
        "仅深度 (换背景)": {
            "types": ["depth"],
            "scales": [0.5],
            "description": "换背景专用：只锁空间深度"
        },
        
        # ============================================================
        # 🟡 双层（效果更好，速度适中）
        # ============================================================
        "姿态+边缘 (换装)": {
            "types": ["openpose", "canny"],
            "scales": [0.5, 0.3],
            "description": "换衣服专用：姿态锁定 + 轻度边缘"
        },
        "姿态+边缘 (强锁)": {
            "types": ["openpose", "canny"],
            "scales": [0.7, 0.5],
            "description": "强锁定：姿态 + 轮廓"
        },
        "姿态+深度 (换背景)": {
            "types": ["openpose", "depth"],
            "scales": [0.5, 0.4],
            "description": "换背景专用：姿态 + 空间深度"
        },
        "姿态+深度 (强锁)": {
            "types": ["openpose", "depth"],
            "scales": [0.7, 0.6],
            "description": "强锁定：姿态 + 深度空间"
        },
        "边缘+深度 (换背景)": {
            "types": ["canny", "depth"],
            "scales": [0.4, 0.5],
            "description": "换背景专用：轮廓 + 空间深度"
        },
        "姿态+软边缘 (风格)": {
            "types": ["openpose", "hed"],
            "scales": [0.4, 0.3],
            "description": "风格转换：姿态 + 软边缘"
        },
        "姿态+法线 (细节)": {
            "types": ["openpose", "normal"],
            "scales": [0.5, 0.4],
            "description": "细节保留：姿态 + 法线图"
        },
        "DWpose+深度 (精准)": {
            "types": ["dwpose", "depth"],
            "scales": [0.6, 0.4],
            "description": "精准姿态 + 深度空间"
        },
        
        # ============================================================
        # 🔴 三层（效果最强，但可能不稳定，速度慢）
        # ============================================================
        "姿态+边缘+深度 (换装)": {
            "types": ["openpose", "canny", "depth"],
            "scales": [0.4, 0.25, 0.15],
            "description": "换衣服专用：三轻锁，给模型更大自由度"
        },
        "姿态+边缘+深度 (强锁)": {
            "types": ["openpose", "canny", "depth"],
            "scales": [0.6, 0.5, 0.4],
            "description": "强锁定：保留原图结构（慎用）"
        },
        "姿态+边缘+深度 (极强锁)": {
            "types": ["openpose", "canny", "depth"],
            "scales": [0.8, 0.7, 0.6],
            "description": "极强锁定：几乎完全保留原图（仅微调）"
        },
        "姿态+软边缘+深度 (风格)": {
            "types": ["openpose", "hed", "depth"],
            "scales": [0.4, 0.3, 0.2],
            "description": "风格转换：姿态 + 软边缘 + 深度"
        },
        "DWpose+Canny+深度 (精准)": {
            "types": ["dwpose", "canny", "depth"],
            "scales": [0.5, 0.3, 0.3],
            "description": "精准控制：增强姿态 + 边缘 + 深度"
        },
    }
    
# ============================================================
# 向后兼容
# ============================================================
_get_controlnet_pipeline = get_controlnet_pipeline
_extract_pose = preprocess_image_for_controlnet  # 兼容旧名称
# ✅ 添加 extract_pose 作为 preprocess_image_for_controlnet 的别名
extract_pose = preprocess_image_for_controlnet


class ControlNetConfig:
    """全局 ControlNet 配置"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.enabled = False
        self.type = "openpose"
        self.strength = 0.8
        self._listeners = []
    
    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        self._notify()
    
    def set_type(self, controlnet_type: str):
        self.type = controlnet_type
        self._notify()
    
    def add_listener(self, callback):
        self._listeners.append(callback)
    
    def _notify(self):
        for cb in self._listeners:
            try:
                cb(self.enabled, self.type)
            except:
                pass

# 全局实例
controlnet_config = ControlNetConfig()