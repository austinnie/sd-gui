# gui/components/nsfw_panel.py
"""
NSFW 控制面板组件
"""

import tkinter as tk
from tkinter import ttk
from config.nsfw_config import NSFWConfig, ContentLevel, nsfw_config
from core.nsfw_filter import nsfw_filter


class NSFWPanel:
    """NSFW 控制面板"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = None
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        self.frame = ttk.LabelFrame(self.parent, text="🔞 NSFW 内容控制", padding=5)
        
        # 主开关
        self.enabled_var = tk.BooleanVar(value=nsfw_config.enabled)
        ttk.Checkbutton(
            self.frame,
            text="启用 NSFW 控制",
            variable=self.enabled_var,
            command=self._on_enabled_changed
        ).pack(side=tk.LEFT, padx=5)
        
        # 等级选择
        ttk.Label(self.frame, text="等级:").pack(side=tk.LEFT, padx=10)
        
        self.level_var = tk.StringVar(value=nsfw_config.level.value)
        level_combo = ttk.Combobox(
            self.frame,
            textvariable=self.level_var,
            values=["safe", "suggestive", "explicit", "extreme"],
            width=10,
            state="readonly"
        )
        level_combo.pack(side=tk.LEFT, padx=5)
        level_combo.bind('<<ComboboxSelected>>', self._on_level_changed)
        
        # 状态显示
        self.status_label = ttk.Label(
            self.frame,
            text=nsfw_filter.get_level_description(),
            foreground="blue",
            font=("", 8)
        )
        self.status_label.pack(side=tk.LEFT, padx=15)
        
        # 额外选项
        self.auto_detect_var = tk.BooleanVar(value=nsfw_config.auto_detect)
        ttk.Checkbutton(
            self.frame,
            text="自动检测",
            variable=self.auto_detect_var,
            command=self._on_auto_detect_changed
        ).pack(side=tk.LEFT, padx=5)
        
        self.filter_var = tk.BooleanVar(value=nsfw_config.filter_keywords)
        ttk.Checkbutton(
            self.frame,
            text="关键词过滤",
            variable=self.filter_var,
            command=self._on_filter_changed
        ).pack(side=tk.LEFT, padx=5)
        
        # 保存按钮
        ttk.Button(
            self.frame,
            text="💾 保存设置",
            command=self._save_config
        ).pack(side=tk.RIGHT, padx=5)
    
    def _on_enabled_changed(self):
        """主开关变化"""
        nsfw_config.enabled = self.enabled_var.get()
        self._update_status()
    
    def _on_level_changed(self, event):
        """等级变化"""
        level_map = {
            "safe": ContentLevel.SAFE,
            "suggestive": ContentLevel.SUGGESTIVE,
            "explicit": ContentLevel.EXPLICIT,
            "extreme": ContentLevel.EXTREME
        }
        nsfw_config.level = level_map.get(self.level_var.get(), ContentLevel.SAFE)
        self._update_status()
    
    def _on_auto_detect_changed(self):
        """自动检测变化"""
        nsfw_config.auto_detect = self.auto_detect_var.get()
    
    def _on_filter_changed(self):
        """过滤变化"""
        nsfw_config.filter_keywords = self.filter_var.get()
    
    def _update_status(self):
        """更新状态显示"""
        self.status_label.config(text=nsfw_filter.get_level_description())
        
        # 更新颜色
        level = nsfw_config.level
        if level == ContentLevel.SAFE:
            self.status_label.config(foreground="green")
        elif level == ContentLevel.SUGGESTIVE:
            self.status_label.config(foreground="orange")
        else:
            self.status_label.config(foreground="red")
    
    def _save_config(self):
        """保存配置"""
        nsfw_config.save()
        self.app.update_status("✅ NSFW 配置已保存")
    
    def get_frame(self):
        return self.frame