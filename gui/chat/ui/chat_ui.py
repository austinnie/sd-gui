# gui/chat/ui/chat_ui.py
"""聊天界面主 UI 构建"""

import tkinter as tk
from tkinter import ttk

from .toolbar import ToolbarBuilder
from .param_bar import ParamBarBuilder


class ChatUI:
    """聊天界面构建器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.frame = tab.frame
    
    def build(self):
        """构建完整 UI"""
        self._build_main_container()
        self._build_toolbar()
        self._build_param_bar()
        self._build_chat_area()
        self._build_input_area()
        self._build_status_bar()
        self._bind_shortcuts()
    
    def _build_main_container(self):
        """构建主容器"""
        self.main_frame = ttk.Frame(self.frame)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _build_toolbar(self):
        """构建工具栏"""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, pady=2)
        ToolbarBuilder(self.tab).build(toolbar)
        self.toolbar = toolbar
    
    def _build_param_bar(self):
        """构建参数栏"""
        param_bar = ttk.Frame(self.main_frame)
        param_bar.pack(fill=tk.X, pady=2)
        ParamBarBuilder(self.tab).build(param_bar)
        self.param_bar = param_bar
    
    def _build_chat_area(self):
        """构建对话区域"""
        container = ttk.Frame(self.main_frame)
        container.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tab.chat_text = tk.Text(
            container,
            height=20,
            wrap=tk.WORD,
            font=("微软雅黑", 10),
            bg="#f5f5f5",
            relief="flat",
            padx=10,
            pady=10
        )
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tab.chat_text.yview)
        self.tab.chat_text.configure(yscrollcommand=scrollbar.set)

        self.tab.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tab.chat_text.config(state=tk.DISABLED)
    
    def _build_input_area(self):
        """构建底部输入区"""
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X, pady=5)

        self.tab.input_text = tk.Text(
            input_frame,
            height=4,
            wrap=tk.WORD,
            font=("微软雅黑", 10),
            relief="sunken",
            borderwidth=1
        )
        self.tab.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        self.tab.send_btn = tk.Button(
            btn_frame,
            text="🚀 发送\n(Ctrl+Enter)",
            command=self.tab._on_send,
            width=12,
            height=2,
            relief="raised",
            bg="#e3f2fd",
            font=("微软雅黑", 9)
        )
        self.tab.send_btn.pack(side=tk.TOP, pady=2)

        self.tab.cancel_btn = tk.Button(
            btn_frame,
            text="⏹️ 取消",
            command=self.tab._cancel_generation,
            state=tk.DISABLED,
            width=12,
            height=1,
            relief="raised",
            font=("微软雅黑", 9)
        )
        self.tab.cancel_btn.pack(side=tk.TOP, pady=2)
    
    def _build_status_bar(self):
        """构建状态栏"""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, pady=2)

        self.tab.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.tab.status_var, foreground="blue").pack(side=tk.LEFT)

        self.tab.progress_bar = ttk.Progressbar(status_frame, length=200, mode='determinate')
        self.tab.progress_bar.pack(side=tk.RIGHT, padx=5)
    
    def _bind_shortcuts(self):
        """绑定快捷键"""
        self.tab.input_text.bind("<Control-Return>", self.tab._on_send)
        self.tab.input_text.bind("<Return>", self.tab._on_send_shift_check)