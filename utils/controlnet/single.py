# utils/controlnet/single.py
"""
单层 ControlNet 处理
"""

import os
import gc
import random
import torch
from datetime import datetime
from PIL import Image

from .preprocess import preprocess_image_for_controlnet
from .pipeline import get_controlnet_pipeline
from .types import get_controlnet_info


from utils.logger import get_logger

logger = get_logger(__name__)
# ControlNet 强度映射
CONTROLNET_STRENGTH_MAP = {
    "openpose": 0.85,
    "openpose_full": 0.85,
    "dwpose": 0.90,
    "canny": 0.70,
    "hed": 0.75,
    "lineart": 0.70,
    "scribble": 0.70,
    "depth": 0.80,
    "midas": 0.80,
    "normal": 0.80,
    "reference": 0.55,
    "mlsd": 0.80,
    "seg": 0.85,
    "tile": 0.90,
}


def process_with_controlnet(
    selected_images,
    prompt,
    negative,
    steps,
    cfg,
    strength,
    seed,
    app,
    params,
    progress_callback,
    status_callback,
    controlnet_type="openpose"
):
    """
    使用 ControlNet 处理图生图
    """
    print("=" * 60)
    logger.info(f"🔍 [ControlNet 调试] process_with_controlnet 被调用")
    logger.info(f"   selected_images: {len(selected_images)} 张")
    logger.info(f"   prompt: {prompt[:50]}...")
    logger.info(f"   controlnet_type: {controlnet_type}")
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
    
    conditioning_scale = CONTROLNET_STRENGTH_MAP.get(controlnet_type, 0.80)
    logger.info(f"   🎛️ ControlNet 强度: {conditioning_scale:.2f} ({controlnet_type})")
    
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
        
        max_size = 512
        if max(new_w, new_h) > max_size:
            scale = max_size / max(new_w, new_h)
            new_w = int(new_w * scale)
            new_h = int(new_h * scale)
            new_w = ((new_w + 31) // 64) * 64
            new_h = ((new_h + 31) // 64) * 64
            init_image = init_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        if controlnet_type == "reference":
            control_image = init_image.copy()
        else:
            status_callback(f"🔄 预处理图片 {img_idx+1}/{total} ({info['name']})...")
            control_image = preprocess_image_for_controlnet(
                image_path,
                controlnet_type=controlnet_type,
                output_size=(new_w, new_h)
            )
            if control_image is None:
                status_callback("⚠️ 预处理失败，跳过该图片")
                continue
        
        status_callback(f"🎨 生成中 {img_idx+1}/{total}...")
        
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
            
            from config.app_config import app_config
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_controlnet_{controlnet_type}_img{img_idx+1}.png"
            filepath = os.path.join(output_dir, filename)
            image.save(filepath)
            
            app.root.after(0, lambda fp=filepath, img=image: app.add_to_preview(fp, img))
            
            from utils.image_post_processor import post_process_image
            final_path = post_process_image(filepath, params, prompt=prompt, log_prefix="[ControlNet]")
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
            status_callback(f"❌ ControlNet 生成失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if pipe:
        del pipe
        gc.collect()
    
    return True, generated_images