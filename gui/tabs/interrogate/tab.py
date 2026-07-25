# gui/tabs/interrogate/tab.py
"""图片反推标签页主类"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from datetime import datetime
from PIL import Image, ImageTk

from ..base_tab import BaseTab
from .ui import InterrogateUI
from .backends import (
    TagBackend,
    ClipBackend,
    BlipBackend,
    CombinedBackend,
)


class InterrogateTab(BaseTab):
    """图片反推标签页"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.interrogate_image_path = None
        self._init_vars()
        self.ui = InterrogateUI(self)
        self.ui.build()
    
    def _init_vars(self):
        """初始化变量"""
        self.path_var = tk.StringVar(value="")
        self.backend_var = tk.StringVar(value="tag")
        self.mode_var = tk.StringVar(value="fast")
        self.thresh_var = tk.DoubleVar(value=0.02)
        self.tag_model_var = tk.StringVar(value="ViT-Large (准确)")
        self.blip_model_var = tk.StringVar(value="BLIP-large (详细)")
        self.clip_model_var = tk.StringVar(value="ViT-L-14/openai")
        self.cancel_interrogate = False
        self.is_interrogating = False
    
    def _select_image(self):
        """选择图片"""
        file = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif"), ("所有文件", "*.*")]
        )
        if file:
            self.interrogate_image_path = file
            self.path_var.set(os.path.basename(file))
            self._show_preview(file)
    
    def _clear_image(self):
        """清除图片"""
        self.interrogate_image_path = None
        self.path_var.set("")
        self.preview_label.config(image='')
        self.preview_label.image = None
        self.update_status("已清除图片")
    
    def _show_preview(self, filepath):
        """显示预览"""
        try:
            img = Image.open(filepath)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
        except Exception as e:
            print(f"⚠️ 预览失败: {e}")
    
    def _on_backend_changed(self, event):
        """后端切换"""
        self.ui._update_ui_state()
    
    def _copy_to_txt2img(self):
        """复制到文生图"""
        result = self.result_text.get("1.0", tk.END).strip()
        if result and not result.startswith("❌"):
            if hasattr(self.app, 'txt2img_tab'):
                self.app.txt2img_tab.set_prompt(result, "")
                self.update_status("✅ 已复制到文生图")
    
    def _copy_to_img2img(self):
        """复制到图生图"""
        result = self.result_text.get("1.0", tk.END).strip()
        if result and not result.startswith("❌"):
            if hasattr(self.app, 'img2img_tab'):
                self.app.img2img_tab.set_prompt(result, "")
                self.update_status("✅ 已复制到图生图")
    
    def _copy_to_img2img_recommended(self):
        """复制到图生图（推荐）"""
        result = self.result_text.get("1.0", tk.END).strip()
        if result and not result.startswith("❌"):
            if hasattr(self.app, 'img2img_tab'):
                self.app.img2img_tab.set_prompt(result, "")
                self.update_status("✅ 已复制到图生图")
    
    def _save_result(self):
        """保存结果"""
        result = self.result_text.get("1.0", tk.END).strip()
        if not result or result.startswith("❌"):
            messagebox.showwarning("提示", "没有有效的反推结果可保存")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="保存反推结果",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=f"interrogate_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result)
            self.update_status(f"✅ 已保存到: {os.path.basename(filepath)}")
    
    def _interrogate_blip_for_img2img(self, image_path):
        """BLIP 专门用于图生图"""
        backend = BlipBackend(self)
        return backend.interrogate(image_path, model_name="BLIP-large (详细)")
    
    def _show_error(self, message):
        """显示错误"""
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", f"❌ {message}")
        self.update_status("❌ 反推失败")
        self._reset_ui_state()
    
    def _reset_ui_state(self):
        """重置 UI 状态"""
        self.is_interrogating = False
        self.interrogate_btn.config(state=tk.NORMAL)
        self.cancel_interrogate_btn.config(state=tk.DISABLED)
    
    def cancel_interrogation(self):
        """取消反推"""
        self.cancel_interrogate = True
        self.update_status("⏹️ 正在取消...")
        self.cancel_interrogate_btn.config(state=tk.DISABLED)
    
    def start_interrogate(self):
        """开始反推"""
        if not self.interrogate_image_path:
            messagebox.showwarning("提示", "请先选择图片")
            return
        
        if self.is_interrogating and self.cancel_interrogate:
            self.is_interrogating = False
        
        if self.is_interrogating:
            messagebox.showwarning("提示", "反推正在进行中，请等待完成")
            return
        
        self.cancel_interrogate = False
        self.is_interrogating = True
        self.interrogate_btn.config(state=tk.DISABLED)
        self.cancel_interrogate_btn.config(state=tk.NORMAL)
        self.update_status("🔍 正在分析图片，请稍候...")
        threading.Thread(target=self._run_interrogate, daemon=True).start()
    
    def _run_interrogate(self):
        """后台执行反推"""
        try:
            backend_name = self.backend_var.get()
            
            backends = {
                "tag": TagBackend(self),
                "clip": ClipBackend(self),
                "blip": BlipBackend(self),
                "combined": CombinedBackend(self),
            }
            
            backend = backends.get(backend_name)
            if not backend:
                self._show_error(f"未知后端: {backend_name}")
                return
            
            # 获取参数
            kwargs = {
                'model_name': self.tag_model_var.get() if backend_name == "tag" else self.blip_model_var.get(),
                'threshold': self.thresh_var.get(),
                'mode': self.mode_var.get(),
                'blip_model': self.blip_model_var.get(),
                'clip_model': self.clip_model_var.get(),
                'clip_mode': self.mode_var.get(),
            }
            
            result = backend.interrogate(self.interrogate_image_path, **kwargs)
            
            if self.cancel_interrogate:
                return
            
            def update_ui():
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", result)
                self.update_status("✅ 反推完成")
                self._reset_ui_state()
            
            self.app.root.after(0, update_ui)
            
        except ImportError as e:
            self._show_error(f"缺少依赖: {e}")
        except Exception as e:
            self._show_error(f"出错: {e}")
        finally:
            self.is_interrogating = False
            if self.cancel_interrogate:
                self.app.root.after(0, self._reset_ui_state)