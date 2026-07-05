#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片预览组件
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import sys


class ImagePreview:
    """图片预览管理器"""
    
    def __init__(self, parent, max_images: int = 20):
        self.parent = parent
        self.max_images = max_images
        self.preview_images = []
        
        self.canvas = None
        self.preview_frame = None
        self.scrollbar = None
        self.canvas_window = None
    
    def create_widgets(self, parent, pack_kwargs: dict = None):
        """创建预览组件"""
        if pack_kwargs is None:
            pack_kwargs = {"fill": tk.X, "padx": 5, "pady": 5}
        
        self.canvas = tk.Canvas(parent, height=120, bg='#f0f0f0', highlightthickness=1)
        self.canvas.pack(**pack_kwargs)
        
        self.preview_frame = ttk.Frame(self.canvas)
        
        self.scrollbar = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.scrollbar.pack(fill=tk.X, padx=5, pady=2)
        
        self.canvas.configure(xscrollcommand=self.scrollbar.set)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.preview_frame, anchor=tk.NW)
        
        self.preview_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
    
    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def add_image(self, filepath: str, image: Image.Image):
        """添加图片到预览"""
        img = image.copy()
        img.thumbnail((100, 100))
        photo = ImageTk.PhotoImage(img)
        
        frame = ttk.Frame(self.preview_frame)
        frame.pack(side=tk.LEFT, padx=2, pady=2)
        
        def on_double_click(e, path=filepath):
            self._open_file(path)
        
        label = ttk.Label(frame, image=photo)
        label.image = photo
        label.pack()
        label.bind("<Double-Button-1>", on_double_click)
        
        name = os.path.basename(filepath)[:20]
        ttk.Label(frame, text=name, font=("", 8)).pack()
        
        self.preview_images.append(photo)
        
        children = self.preview_frame.winfo_children()
        if len(children) > self.max_images:
            for child in children[:self.max_images // 2]:
                child.destroy()
    
    def clear(self):
        """清空预览"""
        for child in self.preview_frame.winfo_children():
            child.destroy()
        self.preview_images.clear()
    
    def _open_file(self, path: str):
        """打开文件"""
        if sys.platform == 'win32':
            os.startfile(path)
        else:
            os.system(f'open "{path}"')