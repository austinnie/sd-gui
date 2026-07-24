# gui/vae_handler.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VAE 处理器 - 处理 VAE 相关的操作
"""

import os
from tkinter import messagebox

from utils.vae_utils import load_vae


class VaeHandler:
    """VAE 处理器"""
    
    def __init__(self, app):
        self.app = app
    
    def load_vae(self):
        """加载 VAE"""
        vae_display = self.app.vae_var.get()
        if not vae_display:
            messagebox.showwarning("提示", "请先选择 VAE 模型")
            return
        
        if vae_display not in self.app.vae_paths:
            messagebox.showwarning("提示", "找不到 VAE 文件")
            return
        
        if not self.app.model_manager.is_sd_loaded:
            messagebox.showwarning("提示", "请先加载主模型")
            return
        
        vae_path = self.app.vae_paths[vae_display]
        
        try:
            self.app.update_status(f"🎨 加载 VAE...")
            vae = load_vae(vae_path)
            self.app.model_manager._sd_pipe.vae = vae
            self.app.update_status(f"✅ VAE 加载成功: {vae_display}")
        except Exception as e:
            self.app.update_status(f"❌ VAE 加载失败: {e}")
            messagebox.showerror("错误", f"VAE 加载失败:\n{str(e)}")
    
    def unload_vae(self):
        """卸载 VAE"""
        if not self.app.model_manager.is_sd_loaded:
            messagebox.showwarning("提示", "请先加载主模型")
            return
        
        if not hasattr(self.app.model_manager, '_sd_pipe') or self.app.model_manager._sd_pipe is None:
            messagebox.showwarning("提示", "没有加载的模型")
            return
        
        try:
            model_name = self.app.model_var.get()
            model_path = self.app._get_model_path(model_name)
            
            if model_name and model_path:
                self.app.update_status("🔄 正在卸载 VAE...")
                self.app.vae_var.set("")
                
                def progress_cb(value, msg):
                    self.app.root.after(0, lambda: self.app.update_progress(value, msg))
                
                success = self.app.model_manager.load_sd(
                    model_path, model_name, progress_cb,
                    lora_path=None, lora_weight=1.0
                )
                
                if success:
                    self.app.update_status("✅ VAE 已卸载（使用默认 VAE）")
                else:
                    self.app.update_status("❌ VAE 卸载失败")
                    
        except Exception as e:
            self.app.update_status(f"❌ VAE 卸载失败: {e}")
            messagebox.showerror("错误", f"VAE 卸载失败:\n{str(e)}")
    
    def clear_vae(self):
        """清除 VAE"""
        if not self.app.model_manager.is_sd_loaded:
            return
        
        self.app.vae_var.set("")
        self.app.update_status("🔄 清除 VAE...")
        
        model_name = self.app.model_var.get()
        model_path = self.app._get_model_path(model_name)
        if model_name and model_path:
            self.app._load_sd_model()