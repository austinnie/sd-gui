# gui/chat/ui/param_bar.py
"""参数栏构建"""

import tkinter as tk
from tkinter import ttk


class ParamBarBuilder:
    """参数栏构建器"""
    
    def __init__(self, tab):
        self.tab = tab
    
    def build(self, parent):
        """构建参数栏"""
        self._build_steps_controls(parent)
        self._build_cfg_controls(parent)
        self._build_mode_selector(parent)
        self._build_llm_toggle(parent)
    
    def _build_steps_controls(self, parent):
        """构建步数控制"""
        ttk.Label(parent, text="步数:").pack(side=tk.LEFT, padx=5)

        self.tab.steps_spinbox = ttk.Spinbox(
            parent,
            from_=4,
            to=50,
            textvariable=self.tab.chat_steps_var,
            width=5,
            increment=1
        )
        self.tab.steps_spinbox.pack(side=tk.LEFT, padx=2)

        for steps in [8, 12, 20, 30]:
            ttk.Button(parent, text=str(steps), width=3,
                      command=lambda s=steps: self.tab.chat_steps_var.set(s)).pack(side=tk.LEFT, padx=1)
    
    def _build_cfg_controls(self, parent):
        """构建 CFG 控制"""
        ttk.Label(parent, text="CFG:").pack(side=tk.LEFT, padx=15)

        self.tab.cfg_spinbox = ttk.Spinbox(
            parent,
            from_=1.0,
            to=20.0,
            textvariable=self.tab.chat_cfg_var,
            width=5,
            increment=0.5
        )
        self.tab.cfg_spinbox.pack(side=tk.LEFT, padx=2)

        for cfg in [5, 7, 7.5, 9]:
            ttk.Button(parent, text=str(cfg), width=3,
                      command=lambda c=cfg: self.tab.chat_cfg_var.set(c)).pack(side=tk.LEFT, padx=1)

        ttk.Label(parent, text="💡 步数越高质量越好", foreground="gray", font=("", 8)).pack(side=tk.LEFT, padx=15)
    
    def _build_mode_selector(self, parent):
        """构建模式选择器"""
        ttk.Separator(parent, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        mode_frame = ttk.Frame(parent)
        mode_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(mode_frame, text="模式:", font=("", 9)).pack(side=tk.LEFT)

        for mode, label, bg in [
            ("快速", "⚡ 快速", "#e8f5e9"),
            ("平衡", "⚖️ 平衡", "#e3f2fd"),
            ("高质量", "🌟 高质量", "#fff3e0"),
            ("超高质量", "🌟 超高质量", "#fce4ec")
        ]:
            btn = tk.Button(
                mode_frame,
                text=label,
                command=lambda m=mode: self.tab._set_quality_mode(m),
                relief="sunken" if self.tab.quality_mode_var.get() == mode else "raised",
                bg=bg if self.tab.quality_mode_var.get() == mode else "#f5f5f5",
                font=("微软雅黑", 8),
                width=6,
                height=1
            )
            setattr(self.tab, f"_{mode}_btn", btn)

        self.tab.mode_hint = ttk.Label(parent, text="⚡ 快速模式", foreground="green", font=("", 8))
        self.tab.mode_hint.pack(side=tk.LEFT, padx=10)
    
    def _build_llm_toggle(self, parent):
        """构建 LLM 开关"""
        ttk.Separator(parent, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.tab.llm_check = ttk.Checkbutton(
            parent,
            text="🧠 LLM增强",
            variable=self.tab.llm_enabled_var,
            command=self.tab._on_llm_toggle
        )
        self.tab.llm_check.pack(side=tk.LEFT, padx=5)

        self.tab.llm_install_btn = ttk.Button(
            parent,
            text="📦 安装 LLM",
            command=self.tab._manual_install_llm,
            width=10
        )
        self.tab.llm_install_btn.pack(side=tk.LEFT, padx=5)

        self.tab.llm_status = ttk.Label(parent, text="●", foreground="gray", font=("", 10))
        self.tab.llm_status.pack(side=tk.LEFT, padx=2)