# utils/controlnet_helper.py

"""
ControlNet 辅助函数 - 用于图生图的姿态控制
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
# 1. 先定义所有函数
# ============================================================

def get_controlnet_pipeline(model_path, controlnet_model_path=None, device="cpu"):
    """加载 ControlNet Pipeline"""
    try:
        # 1. 加载 ControlNet 模型
        if controlnet_model_path:
            controlnet = ControlNetModel.from_single_file(
                controlnet_model_path,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
        else:
            controlnet = ControlNetModel.from_pretrained(
                "lllyasviel/sd-controlnet-openpose",
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
        
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
        
        # 3. 移动到 CPU 并优化
        pipe.to(device)
        pipe.enable_vae_slicing()
        pipe.enable_attention_slicing()
        if hasattr(pipe.vae, 'enable_tiling'):
            pipe.vae.enable_tiling()
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        
        print("✅ ControlNet Pipeline 加载完成")
        return pipe
        
    except Exception as e:
        print(f"❌ ControlNet Pipeline 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_pose(image_path, output_size=(512, 512)):
    """从图片中提取姿态图 (使用 OpenPose)"""
    try:
        from controlnet_aux import OpenposeDetector
        
        # 加载检测器
        detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
        
        # 读取图片
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        # 提取姿态
        pose_image = detector(image, output_type="pil")
        
        # 调整尺寸
        if pose_image:
            pose_image = pose_image.resize(output_size, Image.Resampling.LANCZOS)
        
        return pose_image
        
    except ImportError:
        print("⚠️ controlnet_aux 未安装，请运行: pip install controlnet-aux")
        return None
    except Exception as e:
        print(f"⚠️ 姿态提取失败: {e}")
        return None


def is_controlnet_available():
    """检查 ControlNet 是否可用"""
    try:
        import controlnet_aux
        return True
    except ImportError:
        return False


def process_with_controlnet(selected_images, prompt, negative, steps, cfg, strength, 
                            seed, app, params, progress_callback, status_callback):
    """
    使用 ControlNet 处理图生图
    """
    if not selected_images:
        return False, []
    
    # 获取模型路径
    model_name = app.model_var.get()
    model_path = app._get_model_path(model_name)
    if not model_path:
        status_callback("❌ 找不到模型文件")
        return False, []
    
    # 加载 ControlNet Pipeline
    status_callback("📦 加载 ControlNet...")
    pipe = get_controlnet_pipeline(model_path)  # ✅ 调用上面定义的函数
    if pipe is None:
        return False, []
    
    generated_images = []
    total = len(selected_images)
    
    for img_idx, image_path in enumerate(selected_images):
        if hasattr(app, 'txt2img_tab') and app.txt2img_tab.cancel_generation:
            break
        
        # 提取姿态图
        status_callback(f"🦴 提取姿态图 {img_idx+1}/{len(selected_images)}...")
        pose_image = extract_pose(image_path)  # ✅ 调用上面定义的函数
        if pose_image is None:
            status_callback("⚠️ 姿态提取失败，跳过该图片")
            continue
        
        # 加载原图
        init_image = Image.open(image_path).convert('RGB')
        w, h = init_image.size
        
        # 对齐尺寸到 64 的倍数
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
        
        # 调整姿态图尺寸
        pose_image = pose_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        status_callback(f"🎨 使用 ControlNet 生成 {img_idx+1}/{len(selected_images)}...")
        
        # 生成种子
        current_seed = seed if seed != -1 else random.randint(1, 2**32 - 1)
        generator = torch.Generator("cpu").manual_seed(current_seed + img_idx)
        
        try:
            # 运行 ControlNet 生成
            result = pipe(
                prompt=prompt,
                negative_prompt=negative,
                image=init_image,
                control_image=pose_image,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
                controlnet_conditioning_scale=0.8,
                num_images_per_prompt=1,
            )
            
            image = result.images[0]
            
            # 保存图片
            from config.app_config import app_config
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_controlnet_img{img_idx+1}.png"
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
# 2. 最后定义别名（向后兼容）
# ============================================================
# ✅ 这些别名必须在所有函数定义之后
_get_controlnet_pipeline = get_controlnet_pipeline
_extract_pose = extract_pose