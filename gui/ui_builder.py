# gui/ui_builder.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI 构建器 - 构建主界面的各个部分
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app import SDApp

from config.app_config import app_config


class UIBuilder:
    """UI 构建器"""
    
    def __init__(self, app: 'SDApp'):
        self.app = app
        self.root = app.root
    
    def build_scrollable_frame(self) -> ttk.Frame:
        """创建可滚动的主框架"""
        main_canvas = tk.Canvas(self.root, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame
    
    def build_status_bar(self, parent: ttk.Frame) -> ttk.Frame:
        """构建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.app.model_status_label = ttk.Label(
            status_frame,
            text=self.app.model_manager.get_status_text(),
            foreground="blue",
            font=("", 10)
        )
        self.app.model_status_label.pack(side=tk.LEFT, padx=5)
        
        # 切换按钮
        self.app.switch_to_janus_btn = ttk.Button(
            status_frame,
            text="🔄 切换 Janus",
            command=self.app._switch_to_janus
        )
        self.app.switch_to_janus_btn.pack(side=tk.LEFT, padx=5)
        
        self.app.switch_to_sd_btn = ttk.Button(
            status_frame,
            text="🔄 切换 SD",
            command=self.app._switch_to_sd,
            state=tk.DISABLED
        )
        self.app.switch_to_sd_btn.pack(side=tk.LEFT, padx=5)
        
        self.app.unload_model_btn = ttk.Button(
            status_frame,
            text="🗑️ 卸载模型",
            command=self.app._unload_current_model
        )
        self.app.unload_model_btn.pack(side=tk.LEFT, padx=5)
        
        # 内存监控
        if hasattr(self.app, 'memory_monitor'):
            self.app.memory_monitor.create_widget(status_frame).pack(side=tk.RIGHT, padx=5)
        
        return status_frame
    
    def build_model_selector(self, parent: ttk.Frame) -> ttk.Frame:
        """构建模型选择器"""
        model_frame = ttk.Frame(parent)
        model_frame.pack(fill=tk.X, pady=2, padx=5)
        
        ttk.Label(model_frame, text="📦 SD 模型:").pack(side=tk.LEFT, padx=5)
        
        self.app.model_var = tk.StringVar()
        self.app.model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.app.model_var,
            width=45
        )
        self.app.model_combo.pack(side=tk.LEFT, padx=5)
        
        self.app.load_btn = ttk.Button(
            model_frame,
            text="加载 SD",
            command=self.app._load_sd_model
        )
        self.app.load_btn.pack(side=tk.LEFT, padx=2)
        
        self.app.reload_btn = ttk.Button(
            model_frame,
            text="🔄 重载模块",
            command=self.app._reload_modules
        )
        self.app.reload_btn.pack(side=tk.LEFT, padx=2)
        
        return model_frame
    
    def build_lora_selector(self, parent: ttk.Frame) -> ttk.Frame:
        """构建 LoRA 选择器"""
        lora_frame = ttk.Frame(parent)
        lora_frame.pack(fill=tk.X, pady=2, padx=5)
        
        ttk.Label(lora_frame, text="🔗 LoRA 模型:").pack(side=tk.LEFT, padx=5)
        
        self.app.lora_var = tk.StringVar(value="")
        self.app.lora_combo = ttk.Combobox(
            lora_frame,
            textvariable=self.app.lora_var,
            width=45
        )
        self.app.lora_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(lora_frame, text="权重:").pack(side=tk.LEFT, padx=5)
        self.app.lora_weight_var = tk.DoubleVar(value=1.0)
        self.app.lora_weight_spinbox = ttk.Spinbox(
            lora_frame,
            from_=0.0,
            to=2.0,
            increment=0.1,
            textvariable=self.app.lora_weight_var,
            width=6
        )
        self.app.lora_weight_spinbox.pack(side=tk.LEFT, padx=2)
        
        # 模型类型提示
        self.app.lora_model_type_label = ttk.Label(
            lora_frame,
            text="",
            foreground="gray",
            font=("", 8)
        )
        self.app.lora_model_type_label.pack(side=tk.LEFT, padx=5)
        
        btn_container = ttk.Frame(lora_frame)
        btn_container.pack(side=tk.LEFT, padx=5)
        
        self.app.load_lora_btn = ttk.Button(
            btn_container,
            text="📦 加载 LoRA",
            command=self.app._load_lora_from_ui,
            width=12
        )
        self.app.load_lora_btn.pack(side=tk.LEFT, padx=2)
        
        self.app.unload_lora_btn = ttk.Button(
            btn_container,
            text="🗑️ 卸载 LoRA",
            command=self.app._unload_lora,
            state=tk.DISABLED,
            width=12
        )
        self.app.unload_lora_btn.pack(side=tk.LEFT, padx=2)
        
        self.app.clear_lora_btn = ttk.Button(
            btn_container,
            text="✖ 清除",
            command=self.app._clear_lora,
            width=8
        )
        self.app.clear_lora_btn.pack(side=tk.LEFT, padx=2)
        
        # LoRA 信息查看器
        from gui.components.lora_info_viewer import LoraInfoViewer
        self.app.lora_info_viewer = LoraInfoViewer(parent, self.app)
        self.app.lora_info_viewer.get_frame().pack(fill=tk.X, padx=10, pady=5)
        
        return lora_frame
    
    def build_vae_selector(self, parent: ttk.Frame) -> ttk.Frame:
        """构建 VAE 选择器"""
        vae_frame = ttk.Frame(parent)
        vae_frame.pack(fill=tk.X, pady=2, padx=5)
        
        ttk.Label(vae_frame, text="🎨 VAE 模型:").pack(side=tk.LEFT, padx=5)
        
        self.app.vae_var = tk.StringVar(value="")
        self.app.vae_combo = ttk.Combobox(
            vae_frame,
            textvariable=self.app.vae_var,
            width=45
        )
        self.app.vae_combo.pack(side=tk.LEFT, padx=5)
        
        btn_container = ttk.Frame(vae_frame)
        btn_container.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_container,
            text="📦 加载 VAE",
            command=self.app._load_vae,
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_container,
            text="🗑️ 卸载 VAE",
            command=self.app._unload_vae,
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_container,
            text="✖ 清除 VAE",
            command=self.app._clear_vae,
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        return vae_frame
    
    def build_params_panel(self, parent: ttk.Frame):
        """构建参数面板"""
        self.app.params_panel.create_widgets(parent)
        self.app.params_panel.get_frame().pack(fill=tk.X, padx=10, pady=5)
    
    def build_nsfw_panel(self, parent: ttk.Frame):
        """构建 NSFW 面板"""
        from gui.components.nsfw_panel import NSFWPanel
        self.app.nsfw_panel = NSFWPanel(parent, self.app)
        self.app.nsfw_panel.get_frame().pack(fill=tk.X, padx=10, pady=5)
    
    def build_tabs(self, parent: ttk.Frame) -> ttk.Notebook:
        """构建标签页"""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        from gui.tabs.txt2img_tab import Txt2ImgTab
        from gui.tabs.img2img_tab import Img2ImgTab
        from gui.tabs.interrogate import InterrogateTab
        from gui.tabs.universal_tab import UniversalTab
        from gui.tabs.scene_tab import SceneTab
        from gui.tabs.janus_tab import JanusTab
        from gui.tabs.grid_test_tab import GridTestTab
        from gui.tabs.pipeline_tab import PipelineTab
        from gui.tabs.lora_manager import LoraManagerTab
        from gui.tabs.chat_tab import ChatTab
        
        self.app.txt2img_tab = Txt2ImgTab(notebook, self.app)
        notebook.add(self.app.txt2img_tab.get_frame(), text="📝 文生图")
        
        self.app.scene_tab = SceneTab(notebook, self.app)
        notebook.add(self.app.scene_tab.get_frame(), text="💑 亲密文生图")
        
        self.app.universal_tab = UniversalTab(notebook, self.app)
        notebook.add(self.app.universal_tab.get_frame(), text="🌍 通用生成器")
        
        self.app.img2img_tab = Img2ImgTab(notebook, self.app)
        notebook.add(self.app.img2img_tab.get_frame(), text="🖼️ 图生图")
        
        self.app.interrogate_tab = InterrogateTab(notebook, self.app)
        notebook.add(self.app.interrogate_tab.get_frame(), text="🔍 图片反推")
        
        self.app.janus_tab = JanusTab(notebook, self.app, self.app.model_manager)
        notebook.add(self.app.janus_tab.get_frame(), text="🤖 Janus-Pro")
        
        self.app.grid_test_tab = GridTestTab(notebook, self.app)
        notebook.add(self.app.grid_test_tab.frame, text="🧪 网格测试")
        
        self.app.pipeline_tab = PipelineTab(notebook, self.app)
        notebook.add(self.app.pipeline_tab.get_frame(), text="🔧 流水线")
        
        self.app.lora_manager_tab = LoraManagerTab(notebook, self.app)
        notebook.add(self.app.lora_manager_tab.get_frame(), text="🔧 LoRA 管理")
        
        self.app.chat_tab = ChatTab(notebook, self.app)
        notebook.add(self.app.chat_tab.get_frame(), text="💬 智能生图")
        
        return notebook
    
    def build_progress_and_preview(self, parent: ttk.Frame):
        """构建进度条和预览"""
        self.app.progress_bar.create_widgets(parent)
        self.app.image_preview.create_widgets(parent)