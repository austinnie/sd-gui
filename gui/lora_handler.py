# gui/lora_handler.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LoRA 处理器 - 处理 LoRA 相关的 UI 操作
"""

import os
import threading
from tkinter import messagebox

from gui.model_loader import scan_loras


class LoraHandler:
    """LoRA 处理器"""
    
    def __init__(self, app):
        self.app = app
        self._current_lora_path = None
    
    def scan_and_update(self):
        """扫描并更新 LoRA 列表"""
        lora_files, lora_paths, lora_types = scan_loras()
        self.app.lora_files = lora_files
        self.app.lora_paths = lora_paths
        self.app.lora_types = lora_types
        
        self.app.lora_combo['values'] = lora_files
        if lora_files:
            self.app.lora_var.set("")
        self._update_lora_status()
        self._update_lora_list()
    
    def _update_lora_list(self):
        """根据当前模型类型更新 LoRA 下拉列表"""
        if not hasattr(self.app, 'lora_files') or not self.app.lora_files:
            return
        
        if not self.app.model_manager.is_sd_loaded:
            self.app.lora_combo['values'] = self.app.lora_files
            if self.app.lora_files:
                current = self.app.lora_var.get()
                if current not in self.app.lora_files:
                    self.app.lora_var.set(self.app.lora_files[0])
            self._refresh_lora_viewer()
            return
        
        model_type = self.app.model_manager.get_sd_model_type()
        if model_type == "sdxl":
            filtered = [f for f in self.app.lora_files if "[SDXL]" in f]
        else:
            filtered = [f for f in self.app.lora_files if "[SD1.5]" in f]
        
        self.app.lora_combo['values'] = filtered
        
        current = self.app.lora_var.get()
        if current and current not in filtered:
            if filtered:
                self.app.lora_var.set(filtered[0])
            else:
                self.app.lora_var.set("")
                self.app.lora_combo.set("")
        
        if hasattr(self.app, 'lora_model_type_label'):
            if filtered:
                self.app.lora_model_type_label.config(
                    text=f"✅ 显示 {len(filtered)} 个 {model_type.upper()} LoRA",
                    foreground="green"
                )
            else:
                self.app.lora_model_type_label.config(
                    text=f"⚠️ 没有找到 {model_type.upper()} LoRA",
                    foreground="orange"
                )
        
        self._refresh_lora_viewer()
    
    def _refresh_lora_viewer(self):
        """刷新 LoRA 信息查看器"""
        if hasattr(self.app, 'lora_info_viewer') and self.app.lora_info_viewer:
            self.app.lora_info_viewer._refresh_list()
    
    def _update_lora_status(self):
        """更新 LoRA 状态显示"""
        lora_name = self.app.lora_var.get()
        if lora_name:
            weight = self.app.lora_weight_var.get()
            self.app.update_status(f"🔗 LoRA: {lora_name} (权重: {weight:.1f})")
        else:
            self.app.update_status("🔗 未加载 LoRA")
    
    def load_lora(self):
        """加载选中的 LoRA"""
        lora_display = self.app.lora_var.get()
        if not lora_display:
            messagebox.showwarning("提示", "请先选择 LoRA 模型")
            return
        
        if lora_display not in self.app.lora_paths:
            messagebox.showwarning("提示", "找不到 LoRA 文件")
            return
        
        if not self.app.model_manager.is_sd_loaded:
            if messagebox.askyesno("提示", "主模型未加载，是否同时加载主模型和 LoRA？"):
                self.app._load_sd_model()
            return
        
        lora_path = self.app.lora_paths[lora_display]
        lora_weight = self.app.lora_weight_var.get()
        lora_type = self.app.lora_types.get(lora_display, 'unknown')
        current_model_type = self.app.model_manager.get_sd_model_type()
        
        # 检查兼容性
        if lora_type != 'unknown' and lora_type != current_model_type:
            if not messagebox.askyesno(
                "LoRA 类型不匹配",
                f"当前模型是 {current_model_type.upper()}，\n"
                f"但 LoRA 标记为 {lora_type.upper()}。\n\n"
                f"这可能导致生成失败或效果不佳。\n"
                f"是否继续尝试加载？"
            ):
                return
        
        self.app.update_status(f"🔗 正在加载 LoRA: {lora_display}...")
        self.app.load_lora_btn.config(state=tk.DISABLED)
        
        def load_thread():
            try:
                success, msg = self.app.model_manager.load_lora_to_existing_pipe(
                    lora_path, lora_weight
                )
                
                if success:
                    self._current_lora_path = lora_path
                    self.app.root.after(0, lambda: self._on_load_success(lora_display))
                    return
                
                # 重新加载主模型
                model_name = self.app.model_var.get()
                model_path = self.app._get_model_path(model_name)
                
                if not model_path:
                    self.app.root.after(0, lambda: self._on_load_error("找不到模型文件"))
                    return
                
                def progress_cb(value, msg):
                    self.app.root.after(0, lambda: self.app.update_progress(value, msg))
                
                success = self.app.model_manager.load_sd(
                    model_path, model_name, progress_cb,
                    lora_path=lora_path,
                    lora_weight=lora_weight
                )
                
                if success:
                    self._current_lora_path = lora_path
                    self.app.root.after(0, lambda: self._on_load_success(lora_display))
                else:
                    self.app.root.after(0, lambda: self._on_load_error("模型加载失败"))
                
            except Exception as e:
                self.app.root.after(0, lambda err=e: self._on_load_error(str(err)))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def _on_load_success(self, lora_display):
        """LoRA 加载成功"""
        self.app.load_lora_btn.config(state=tk.NORMAL)
        self.app.unload_lora_btn.config(state=tk.NORMAL)
        self.app.update_status(f"✅ LoRA 加载成功: {lora_display}")

    def _on_load_error(self, error):
        """LoRA 加载失败"""
        self.app.load_lora_btn.config(state=tk.NORMAL)
        self.app.update_status(f"❌ LoRA 加载失败: {error}")
        messagebox.showerror("错误", f"LoRA 加载失败:\n{error}")
    
    def unload_lora(self):
        """卸载 LoRA"""
        if not self.app.model_manager.is_sd_loaded:
            return
        
        if self.app.model_manager.unload_lora_from_pipe():
            self._current_lora_path = None
            self.app.lora_var.set("")
            self.app.lora_weight_var.set(1.0)
            self.app.unload_lora_btn.config(state=tk.DISABLED)
            self.app.update_status("✅ LoRA 已卸载")
            return
        
        if not messagebox.askyesno("确认卸载",
            "无法直接卸载 LoRA，需要重新加载主模型。\n\n确定要继续吗？"
        ):
            return
        
        self.app.update_status("🔄 正在卸载 LoRA...")
        self.app.unload_lora_btn.config(state=tk.DISABLED)
        
        self.app.lora_var.set("")
        self.app.lora_weight_var.set(1.0)
        self._current_lora_path = None
        
        model_name = self.app.model_var.get()
        if model_name and model_name in self.app.checkpoint_paths:
            model_path = self.app.checkpoint_paths[model_name]
            
            def reload_thread():
                def progress_cb(value, msg):
                    self.app.root.after(0, lambda: self.app.update_progress(value, msg))
                
                success = self.app.model_manager.load_sd(
                    model_path, model_name, progress_cb,
                    lora_path=None, lora_weight=1.0
                )
                self.app.root.after(0, lambda: self._on_unload_complete(success))
            
            threading.Thread(target=reload_thread, daemon=True).start()
        else:
            self.app.unload_lora_btn.config(state=tk.NORMAL)
    
    def _on_unload_complete(self, success):
        """LoRA 卸载完成"""
        self.app.unload_lora_btn.config(state=tk.NORMAL)
        if success:
            self.app.update_status("✅ LoRA 已卸载")
        else:
            self.app.update_status("❌ LoRA 卸载失败")
    
    def clear_lora(self):
        """清除 LoRA 选择"""
        self.app.lora_var.set("")
        self.app.lora_weight_var.set(1.0)
        self._current_lora_path = None
        self._update_lora_status()
        
        if self.app.model_manager.is_sd_loaded:
            model_name = self.app.model_var.get()
            if model_name and model_name in self.app.checkpoint_paths:
                self.app._load_sd_model()