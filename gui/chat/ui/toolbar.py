# gui/chat/ui/toolbar.py
"""工具栏构建"""

import tkinter as tk
from tkinter import ttk


class ToolbarBuilder:
    """工具栏构建器"""
    
    def __init__(self, tab):
        self.tab = tab
    
    def build(self, parent):
        """构建工具栏"""
        # LoRA 控制
        self._build_lora_controls(parent)
        
        ttk.Separator(parent, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # ControlNet 控制
        self._build_controlnet_controls(parent)
        
        ttk.Separator(parent, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 图片控制
        self._build_image_controls(parent)
        
        # 安全模式
        self._build_safety_controls(parent)
        
        # LLM 测试
        ttk.Button(parent, text="🔧 测试 LLM", command=self.tab._debug_test_llm, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(parent, text="🗑️ 清除对话", command=self.tab._clear_chat, width=12).pack(side=tk.LEFT, padx=2)
        
        # 上传图片
        self.tab.upload_btn = ttk.Button(parent, text="📎 上传图片", command=self.tab._upload_image, width=12)
        self.tab.upload_btn.pack(side=tk.LEFT, padx=2)
        
        self.tab.preview_label = ttk.Label(parent)
        self.tab.preview_label.pack(side=tk.LEFT, padx=5)
    
    def _build_lora_controls(self, parent):
        """构建 LoRA 控制"""
        lora_frame = ttk.Frame(parent)
        lora_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(lora_frame, text="🔗 LoRA:").pack(side=tk.LEFT, padx=2)

        lora_files = self.tab.lora_manager.scan_files()
        self.tab.lora_combo = ttk.Combobox(
            lora_frame,
            textvariable=self.tab.lora_var,
            values=lora_files,
            width=25,
            state="readonly"
        )
        self.tab.lora_combo.pack(side=tk.LEFT, padx=2)
        self.tab.lora_combo.bind('<<ComboboxSelected>>', self.tab.lora_manager.on_selected)

        self.tab.lora_check = ttk.Checkbutton(
            lora_frame,
            text="启用",
            variable=self.tab.lora_enabled_var,
            command=self.tab.lora_manager.toggle
        )
        self.tab.lora_check.pack(side=tk.LEFT, padx=5)

        self.tab.lora_status_label = ttk.Label(
            lora_frame,
            text="🔴 未加载",
            foreground="red",
            font=("", 8)
        )
        self.tab.lora_status_label.pack(side=tk.LEFT, padx=5)

        ttk.Button(lora_frame, text="🔄", width=2, command=self.tab.lora_manager.refresh_list).pack(side=tk.LEFT, padx=2)
    
    def _build_controlnet_controls(self, parent):
        """构建 ControlNet 控制"""
        from utils.controlnet_helper import get_controlnet_display_names
        
        cn_frame = ttk.Frame(parent)
        cn_frame.pack(side=tk.LEFT, padx=5)

        ttk.Checkbutton(
            cn_frame,
            text="🧠 ControlNet",
            variable=self.tab.use_controlnet_var,
            command=self.tab.controlnet_manager.toggle
        ).pack(side=tk.LEFT, padx=2)

        self.tab.controlnet_combo = ttk.Combobox(
            cn_frame,
            textvariable=self.tab.controlnet_type_var,
            values=get_controlnet_display_names(),
            width=20,
            state="readonly"
        )
        self.tab.controlnet_combo.pack(side=tk.LEFT, padx=2)
        self.tab.controlnet_combo.bind('<<ComboboxSelected>>', self.tab.controlnet_manager.on_type_changed)

        self.tab.controlnet_status_label = ttk.Label(
            cn_frame,
            text="",
            foreground="gray",
            font=("", 8)
        )
        self.tab.controlnet_status_label.pack(side=tk.LEFT, padx=2)
    
    def _build_image_controls(self, parent):
        """构建图片控制"""
        ttk.Button(parent, text="🗑️ 清除图片", command=self.tab._clear_upload, width=10).pack(side=tk.LEFT, padx=2)
        self.tab.image_status = ttk.Label(parent, text="", foreground="green")
        self.tab.image_status.pack(side=tk.LEFT, padx=10)
    
    def _build_safety_controls(self, parent):
        """构建安全模式控制"""
        ttk.Separator(parent, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.tab.safe_mode_btn = tk.Button(
            parent,
            text="🛡️ 安全模式",
            command=self.tab._toggle_safe_mode,
            relief="sunken",
            bg="#e8f5e9",
            font=("微软雅黑", 8),
            width=10,
            height=1
        )
        self.tab.safe_mode_btn.pack(side=tk.LEFT, padx=5)

        self.tab.safe_mode_label = ttk.Label(
            parent,
            text="🟢 已启用",
            foreground="green",
            font=("", 8)
        )
        self.tab.safe_mode_label.pack(side=tk.LEFT, padx=2)