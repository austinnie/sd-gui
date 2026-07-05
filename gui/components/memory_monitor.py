#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存监控组件
"""

import tkinter as tk
from tkinter import ttk
import psutil
import torch


def get_memory_usage():
    """获取当前进程内存使用量 (GB)"""
    return psutil.Process().memory_info().rss / 1024 / 1024 / 1024


def get_memory_usage_mb():
    """获取当前进程内存使用量 (MB)"""
    return psutil.Process().memory_info().rss / 1024 / 1024


def force_memory_cleanup():
    """强制执行内存清理"""
    import gc
    print("   🔧 执行内存清理...")
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    print(f"   ✅ 内存清理完成，当前内存: {get_memory_usage():.1f} GB")


class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, parent, update_interval: int = 5000):
        self.parent = parent
        self.update_interval = update_interval
        self.memory_var = tk.StringVar(value="💾 内存: -- GB")
        self.label = None
        self._after_id = None
    
    def create_widget(self, parent) -> ttk.Label:
        """创建内存显示标签"""
        self.label = ttk.Label(parent, textvariable=self.memory_var, foreground="green", font=("", 9))
        return self.label
    
    def start_monitoring(self):
        """开始监控"""
        self._update_memory()
    
    def stop_monitoring(self):
        """停止监控"""
        if self._after_id:
            self.parent.after_cancel(self._after_id)
            self._after_id = None
    
    def _update_memory(self):
        """更新内存显示"""
        try:
            mem_gb = get_memory_usage()
            # 如果返回的是 None 或者非法数字，抛个异常走下面
            if mem_gb is None or mem_gb <= 0:
                raise ValueError("Invalid memory value")
                
            color = "green" if mem_gb < 8 else "orange" if mem_gb < 12 else "red"
            self.memory_var.set(f"💾 内存: {mem_gb:.1f} GB")
            if self.label:
                self.label.config(foreground=color)
        except Exception:
            # ✅ 只要获取失败，直接显示一个固定的文字，绝对不会显示 -- GB
            self.memory_var.set("💾 内存: 计算中...")
            if self.label:
                self.label.config(foreground="gray")
        
        self._after_id = self.parent.after(self.update_interval, self._update_memory)