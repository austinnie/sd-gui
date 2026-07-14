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


def preprocess_image_for_controlnet(image_path, controlnet_type="openpose", output_size=(512, 512)):
    """
    根据 ControlNet 类型预处理图片
    
    参数:
        image_path: 图片路径
        controlnet_type: ControlNet 类型
        output_size: 输出尺寸
    
    返回:
        预处理后的 PIL Image
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
        # 不需要预处理（如 reference）
        pil_image = Image.open(image_path).convert('RGB')
        return pil_image.resize(output_size, Image.Resampling.LANCZOS)
    
    try:
        # 根据类型选择检测器
        if preprocessor == "openpose":
            detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
            result = detector(image, output_type="pil")
        elif preprocessor == "openpose_full":
            detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
            result = detector(image, output_type="pil", include_hands=True, include_face=True)
        elif preprocessor == "dwpose":
            detector = DWposeDetector.from_pretrained("lllyasviel/ControlNet")
            result = detector(image, output_type="pil")
        elif preprocessor == "canny":
            detector = CannyDetector()
            result = detector(image, output_type="pil")
        elif preprocessor == "hed":
            detector = HEDdetector.from_pretrained("lllyasviel/ControlNet")
            result = detector(image, output_type="pil")
        elif preprocessor == "lineart":
            detector = LineartDetector.from_pretrained("lllyasviel/ControlNet")
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
            # 默认：直接返回原图
            result = Image.open(image_path).convert('RGB')
        
        if result:
            return result.resize(output_size, Image.Resampling.LANCZOS)
        return None
        
    except Exception as e:
        print(f"⚠️ 预处理失败 ({preprocessor}): {e}")
        return None


def get_controlnet_pipeline(model_path, controlnet_type="openpose", controlnet_model_path=None, device="cpu"):
    """
    加载 ControlNet Pipeline
    
    参数:
        model_path: 主模型路径
        controlnet_type: ControlNet 类型
        controlnet_model_path: 自定义 ControlNet 路径
        device: 设备
    """
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
                            controlnet_type="openpose"):  # ✅ 新增参数
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
            conditioning_scale = 0.7
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
            
            conditioning_scale = 0.8
        
        status_callback(f"🎨 生成中 {img_idx+1}/{len(selected_images)}...")
        
        # 生成种子
        current_seed = seed if seed != -1 else random.randint(1, 2**32 - 1)
        generator = torch.Generator("cpu").manual_seed(current_seed + img_idx)
        
        try:
            result = pipe(
                prompt=prompt,
                negative_prompt=negative,
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
# 向后兼容
# ============================================================
_get_controlnet_pipeline = get_controlnet_pipeline
_extract_pose = preprocess_image_for_controlnet  # 兼容旧名称
# ✅ 添加 extract_pose 作为 preprocess_image_for_controlnet 的别名
extract_pose = preprocess_image_for_controlnet