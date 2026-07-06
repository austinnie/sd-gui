# gui/components/progress_bar.py

import tkinter as tk
from tkinter import ttk


class ProgressBar:
    """进度条管理器"""
    
    def __init__(self, parent):
        self.parent = parent
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_label = ttk.Label(parent, text="")
        self.progress_bar = ttk.Progressbar(parent, variable=self.progress_var, maximum=1.0)
        self._visible = False
        self._current_source = ""  # ✅ 记录当前进度来源
    
    def create_widgets(self, parent=None, pack_kwargs: dict = None):
        """创建进度条组件"""
        if parent is None:
            parent = self.parent
        
        if pack_kwargs is None:
            pack_kwargs = {"fill": tk.X, "padx": 5, "pady": 5}
        
        self.progress_bar.pack(**pack_kwargs)
        self.progress_label.pack(**pack_kwargs)
        self.hide()
    
    def update(self, value: float, message: str = "", source: str = ""):
        """
        更新进度
        
        参数:
            value: 进度值 (0-1)
            message: 进度消息
            source: 来源标识 (如 "文生图", "图生图", "网格测试")
        """
        self.progress_var.set(value)
        
        # ✅ 如果有来源标识，添加到消息前面
        if source:
            display_msg = f"[{source}] {message}"
        else:
            display_msg = message
        
        self.progress_label.config(text=display_msg)
        self._current_source = source
        self.show()
    
    def reset(self):
        """重置进度"""
        self.progress_var.set(0)
        self.progress_label.config(text="")
        self._current_source = ""
        self.hide()
    
    def show(self):
        """显示进度条"""
        if not self._visible:
            self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
            self.progress_label.pack(fill=tk.X, padx=5)
            self._visible = True
    
    def hide(self):
        """隐藏进度条"""
        if self._visible:
            self.progress_bar.pack_forget()
            self.progress_label.pack_forget()
            self._visible = False
    
    def get_callback(self, source: str = ""):
        """
        获取进度回调函数
        
        参数:
            source: 来源标识
        """
        def callback(value: float, message: str):
            self.update(value, message, source)
        return callback