#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文生图标签页 - 集成完整的 SD 生成逻辑
"""
from utils.watermark_remover import WatermarkRemover

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
import threading
import time
from datetime import datetime
from PIL import Image, ImageTk
import torch
from diffusers import DPMSolverMultistepScheduler
import gc
import psutil

from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    
from .base_tab import BaseTab
from gui.components.memory_monitor import force_memory_cleanup, get_memory_usage


# ========== 辅助函数 ==========
def auto_shorten_prompt(prompt, max_len=350):
    """自动精简提示词：去重 + 按长度优先保留 + 限制长度"""
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
class Txt2ImgStepCallback:
    def __init__(self, progress_callback, total_steps, start_time, cancel_flag_ref):
        self.progress_callback = progress_callback
        self.total_steps = total_steps
        self.start_time = start_time
        self.last_percent = 0
        self.cancel_flag_ref = cancel_flag_ref
        
    def __call__(self, pipe, step, timestep, callback_kwargs):

        # ✅ 如果传入的是 lambda
        if self.cancel_flag_ref and callable(self.cancel_flag_ref):
            if self.cancel_flag_ref():
                raise Exception("用户取消了生成")
        # ✅ 如果传入的是 tk.BooleanVar
        elif self.cancel_flag_ref and hasattr(self.cancel_flag_ref, 'get'):
            if self.cancel_flag_ref.get():
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
            self.progress_callback(percent, f"🎨 步骤 {current_step}/{self.total_steps} | {eta_str}")
        return callback_kwargs


class Txt2ImgTab(BaseTab):
    """文生图标签页 - 完整版"""
    
    def __init__(self, parent, app):       

        self.batch_running = False
        self.batch_current = 0
        self.batch_total = 0
        self.batch_prompts = []
        self.batch_negs = []
        
        # 水印去除器
        self.watermark_remover = WatermarkRemover()

        # ✅ 添加场景管理器
        try:
            from gui.scene_manager import SceneManager  # ✅ 正确路径
            self.scene_manager = SceneManager()
        except ImportError:
            self.scene_manager = None
            print("⚠️ SceneManager 未找到，场景模式不可用")
        
        super().__init__(parent, app)
        self._init_vars()
        self.setup_ui()
    
    def _init_vars(self):
        """初始化变量"""
        from config.app_config import app_config
            
        # ✅ 使用共享参数面板（不再自己创建参数变量）
        self.params = self.app.params_panel
        
       
        # ===== 水印去除 =====
        self.remove_watermark_var = tk.BooleanVar(value=True)
        self.watermark_strength_var = tk.StringVar(value="strong")
        self.watermark_methods_var = tk.StringVar(value="all")
        self.watermark_auto_detect_var = tk.BooleanVar(value=True)
        self.watermark_post_process_var = tk.BooleanVar(value=True)
        
        # ===== 修改默认负面提示词（大幅度精简，防止CPU卡死） =====
        # 不要把时间浪费在让AI“不要画白人”上，直接把重心放在“画好亚洲人”上
        self.default_negative = (
            "worst quality, low quality, ugly, deformed, blurry, "
            "bad anatomy, bad hands, missing fingers, extra digits, "
            "watermark, text, signature"
        )
        
        # ===== 修改默认正面提示词（强化亚洲人特征） =====
        # 明确告诉它要画“亚洲女性、旗袍、东方建筑”，AI就知道怎么干活了。
        self.default_positive = (
            "masterpiece, best quality, photorealistic, 8k, "
            "a beautiful Asian woman, Chinese, hanfu dress, "
            "traditional Chinese garden, East Asian architecture, "
            "full body shot, standing, smiling, looking at viewer"
        )
        
        # 生成状态
        self.cancel_generation = False
        self.is_generating = False
    
    def setup_ui(self):
        frame = self.frame
        row = 0
        
        # ===== 提示词区域 =====
        ttk.Separator(frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(frame, text="正面提示词:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.prompt_text = tk.Text(frame, height=5, width=70)
        self.prompt_text.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.prompt_text.insert("1.0", self.default_positive)
        row += 1
        
        ttk.Label(frame, text="负面提示词:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.neg_text = tk.Text(frame, height=4, width=70)
        self.neg_text.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.neg_text.insert("1.0", self.default_negative)
        row += 1     

        
        # ===== 水印去除控制 =====
        watermark_frame = ttk.LabelFrame(frame, text="🚫 水印去除", padding=5)
        watermark_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        wm_row1 = ttk.Frame(watermark_frame)
        wm_row1.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(
            wm_row1, 
            text="启用水印去除", 
            variable=self.remove_watermark_var
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(wm_row1, text="负面词强度:").pack(side=tk.LEFT, padx=5)
        ttk.Combobox(
            wm_row1, 
            textvariable=self.watermark_strength_var,
            values=["light", "medium", "strong", "extreme"],
            width=8
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(
            wm_row1, 
            text="后处理增强", 
            variable=self.watermark_post_process_var
        ).pack(side=tk.LEFT, padx=15)
        
        wm_row2 = ttk.Frame(watermark_frame)
        wm_row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(wm_row2, text="处理方法:").pack(side=tk.LEFT, padx=5)
        ttk.Combobox(
            wm_row2, 
            textvariable=self.watermark_methods_var,
            values=["all", "inpaint", "blur", "ai_detection"],
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(
            wm_row2, 
            text="自动检测水印", 
            variable=self.watermark_auto_detect_var
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            wm_row2, 
            text="💡 组合使用负面词强化 + 后处理，有效去除水印", 
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # ===== 生成按钮 =====
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)
        self.generate_btn = ttk.Button(btn_frame, text="🚀 文生图", command=self.start_generate)
        self.generate_btn.pack(side=tk.LEFT, padx=10)
        self.cancel_btn = ttk.Button(btn_frame, text="⏹️ 取消", command=self.cancel_generation_cmd, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="📁 打开输出文件夹", command=self.app.open_output_folder).pack(side=tk.LEFT, padx=10)
        row += 1


    def _set_size(self, width: int, height: int):
        """设置尺寸"""
        self.app.params_panel.width_var.set(width)
        self.app.params_panel.height_var.set(height)
        self.update_status(f"尺寸已设置为 {width}x{height}")
    
    def _run_batch(self):
        """运行批量生成"""
        from config.app_config import app_config
        
        for idx, prompt in enumerate(self.batch_prompts):
            if not self.batch_running:
                self.update_status("⏹️ 批量生成已停止")
                break
            
            negative = self.batch_negs[idx] if idx < len(self.batch_negs) else self.default_negative
            self.batch_current = idx + 1
            
            self.update_status(f"🔄 正在生成: 第 {self.batch_current}/{self.batch_total} 组")
            
            # 生成图片
            seed = self.app.params_panel.seed_var.get()
            if seed == -1:
                seed = random.randint(1, 2**32 - 1)
            seed = seed + idx
            
            self._generate_single_image(
                prompt, negative, 
                seed=seed,
                index=idx+1,
                total=self.batch_total
            )
            
            time.sleep(0.5)
        
        self.batch_running = False
        self.update_status(f"✅ 批量生成完成！共生成 {self.batch_current} 张")
    
    def _stop_batch(self):
        """停止批量生成"""
        self.batch_running = False
        self.cancel_generation = True
        self.update_status("正在停止批量生成...")
        self.batch_stop_btn.config(state=tk.DISABLED)
    
    # ==================== 核心生成方法 ====================
    
    def start_generate(self):
        """开始生成（单张/多张）"""
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        negative = self.neg_text.get("1.0", tk.END).strip()
        
        if not prompt:
            messagebox.showwarning("提示", "请输入正面提示词")
            return
        
        self.cancel_generation = False
        self.is_generating = True
        
        # 获取参数
        # ✅ 从共享参数面板获取参数
        params = self.app.params_panel.get_params()
        steps = params["steps"]
        cfg = params["cfg"]
        seed = params["seed"]
        width = params["width"]
        height = params["height"]
        num_images = params["num_images"]
        
        self.update_status("🚀 开始文生图...")
        self.generate_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        
        # 在后台线程中生成
        threading.Thread(
            target=self._generate_images,
            args=(prompt, negative, steps, cfg, seed, height, width, num_images),
            daemon=True
        ).start()
    
    def _generate_images(self, prompt, negative, steps, cfg, seed, height, width, num_images):
        """在后台线程中生成多张图片"""
        try:
            # ✅ 从配置读取最大允许数量，防止用户填得太高（虽然 UI 限制到了 4，但双重保险）
            from config.app_config import app_config
            max_allowed = app_config.generation.max_images
            num_images = max(1, min(max_allowed, num_images))  # ✅ 配置驱动限制

            for i in range(num_images): # ✅ 这里现在会根据 num_images 循环了！
                if self.cancel_generation:
                    break
                
                # 种子逻辑保持不变
                current_seed = seed if seed != -1 else random.randint(1, 2**32 - 1)
                current_seed = current_seed + i
                
                # 调用底层单张生成器
                self._generate_single_image(
                    prompt, negative,
                    steps=steps, cfg=cfg, seed=current_seed,
                    height=height, width=width,
                    index=i+1, total=num_images
                )
            
            self.app.root.after(0, self._on_generation_complete)
            
        except Exception as e:
            self.app.root.after(0, lambda err=e: self._on_generation_error(err))
    
    def _generate_single_image(self, prompt, negative, steps=None, cfg=None, seed=None,
                                height=None, width=None, index=1, total=1, callback=None):
        """
        生成单张图片 - 核心生成逻辑（针对 CPU 环境优化）
        """
        # ✅【新增这一行】修复 os 未定义错误
        import os         
        log(f"开始生成第 {index}/{total} 张")
         
        from config.app_config import app_config

        # 使用默认值
        if steps is None:
            steps = self.app.params_panel.steps_var.get()
        if cfg is None:
            cfg = self.app.params_panel.cfg_var.get()
        if seed is None:
            seed = self.app.params_panel.seed_var.get()
        if height is None:
            height = self.app.params_panel.height_var.get()
        if width is None:
            width = self.app.params_panel.width_var.get()
        
        # ===== 获取 pipeline =====
        if self.app.pipeline is None:
            self.app.root.after(0, lambda: self._on_generation_error("请先加载模型"))
            return

        # ===== 1. 核心优化：安全的尺寸对齐逻辑 =====
        # 避免因为 height/width 为 0 导致崩溃
        width = max(1, width)
        height = max(1, height)

        # ===== 1. 从配置获取全局范围 =====
        from config.app_config import app_config
        gen_cfg = app_config.generation
        size_cfg = gen_cfg.size        
        
        # 强制对齐到 64 的倍数 (VAE 必须要求 64 倍数)
        width = ((width + 31) // 64) * 64
        height = ((height + 31) // 64) * 64

        # CPU 安全上限（从 JSON 读取，极大概率是 1024）
        max_cpu_w = size_cfg.get("cpu_safe_max_width", 1024)
        max_cpu_h = size_cfg.get("cpu_safe_max_height", 1024)
        
        # 尺寸约束：下限从配置读取，上限取配置上限和 CPU 安全上限的较小值
        width = min(max_cpu_w, max(size_cfg["min_width"], width))
        height = min(max_cpu_h, max(size_cfg["min_height"], height))
        
        # ===== 3. 步数和 CFG 的安全限制（完全由配置驱动） =====
        steps = max(gen_cfg.steps["min"], min(gen_cfg.steps["max"], steps))
        cfg = max(gen_cfg.cfg["min"], min(gen_cfg.cfg["max"], cfg))
        
        if seed == -1:
            seed = random.randint(1, 2**32 - 1)
            
        pipe = self.app.pipeline
        
        # ===== 3. 核心优化：精简提示词 =====
        prompt = auto_shorten_prompt(prompt, max_len=150)
        negative = auto_shorten_prompt(negative, max_len=150)
        
        # ===== 4. 核心优化：根据【当前实际尺寸】智能检测提示词 =====
        # 如果用户尺寸小于 600x600，强行画全身照会糊成色块。
        # 因此删去原代码中“无脑添加 full body”的逻辑。
        if width < 600 and height < 600:
            if "full body" in prompt.lower():
                prompt = prompt.lower().replace("full body", "upper body, half body")
                print(f"⚠️ 尺寸为 {width}x{height}，强行画全身会崩，已自动改为 [半身照]")
        
        elif (width < 800 and height > 700) and "full body" not in prompt.lower():
            # 竖图尺寸（如 512x768），如果没有指定全身，补充半身说明
            prompt = f"{prompt}, upper body, half body shot"
            print(f"📐 竖图尺寸 {width}x{height}，自动补充 [半身照] 以确保面部清晰")
        
        # ===== 5. 水印去除：增强负面提示词 =====
        enhanced_negative = negative
        if self.remove_watermark_var.get():
            strength = self.watermark_strength_var.get()
            if strength not in ["light", "medium", "strong", "extreme"]:
                strength = "strong"
            enhanced_negative = self.watermark_remover.get_enhanced_negative(enhanced_negative, strength)
            print(f"✅ 负面提示词已增强 (强度: {strength})")
        
        # ===== 更新进度 =====
        start_time = time.time()
        def progress_cb(value, msg):
            self.app.root.after(0, lambda: self.update_progress(value, msg))
        
        progress_cb((index - 1) / total, f"🎨 生成第 {index}/{total} 张...")

        # ===== 获取高清修复参数 =====
        hires_enabled = self.app.params_panel.hires_fix_var.get()
        hires_scale = self.app.params_panel.hires_scale_var.get()
        hires_denoise = self.app.params_panel.hires_denoise_var.get()
        
        # ===== 执行生成 =====
        try:
            # ✅ 【新增这一行】每次生成前，强制把模型固定在 CPU 上，避免之前报错
            # 注意：如果您发现每次生成前卡顿一下，请把这一行删掉。
            self.app.pipeline = self.app.pipeline.to("cpu")
            
            # CPU 环境强制使用 "cpu" 生成器
            generator = torch.Generator("cpu").manual_seed(seed)

            # 创建取消标志
            cancel_flag = lambda: self.cancel_generation
            step_callback = Txt2ImgStepCallback(progress_cb, steps, start_time, cancel_flag)
            
            log("调用 pipeline...")
            with torch.no_grad():
                # ===== 分支1：不勾选高清修复 (极速模式) =====
                if not hires_enabled:
                    result = pipe(
                        prompt=prompt,
                        negative_prompt=enhanced_negative,
                        num_inference_steps=steps,
                        guidance_scale=cfg,
                        generator=generator,
                        height=height,
                        width=width,
                        num_images_per_prompt=1,
                        callback_on_step_end=step_callback
                    )
                else:
                    # ===== 分支2：勾选了高清修复 (高质量全身照) =====
                    # 先计算一个低分辨率的草稿尺寸（节省内存）
                    low_res_w = int(width / hires_scale)
                    low_res_h = int(height / hires_scale)
                    # 草稿尺寸不能太小，最低 512 起步，并强制对齐 64
                    low_res_w = max(512, ((low_res_w + 31) // 64) * 64)
                    low_res_h = max(512, ((low_res_h + 31) // 64) * 64)

                    print(f"📐 启用高清修复: 初稿 {low_res_w}x{low_res_h} -> 最终 {width}x{height}")
                    progress_cb((index - 1) / total, f"🎨 生成初稿 ({low_res_w}x{low_res_h})...")

                    # 第 1 步：生成底图
                    low_res_result = pipe(
                        prompt=prompt,
                        negative_prompt=enhanced_negative,
                        num_inference_steps=steps,
                        guidance_scale=cfg,
                        generator=generator,
                        height=low_res_w,
                        width=low_res_h,
                        num_images_per_prompt=1,
                        callback_on_step_end=step_callback
                    )
                    low_res_img = low_res_result.images[0]

                    # 第 2 步：把底图传入图生图，放大并重绘细节
                    progress_cb((index - 1) / total, f"🔄 放大并重绘 (幅度 {hires_denoise})...")
                    result = pipe(
                        prompt=prompt,
                        negative_prompt=enhanced_negative,
                        image=low_res_img,
                        strength=hires_denoise,
                        num_inference_steps=steps,
                        guidance_scale=cfg,
                        generator=generator,
                        height=height,
                        width=width,
                        num_images_per_prompt=1,
                        callback_on_step_end=step_callback
                    )
                    
                    # 清理底图占用的内存
                    safe_del(low_res_result)
                    safe_del(low_res_img)
                
            log("pipeline 调用完成")
            image = result.images[0]
                
            
            # ===== 保存图片 =====
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prompt_preview = "".join(c for c in prompt[:30] if c.isalnum() or c in " _-") or "image"
            if len(prompt_preview) > 50:
                prompt_preview = prompt_preview[:50]
            filename = f"{timestamp}_txt2img_{index}_{prompt_preview}.png"
            
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            
            # ===== 水印去除：后处理 =====
            if self.remove_watermark_var.get() and self.watermark_post_process_var.get():
                method_map = {
                    "all": ["opencv_inpaint", "opencv_blur"],
                    "inpaint": ["opencv_inpaint"],
                    "blur": ["opencv_blur"],
                    "ai_detection": ["ai_detection"]
                }
                methods = method_map.get(
                    self.watermark_methods_var.get(), 
                    ["opencv_inpaint", "opencv_blur"]
                )
                
                cleaned = self.watermark_remover.remove_watermark(
                    image,
                    methods=methods,
                    strength=self.watermark_strength_var.get(),
                    auto_detect=self.watermark_auto_detect_var.get()
                )
                cleaned.save(filepath, quality=95)
                print(f"✅ 水印已去除: {filename}")
            else:
                image.save(filepath)
            
            # ===== 添加到预览 =====
            self.app.root.after(0, lambda: self.app.add_to_preview(filepath, image))
            
            # ===== 清理内存 =====
            safe_del(result)
            safe_del(generator)
            
            # 检查内存阈值 (CPU 环境下，内存一旦超过 8GB 立即强制清理)
            mem_gb = get_memory_usage()
            if mem_gb > 8.0:
                force_memory_cleanup()
            
            # ===== 更新进度 =====
            progress_cb(index / total, f"✅ 已保存 {index}/{total}")
            
            if callback:
                callback()
                    
        except Exception as e:
            error_msg = str(e)
            if "用户取消" in error_msg or "cancelled" in error_msg.lower():
                self.app.root.after(0, lambda: self.update_status("⏹️ 已取消"))
            else:
                self.app.root.after(0, lambda err=error_msg: self._on_generation_error(err))
                raise
                
 
    def _on_generation_complete(self):
        """生成完成"""
        self.is_generating = False
        self.generate_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.update_progress(1.0, "✅ 生成完成！")
        self.update_status("✅ 文生图完成")
        force_memory_cleanup()
    
    def _on_generation_error(self, error):
        """生成出错"""
        self.is_generating = False
        self.generate_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.update_status(f"❌ 生成出错: {error}")
        messagebox.showerror("错误", f"生成失败:\n{error}")
    
    def cancel_generation_cmd(self):
        """取消生成（按钮回调）"""
        self.cancel_generation = True
        self.is_generating = False
        self.update_status("⏹️ 正在取消...")
        self.cancel_btn.config(state=tk.DISABLED)
        


    def batch_generate(self, prompts):
        """批量生成 - 从全局批量面板调用"""
        if self.batch_running:
            messagebox.showwarning("提示", "批量生成正在运行中")
            return
        
        negs = self._get_batch_negs_from_panel()
        while len(negs) < len(prompts):
            negs.append(self.default_negative)
        negs = negs[:len(prompts)]
        
        self.batch_prompts = prompts
        self.batch_negs = negs
        self.batch_current = 0
        self.batch_total = len(prompts)
        self.batch_running = True
        
        # ✅ 只更新状态，不操作 UI 组件
        self.update_status(f"🚀 开始批量生成，共 {len(prompts)} 组...")
        
        threading.Thread(target=self._run_batch, daemon=True).start()
        
    def _get_batch_negs_from_panel(self):
        """从全局批量面板获取负面词"""
        if hasattr(self.app, 'batch_panel'):
            return self.app.batch_panel.get_negatives()
        return []
    
    
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
    
    def generate(self):
        """外部调用生成"""
        self.start_generate()


# ========== 辅助函数 ==========
def safe_del(obj):
    try:
        if obj is not None:
            del obj
    except:
        pass