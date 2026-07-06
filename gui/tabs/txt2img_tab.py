#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文生图标签页 - 集成完整的 SD 生成逻辑
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
import threading
import time
from datetime import datetime
from PIL import Image
import torch
import gc
import psutil
import math

from .base_tab import BaseTab
from gui.components.memory_monitor import force_memory_cleanup, get_memory_usage
from core.nsfw_filter import nsfw_filter
from config.nsfw_config import nsfw_config, ContentLevel

import os
from config.app_config import app_config
from utils.watermark_remover import WatermarkRemover
from utils.image_post_processor import post_process_image

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


# ==================== 智能尺寸调整 ====================
def get_smart_size(width, height, prompt="", aspect_ratio=None, max_pixels=1024*1024):
    """
    智能尺寸调整 - 根据提示词内容和比例自动优化
    
    参数:
        width: 用户指定宽度 (0 表示自动)
        height: 用户指定高度 (0 表示自动)
        prompt: 提示词内容（用于检测场景类型）
        aspect_ratio: 强制宽高比 (可选)
        max_pixels: 最大像素数 (CPU 安全限制)
    
    返回:
        (调整后的宽度, 调整后的高度, 调整说明)
    """
    from config.app_config import app_config
    size_cfg = app_config.generation.size
    
    # CPU 安全上限
    max_cpu_w = size_cfg.get("cpu_safe_max_width", 1024)
    max_cpu_h = size_cfg.get("cpu_safe_max_height", 1024)
    
    # 检测提示词中的场景类型
    prompt_lower = prompt.lower()
    
    # 检测场景类型
    is_portrait = any(k in prompt_lower for k in ['portrait', 'headshot', 'close up', 'face', '头像', '特写', '面部'])
    is_full_body = any(k in prompt_lower for k in ['full body', 'standing', '全身', '站立'])
    is_landscape = any(k in prompt_lower for k in ['landscape', 'scenery', 'building', 'city', '风景', '建筑', '城市'])
    is_couple = any(k in prompt_lower for k in ['couple', 'two people', '双人', '情侣', '两人'])
    is_group = any(k in prompt_lower for k in ['group', 'three people', '多人', '三人'])
    
    # 1. 如果用户指定了尺寸 (width > 0 且 height > 0)
    if width > 0 and height > 0:
        # 对齐到 64 的倍数
        new_w = ((width + 31) // 64) * 64
        new_h = ((height + 31) // 64) * 64
        
        # 检查像素数限制
        if new_w * new_h > max_pixels:
            scale = math.sqrt(max_pixels / (new_w * new_h))
            new_w = int(new_w * scale)
            new_h = int(new_h * scale)
            new_w = ((new_w + 31) // 64) * 64
            new_h = ((new_h + 31) // 64) * 64
        
        # 检查 CPU 上限
        new_w = min(max_cpu_w, new_w)
        new_h = min(max_cpu_h, new_h)
        
        return new_w, new_h, f"用户指定 {width}x{height} → {new_w}x{new_h}"
    
    # 2. 根据场景类型智能推荐尺寸
    if aspect_ratio:
        # 使用指定的宽高比
        target_ratio = aspect_ratio
    elif is_portrait:
        # 头像/特写：偏向正方形
        target_ratio = 0.9
    elif is_full_body or is_couple:
        # 全身照/双人：偏向竖图
        target_ratio = 0.7
    elif is_landscape:
        # 风景：偏向横图
        target_ratio = 1.5
    elif is_group:
        # 多人：偏向横图
        target_ratio = 1.3
    else:
        # 默认：竖图 (适合人物)
        target_ratio = 0.75
    
    # 3. 根据比例计算尺寸
    base_pixels = min(max_pixels, 512 * 768)  # 基础像素数
    
    if target_ratio >= 1.0:
        # 横图
        new_w = int(math.sqrt(base_pixels * target_ratio))
        new_h = int(new_w / target_ratio)
    else:
        # 竖图
        new_h = int(math.sqrt(base_pixels / target_ratio))
        new_w = int(new_h * target_ratio)
    
    # 对齐到 64 的倍数
    new_w = ((new_w + 31) // 64) * 64
    new_h = ((new_h + 31) // 64) * 64
    
    # 确保最小尺寸
    min_size = 512
    if new_w < min_size:
        new_w = min_size
        new_h = int(new_w / target_ratio)
        new_h = ((new_h + 31) // 64) * 64
    if new_h < min_size:
        new_h = min_size
        new_w = int(new_h * target_ratio)
        new_w = ((new_w + 31) // 64) * 64
    
    # CPU 上限
    new_w = min(max_cpu_w, new_w)
    new_h = min(max_cpu_h, new_h)
    
    return new_w, new_h, f"智能推荐 → {new_w}x{new_h}"


# ==================== 智能参数调整 ====================
def get_smart_params(prompt, steps=None, cfg=None, strength=None, **kwargs):
    """
    根据提示词内容智能调整参数
    
    返回:
        (steps, cfg, strength, 调整说明)
    """
    prompt_lower = prompt.lower()
    
    # 检测场景类型
    is_portrait = any(k in prompt_lower for k in ['portrait', 'headshot', 'close up', 'face', '头像', '特写'])
    is_nude = any(k in prompt_lower for k in ['nude', 'naked', '裸体', '裸'])
    is_complex = any(k in prompt_lower for k in ['detailed', 'intricate', 'complex', '详细', '复杂'])
    is_anime = any(k in prompt_lower for k in ['anime', 'manga', '动漫', '二次元'])
    is_realistic = any(k in prompt_lower for k in ['photorealistic', 'realistic', '真实', '写实'])
    
    # 步数调整
    if steps is None or steps <= 0:
        if is_portrait:
            steps = 15  # 头像不需要太多步数
        elif is_nude:
            steps = 25  # 裸体需要更多细节
        elif is_complex:
            steps = 30  # 复杂场景需要更多步数
        elif is_anime:
            steps = 20  # 动漫风格适中
        else:
            steps = 20  # 默认
    
    # CFG 调整
    if cfg is None or cfg <= 0:
        if is_nude:
            cfg = 6.0  # 裸体用较低 CFG 更自然
        elif is_portrait:
            cfg = 7.5  # 头像适中
        elif is_anime:
            cfg = 8.0  # 动漫需要更高 CFG
        else:
            cfg = 7.0  # 默认
    
    # 强度调整 (图生图)
    if strength is None or strength <= 0:
        if is_portrait:
            strength = 0.35  # 头像低强度保持特征
        elif is_nude:
            strength = 0.45  # 裸体中等强度
        else:
            strength = 0.40  # 默认
    
    adjustments = []
    if steps:
        adjustments.append(f"步数={steps}")
    if cfg:
        adjustments.append(f"CFG={cfg}")
    if strength:
        adjustments.append(f"强度={strength}")
    
    return steps, cfg, strength, f"智能调整: {', '.join(adjustments)}"


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


class Txt2ImgStepCallback:
    def __init__(self, progress_callback, total_steps, start_time, cancel_flag_ref):
        self.progress_callback = progress_callback
        self.total_steps = total_steps
        self.start_time = start_time
        self.last_percent = 0
        self.cancel_flag_ref = cancel_flag_ref
        
    def __call__(self, pipe, step, timestep, callback_kwargs):
        if self.cancel_flag_ref and callable(self.cancel_flag_ref):
            if self.cancel_flag_ref():
                raise Exception("用户取消了生成")
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
        super().__init__(parent, app)
        self.params = self.app.params_panel
        self._init_vars()
        self.setup_ui()
    
    def _init_vars(self):
        """初始化变量"""
        from config.app_config import app_config
        
        # ✅ 使用共享参数面板
        self.params = self.app.params_panel
        
        # 默认提示词
        self.default_negative = (
            "worst quality, low quality, ugly, deformed, blurry, "
            "bad anatomy, bad hands, missing fingers, extra digits, "
            "watermark, text, signature"
        )
        
        self.default_positive = (
            "masterpiece, best quality, photorealistic, 8k, "
            "a beautiful Asian woman, Chinese, hanfu dress, "
            "traditional Chinese garden, East Asian architecture, "
            "full body shot, standing, smiling, looking at viewer"
        )
        
        # 生成状态
        self.cancel_generation = False
        self.is_generating = False
        
        # 批量生成状态
        self.batch_running = False
        self.batch_current = 0
        self.batch_total = 0
        self.batch_prompts = []
        self.batch_negs = []
    
    def setup_ui(self):
        """设置 UI - 移除了重复的水印去除控件"""
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

        # ===== 【已删除】独立的水印去除控件 =====
        # 水印去除功能已移至共享参数面板，避免重复
        
        # ===== 智能参数提示 =====
        hint_frame = ttk.Frame(frame)
        hint_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2, padx=5)
        ttk.Label(
            hint_frame,
            text="💡 参数（步数、CFG、种子、尺寸等）请在顶部的「共享参数面板」调整 | 尺寸会根据提示词智能优化",
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
    
    # ==================== 核心生成方法 ====================
    
    def start_generate(self):
        """开始生成（单张/多张）"""
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        negative = self.neg_text.get("1.0", tk.END).strip()
        
        if not prompt:
            messagebox.showwarning("提示", "请输入正面提示词")
            return
        
        # ===== NSFW 过滤 =====
        if nsfw_config.enabled:
            has_nsfw, matched = nsfw_filter.detect_nsfw(prompt)
            if has_nsfw:
                print(f"🔞 检测到 NSFW 关键词: {matched}")
                print(f"   当前等级: {nsfw_config.level.value}")
            
            # 根据等级过滤
            prompt, negative = nsfw_filter.filter_prompt(prompt, negative)
            print(f"   NSFW 过滤后提示词长度: {len(prompt)} 字符")
        
        self.cancel_generation = False
        self.is_generating = True
        
        # 获取参数
        params = self.params.get_params()
        steps = params["steps"]
        cfg = params["cfg"]
        seed = params["seed"]
        width = params["width"]
        height = params["height"]
        num_images = params["num_images"]
        
        # ===== 智能尺寸调整 =====
        smart_w, smart_h, size_msg = get_smart_size(width, height, prompt)
        if width > 0 or height > 0:
            print(f"📐 原尺寸: {width}x{height} → {size_msg}")
        else:
            print(f"📐 {size_msg}")
        
        # ===== 智能参数调整 =====
        smart_steps, smart_cfg, smart_strength, param_msg = get_smart_params(
            prompt, steps, cfg, None
        )
        if smart_steps != steps or smart_cfg != cfg:
            print(f"⚙️ {param_msg}")
        
        self.update_status("🚀 开始文生图...")
        self.generate_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        
        # 在后台线程中生成
        threading.Thread(
            target=self._generate_images,
            args=(prompt, negative, smart_steps, smart_cfg, seed, smart_h, smart_w, num_images),
            daemon=True
        ).start()
    
    def _generate_images(self, prompt, negative, steps, cfg, seed, height, width, num_images):
        """在后台线程中生成多张图片"""
        from config.app_config import app_config
        max_allowed = app_config.generation.max_images
        num_images = max(1, min(max_allowed, num_images))
        
        try:
            for i in range(num_images):
                if self.cancel_generation:
                    break
                
                current_seed = seed if seed != -1 else random.randint(1, 2**32 - 1)
                current_seed = current_seed + i
                
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
        """生成单张图片 - 核心生成逻辑"""

       
        
        log(f"开始生成第 {index}/{total} 张")
        
        # 使用默认值
        if steps is None:
            steps = self.params.steps_var.get()
        if cfg is None:
            cfg = self.params.cfg_var.get()
        if seed is None:
            seed = self.params.seed_var.get()
        if height is None or height <= 0:
            height = self.params.height_var.get()
        if width is None or width <= 0:
            width = self.params.width_var.get()
        
        # ===== 安全检查 =====
        if self.app.pipeline is None:
            self.app.root.after(0, lambda: self._on_generation_error("请先加载模型"))
            return
        
        # ===== 尺寸安全处理 =====
        width = max(1, width)
        height = max(1, height)
        
        gen_cfg = app_config.generation
        size_cfg = gen_cfg.size
        
        # 对齐到 64 的倍数
        width = ((width + 31) // 64) * 64
        height = ((height + 31) // 64) * 64
        
        # CPU 安全上限
        max_cpu_w = size_cfg.get("cpu_safe_max_width", 1024)
        max_cpu_h = size_cfg.get("cpu_safe_max_height", 1024)
        
        width = min(max_cpu_w, max(size_cfg["min_width"], width))
        height = min(max_cpu_h, max(size_cfg["min_height"], height))
        
        # 步数和 CFG 安全限制
        steps = max(gen_cfg.steps["min"], min(gen_cfg.steps["max"], steps))
        cfg = max(gen_cfg.cfg["min"], min(gen_cfg.cfg["max"], cfg))
        
        if seed == -1:
            seed = random.randint(1, 2**32 - 1)
        
        # ===== 精简提示词 =====
        prompt = auto_shorten_prompt(prompt, max_len=150)
        negative = auto_shorten_prompt(negative, max_len=150)
        
        # ===== 水印去除 - 增强负面提示词 =====
        watermark_remover = WatermarkRemover()
        enhanced_negative = negative
        if self.params.remove_watermark_var.get():
            strength = self.params.watermark_strength_var.get()
            enhanced_negative = watermark_remover.get_enhanced_negative(enhanced_negative, strength)
            print(f"✅ 负面提示词已增强 (水印强度: {strength})")
        
        # ===== 更新进度 =====
        start_time = time.time()
        def progress_cb(value, msg):
            self.app.root.after(0, lambda: self.update_progress(value, msg))
        
        progress_cb((index - 1) / total, f"🎨 生成第 {index}/{total} 张...")
        
        # ===== 获取高清修复参数 =====
        hires_enabled = self.params.hires_fix_var.get()
        hires_scale = self.params.hires_scale_var.get()
        hires_denoise = self.params.hires_denoise_var.get()
        
        pipe = self.app.pipeline
        
        try:
            # 强制模型在 CPU
            self.app.pipeline = pipe.to("cpu")
            generator = torch.Generator("cpu").manual_seed(seed)
            
            cancel_flag = lambda: self.cancel_generation
            step_callback = Txt2ImgStepCallback(progress_cb, steps, start_time, cancel_flag)
            
            log("调用 pipeline...")
            with torch.no_grad():
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
                    # 高清修复模式
                    low_res_w = int(width / hires_scale)
                    low_res_h = int(height / hires_scale)
                    low_res_w = max(512, ((low_res_w + 31) // 64) * 64)
                    low_res_h = max(512, ((low_res_h + 31) // 64) * 64)
                    
                    print(f"📐 启用高清修复: 初稿 {low_res_w}x{low_res_h} -> 最终 {width}x{height}")
                    progress_cb((index - 1) / total, f"🎨 生成初稿 ({low_res_w}x{low_res_h})...")
                    
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
                        
            # ===== 先处理水印去除（如果有） =====
            if self.params.remove_watermark_var.get() and self.params.watermark_post_process_var.get():
                methods = ["opencv_inpaint", "opencv_blur"]
                cleaned = watermark_remover.remove_watermark(
                    image,
                    methods=methods,
                    strength=self.params.watermark_strength_var.get(),
                    auto_detect=self.params.watermark_auto_detect_var.get()
                )
                cleaned.save(filepath, quality=95)
                print(f"✅ 水印已去除: {filename}")
            else:
                image.save(filepath)

            # ===== 【新增】图片后期处理 =====
            from utils.image_post_processor import post_process_image

            # 执行后期处理（注意：这里不要再次保存 image，因为上面已经保存过了）
            final_path = post_process_image(
                filepath,  # ← 传入已保存的文件路径
                self.params,
                prompt=prompt,
                log_prefix="[文生图]"
            )

            # 如果后期处理返回了不同路径，使用最终路径
            if final_path != filepath:
                try:
                    os.remove(filepath)
                except:
                    pass
                filepath = final_path
            
            # ===== 添加到预览 =====
            self.app.root.after(0, lambda: self.app.add_to_preview(filepath, image))
            
            # ===== 清理内存 =====
            safe_del(result)
            safe_del(generator)
            
            mem_gb = get_memory_usage()
            if mem_gb > 8.0:
                force_memory_cleanup()
            
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
    
    # ==================== 批量生成 ====================
    
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
        
        self.update_status(f"🚀 开始批量生成，共 {len(prompts)} 组...")
        threading.Thread(target=self._run_batch, daemon=True).start()
    
    def _run_batch(self):
        """运行批量生成"""
        for idx, prompt in enumerate(self.batch_prompts):
            if not self.batch_running or self.cancel_generation:
                self.update_status("⏹️ 批量生成已停止")
                break
            
            negative = self.batch_negs[idx] if idx < len(self.batch_negs) else self.default_negative
            self.batch_current = idx + 1
            
            self.update_status(f"🔄 正在生成: 第 {self.batch_current}/{self.batch_total} 组")
            
            seed = self.params.seed_var.get()
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
        params = self.params
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