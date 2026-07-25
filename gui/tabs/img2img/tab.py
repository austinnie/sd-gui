# gui/tabs/img2img/tab.py
"""图生图标签页主类"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import random
from datetime import datetime
from pathlib import Path
from PIL import Image

from ..base_tab import BaseTab
from .ui import Img2ImgUI
from .generator import ImageGenerator
from .batch import BatchGenerator
from .mask_editor import MaskEditor
from .controlnet import ControlNetHandler
from .utils import log

from gui.components.memory_monitor import force_memory_cleanup, get_memory_usage


class Img2ImgTab(BaseTab):
    """图生图标签页"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.selected_images = []
        self._init_vars()
        
        self.generator = ImageGenerator(self)
        self.batch_generator = BatchGenerator(self)
        self.mask_editor = MaskEditor(self)
        self.controlnet_handler = ControlNetHandler(self)
        
        self.ui = Img2ImgUI(self)
        self.ui.build()
    
    def _init_vars(self):
        """初始化变量"""
        from config.app_config import app_config
        
        self.params = self.app.params_panel
        
        self.img_paths_var = tk.StringVar(value="")
        self.strength_var = tk.DoubleVar(value=0.35)
        self.per_image_var = tk.IntVar(value=1)
        self.size_var = tk.StringVar(value="自动(保持比例)")
        
        self.default_prompt = ""
        self.default_negative = app_config.generation.negative_prompt or \
            "worst quality, low quality, ugly, deformed, blurry"
        
        self.cancel_generation = False
        self.is_generating = False
        
        self.use_inpaint_var = tk.BooleanVar(value=False)
        self.use_controlnet_var = tk.BooleanVar(value=True)
        self.controlnet_combo_var = tk.StringVar(value="姿态+边缘+深度")
        self.mask_image = None
        
        self.image_mode_var = tk.StringVar(value="single")
        self.selected_images = []
        self.batch_prompts = []
    
    # ==================== 图片选择 ====================
    
    def _on_mode_changed(self):
        """切换图片选择模式"""
        mode = self.image_mode_var.get()
        
        self.single_path_frame.pack_forget()
        self.multiple_path_frame.pack_forget()
        self.directory_path_frame.pack_forget()
        
        if mode == "single":
            self.single_path_frame.pack(fill=tk.X)
        elif mode == "multiple":
            self.multiple_path_frame.pack(fill=tk.X)
        elif mode == "directory":
            self.directory_path_frame.pack(fill=tk.X)
        
        self._update_image_count()
    
    def _select_single_image(self):
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
        files = filedialog.askopenfilenames(
            title="选择多张图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("所有文件", "*.*")]
        )
        if files:
            self.selected_images = list(files)
            self.multiple_count_label.config(text=f"已选择 {len(files)} 张图片")
            self._update_image_count()
            if files:
                self._show_preview(files[0])
    
    def _select_directory(self):
        dir_path = filedialog.askdirectory(title="选择图片目录")
        if dir_path:
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
    
    def _clear_images(self):
        self.selected_images = []
        self.img_paths_var.set("")
        self.multiple_count_label.config(text="未选择")
        self._update_image_count()
        self.preview_label.config(image='')
        self.preview_label.image = None
    
    def _update_image_count(self):
        count = len(self.selected_images)
        if count == 0:
            self.image_count_label.config(text="")
        else:
            self.image_count_label.config(text=f"🖼️ {count} 张图片")
    
    def _show_preview(self, filepath):
        try:
            from PIL import Image, ImageTk
            img = Image.open(filepath)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
        except Exception as e:
            print(f"⚠️ 预览失败: {e}")
    
    # ==================== 模板 ====================
    
    def _clear_template_prompt(self):
        """清空模板内容"""
        self.prompt_text.delete("1.0", tk.END)
        self.neg_text.delete("1.0", tk.END)
        self.update_status("已清空模板内容")
    
    def _on_template_selected(self, template):
        """模板选择回调"""
        if not template:
            return
        
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", template.prompt)
        
        if template.negative:
            self.neg_text.delete("1.0", tk.END)
            self.neg_text.insert("1.0", template.negative)
        
        self.update_status(f"✅ 已应用模板: {template.name}")
    
    # ==================== ControlNet ====================
    
    def _on_controlnet_combo_changed(self, event):
        """ControlNet 组合切换"""
        from utils.controlnet import get_recommended_multi_controlnet_combos
        
        combos = get_recommended_multi_controlnet_combos()
        selected = self.controlnet_combo_var.get()
        combo_info = combos.get(selected)
        
        if combo_info:
            types_str = " + ".join(combo_info["types"])
            scales_str = ", ".join([str(s) for s in combo_info["scales"]])
            self.controlnet_hint.config(
                text=f"💡 {combo_info['description']} | 权重: [{scales_str}]"
            )
    
    def _on_controlnet_toggle(self):
        """ControlNet 开关"""
        self.controlnet_handler.toggle()
    
    # ==================== 遮罩 ====================
    
    def _open_mask_editor(self):
        """打开遮罩编辑器"""
        self.mask_editor.open_editor()
    
    # ==================== 生成 ====================
    
    def start_generate(self):
        """开始生成"""
        if not self.selected_images:
            messagebox.showwarning("提示", "请先选择图片")
            return
        
        if not self.app.model_manager.is_sd_loaded:
            messagebox.showwarning("提示", "请先加载模型")
            return
        
        self.cancel_generation = False
        self.is_generating = True
        
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        negative = self.neg_text.get("1.0", tk.END).strip()
        
        if not prompt:
            prompt = "a high-quality photograph, detailed, sharp focus, natural lighting"
            self.update_status("ℹ️ 未检测到提示词，已使用默认中性提示词。")
        
        params = self.params.get_params()
        steps = params["steps"]
        cfg = params["cfg"]
        seed = params["seed"]
        target_width = params["width"]
        target_height = params["height"]
        
        strength = self.strength_var.get()
        num_images_per = self.per_image_var.get()
        total_tasks = len(self.selected_images) * num_images_per
        
        use_controlnet = self.use_controlnet_var.get()
        controlnet_types = []
        conditioning_scales = []
        
        if use_controlnet:
            from utils.controlnet import get_recommended_multi_controlnet_combos
            combo_name = self.controlnet_combo_var.get()
            combos = get_recommended_multi_controlnet_combos()
            combo_info = combos.get(combo_name, list(combos.values())[0])
            controlnet_types = combo_info["types"]
            conditioning_scales = combo_info["scales"]
            print(f"🧠 ControlNet 组合: {combo_name}")
            print(f"   类型: {controlnet_types}")
            print(f"   权重: {conditioning_scales}")
        
        self.update_status(f"🎨 开始图生图... (共 {total_tasks} 张)")
        self.generate_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        
        threading.Thread(
            target=self.generator.generate,
            args=(prompt, negative, strength, steps, cfg, seed, num_images_per,
                  target_width, target_height),
            kwargs={'use_controlnet': use_controlnet},
            daemon=True
        ).start()
    
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
        """取消生成"""
        self.cancel_generation = True
        self.is_generating = False
        self.update_status("⏹️ 正在取消...")
        self.cancel_btn.config(state=tk.DISABLED)
    
    # ==================== 强度测试 ====================
    
    def _run_strength_test(self):
        """运行强度测试"""
        if not self.selected_images:
            messagebox.showwarning("提示", "请先选择一张图片")
            return
        
        if self.is_generating:
            messagebox.showwarning("提示", "正在生成中，请等待完成")
            return
        
        if not self.app.model_manager.is_sd_loaded:
            messagebox.showwarning("提示", "请先加载模型")
            return
        
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        negative = self.neg_text.get("1.0", tk.END).strip()
        
        if not prompt:
            prompt = "a high-quality photograph, detailed, sharp focus, natural lighting"
            self.update_status("ℹ️ 使用默认中性提示词")
        
        image_path = self.selected_images[0]
        base_strength = self.strength_var.get()
        
        if not messagebox.askyesno("确认测试",
            f"将进行强度批量测试\n\n"
            f"图片: {os.path.basename(image_path)}\n"
            f"基础强度: {base_strength:.2f}\n"
            f"预计生成 9 张图片\n\n确定开始吗？"
        ):
            return
        
        self.update_status("🧪 开始强度测试...")
        self.generate_btn.config(state=tk.DISABLED)
        
        import threading
        threading.Thread(
            target=self._run_strength_test_thread,
            args=(image_path, prompt, negative, base_strength),
            daemon=True
        ).start()
    
    def _run_strength_test_thread(self, image_path, prompt, negative, base_strength):
        """后台运行强度测试"""
        try:
            from utils.strength_tester import run_strength_test
            
            def progress_cb(current, total, msg):
                self.app.root.after(0, lambda: self.app.update_progress(
                    current / total, f"🧪 [{current}/{total}] {msg}"
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
        self.update_status(f"✅ 测试完成！共 {result['total']} 张")
        try:
            os.startfile(result['test_dir'])
        except:
            pass
        messagebox.showinfo("测试完成", f"✅ 强度测试完成\n\n输出目录: {result['test_dir']}")
    
    def _on_test_error(self, error):
        """测试出错"""
        self.is_generating = False
        self.generate_btn.config(state=tk.NORMAL)
        self.update_status(f"❌ 测试失败: {error}")
        messagebox.showerror("错误", f"测试失败:\n{error}")
    
    # ==================== 外部接口 ====================
    
    def set_prompt(self, prompt: str, negative: str):
        """设置提示词"""
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", prompt)
        if negative:
            self.neg_text.delete("1.0", tk.END)
            self.neg_text.insert("1.0", negative)
    
    def set_params(self, steps=None, cfg=None, seed=None, width=None, height=None, num_images=None):
        """设置参数"""
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
        """批量生成"""
        if not self.selected_images:
            messagebox.showwarning("提示", "请先选择图片")
            return
        
        if self.is_generating:
            messagebox.showwarning("提示", "正在生成中，请等待完成")
            return
        
        prompts_list = [p.strip() for p in prompts if p.strip()]
        if not prompts_list:
            messagebox.showwarning("提示", "请输入提示词")
            return
        
        self.batch_generator.run_batch(prompts_list)