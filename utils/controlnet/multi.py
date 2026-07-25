# utils/controlnet/multi.py
"""
多层 ControlNet 处理
"""

import os
import gc
import random
import torch
from datetime import datetime
from PIL import Image

from .preprocess import preprocess_image_for_controlnet
from .pipeline import get_multi_controlnet_pipeline
from .types import get_controlnet_info


from utils.logger import get_logger

logger = get_logger(__name__)
def get_recommended_multi_controlnet_combos():
    """
    获取推荐的多层 ControlNet 组合
    """
    return {
        # ===== 单层 =====
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
        "仅深度 (换背景)": {
            "types": ["depth"],
            "scales": [0.5],
            "description": "换背景专用：只锁空间深度"
        },
        # ===== 双层 =====
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
        "DWpose+深度 (精准)": {
            "types": ["dwpose", "depth"],
            "scales": [0.6, 0.4],
            "description": "精准姿态 + 深度空间"
        },
        # ===== 三层 =====
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
        "DWpose+Canny+深度 (精准)": {
            "types": ["dwpose", "canny", "depth"],
            "scales": [0.5, 0.3, 0.3],
            "description": "精准控制：增强姿态 + 边缘 + 深度"
        },
    }


def process_with_multi_controlnet(
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
    controlnet_types=None,
    conditioning_scales=None
):
    """
    使用多层 ControlNet 处理图生图
    """
    if controlnet_types is None:
        controlnet_types = ["openpose", "canny", "depth"]
    
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
    logger.info(f"🔍 [多层 ControlNet] process_with_multi_controlnet 被调用")
    logger.info(f"   selected_images: {len(selected_images)} 张")
    logger.info(f"   controlnet_types: {controlnet_types}")
    logger.info(f"   conditioning_scales: {conditioning_scales}")
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
        
        max_size = 512
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
            logger.info(f"   🎨 生成 {info['name']} 控制图...")
            
            control_img = preprocess_image_for_controlnet(
                image_path,
                controlnet_type=ctype,
                output_size=(new_w, new_h)
            )
            if control_img is not None:
                control_images.append(control_img)
                logger.info(f"      ✅ {ctype} 控制图已生成")
            else:
                logger.info(f"      ⚠️ {ctype} 控制图生成失败，使用原图")
                control_images.append(init_image.copy())
        
        if not control_images:
            status_callback("⚠️ 所有控制图生成失败，跳过")
            continue
        
        status_callback(f"🎨 生成中 {img_idx+1}/{total} (多层 ControlNet)...")
        
        current_seed = seed if seed != -1 else random.randint(1, 2**32 - 1)
        generator = torch.Generator("cpu").manual_seed(current_seed + img_idx)
        
        try:
            num_controls = len(control_images)
            negative_full = negative
            
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_full,
                image=[init_image] * num_controls,
                control_image=control_images,
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