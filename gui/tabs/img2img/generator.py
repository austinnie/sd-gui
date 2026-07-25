# gui/tabs/img2img/generator.py
"""图生图核心生成逻辑"""

import os
import gc
import time
import random
import torch
from datetime import datetime
from PIL import Image

from .utils import log, safe_del, auto_shorten_prompt
from .callbacks import Img2ImgStepCallback
from .saver import ImageSaver

from utils.logger import get_logger

logger = get_logger(__name__)
MAX_PIXELS = 1024 * 1024


class ImageGenerator:
    """图生图图片生成器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.params = tab.params
        self.saver = ImageSaver(tab)
    
    def generate(self, prompt, negative, strength, steps, cfg, seed,
                 num_images_per, target_width, target_height, use_controlnet=False):
        """生成图生图"""
        from utils.pipeline_pool import pipeline_pool
        from utils.scheduler_fix import fix_euler_scheduler_for_img2img
        
        log("开始图生图...")
        
        task_id = f"img2img_{datetime.now().strftime('%H%M%S')}"
        
        # 尺寸逻辑
        user_width = self.params.width_var.get()
        user_height = self.params.height_var.get()
        
        if user_width > 0 and user_height > 0:
            target_width = ((user_width + 31) // 64) * 64
            target_height = ((user_height + 31) // 64) * 64
            logger.info(f"📐 使用用户指定尺寸: {target_width}x{target_height}")
        else:
            target_width = 0
            target_height = 0
            logger.info(f"📐 使用原图尺寸")
        
        # ControlNet 模式
        if use_controlnet:
            try:
                log("🧠 启用多层 ControlNet 模式...")
                from utils.controlnet import get_recommended_multi_controlnet_combos
                from utils.controlnet import preprocess_image_for_controlnet
                from utils.controlnet import process_with_multi_controlnet
                from config.app_config import app_config
                
                combo_name = self.tab.controlnet_combo_var.get()
                combos = get_recommended_multi_controlnet_combos()
                combo_info = combos.get(combo_name, list(combos.values())[0])
                
                controlnet_types = combo_info["types"]
                conditioning_scales = combo_info["scales"]
                
                self.tab.update_status(f"🧠 启用 ControlNet: {combo_name}")
                
                filtered_images = []
                temp_dir = app_config.paths.output_dir
                os.makedirs(temp_dir, exist_ok=True)
                
                for img_path in self.tab.selected_images:
                    from PIL import Image as PILImage
                    temp_img = PILImage.open(img_path)
                    orig_w, orig_h = temp_img.size
                    proc_w = ((orig_w + 31) // 64) * 64
                    proc_h = ((orig_h + 31) // 64) * 64
                    
                    control_img = preprocess_image_for_controlnet(
                        img_path, controlnet_type="openpose", output_size=(proc_w, proc_h)
                    )
                    if control_img is not None:
                        temp_path = os.path.join(temp_dir, f"_temp_pose_{os.path.basename(img_path)}")
                        control_img.save(temp_path)
                        filtered_images.append(temp_path)
                
                success, controlnet_results = process_with_multi_controlnet(
                    selected_images=filtered_images,
                    prompt=prompt,
                    negative=negative,
                    steps=steps,
                    cfg=cfg,
                    strength=strength,
                    seed=seed,
                    app=self.app,
                    params=self.params,
                    progress_callback=self.tab._progress_callback,
                    status_callback=self.tab.update_status,
                    controlnet_types=controlnet_types,
                    conditioning_scales=conditioning_scales
                )
                
                for f in filtered_images:
                    try:
                        os.remove(f)
                    except:
                        pass
                
                if success and controlnet_results:
                    self.tab.update_status(f"✅ ControlNet 完成！共生成 {len(controlnet_results)} 张")
                    self.tab._on_generation_complete(0)
                    return
                else:
                    self.tab.update_status("⚠️ ControlNet 处理失败，回退到普通模式")
                    
            except Exception as e:
                log(f"❌ ControlNet 错误: {e}")
                import traceback
                traceback.print_exc()
                self.tab.update_status(f"⚠️ ControlNet 错误: {e}，回退到普通模式")
        
        # 普通图生图
        try:
            images = []
            for path in self.tab.selected_images:
                try:
                    log(f"加载图片: {os.path.basename(path)}")
                    img = Image.open(path).convert('RGB')
                    w, h = img.size
                    new_w = ((w + 31) // 64) * 64
                    new_h = ((h + 31) // 64) * 64
                    if new_w != w or new_h != h:
                        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        logger.info(f"   📐 原图尺寸对齐: {w}x{h} -> {new_w}x{new_h}")
                    images.append(img)
                except Exception as load_err:
                    logger.info(f"❌ 无法加载图片 {path}: {load_err}")
                    continue
            
            total_images = len(images) * num_images_per
            self.tab.update_status(f"开始处理 {len(images)} 张图片，每张生成 {num_images_per} 张变体")
            
            if seed == -1:
                seed = random.randint(1, 2**32 - 1)
            
            start_time = time.time()
            
            model_name = self.app.model_var.get()
            model_path = self.app._get_model_path(model_name)
            
            lora_display = self.app.lora_var.get() if hasattr(self.app, 'lora_var') else ""
            lora_path = None
            lora_weight = 1.0
            if lora_display and hasattr(self.app, 'lora_paths'):
                lora_path = self.app.lora_paths.get(lora_display)
                lora_weight = self.app.lora_weight_var.get() if hasattr(self.app, 'lora_weight_var') else 1.0
            
            pipe, is_new = pipeline_pool.get_pipeline(
                model_path=model_path,
                model_name=model_name,
                lora_path=lora_path,
                lora_weight=lora_weight,
                task_id=task_id
            )
            
            pipe, steps, current_strength = fix_euler_scheduler_for_img2img(pipe, steps, strength)
            
            # 局部重绘
            use_inpaint = self.tab.use_inpaint_var.get()
            mask_image = self.tab.mask_image
            mask_tensor = None
            
            if use_inpaint and mask_image is not None:
                try:
                    from diffusers import StableDiffusionInpaintPipeline
                    if not hasattr(self.tab, '_inpaint_pipe'):
                        logger.info(f"📦 首次加载 Inpaint 模型（额外内存占用）...")
                        StableDiffusionInpaintPipeline.from_pretrained(
                            "runwayml/stable-diffusion-inpainting",
                            torch_dtype=torch.float32
                        )
                        logger.info(f"✅ Inpaint 模型下载/缓存完成！")
                        self.tab._inpaint_pipe = StableDiffusionInpaintPipeline(
                            vae=pipe.vae,
                            text_encoder=pipe.text_encoder,
                            tokenizer=pipe.tokenizer,
                            unet=pipe.unet,
                            scheduler=pipe.scheduler,
                            safety_checker=None,
                            feature_extractor=None,
                            requires_safety_checker=False
                        )
                        logger.info(f"✅ Inpaint 模型从现有管道拼接成功！")
                    
                    pipe = self.tab._inpaint_pipe
                    pipe, steps, current_strength = fix_euler_scheduler_for_img2img(pipe, steps, current_strength)
                    mask_tensor = mask_image.convert("L")
                    logger.info(f"🖌️ 启用局部重绘，遮罩已加载")
                    
                except Exception as e:
                    logger.info(f"⚠️ 启用局部重绘失败，回退到普通图生图: {e}")
                    use_inpaint = False
            
            # 精简提示词
            if prompt:
                prompt = auto_shorten_prompt(prompt, max_len=280)
            if negative:
                negative = auto_shorten_prompt(negative, max_len=280)
            
            from config.app_config import app_config
            gen_cfg = app_config.generation
            size_cfg = gen_cfg.size
            
            steps = max(gen_cfg.steps["min"], min(gen_cfg.steps["max"], steps))
            cfg = max(gen_cfg.cfg["min"], min(gen_cfg.cfg["max"], cfg))
            strength = max(0.05, min(0.99, strength))
            num_images_per = max(1, min(num_images_per, 4))
            
            def progress_cb(value, msg):
                self.app.root.after(0, lambda: self.app.progress_bar.update(value, msg, "图生图"))
            
            for img_idx, init_image in enumerate(images):
                self.tab.update_progress(img_idx / total_images, f"🔄 正在处理图片 {img_idx+1}/{len(images)}...")
                if self.tab.cancel_generation:
                    break
                
                original_w, original_h = init_image.size
                has_prompt = prompt and prompt.strip()
                init_image = self._adjust_image_size(init_image, original_w, original_h, has_prompt,
                                                       target_width, target_height)
                
                # 人脸检测
                import cv2
                import numpy as np
                img_cv = np.array(init_image.convert('RGB'))[:, :, ::-1].copy()
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                
                try:
                    if hasattr(cv2, 'CascadeClassifier'):
                        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
                        if len(faces) > 0:
                            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                            face_area = w * h
                            image_area = original_w * original_h
                            face_ratio = face_area / image_area
                            if face_ratio > 0.15:
                                strength = min(strength, 0.3)
                                logger.info(f"   🧑 检测到头像 (人脸占比 {face_ratio:.1%})，强度自动调整为: {strength:.2f}")
                except Exception as e:
                    pass
                
                for i in range(num_images_per):
                    if self.tab.cancel_generation:
                        break
                    
                    log(f"生成变体 {i+1}/{num_images_per}")
                    current_seed = seed + img_idx * num_images_per + i
                    generator = torch.Generator("cpu").manual_seed(current_seed)
                    current_strength = strength
                    
                    cancel_flag = lambda: self.tab.cancel_generation
                    step_callback = Img2ImgStepCallback(
                        progress_cb, steps, start_time, cancel_flag,
                        img_idx, i, len(images), num_images_per,
                        source="图生图"
                    )
                    
                    log("调用 pipeline...")
                    with torch.no_grad():
                        if use_inpaint and mask_tensor is not None:
                            result = pipe(
                                prompt=prompt,
                                negative_prompt=negative,
                                image=init_image,
                                mask_image=mask_tensor,
                                strength=current_strength,
                                num_inference_steps=steps,
                                guidance_scale=cfg,
                                generator=generator,
                                callback_on_step_end=step_callback
                            )
                        else:
                            result = pipe(
                                prompt=prompt,
                                negative_prompt=negative,
                                image=init_image,
                                strength=current_strength,
                                num_inference_steps=steps,
                                guidance_scale=cfg,
                                generator=generator,
                                callback_on_step_end=step_callback
                            )
                    
                    log("pipeline 调用完成")
                    image = result.images[0]
                    
                    # 保存图片 - 使用 saver
                    filepath = self.saver.save(
                        image=image,
                        prompt=prompt,
                        img_idx=img_idx,
                        var_idx=i
                    )
                    
                    # 添加到预览
                    self.app.root.after(0, lambda fp=filepath, img=image: self.app.add_to_preview(fp, img))
                    
                    safe_del(result)
                    safe_del(generator)
                    import gc
                    gc.collect()
                    
                    from gui.components.memory_monitor import get_memory_usage, force_memory_cleanup
                    mem_gb = get_memory_usage()
                    if mem_gb > 8.0:
                        force_memory_cleanup()
                    
                    if i < num_images_per - 1:
                        time.sleep(0.5)
                
                force_memory_cleanup()
            
            elapsed = time.time() - start_time
            self.app.root.after(0, lambda e=elapsed: self.tab._on_generation_complete(e))
            
        except Exception as e:
            error_msg = str(e)
            import traceback
            traceback.print_exc()
            if "用户取消" in error_msg or "cancelled" in error_msg.lower():
                self.app.root.after(0, lambda: self.tab.update_status("⏹️ 已取消"))
            else:
                self.app.root.after(0, lambda err=error_msg: self.tab._on_generation_error(err))
        finally:
            if 'model_path' in locals() and 'lora_path' in locals():
                pipeline_pool.release_pipeline(model_path, lora_path, task_id)
    
    def _adjust_image_size(self, image, original_w, original_h, has_prompt, target_width, target_height):
        """调整图片尺寸"""
        new_w, new_h = original_w, original_h
        
        if has_prompt and target_width > 0 and target_height > 0:
            new_w = target_width
            new_h = target_height
        else:
            if has_prompt:
                if max(original_w, original_h) > 1024:
                    scale = 1024 / max(original_w, original_h)
                    new_w = int(original_w * scale)
                    new_h = int(original_h * scale)
                else:
                    new_w = original_w
                    new_h = original_h
                
                min_size = 512
                if new_w < min_size:
                    scale = min_size / new_w
                    new_w = min_size
                    new_h = int(new_h * scale)
                if new_h < min_size:
                    scale = min_size / new_h
                    new_h = min_size
                    new_w = int(new_w * scale)
        
        current_pixels = new_w * new_h
        if current_pixels > MAX_PIXELS:
            scale = (MAX_PIXELS / current_pixels) ** 0.5
            new_w = int(new_w * scale)
            new_h = int(new_h * scale)
        
        new_w = ((new_w + 31) // 64) * 64
        new_h = ((new_h + 31) // 64) * 64
        
        from config.app_config import app_config
        size_cfg = app_config.generation.size
        max_cpu_w = size_cfg.get("cpu_safe_max_width", 1024)
        max_cpu_h = size_cfg.get("cpu_safe_max_height", 1024)
        new_w = min(max_cpu_w, new_w)
        new_h = min(max_cpu_h, new_h)
        
        if new_w != original_w or new_h != original_h:
            logger.info(f"   📐 图片尺寸调整: {original_w}x{original_h} -> {new_w}x{new_h}")
            return image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        return image