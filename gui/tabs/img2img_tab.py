#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图生图标签页 - 集成完整的 SD 图生图逻辑
"""
from utils.watermark_remover import WatermarkRemover
from utils.image_post_processor import post_process_image
from utils.scheduler_fix import fix_euler_scheduler_for_img2img

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


# ✅ 简化导入
from utils import process_with_controlnet

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
                 img_idx, var_idx, total_imgs, total_vars, source=""):  # ✅ 添加 source
        self.progress_callback = progress_callback
        self.total_steps = total_steps
        self.start_time = start_time
        self.last_percent = 0
        self.cancel_flag_ref = cancel_flag_ref
        self.img_idx = img_idx
        self.var_idx = var_idx
        self.total_imgs = total_imgs
        self.total_vars = total_vars
        self.source = source  # ✅ 新增
        
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
        self.strength_var = tk.DoubleVar(value=0.15)
        self.per_image_var = tk.IntVar(value=1)  # 图生图特有：每张图片生成几个变体
        self.size_var = tk.StringVar(value="自动(保持比例)")
        
        self.default_prompt = ""  # ✅ 图生图默认不需要提示词
        self.default_negative = app_config.generation.negative_prompt or \
            "worst quality, low quality, ugly, deformed, blurry"
        
        # 生成状态
        self.cancel_generation = False
        self.is_generating = False
        
        self.use_inpaint_var = tk.BooleanVar(value=False)  # 是否使用局部重绘
        self.use_controlnet_var = tk.BooleanVar(value=False) 
        self.mask_image = None  # 存放用户涂抹的遮罩
        
        # ✅ 新增：图片选择模式
        self.image_mode_var = tk.StringVar(value="single")  # single, multiple, directory
        self.selected_images = []
        self.batch_prompts = []    
    
    def setup_ui(self):
        frame = self.frame
        row = 0
        
        # ===== 图片选择模式 =====
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(mode_frame, text="选择模式:").pack(side=tk.LEFT, padx=5)
        
        self.mode_single_btn = ttk.Radiobutton(
            mode_frame, text="📷 单张", variable=self.image_mode_var, 
            value="single", command=self._on_mode_changed
        )
        self.mode_single_btn.pack(side=tk.LEFT, padx=5)
        
        self.mode_multiple_btn = ttk.Radiobutton(
            mode_frame, text="📚 多张", variable=self.image_mode_var, 
            value="multiple", command=self._on_mode_changed
        )
        self.mode_multiple_btn.pack(side=tk.LEFT, padx=5)
        
        self.mode_directory_btn = ttk.Radiobutton(
            mode_frame, text="📁 目录", variable=self.image_mode_var, 
            value="directory", command=self._on_mode_changed
        )
        self.mode_directory_btn.pack(side=tk.LEFT, padx=5)
        
        # 图片数量显示
        self.image_count_label = ttk.Label(mode_frame, text="", foreground="blue")
        self.image_count_label.pack(side=tk.RIGHT, padx=10)
        
        row += 1
        
        # ===== 图片选择区域 =====
        self.image_select_frame = ttk.Frame(frame)
        self.image_select_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # 单张模式 - 路径显示
        self.single_path_frame = ttk.Frame(self.image_select_frame)
        ttk.Label(self.single_path_frame, text="图片:").pack(side=tk.LEFT, padx=5)
        self.path_label = ttk.Label(
            self.single_path_frame,
            textvariable=self.img_paths_var,
            foreground="gray",
            background="white",
            relief="sunken"
        )
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(self.single_path_frame, text="选择图片", command=self._select_single_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.single_path_frame, text="清空", command=self._clear_images).pack(side=tk.LEFT, padx=2)
        self.single_path_frame.pack(fill=tk.X)
        
        # 多张模式 - 显示已选文件数
        self.multiple_path_frame = ttk.Frame(self.image_select_frame)
        self.multiple_path_frame.pack(fill=tk.X)
        self.multiple_path_frame.pack_forget()  # 默认隐藏
        
        ttk.Label(self.multiple_path_frame, text="已选:").pack(side=tk.LEFT, padx=5)
        self.multiple_count_label = ttk.Label(
            self.multiple_path_frame,
            text="未选择",
            foreground="gray",
            background="white",
            relief="sunken"
        )
        self.multiple_count_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(self.multiple_path_frame, text="选择多张", command=self._select_multiple_images).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.multiple_path_frame, text="清空", command=self._clear_images).pack(side=tk.LEFT, padx=2)
        
        # 目录模式 - 显示目录路径
        self.directory_path_frame = ttk.Frame(self.image_select_frame)
        self.directory_path_frame.pack(fill=tk.X)
        self.directory_path_frame.pack_forget()  # 默认隐藏
        
        ttk.Label(self.directory_path_frame, text="目录:").pack(side=tk.LEFT, padx=5)
        self.directory_path_label = ttk.Label(
            self.directory_path_frame,
            textvariable=self.img_paths_var,
            foreground="gray",
            background="white",
            relief="sunken"
        )
        self.directory_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(self.directory_path_frame, text="选择目录", command=self._select_directory).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.directory_path_frame, text="清空", command=self._clear_images).pack(side=tk.LEFT, padx=2)
        
        row += 1

        # ===== 【新增】图片预览行 =====
        preview_frame = ttk.Frame(frame)
        preview_frame.grid(row=row, column=0, columnspan=3, pady=5, padx=5)
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack()
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

        # --- 新增: ControlNet 控件 ---
        controlnet_row = ttk.Frame(param_frame)
        controlnet_row.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(
            controlnet_row,
            text="🧠 启用 ControlNet (姿态控制)",
            variable=self.use_controlnet_var,
            command=self._on_controlnet_toggle  # ← 添加这行
        ).pack(side=tk.LEFT, padx=5)
        
        # ✅ ControlNet 类型下拉选择
        ttk.Label(controlnet_row, text="类型:").pack(side=tk.LEFT, padx=5)

        from utils.controlnet_helper import get_controlnet_display_names
        self.controlnet_type_var = tk.StringVar(value="openpose (OpenPose (姿态))")
        self.controlnet_combo = ttk.Combobox(
            controlnet_row,
            textvariable=self.controlnet_type_var,
            values=get_controlnet_display_names(),
            width=25,
            state="readonly"
        )
        self.controlnet_combo.pack(side=tk.LEFT, padx=5)

        # 提示标签
        self.controlnet_hint = ttk.Label(
            controlnet_row,
            text="💡 锁定人体姿态",
            foreground="gray",
            font=("", 8)
        )
        self.controlnet_hint.pack(side=tk.LEFT, padx=5)

        # 绑定选择事件
        self.controlnet_combo.bind('<<ComboboxSelected>>', self._on_controlnet_type_changed)
        # --- 新增结束 ---
        
        # 重绘强度
        param_row1 = ttk.Frame(param_frame)
        param_row1.pack(fill=tk.X, pady=2)

        ttk.Label(param_row1, text="重绘强度:").pack(side=tk.LEFT, padx=5)
        scale = ttk.Scale(param_row1, from_=0.2, to=0.9, variable=self.strength_var, 
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
        
        # 在 btn_frame 中添加
        ttk.Button(
            btn_frame,
            text="🎯 强度测试",
            command=self._run_strength_test
        ).pack(side=tk.LEFT, padx=5)       

    # gui/tabs/img2img_tab.py

    def _on_controlnet_type_changed(self, event):
        """ControlNet 类型切换时更新提示"""
        from utils.controlnet_helper import get_controlnet_info
        
        selected = self.controlnet_type_var.get()
        # 从显示名称中提取 key
        key = selected.split(" ")[0] if " " in selected else selected
        info = get_controlnet_info(key)
        
        self.controlnet_hint.config(text=f"💡 {info['description']}")
        
    def _on_mode_changed(self):
        """切换图片选择模式"""
        mode = self.image_mode_var.get()
        
        # 隐藏所有模式面板
        self.single_path_frame.pack_forget()
        self.multiple_path_frame.pack_forget()
        self.directory_path_frame.pack_forget()
        
        if mode == "single":
            self.single_path_frame.pack(fill=tk.X)
            self.image_select_frame.config(text="📷 单张图片")
        elif mode == "multiple":
            self.multiple_path_frame.pack(fill=tk.X)
            self.image_select_frame.config(text="📚 多张图片")
        elif mode == "directory":
            self.directory_path_frame.pack(fill=tk.X)
            self.image_select_frame.config(text="📁 图片目录")
        
        self._update_image_count()

    def _select_single_image(self):
        """选择单张图片"""
        file = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("所有文件", "*.*")]
        )
        if file:
            self.selected_images = [file]
            self.img_paths_var.set(os.path.basename(file))
            self._update_image_count()
            self._show_preview(file)

    def _select_multiple_images(self):
        """选择多张图片"""
        files = filedialog.askopenfilenames(
            title="选择多张图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("所有文件", "*.*")]
        )
        if files:
            self.selected_images = list(files)
            self.multiple_count_label.config(text=f"已选择 {len(files)} 张图片")
            self._update_image_count()
            # 显示第一张预览
            if files:
                self._show_preview(files[0])

    def _select_directory(self):
        """选择包含图片的目录"""
        dir_path = filedialog.askdirectory(title="选择图片目录")
        if dir_path:
            # 扫描目录下所有图片
            extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
            images = []
            for f in os.listdir(dir_path):
                if Path(f).suffix.lower() in extensions:
                    images.append(os.path.join(dir_path, f))
            if images:
                self.selected_images = sorted(images)
                self.img_paths_var.set(f"{dir_path} ({len(images)} 张图片)")
                self._update_image_count()
                self._show_preview(images[0])
            else:
                messagebox.showwarning("提示", "目录中没有找到图片文件")
                self.selected_images = []
                self.img_paths_var.set("")

    def _update_image_count(self):
        """更新图片数量显示"""
        count = len(self.selected_images)
        if count == 0:
            self.image_count_label.config(text="")
        else:
            self.image_count_label.config(text=f"🖼️ {count} 张图片")

    def _clear_images(self):
        """清空图片"""
        self.selected_images = []
        self.img_paths_var.set("")
        self.multiple_count_label.config(text="未选择")
        self._update_image_count()
        self.preview_label.config(image='')
        self.preview_label.image = None

    def _show_preview(self, filepath):
        """显示图片预览"""
        try:
            from PIL import Image, ImageTk
            img = Image.open(filepath)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
        except Exception as e:
            print(f"⚠️ 预览失败: {e}")
            
    
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
        """开始生成（支持单张/多张/目录）"""
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

        # 如果 Prompt 为空，使用默认中性提示词
        if not prompt:
            prompt = "a high-quality photograph, detailed, sharp focus, natural lighting"
            self.update_status("ℹ️ 未检测到提示词，已使用默认中性提示词。")
        
        # 获取参数
        params = self.params.get_params()
        steps = params["steps"]
        cfg = params["cfg"]
        seed = params["seed"]
        target_width = params["width"]
        target_height = params["height"]
        
        strength = self.strength_var.get()
        num_images_per = self.per_image_var.get()
        
        # 计算总任务数
        total_tasks = len(self.selected_images) * num_images_per

        # 获取 ControlNet 开关状态
        use_controlnet = self.use_controlnet_var.get()  # ✅ 新增
        
        self.update_status(f"🎨 开始图生图... (共 {total_tasks} 张)")
        self.generate_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        
        # 在后台线程中生成
        threading.Thread(
            target=self._generate_images,
            args=(prompt, negative, strength, steps, cfg, seed, num_images_per, target_width, target_height),
            kwargs={'use_controlnet': use_controlnet},  # <-- 修改: 传递 ControlNet 状态
            daemon=True
        ).start()
    
    def _progress_callback(self, value, msg):
        """进度回调 - 供 ControlNet 使用"""
        self.app.root.after(0, lambda: self.update_progress(value, msg))
        
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
                         num_images_per, target_width, target_height,use_controlnet=False):
        """在后台线程中生成图生图"""
        
        log("开始图生图...")
        
        # ✅ 生成 task_id
        task_id = f"img2img_{datetime.now().strftime('%H%M%S')}"
        
        from utils.pipeline_pool import pipeline_pool
        from utils.scheduler_fix import fix_euler_scheduler_for_img2img
    
        # ===== 图生图尺寸逻辑 =====
        # 使用用户设定的尺寸（如果用户指定了）
        user_width = self.params.width_var.get()
        user_height = self.params.height_var.get()
        
        if user_width > 0 and user_height > 0:
            # 用户指定了尺寸，使用用户尺寸
            target_width = ((user_width + 31) // 64) * 64
            target_height = ((user_height + 31) // 64) * 64
            print(f"📐 使用用户指定尺寸: {target_width}x{target_height}")
        else:
            # 用户未指定，使用原图尺寸
            target_width = 0
            target_height = 0
            print(f"📐 使用原图尺寸")

        # ================================================================
        # ✅ ControlNet 模式处理（优先执行）
        # ================================================================
        if use_controlnet:
            try:
                log("🧠 启用 ControlNet 模式...")
                self.update_status("🧠 正在启用 ControlNet 姿态控制...")

                # ✅ 预处理时强制过滤多人骨架
                from utils.controlnet_helper import preprocess_image_for_controlnet
                from config.app_config import app_config
            
                # 对每张选中的图片进行预处理，只保留主体
                filtered_images = []
                temp_dir = app_config.paths.output_dir
                os.makedirs(temp_dir, exist_ok=True)
                
                for img_path in self.selected_images:
                    # ✅ 获取原图尺寸作为预处理尺寸
                    from PIL import Image as PILImage
                    temp_img = PILImage.open(img_path)
                    orig_w, orig_h = temp_img.size
                    # 对齐到 64 的倍数
                    proc_w = ((orig_w + 31) // 64) * 64
                    proc_h = ((orig_h + 31) // 64) * 64
                    
                    # 先预处理，再传给 ControlNet
                    control_img = preprocess_image_for_controlnet(
                        img_path,
                        controlnet_type="openpose",
                        output_size=(proc_w, proc_h)  # ✅ 使用原图尺寸
                    )
                    if control_img is not None:
                        # 保存过滤后的骨架图
                        temp_path = os.path.join(temp_dir, f"_temp_pose_{os.path.basename(img_path)}")
                        control_img.save(temp_path)
                        filtered_images.append(temp_path)
                    
                # ✅ 获取用户选择的 ControlNet 类型
                selected_type = self.controlnet_type_var.get()
                controlnet_type = selected_type.split(" ")[0] if " " in selected_type else "openpose"

                print(f"🔍 [ControlNet 调试] use_controlnet={use_controlnet}")
                print(f"🔍 [ControlNet 调试] controlnet_type={controlnet_type}")
                print(f"🔍 [ControlNet 调试] filtered_images={len(filtered_images)} 张")
                
                # 调用 ControlNet 处理函数
                success, controlnet_results = process_with_controlnet(
                    selected_images=filtered_images,
                    prompt=prompt,
                    negative=negative,
                    steps=steps,
                    cfg=cfg,
                    strength=strength,
                    seed=seed,
                    app=self.app,
                    params=self.params,
                    progress_callback=self._progress_callback,
                    status_callback=self.update_status,
                    controlnet_type=controlnet_type
                )
                
                # 清理临时文件
                for f in filtered_images:
                    try:
                        os.remove(f)
                    except:
                        pass                
                
                print(f"🔍 [ControlNet 调试] success={success}, results={len(controlnet_results) if controlnet_results else 0}")
        
                if success and controlnet_results:
                    self.update_status(f"✅ ControlNet 完成！共生成 {len(controlnet_results)} 张")
                    self._on_generation_complete(0)
                    return
                else:
                    self.update_status("⚠️ ControlNet 处理失败，回退到普通模式")
                    # 继续执行普通图生图
                        
            except Exception as e:
                log(f"❌ ControlNet 错误: {e}")
                import traceback
                traceback.print_exc()
                self.update_status(f"⚠️ ControlNet 错误: {e}，回退到普通模式")


        # ================================================================
        # 普通图生图模式（原有逻辑）
        # ================================================================
        
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

            # ===== 获取独立的 pipeline 实例 =====
            model_name = self.app.model_var.get()
            model_path = self.app._get_model_path(model_name)
            
            # 获取 LoRA 信息
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
        
            
            ## ✅ 修复：使用 strength 变量，不是 current_strength
            pipe, steps, current_strength = fix_euler_scheduler_for_img2img(pipe, steps, strength)
            
            # ===== 2. 如果启用了局部重绘，切换为 Inpaint 管道 =====
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

                    # ✅ 如果是 Inpaint 管道，也需要修复调度器
                    pipe, steps, current_strength = fix_euler_scheduler_for_img2img(pipe, steps, current_strength)
                    
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
            
            ## ✅ 【修复】重置调度器状态，防止 Euler 调度器在图生图中索引越界
            #from diffusers import EulerDiscreteScheduler
            #if hasattr(pipe, 'scheduler') and isinstance(pipe.scheduler, EulerDiscreteScheduler):
            #    # 重新创建调度器，清除内部状态
            #    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
            #    print("   🔄 Euler 调度器已重置")

            # ✅ 进度回调带 source
            def progress_cb(value, msg):
                self.app.root.after(0, lambda: self.app.progress_bar.update(value, msg, "图生图"))
            
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
                    
                # ✅ 头像检测：使用 OpenCV 判断人脸占比
                import cv2
                import numpy as np

                # 将 PIL Image 转为 OpenCV 格式
                img_cv = np.array(init_image.convert('RGB'))[:, :, ::-1].copy()
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

                # ✅ 修复：使用 try-except 处理 CascadeClassifier 不可用的情况
                try:
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
                        
                except Exception as e:
                    print(f"   ⚠️ 人脸检测失败 (使用简化方法): {e}")
                    # 使用简化的人脸检测方法：基于图片比例判断
                    if original_h > original_w * 1.3:
                        # 竖图可能是全身照，降低强度
                        strength = min(strength, 0.3)
                        print(f"   📐 竖图检测，强度自动调整为: {strength:.2f}")
                    else:
                        print(f"   📐 保持原强度: {strength:.2f}")

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
                    

                    # ✅ 步骤回调带 source
                    step_callback = Img2ImgStepCallback(
                        progress_cb, steps, start_time, cancel_flag,
                        img_idx, i, len(images), num_images_per,
                        source="图生图"
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
                    
                    # ===== 【新增】水印去除（图生图也支持） =====
                    from utils.watermark_remover import WatermarkRemover
                    watermark_remover = WatermarkRemover()
                    
                    if self.params.remove_watermark_var.get() and self.params.watermark_post_process_var.get():
                        methods = ["opencv_inpaint", "opencv_blur"]
                        cleaned = watermark_remover.remove_watermark(
                            image,
                            methods=methods,
                            strength=self.params.watermark_strength_var.get(),
                            auto_detect=self.params.watermark_auto_detect_var.get()
                        )
                        cleaned.save(filepath, quality=95)
                        print(f"✅ 图生图水印已去除: {filename}")
                    else:
                        image.save(filepath)
                    
                    # ===== 图片后期处理（清理元数据/注入EXIF/真实化） =====
                    from utils.image_post_processor import post_process_image
                    
                    final_path = post_process_image(
                        filepath,
                        self.params,
                        prompt=prompt,
                        log_prefix="[图生图]"
                    )
                    
                    if final_path != filepath:
                        try:
                            os.remove(filepath)
                        except:
                            pass
                        filepath = final_path
                    
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
        finally:
            # ✅ 释放 pipeline，传入 task_id
            if 'model_path' in locals() and 'lora_path' in locals():
                pipeline_pool.release_pipeline(model_path, lora_path, task_id)

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
          

    def _run_strength_test(self):
        """运行强度批量测试"""
        if not self.selected_images:
            messagebox.showwarning("提示", "请先选择一张图片")
            return
        
        if self.is_generating:
            messagebox.showwarning("提示", "正在生成中，请等待完成")
            return
        
        if self.app.pipeline is None:
            messagebox.showwarning("提示", "请先加载模型")
            return
        
        # 获取提示词
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        negative = self.neg_text.get("1.0", tk.END).strip()
        
        if not prompt:
            # 如果图生图没有提示词，使用默认中性提示词
            prompt = "a high-quality photograph, detailed, sharp focus, natural lighting"
            self.update_status("ℹ️ 使用默认中性提示词")
        
        # 选择第一张图片
        image_path = self.selected_images[0]
        
        # 确定基础强度
        base_strength = self.strength_var.get()
        
        # 确认
        if not messagebox.askyesno("确认测试",
            f"将进行强度批量测试\n\n"
            f"图片: {os.path.basename(image_path)}\n"
            f"基础强度: {base_strength:.2f}\n"
            f"测试范围: ±0.20\n"
            f"预计生成 9 张图片\n\n"
            f"确定开始吗？"
        ):
            return
        
        self.update_status("🧪 开始强度测试...")
        self.generate_btn.config(state=tk.DISABLED)
        
        # 在后台线程中运行
        import threading
        threading.Thread(
            target=self._run_strength_test_thread,
            args=(image_path, prompt, negative, base_strength),
            daemon=True
        ).start()

    def _run_strength_test_thread(self, image_path: str, prompt: str, negative: str, base_strength: float):
        """后台线程运行强度测试"""
        try:
            from utils.strength_tester import run_strength_test
            
            def progress_cb(current, total, msg):
                self.app.root.after(0, lambda: self.app.update_progress(
                    current / total,
                    f"🧪 [{current}/{total}] {msg}"
                ))
            
            result = run_strength_test(
                app=self.app,
                image_path=image_path,
                prompt=prompt,
                negative=negative,
                base_strength=base_strength,
                output_dir="./output/strength_tests",
                progress_callback=progress_cb
            )
            
            self.app.root.after(0, lambda: self._on_test_complete(result))
            
        except Exception as e:
            self.app.root.after(0, lambda err=e: self._on_test_error(err))

    def _on_test_complete(self, result):
        """测试完成"""
        self.is_generating = False
        self.generate_btn.config(state=tk.NORMAL)
        self.update_progress(1.0, "✅ 强度测试完成")
        self.update_status(f"✅ 测试完成！共 {result['total']} 张，输出: {result['test_dir']}")
        
        # 打开输出目录
        try:
            os.startfile(result['test_dir'])
        except:
            pass
        
        messagebox.showinfo("测试完成",
            f"✅ 强度测试完成\n\n"
            f"测试数: {result['total']}\n"
            f"成功: {sum(1 for r in result['results'] if r['success'])}\n"
            f"输出目录: {result['test_dir']}\n\n"
            f"📊 请查看 report.html 获得详细报告"
        )

    def _on_test_error(self, error):
        """测试出错"""
        self.is_generating = False
        self.generate_btn.config(state=tk.NORMAL)
        self.update_status(f"❌ 测试失败: {error}")
        messagebox.showerror("错误", f"测试失败:\n{error}")
        

    def _on_controlnet_toggle(self):
        """ControlNet 开关切换"""
        from utils.controlnet_helper import controlnet_config
        enabled = self.use_controlnet_var.get()
        controlnet_config.set_enabled(enabled)
        if enabled:
            selected = self.controlnet_type_var.get()
            controlnet_type = selected.split(" ")[0] if " " in selected else "openpose"
            controlnet_config.set_type(controlnet_type)
        
# ========== 辅助函数 ==========
def safe_del(obj):
    try:
        if obj is not None:
            del obj
    except:
        pass