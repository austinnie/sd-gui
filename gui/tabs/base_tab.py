#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
标签页基类
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable


class BaseTab:
    """所有标签页的基类"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)
        self._callbacks = {}
    
    def get_frame(self) -> ttk.Frame:
        """获取标签页框架"""
        return self.frame
    
    def setup_ui(self):
        """设置UI - 子类重写"""
        pass
    
    def on_show(self):
        """标签页显示时调用"""
        pass
    
    def on_hide(self):
        """标签页隐藏时调用"""
        pass
    
    def update_status(self, message: str):
        """更新状态"""
        if self.app:
            self.app.update_status(message)
    
    def update_progress(self, value: float, message: str = ""):
        """更新进度"""
        if self.app and hasattr(self.app, 'progress_bar'):
            self.app.progress_bar.update(value, message)
    
    def register_callback(self, name: str, callback: Callable):
        """注册回调函数"""
        self._callbacks[name] = callback
    
    def get_callback(self, name: str) -> Optional[Callable]:
        """获取回调函数"""
        return self._callbacks.get(name)
    
    def create_label(self, parent, text: str, row: int, column: int, **kwargs):
        """创建标签"""
        label = ttk.Label(parent, text=text)
        label.grid(row=row, column=column, sticky=tk.W, **kwargs)
        return label
    
    def create_entry(self, parent, row: int, column: int, width: int = 30, **kwargs):
        """创建输入框"""
        var = kwargs.get('textvariable')
        if var:
            entry = ttk.Entry(parent, textvariable=var, width=width)
        else:
            entry = ttk.Entry(parent, width=width)
        entry.grid(row=row, column=column, sticky=(tk.W, tk.E), **kwargs)
        return entry
    
    def create_text(self, parent, height: int = 5, width: int = 70, **kwargs):
        """创建文本区域"""
        text = tk.Text(parent, height=height, width=width)
        text.grid(**kwargs)
        return text
    
    def create_button(self, parent, text: str, command: Callable, **kwargs):
        """创建按钮"""
        btn = ttk.Button(parent, text=text, command=command)
        btn.grid(**kwargs)
        return btn
    
    def create_combobox(self, parent, values: list, row: int, column: int, **kwargs):
        """创建下拉框"""
        var = kwargs.get('textvariable', tk.StringVar())
        combo = ttk.Combobox(parent, textvariable=var, values=values)
        combo.grid(row=row, column=column, **kwargs)
        return combo, var