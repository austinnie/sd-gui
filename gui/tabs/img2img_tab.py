#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图生图标签页 - 集成完整的 SD 图生图逻辑
"""
from utils.watermark_remover import WatermarkRemover

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import colorchooser
import threading
import os
import time
import random
from PIL import Image,ImageTk, ImageDraw
import torch

from .base_tab import BaseTab
from gui.components.memory_monitor import force_memory_cleanup, get_memory_usage
from datetime import datetime
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

MAX_PIXELS = 1024 * 1024  # 限制总像素不超过 1024x1024

# ========== 辅助函数 ==========
def auto_shorten_prompt(prompt, max_len=350):
    """自动精简提示词"""
    if not prompt or len(prompt) <= max_len:
        return prompt
    
    parts = [p.strip() for p in prompt.split(',') if p.strip()]
    seen = set()
    unique_parts = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            unique_parts.append(p)
    unique_parts.sort(key=lambda x: len(x), reverse=True)
    result = []
    current_len = 0
    for part in unique_parts:
        add_len = len(part) + 2
        if current_len + add_len <= max_len:
            result.append(part)
            current_len += add_len
    if not result:
        return prompt[:max_len]
    shortened = ", ".join(result)
    if len(shortened) < len(prompt):
        print(f"✂️ 提示词已精简: {len(prompt)} -> {len(shortened)} 字符")
    return shortened


# ========== 进度回调类 ==========
class Img2ImgStepCallback:
    def __init__(self, progress_callback, total_steps, start_time, cancel_flag_ref,
                 img_idx, var_idx, total_imgs, total_vars):
        self.progress_callback = progress_callback
        self.total_steps = total_steps
        self.start_time = start_time
        self.last_percent = 0
        self.cancel_flag_ref = cancel_flag_ref
        self.img_idx = img_idx
        self.var_idx = var_idx
        self.total_imgs = total_imgs
        self.total_vars = total_vars
        
    def __call__(self, pipe, step, timestep, callback_kwargs):
        # ✅ 兼容两种方式
        if self.cancel_flag_ref:
            if callable(self.cancel_flag_ref):
                if self.cancel_flag_ref():
                    raise Exception("用户取消了生成")
            elif hasattr(self.cancel_flag_ref, 'get') and self.cancel_flag_ref.get():
                raise Exception("用户取消了生成")
        
        current_step = step + 1
        percent = current_step / self.total_steps
        if percent - self.last_percent >= 0.02 or current_step == self.total_steps:
            self.last_percent = percent
            elapsed = time.time() - self.start_time
            if current_step > 0:
                eta = (elapsed / current_step) * (self.total_steps - current_step)
                eta_str = f"预计剩余: {int(eta//60)}分{int(eta%60)}秒" if eta > 60 else f"预计剩余: {eta:.0f}秒"
            else:
                eta_str = "计算中..."
            completed_before = self.img_idx * self.total_vars + self.var_idx
            step_progress = (step + 1) / self.total_steps
            overall_progress = (completed_before + step_progress) / (self.total_imgs * self.total_vars)
            self.progress_callback(overall_progress, 
                f"🎨 图片 {self.img_idx+1}/{self.total_imgs}，变体 {self.var_idx+1}/{self.total_vars} - 步骤 {current_step}/{self.total_steps} | {eta_str}")
        return callback_kwargs


class Img2ImgTab(BaseTab):
    """图生图标签页"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.selected_images = []
        self._init_vars()
        self.setup_ui()
    
    def _init_vars(self):
        """初始化变量"""
        from config.app_config import app_config
        
        
        # ✅ 使用共享参数面板
        self.params = self.app.params_panel
    
        self.img_paths_var = tk.StringVar(value="")
        self.strength_var = tk.DoubleVar(value=0.20)
        self.per_image_var = tk.IntVar(value=1)  # 图生图特有：每张图片生成几个变体
        self.size_var = tk.StringVar(value="自动(保持比例)")
        
        self.default_prompt = ""  # ✅ 图生图默认不需要提示词
        self.default_negative = app_config.generation.negative_prompt or \
            "worst quality, low quality, ugly, deformed, blurry"
        
        # 生成状态
        self.cancel_generation = False
        self.is_generating = False
        
        self.use_inpaint_var = tk.BooleanVar(value=False)  # 是否使用局部重绘
        self.mask_image = None  # 存放用户涂抹的遮罩
    
    
    def setup_ui(self):
        frame = self.frame
        row = 0
        
        # 图片选择
        ttk.Label(frame, text="选择图片:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.path_label = ttk.Label(frame, textvariable=self.img_paths_var, 
                                    foreground="gray", background="white", relief="sunken")
        self.path_label.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        img_btn_frame = ttk.Frame(frame)
        img_btn_frame.grid(row=row, column=2, sticky=tk.W)
        ttk.Button(img_btn_frame, text="选择图片", command=self._select_images).pack(side=tk.LEFT, padx=2)
        ttk.Button(img_btn_frame, text="清空", command=self._clear_images).pack(side=tk.LEFT, padx=2)
        row += 1
        
        # 提示词
        ttk.Label(frame, text="目标提示词:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.prompt_text = tk.Text(frame, height=4, width=70)
        self.prompt_text.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.prompt_text.insert("1.0", self.default_prompt)
        row += 1
        
        ttk.Label(frame, text="负面提示词:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.neg_text = tk.Text(frame, height=3, width=70)
        self.neg_text.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.neg_text.insert("1.0", self.default_negative)
        row += 1

        # ===== 参数提示 =====
        hint_frame = ttk.Frame(frame)
        hint_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2, padx=5)
        ttk.Label(
            hint_frame,
            text="💡 参数（步数、CFG、种子、尺寸等）请在顶部的「共享参数面板」调整",
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # ===== 图生图特有参数 =====
        param_frame = ttk.Frame(frame)
        param_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)

        # 在 param_frame 中添加
        inpaint_row = ttk.Frame(param_frame)
        inpaint_row.pack(fill=tk.X, pady=2)

        ttk.Checkbutton(
            inpaint_row,
            text="🩲 启用局部重绘（去除衣物区域）",
            variable=self.use_inpaint_var
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            inpaint_row,
            text="🖱️ 涂抹遮罩",
            command=self._open_mask_editor
        ).pack(side=tk.LEFT, padx=5)

        # 重绘强度
        param_row1 = ttk.Frame(param_frame)
        param_row1.pack(fill=tk.X, pady=2)

        ttk.Label(param_row1, text="重绘强度:").pack(side=tk.LEFT, padx=5)
        scale = ttk.Scale(param_row1, from_=0.2, to=0.5, variable=self.strength_var, 
                          orient=tk.HORIZONTAL, length=120)
        scale.pack(side=tk.LEFT, padx=5)
        self.strength_label = ttk.Label(param_row1, text="0.20", width=5)
        self.strength_label.pack(side=tk.LEFT, padx=5)
        self.strength_var.trace('w', lambda *_: self.strength_label.config(
            text=f"{self.strength_var.get():.2f}"))

        # 每张生成变体数
        param_row2 = ttk.Frame(param_frame)
        param_row2.pack(fill=tk.X, pady=2)

        ttk.Label(param_row2, text="每张生成:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(param_row2, from_=1, to=4, textvariable=self.per_image_var, width=4).pack(side=tk.LEFT, padx=5)
        # ✅ 添加数值显示标签
        per_image_label = ttk.Label(param_row2, textvariable=self.per_image_var, width=3)
        per_image_label.pack(side=tk.LEFT, padx=5)

        row += 1
       
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)
        self.generate_btn = ttk.Button(btn_frame, text="🎨 图生图", command=self.start_generate)
        self.generate_btn.pack(side=tk.LEFT, padx=10)
        self.cancel_btn = ttk.Button(btn_frame, text="⏹️ 取消", command=self.cancel_generation, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="📁 打开输出文件夹", command=self.app.open_output_folder).pack(side=tk.LEFT, padx=10)
    
    def _select_images(self):
        """选择图片"""
        files = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif"), ("所有文件", "*.*")]
        )
        if files:
            self.selected_images = list(files)
            self.img_paths_var.set(f"已选择 {len(files)} 张图片")
    
    def _clear_images(self):
        """清空图片"""
        self.selected_images = []
        self.img_paths_var.set("")
    
    def _on_size_change(self, event):
        """尺寸改变"""
        val = self.size_var.get()
        if val != "自动(保持比例)":
            try:
                w, h = map(int, val.split('x'))
                # ✅ 对齐到 64 的倍数
                w = ((w + 31) // 64) * 64
                h = ((h + 31) // 64) * 64
                # ✅ 使用共享参数面板
                self.params.width_var.set(w)
                self.params.height_var.set(h)
            except:
                pass
        else:
            self.params.width_var.set(0)
            self.params.height_var.set(0)
        
    # ==================== 核心生成方法 ====================
    
    def start_generate(self):
        """开始生成"""
        if not self.selected_images:
            messagebox.showwarning("提示", "请先选择图片")
            return
        
        if self.app.pipeline is None:
            messagebox.showwarning("提示", "请先加载模型")
            return
        
        self.cancel_generation = False
        self.is_generating = True
        
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        negative = self.neg_text.get("1.0", tk.END).strip()

        # === [优化] 如果 Prompt 为空，使用默认中性提示词 ===
        if not prompt:
            prompt = "a high-quality photograph, detailed, sharp focus, natural lighting"
            self.update_status("ℹ️ 未检测到提示词，已使用默认中性提示词。")
        # === [优化] 结束 ===
    
        # 获取参数
        # ✅ 从共享参数面板获取参数
        params = self.params.get_params()
        steps = params["steps"]
        cfg = params["cfg"]
        seed = params["seed"]
        target_width = params["width"]
        target_height = params["height"]
        
        strength = self.strength_var.get()
        num_images_per = self.per_image_var.get()
        
        self.update_status("🎨 开始图生图...")
        self.generate_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        
        # 在后台线程中生成
        threading.Thread(
            target=self._generate_images,
            args=(prompt, negative, strength, steps, cfg, seed, num_images_per, target_width, target_height),
            daemon=True
        ).start()
    
        
    def _adjust_image_size(self, image, original_w, original_h, has_prompt, target_width, target_height):
        """
        统一处理图片尺寸调整
        
        参数:
            image: PIL Image 对象
            original_w: 原始宽度
            original_h: 原始高度
            has_prompt: 是否有提示词
            target_width: 用户指定宽度 (0 表示自动)
            target_height: 用户指定高度 (0 表示自动)
        
        返回:
            调整后的 PIL Image 对象
        """
        new_w, new_h = original_w, original_h
        
        # 1. 如果用户指定了尺寸，优先使用
        if has_prompt and target_width > 0 and target_height > 0:
            new_w = target_width
            new_h = target_height
        else:
            # 2. 如果有提示词，自动调整到 512x768 附近
            # 2. 如果有提示词，让图片保持在安全尺寸内，尽量不动原图尺寸
            if has_prompt:
                # 如果原图太大（超过 1024），稍微缩小；如果原来就小于 1024，绝对不放大也不缩小
                if max(original_w, original_h) > 1024:
                    scale = 1024 / max(original_w, original_h)
                    new_w = int(original_w * scale)
                    new_h = int(original_h * scale)
                else:
                    # 小于 1024 的图，保持原样，绝不动它！
                    new_w = original_w
                    new_h = original_h
                
                # ⚠️ 【下面这 6 行是之前 512x768 的旧代码，现在没用了，需要删掉】
                #current_pixels = original_w * original_h
                #
                #if current_pixels > target_pixels:
                #    scale = (target_pixels / current_pixels) ** 0.5
                #else:
                #    scale = min(1.5, (target_pixels / current_pixels) ** 0.5)
                #
                #new_w = int(original_w * scale)
                #new_h = int(original_h * scale)
                
                # 确保最小尺寸为 512
                min_size = 512
                if new_w < min_size:
                    scale = min_size / new_w
                    new_w = min_size
                    new_h = int(new_h * scale)
                if new_h < min_size:
                    scale = min_size / new_h
                    new_h = min_size
                    new_w = int(new_w * scale)
            else:
                # 无 prompt：保持原图尺寸
                new_w = original_w
                new_h = original_h
        
        # 3. 强制像素数限制 (在应用用户尺寸后执行)
        current_pixels = new_w * new_h
        if current_pixels > MAX_PIXELS:
            scale = (MAX_PIXELS / current_pixels) ** 0.5
            new_w = int(new_w * scale)
            new_h = int(new_h * scale)
        
        # 4. 统一对齐到 64 的倍数
        new_w = ((new_w + 31) // 64) * 64
        new_h = ((new_h + 31) // 64) * 64
        
        # 5. 确保不超过 CPU 安全范围
        from config.app_config import app_config
        size_cfg = app_config.generation.size
        max_cpu_w = size_cfg.get("cpu_safe_max_width", 1024)
        max_cpu_h = size_cfg.get("cpu_safe_max_height", 1024)
        new_w = min(max_cpu_w, new_w)
        new_h = min(max_cpu_h, new_h)
        
        # 6. 如果尺寸发生了变化，调整图片
        if new_w != original_w or new_h != original_h:
            print(f"   📐 图片尺寸调整: {original_w}x{original_h} -> {new_w}x{new_h}")
            return image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        return image
    
    def _generate_images(self, prompt, negative, strength, steps, cfg, seed, 
                         num_images_per, target_width, target_height):
        """在后台线程中生成图生图"""
        
        log("开始图生图...")
        
        # ===== 【核心修改】图生图强制使用原图尺寸逻辑 =====
        # 不管共享面板传什么尺寸过来，图生图强制设为 0
        
        target_width = 0
        target_height = 0
        
        # ===== 强制对齐用户指定尺寸到 64 的倍数 =====
        if target_width > 0:
            target_width = ((target_width + 31) // 64) * 64
        if target_height > 0:
            target_height = ((target_height + 31) // 64) * 64
        
        try:
            # 加载所有图片
            images = []
            for path in self.selected_images:
                try:
                    log(f"加载图片: {os.path.basename(path)}")
                    
                    img = Image.open(path).convert('RGB')
                    
                    # ✅ 强制对齐原图尺寸到 64 的倍数（VAE 要求）
                    w, h = img.size
                    new_w = ((w + 31) // 64) * 64
                    new_h = ((h + 31) // 64) * 64
                    if new_w != w or new_h != h:
                        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        print(f"   📐 原图尺寸对齐: {w}x{h} -> {new_w}x{new_h}")
                    
                    images.append(img)
                    print(f"   已加载: {os.path.basename(path)}")
                except Exception as load_err:
                    print(f"❌ 无法加载图片 {path}: {load_err}")
                    continue  # 跳过这张图片，继续处理下一张
            
            total_images = len(images) * num_images_per
            self.update_status(f"开始处理 {len(images)} 张图片，每张生成 {num_images_per} 张变体")
            
            if seed == -1:
                seed = random.randint(1, 2**32 - 1)
            
            saved_paths = []
            start_time = time.time()
            

            pipe = self.app.pipeline

            # ===== [新增] 如果启用了局部重绘，切换为 Inpaint 管道 =====
            use_inpaint = self.use_inpaint_var.get()
            mask_image = self.mask_image
            
            if use_inpaint and mask_image is not None:
                try:
                    from diffusers import StableDiffusionInpaintPipeline
                    # 尝试复用当前模型，加载为 Inpaint 管道
                    # 注意：如果内存足够，建议预先加载并缓存
                    if not hasattr(self, '_inpaint_pipe'):
                        print("📦 首次加载 Inpaint 模型（额外内存占用）...")
                        model_path = self.app.model_manager._sd_model_name
                        if model_path is None:
                            # 如果无法获取模型路径，尝试用当前管道的配置
                            self._inpaint_pipe = StableDiffusionInpaintPipeline(
                                vae=pipe.vae,
                                text_encoder=pipe.text_encoder,
                                tokenizer=pipe.tokenizer,
                                unet=pipe.unet,
                                scheduler=pipe.scheduler,
                                safety_checker=None,
                                feature_extractor=None,
                                requires_safety_checker=False
                            )
                        else:
                            self._inpaint_pipe = StableDiffusionInpaintPipeline.from_single_file(
                                model_path,
                                torch_dtype=torch.float32,
                                safety_checker=None,
                                requires_safety_checker=False,
                                low_cpu_mem_usage=False  # 关闭元张量模式
                            )
                        self._inpaint_pipe.to("cpu")
                        self._inpaint_pipe.enable_attention_slicing()
                        self._inpaint_pipe.vae.enable_slicing()
                        self._inpaint_pipe.vae.enable_tiling()
                        print("✅ Inpaint 模型加载完成")
                    
                    # 切换到 Inpaint 管道
                    pipe = self._inpaint_pipe
                    # 将遮罩转换为灰度图
                    mask_tensor = mask_image.convert("L")
                    print(f"🖌️ 启用局部重绘，遮罩已加载")
                    
                except Exception as e:
                    print(f"⚠️ 启用局部重绘失败，回退到普通图生图: {e}")
                    use_inpaint = False
                    pipe = self.app.pipeline
            # ===== [新增] 结束 =====
            
            
            # ===== 自动精简提示词 =====
            if prompt:
                prompt = auto_shorten_prompt(prompt, max_len=280)
            if negative:
                negative = auto_shorten_prompt(negative, max_len=280)
                
            # ===== 参数限制 =====
            from config.app_config import app_config
            gen_cfg = app_config.generation
            size_cfg = gen_cfg.size
            
            steps = max(gen_cfg.steps["min"], min(gen_cfg.steps["max"], steps))
            cfg = max(gen_cfg.cfg["min"], min(gen_cfg.cfg["max"], cfg))
            strength = max(0.2, min(0.5, strength))
            num_images_per = max(1, min(num_images_per, 4))
            
            # ===== 图生图尺寸强制安全范围 =====
            max_cpu_w = size_cfg.get("cpu_safe_max_width", 1024)
            max_cpu_h = size_cfg.get("cpu_safe_max_height", 1024)
            if target_width > 0:
                target_width = min(max_cpu_w, max(size_cfg["min_width"], target_width))
            if target_height > 0:
                target_height = min(max_cpu_h, max(size_cfg["min_height"], target_height))
            
            for img_idx, init_image in enumerate(images):
                self.update_progress(img_idx / total_images, f"🔄 正在处理图片 {img_idx+1}/{len(images)}...")
                if self.cancel_generation:
                    break
                
                # ===== 尺寸调整 =====
                original_w, original_h = init_image.size
                has_prompt = prompt and prompt.strip()
                
                # 使用封装好的尺寸调整函数
                init_image = self._adjust_image_size(
                    image=init_image,
                    original_w=original_w,
                    original_h=original_h,
                    has_prompt=has_prompt,
                    target_width=target_width,
                    target_height=target_height
                )

                log(f"原图尺寸: {original_w}x{original_h}")
                aspect_ratio = original_w / original_h
                    
                # ✅ 头像检测：降低强度
                # ✅ 头像检测：使用 OpenCV 判断人脸占比
                import cv2
                import numpy as np

                # 将 PIL Image 转为 OpenCV 格式
                img_cv = np.array(init_image.convert('RGB'))[:, :, ::-1].copy()
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

                # 如果检测到人脸，计算面积占比
                if len(faces) > 0:
                    # 取最大的人脸
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    face_area = w * h
                    image_area = original_w * original_h
                    face_ratio = face_area / image_area

                    # 如果人脸面积占整图超过 15%，判定为头像/特写
                    if face_ratio > 0.15:
                        strength = min(strength, 0.3)
                        print(f"   🧑 检测到头像 (人脸占比 {face_ratio:.1%})，强度自动调整为: {strength:.2f}")
                    else:
                        print(f"   👤 检测到人脸，但占比 {face_ratio:.1%}，不限制强度")
                else:
                    print("   ❕ 未检测到人脸，保持原强度")

                # ===== 生成变体 =====
                for i in range(num_images_per):
                    if self.cancel_generation:
                        break
                    
                    log(f"生成变体 {i+1}/{num_images_per}")
                    current_seed = seed + img_idx * num_images_per + i
                    generator = torch.Generator("cpu").manual_seed(current_seed)

                    # ✅ 修复 1：每生成一张图之前，都重置 strength 为初始用户设定的值
                    # 防止由于上一条图片修改了 strength 导致后续图片“叠在一起”
                    current_strength = strength
                    
                    overall_progress = (img_idx * num_images_per + i) / total_images
                    img_num = img_idx + 1
                    total_imgs = len(images)
                    var_num = i + 1
                    self.app.root.after(0, lambda v=overall_progress, img=img_num, total=total_imgs, var=var_num, per=num_images_per:
                        self.update_progress(v, f"🎨 图片 {img}/{total} 变体 {var}/{per}"))
                    
                    # 创建取消标志引用
                    cancel_flag = lambda: self.cancel_generation
                    
                    # 创建进度回调
                    step_callback = Img2ImgStepCallback(
                        self._progress_callback, steps, start_time, cancel_flag,
                        img_idx, i, len(images), num_images_per
                    )
                    
                    log("调用 pipeline...")
                    with torch.no_grad():
                        if use_inpaint and mask_tensor is not None:
                            # ===== 局部重绘模式 =====
                            result = pipe(
                                prompt=prompt,
                                negative_prompt=negative,
                                image=init_image,
                                mask_image=mask_tensor,
                                strength=current_strength,  # ✅ 使用重置后的强度变量
                                num_inference_steps=steps,
                                guidance_scale=cfg,
                                generator=generator,
                                callback_on_step_end=step_callback
                            )
                        else:
                            # ===== 普通图生图模式 =====
                            result = pipe(
                                prompt=prompt,
                                negative_prompt=negative,
                                image=init_image,
                                strength=current_strength,  # ✅ 使用重置后的强度变量
                                num_inference_steps=steps,
                                guidance_scale=cfg,
                                generator=generator,
                                callback_on_step_end=step_callback
                            )
                    
                    log("pipeline 调用完成")
                    
                    image = result.images[0]
                    
                    # ===== 保存图片 =====
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    prompt_preview = "".join(c for c in prompt[:30] if c.isalnum() or c in " _-") or "image"
                    if len(prompt_preview) > 50:
                        prompt_preview = prompt_preview[:50]
                    filename = f"{timestamp}_img2img_img{img_idx+1}_var{i+1}_{prompt_preview}.png"
                    
                    from config.app_config import app_config
                    output_dir = app_config.paths.output_dir
                    os.makedirs(output_dir, exist_ok=True)
                    filepath = os.path.join(output_dir, filename)
                    image.save(filepath)
                    
                    self.update_progress((img_idx + 1) / total_images, f"✅ 图片 {img_idx+1}/{len(images)} 已生成并保存。")
                    
                    # ===== 添加到预览 =====
                    self.app.root.after(0, lambda fp=filepath, img=image: self.app.add_to_preview(fp, img))
                    
                    # ===== 清理内存 =====
                    safe_del(result)
                    safe_del(generator)
                    import gc
                    gc.collect()
                    
                    mem_gb = get_memory_usage()
                    if mem_gb > 8.0:
                        force_memory_cleanup()
                    
                    if i < num_images_per - 1:
                        time.sleep(0.5)
                
                force_memory_cleanup()
            
            elapsed = time.time() - start_time
            self.app.root.after(0, lambda e=elapsed: self._on_generation_complete(e))
            
        except Exception as e:
            error_msg = str(e)
            import traceback
            traceback.print_exc()
            if "用户取消" in error_msg or "cancelled" in error_msg.lower():
                self.app.root.after(0, lambda: self.update_status("⏹️ 已取消"))
            else:
                self.app.root.after(0, lambda err=error_msg: self._on_generation_error(err))


    def _save_mask(self, mask_layer, window):
        """保存遮罩并关闭窗口"""
        # 将 RGBA 遮罩层转换为灰度遮罩（白色区域为重绘区）
        # 这里我们需要保留红色涂抹区域的掩膜
        alpha = mask_layer.split()[3]  # 获取 Alpha 通道
        # 将 Alpha 通道二值化，大于 0 的区域即为涂抹区域
        mask = alpha.point(lambda p: 255 if p > 0 else 0)
        
        # 保存到 self.mask_image
        self.mask_image = mask
        
        # 关闭窗口
        window.destroy()
        
        # 更新状态提示
        self.update_status("✅ 遮罩已保存，可以开始图生图了")
        
    # ==================== 辅助方法 ====================        
    def _progress_callback(self, value, msg):
        """进度回调"""
        self.app.root.after(0, lambda: self.update_progress(value, msg))
    
    def _on_generation_complete(self, elapsed):
        """生成完成"""
        self.is_generating = False
        self.generate_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.update_progress(1.0, "✅ 图生图完成！")
        self.update_status(f"✅ 图生图完成，耗时 {elapsed:.1f}秒")
        force_memory_cleanup()
    
    def _on_generation_error(self, error):
        """生成出错"""
        self.is_generating = False
        self.generate_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.update_status(f"❌ 生成出错: {error}")
        messagebox.showerror("错误", f"图生图失败:\n{error}")
    
    def cancel_generation(self):
        self.cancel_generation = True
        self.is_generating = False
        self.update_status("⏹️ 正在取消...")
        self.cancel_btn.config(state=tk.DISABLED)
        
        # 如果 pipeline 支持中断，直接停止
        if hasattr(self.app.pipeline, 'cancel'):
            self.app.pipeline.cancel()



    # 去除遮障
    def _open_mask_editor(self):
        """打开一个简单的遮罩涂抹窗口"""
        if not self.selected_images:
            messagebox.showwarning("提示", "请先选择图片")
            return
        
        # 创建新窗口
        mask_window = tk.Toplevel(self.app.root)
        mask_window.title("手动涂抹遮罩 - 红色区域将被重绘")
        mask_window.geometry("800x800")
        
        # 加载当前图片
        img_path = self.selected_images[0]
        pil_img = Image.open(img_path).convert("RGB")
        # 缩放以适配界面（保持比例）
        max_size = 700
        pil_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # 转换为 PhotoImage 用于显示
        self._display_img = ImageTk.PhotoImage(pil_img)
        
        # 创建遮罩图层（全透明）
        mask_layer = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(mask_layer)
        
        # 画布
        canvas = tk.Canvas(mask_window, width=pil_img.width, height=pil_img.height)
        canvas.pack(pady=10)
        
        # 显示图片
        canvas.create_image(0, 0, anchor="nw", image=self._display_img)
        # 创建遮罩层（用红色半透明覆盖）
        self._mask_id = canvas.create_image(0, 0, anchor="nw", image=None)
        
        # 涂抹状态
        drawing = False
        last_x, last_y = None, None
        brush_size = 15
        
        # 鼠标事件
        def on_mouse_down(event):
            nonlocal drawing, last_x, last_y
            drawing = True
            last_x, last_y = event.x, event.y
        
        def on_mouse_move(event):
            nonlocal drawing, last_x, last_y
            if drawing and last_x is not None:
                draw.ellipse(
                    [last_x - brush_size, last_y - brush_size,
                     last_x + brush_size, last_y + brush_size],
                    fill=(255, 0, 0, 180)
                )
                # 更新画布显示
                mask_tk = ImageTk.PhotoImage(mask_layer)
                canvas.itemconfig(self._mask_id, image=mask_tk)
                canvas.image = mask_tk  # 防止被垃圾回收
                last_x, last_y = event.x, event.y
        
        def on_mouse_up(event):
            nonlocal drawing, last_x, last_y
            drawing = False
            last_x, last_y = None, None
        
        canvas.bind("<Button-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_move)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)
        
        # 底部按钮
        btn_frame = ttk.Frame(mask_window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="✅ 保存遮罩并关闭", 
                   command=lambda: self._save_mask(mask_layer, mask_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ 取消", command=mask_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # 说明标签
        ttk.Label(mask_window, text="💡 在图片上涂抹红色区域，这些区域将被重新生成（用于去除衣物等）").pack(pady=5)
    
    # ==================== 外部调用接口 ====================

    
    def set_prompt(self, prompt: str, negative: str):
        """设置提示词"""
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", prompt)
        if negative:
            self.neg_text.delete("1.0", tk.END)
            self.neg_text.insert("1.0", negative)

    def set_params(self, steps: int = None, cfg: float = None, seed: int = None,
                   width: int = None, height: int = None, num_images: int = None):
        """设置生成参数"""
        params = self.app.params_panel
        if steps is not None:
            params.steps_var.set(steps)
        if cfg is not None:
            params.cfg_var.set(cfg)
        if seed is not None:
            params.seed_var.set(seed)
        if width is not None:
            params.width_var.set(width)
        if height is not None:
            params.height_var.set(height)
        if num_images is not None:
            params.num_images_var.set(num_images)

    def batch_generate(self, prompts):
        """批量生成（图生图）"""
        if not self.selected_images:
            messagebox.showwarning("提示", "请先选择图片")
            return
        
        if self.is_generating:
            messagebox.showwarning("提示", "正在生成中，请等待完成")
            return
        
        # 图生图批量：每行提示词对应一张图片
        # 如果提示词数量少于图片数量，剩余的用空白提示词
        # 如果提示词数量多于图片数量，循环使用
        
        prompts_list = [p.strip() for p in prompts if p.strip()]
        if not prompts_list:
            messagebox.showwarning("提示", "请输入提示词")
            return
        
        self._run_batch_generation(prompts_list)


    def _run_batch_generation(self, prompts_list):
        """运行批量生成（图生图）"""
        if not self.selected_images:
            self.update_status("❌ 没有选择图片")
            return
        
        original_images = self.selected_images.copy()
        
        try:
            for idx, prompt in enumerate(prompts_list):
                if self.cancel_generation:
                    break
                
                img_idx = idx % len(original_images)
                img_path = original_images[img_idx]
                self.selected_images = [img_path]
                
                self.update_status(f"🔄 正在生成第 {idx+1}/{len(prompts_list)} 张...")
                self.set_prompt(prompt, self.default_negative)
                self.start_generate()
                
                wait_count = 0
                while self.is_generating and wait_count < 600:
                    time.sleep(0.5)
                    wait_count += 1
                
                time.sleep(0.5)
        finally:
            # ✅ 确保恢复状态
            self.selected_images = original_images
            self.is_generating = False
            self.update_status("✅ 批量生成完成")
            
# ========== 辅助函数 ==========
def safe_del(obj):
    try:
        if obj is not None:
            del obj
    except:
        pass