# gui/components/memory_monitor.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存监控组件 - 增加自动清理
"""

import tkinter as tk
from tkinter import ttk
import psutil
import torch
import gc
from datetime import datetime
import threading

 ✅ 添加 logger 导入
from utils.logger import get_logger

logger = get_logger(__name__)  # ✅ 添加这行

def get_memory_usage():
    """获取当前进程内存使用量 (GB)"""
    try:
        return psutil.Process().memory_info().rss / 1024 / 1024 / 1024
    except:
        return 0


def get_memory_usage_mb():
    """获取当前进程内存使用量 (MB)"""
    try:
        return psutil.Process().memory_info().rss / 1024 / 1024
    except:
        return 0


def get_system_memory_percent():
    """获取系统内存使用百分比"""
    try:
        return psutil.virtual_memory().percent
    except:
        return 0


# gui/components/memory_monitor.py

def force_memory_cleanup(threshold_gb: float = 12.0):
    """强制执行内存清理 - 增强版"""
    import gc
    
    before = get_memory_usage()
    logger.info(f"   🔧 内存清理前: {before:.1f} GB")
    
    # ===== ✅ 1. 清理 Pipeline 池 =====
    try:
        from utils.pipeline_pool import pipeline_pool
        status = pipeline_pool.get_status()
        if status.get('active_count', 0) > 0:
            logger.info(f"   🗑️ 清理 Pipeline 池 ({status['active_count']} 个实例)...")
            # 强制释放所有 Pipeline
            for key, data in list(pipeline_pool._pipelines.items()):
                if data.get('ref_count', 0) <= 0:
                    pipe = data.get('pipe')
                    if pipe is not None:
                        del pipe
                    del pipeline_pool._pipelines[key]
    except Exception as e:
        logger.debug(f"   ⚠️ Pipeline 池清理失败: {e}")
    
    # ===== ✅ 2. 清理图片缓存 =====
    try:
        from utils.image_cache import image_cache
        cache_size = len(image_cache._cache)
        if cache_size > 0:
            logger.info(f"   🗑️ 清理图片缓存 ({cache_size} 张)...")
            image_cache.clear()
    except Exception as e:
        logger.debug(f"   ⚠️ 图片缓存清理失败: {e}")
    
    # ===== ✅ 3. 多次垃圾回收 =====
    for i in range(5):  # 增加到 5 次
        gc.collect()
    
    # ===== ✅ 4. 清理 CUDA 缓存 =====
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    # ===== ✅ 5. 再回收一次 =====
    gc.collect()
    
    after = get_memory_usage()
    freed = before - after
    
    if freed < 0:
        logger.info(f"   ⚠️ 内存统计异常 (释放: {freed:.2f} GB)")
        freed = 0
    
    logger.info(f"   ✅ 内存清理完成，释放: {freed:.2f} GB，当前: {after:.1f} GB")
    return freed
    
class MemoryMonitor:
    """内存监控器 - 带自动清理"""
    
    def __init__(self, parent, update_interval: int = 5000):
        self.parent = parent
        self.update_interval = update_interval
        self.memory_var = tk.StringVar(value="💾 内存: -- GB")
        self.mem_percent_var = tk.StringVar(value="")
        self.label = None
        self._after_id = None
        self._running = False
    
    def create_widget(self, parent) -> ttk.Label:
        """创建内存显示标签"""
        frame = ttk.Frame(parent)
        self.label = ttk.Label(frame, textvariable=self.memory_var, font=("", 9))
        self.label.pack(side=tk.LEFT)
        
        self.percent_label = ttk.Label(frame, textvariable=self.mem_percent_var, font=("", 8), foreground="gray")
        self.percent_label.pack(side=tk.LEFT, padx=5)
        
        # 清理按钮
        self.cleanup_btn = ttk.Button(
            frame,
            text="🧹",
            width=2,
            command=self._manual_cleanup
        )
        self.cleanup_btn.pack(side=tk.LEFT, padx=2)
        
        return frame
    
    def start_monitoring(self):
        """开始监控"""
        self._running = True
        self._update_memory()
    
    def stop_monitoring(self):
        """停止监控"""
        self._running = False
        if self._after_id:
            self.parent.after_cancel(self._after_id)
            self._after_id = None
    
    def _manual_cleanup(self):
        """手动清理"""
        freed = force_memory_cleanup()
        if freed > 0.1:
            self.memory_var.set(f"💾 内存: {get_memory_usage():.1f} GB (释放 {freed:.2f} GB)")
            self.parent.after(2000, self._update_memory)
    
    def _update_memory(self):
        """更新内存显示"""
        if not self._running:
            return
        
        try:
            mem_gb = get_memory_usage()
            sys_percent = get_system_memory_percent()
            
            if mem_gb > 0:
                color = "green" if mem_gb < 8 else "orange" if mem_gb < 12 else "red"
                self.memory_var.set(f"💾 内存: {mem_gb:.1f} GB")
                if self.label:
                    self.label.config(foreground=color)
                
                self.mem_percent_var.set(f"系统: {sys_percent}%")
            else:
                self.memory_var.set("💾 内存: 计算中...")
                if self.label:
                    self.label.config(foreground="gray")
                
        except Exception:
            self.memory_var.set("💾 内存: --")
            if self.label:
                self.label.config(foreground="gray")
        
        self._after_id = self.parent.after(self.update_interval, self._update_memory)