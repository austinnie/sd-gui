#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Janus-Pro 独立版 - 纯 Janus 功能
使用独立配置 janus_config.json
支持热重载: Ctrl+R
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import datetime
from PIL import Image, ImageTk

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 使用独立配置
from config.janus_config import janus_config

# 从 core.janus 导入核心模块
from core.janus import janus_loader, janus_understand, janus_generate, janus_chat


class JanusStandalone:
    """Janus-Pro 独立版 - 支持热重载"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 Janus-Pro 独立版")
        
        # 从配置读取窗口大小
        self.root.geometry(f"{janus_config.ui.window_width}x{janus_config.ui.window_height}")
        self.root.minsize(700, 600)

        # 状态变量
        self._image_path = None
        self._is_generating = False
        self._cancel = False
        self.chat_history = []

        # 模块缓存（用于热重载）
        self._janus_loader = None
        self._janus_understand = None
        self._janus_generate = None
        self._janus_chat = None

        self._init_vars()
        self._setup_menu()
        self._setup_ui()
        
        # 加载模块
        self._load_modules()
        self._update_ui_state()

        # 绑定热键
        self.root.bind("<Control-r>", lambda e: self._reload_modules())
        self.root.bind("<Control-R>", lambda e: self._reload_modules())
        self.root.bind("<Control-o>", lambda e: self._select_image())
        self.root.bind("<Control-O>", lambda e: self._select_image())
        self.root.bind("<Control-s>", lambda e: self._save_result())
        self.root.bind("<Control-S>", lambda e: self._save_result())

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _load_modules(self):
        """加载 Janus 模块"""
        self._janus_loader = janus_loader
        self._janus_understand = janus_understand
        self._janus_generate = janus_generate
        self._janus_chat = janus_chat

    def _init_vars(self):
        self.model_var = tk.StringVar(value="1B")
        self.mode_var = tk.StringVar(value="understand")
        self.temperature_var = tk.DoubleVar(value=janus_config.janus.temperature)
        self.max_tokens_var = tk.IntVar(value=janus_config.janus.max_tokens)
        self.image_path_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="就绪")
        self.progress_var = tk.DoubleVar(value=0.0)

        self.default_question = "请描述这张图片中的人物，包括：性别、年龄、发型、服装、表情、背景、光线、氛围。用中文回答。"

    def _reload_modules(self):
        """热重载所有模块"""
        import importlib

        self.status_var.set("🔄 正在重载模块...")
        self.root.update_idletasks()

        try:
            # 要重载的模块列表（只保留 Janus 相关）
            modules_to_reload = [
                "core.janus",
                "core.janus.loader",
                "core.janus.understand",
                "core.janus.generate",
                "core.janus.chat",
                "config.janus_config",
            ]

            reloaded = []
            failed = []

            for mod_name in modules_to_reload:
                try:
                    if mod_name in sys.modules:
                        importlib.reload(sys.modules[mod_name])
                        reloaded.append(mod_name)
                        print(f"   ✅ 重载: {mod_name}")
                except Exception as e:
                    print(f"   ❌ 重载失败 {mod_name}: {e}")
                    failed.append(mod_name)

            # 重新导入模块
            from core.janus import janus_loader, janus_understand, janus_generate, janus_chat
            from config.janus_config import janus_config

            self._janus_loader = janus_loader
            self._janus_understand = janus_understand
            self._janus_generate = janus_generate
            self._janus_chat = janus_chat

            # 更新 UI 状态
            self._update_ui_state()

            if failed:
                self.status_var.set(f"⚠️ 重载完成，{len(failed)} 个模块失败")
            else:
                self.status_var.set(f"✅ 热重载完成！已重载 {len(reloaded)} 个模块")

            # 显示提示到结果框
            if hasattr(self, 'result_text') and self.result_text.winfo_exists():
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0",
                    f"✅ 热重载完成！\n"
                    f"已重载 {len(reloaded)} 个模块\n"
                    f"时间: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    f"💡 修改代码后按 Ctrl+R 即可重载"
                )

            print(f"✅ 热重载完成！已重载 {len(reloaded)} 个模块")

        except Exception as e:
            self.status_var.set(f"❌ 重载失败: {e}")
            print(f"❌ 热重载失败: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("重载失败", str(e))
        
    def _setup_menu(self):
        """菜单栏"""
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开图片 (Ctrl+O)", command=self._select_image)
        file_menu.add_separator()
        file_menu.add_command(label="保存结果 (Ctrl+S)", command=self._save_result)
        file_menu.add_separator()
        file_menu.add_command(label="退出 (Ctrl+W)", command=self._on_close)
        menubar.add_cascade(label="文件", menu=file_menu)

        model_menu = tk.Menu(menubar, tearoff=0)
        model_menu.add_command(label="加载 1B 模型", command=lambda: self._load_model("1B"))
        model_menu.add_command(label="加载 7B 模型", command=lambda: self._load_model("7B"))
        model_menu.add_separator()
        model_menu.add_command(label="卸载模型", command=self._unload_model)
        menubar.add_cascade(label="模型", menu=model_menu)

        # 开发菜单 - 热重载
        dev_menu = tk.Menu(menubar, tearoff=0)
        dev_menu.add_command(label="🔄 热重载模块 (Ctrl+R)", command=self._reload_modules)
        dev_menu.add_command(label="🔄 重载并重置界面", command=self._reload_and_reset)
        menubar.add_cascade(label="开发", menu=dev_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="快捷键", command=self._show_shortcuts)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.root.config(menu=menubar)

    def _reload_and_reset(self):
        """重载模块并重置界面"""
        self._clear_content()
        mode = self.mode_var.get()
        if mode == "understand":
            self._build_understand_mode()
        elif mode == "generate":
            self._build_generate_mode()
        elif mode == "chat":
            self._build_chat_mode()
        self._reload_modules()

    def _show_shortcuts(self):
        messagebox.showinfo(
            "快捷键",
            "⌨️ Janus-Pro 独立版 快捷键\n\n"
            "Ctrl+R         热重载模块\n"
            "Ctrl+Enter     发送消息 (对话模式)\n"
            "Ctrl+O         打开图片 (理解模式)\n"
            "Ctrl+S         保存结果\n"
            "Ctrl+W         关闭窗口\n"
        )

    def _setup_ui(self):
        """主界面 - 带滚动条"""
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient=tk.VERTICAL, command=canvas.yview)

        main_frame = ttk.Frame(canvas)
        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=main_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_mousewheel_win(event):
            canvas.yview_scroll(int(-1 * event.delta), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel_win)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        self._canvas = canvas
        self._main_frame = main_frame

        # ===== 标题 =====
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(title_frame, text="🤖 Janus-Pro 独立版", font=("", 16, "bold")).pack(side=tk.LEFT)
        ttk.Label(title_frame, text="多模态理解与生成 | Ctrl+R 热重载", font=("", 9), foreground="gray").pack(side=tk.LEFT, padx=10)

        # ===== 控制面板 =====
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
        control_frame.pack(fill=tk.X, pady=5)

        # 模型行
        model_row = ttk.Frame(control_frame)
        model_row.pack(fill=tk.X, pady=2)

        ttk.Label(model_row, text="模型:").pack(side=tk.LEFT, padx=5)

        self.model_combo = ttk.Combobox(
            model_row,
            textvariable=self.model_var,
            values=["1B (快速, ~4GB)", "7B (高质量, ~15GB)"],
            width=18,
            state="readonly"
        )
        self.model_combo.pack(side=tk.LEFT, padx=5)
        self.model_combo.bind('<<ComboboxSelected>>', self._on_model_changed)

        self.model_status = ttk.Label(model_row, text="🔴 未加载", foreground="red")
        self.model_status.pack(side=tk.LEFT, padx=10)

        self.load_btn = ttk.Button(model_row, text="📦 加载", command=self._load_model, width=8)
        self.load_btn.pack(side=tk.LEFT, padx=2)

        self.unload_btn = ttk.Button(model_row, text="🔄 卸载", command=self._unload_model, width=8, state=tk.DISABLED)
        self.unload_btn.pack(side=tk.LEFT, padx=2)

        # 模式行
        mode_row = ttk.Frame(control_frame)
        mode_row.pack(fill=tk.X, pady=5)

        ttk.Label(mode_row, text="模式:").pack(side=tk.LEFT, padx=5)

        self.mode_btns = {}
        for key, label, tip in [
            ("understand", "🧠 理解", "图生文"),
            ("generate", "🎨 生成", "文生图"),
            ("chat", "💬 对话", "文生文")
        ]:
            btn = ttk.Button(
                mode_row,
                text=label,
                command=lambda k=key: self._switch_mode(k),
                width=10
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.mode_btns[key] = btn

        self.mode_tip = ttk.Label(mode_row, text="图生文 - 上传图片分析", foreground="gray", font=("", 8))
        self.mode_tip.pack(side=tk.LEFT, padx=15)

        # 参数行
        param_row = ttk.Frame(control_frame)
        param_row.pack(fill=tk.X, pady=5)

        ttk.Label(param_row, text="温度:").pack(side=tk.LEFT, padx=5)
        scale = ttk.Scale(
            param_row,
            from_=0.1, to=2.0,
            variable=self.temperature_var,
            orient=tk.HORIZONTAL,
            length=120
        )
        scale.pack(side=tk.LEFT, padx=5)
        self.temp_label = ttk.Label(param_row, text=f"{self.temperature_var.get():.1f}", width=4)
        self.temp_label.pack(side=tk.LEFT, padx=5)
        self.temperature_var.trace('w', lambda *_: self.temp_label.config(text=f"{self.temperature_var.get():.1f}"))

        ttk.Label(param_row, text="最大Token:").pack(side=tk.LEFT, padx=15)
        ttk.Spinbox(
            param_row,
            from_=64, to=2048,
            textvariable=self.max_tokens_var,
            width=6,
            increment=64
        ).pack(side=tk.LEFT, padx=5)

        # ===== 内容区域 =====
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self._build_understand_mode()

        # ===== 底部控制 =====
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=5)

        self.action_btn = ttk.Button(bottom_frame, text="🚀 执行", command=self._execute_action, state=tk.DISABLED, width=12)
        self.action_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_btn = ttk.Button(bottom_frame, text="⏹️ 取消", command=self._cancel_action, state=tk.DISABLED, width=12)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(bottom_frame, text="📁 保存结果", command=self._save_result, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="🗑️ 清空", command=self._clear_content, width=12).pack(side=tk.LEFT, padx=5)

        # ===== 进度 =====
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.pack(fill=tk.X, pady=2)

        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(anchor=tk.W, pady=2)

        # ===== 状态栏 =====
        status_bar = ttk.Frame(main_frame)
        status_bar.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(status_bar, text="💡 Ctrl+R 热重载 | Ctrl+O 打开图片 | 加载模型后即可使用", foreground="gray", font=("", 8)).pack(side=tk.LEFT)

        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    # ==================== 模式构建 ====================

    def _switch_mode(self, mode_key: str):
        """切换模式"""
        self.mode_var.set(mode_key)
        self._clear_content()

        tips = {
            "understand": "图生文 - 上传图片分析",
            "generate": "文生图 - 输入提示词生成",
            "chat": "文生文 - 多轮对话"
        }
        self.mode_tip.config(text=tips.get(mode_key, ""))

        if mode_key == "understand":
            self._build_understand_mode()
            self.action_btn.config(text="🔍 分析图片")
        elif mode_key == "generate":
            self._build_generate_mode()
            self.action_btn.config(text="🎨 生成图片")
        elif mode_key == "chat":
            self._build_chat_mode()
            self.action_btn.config(text="💬 发送")

        self._update_ui_state()

    def _clear_content(self):
        for child in self.content_frame.winfo_children():
            child.destroy()

    def _build_understand_mode(self):
        """理解模式"""
        # 图片上传
        image_frame = ttk.LabelFrame(self.content_frame, text="📷 上传图片", padding=5)
        image_frame.pack(fill=tk.X, pady=2)

        img_row = ttk.Frame(image_frame)
        img_row.pack(fill=tk.X, pady=2)

        ttk.Button(img_row, text="📁 选择图片", command=self._select_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(img_row, text="🗑️ 清除", command=self._clear_image).pack(side=tk.LEFT, padx=5)

        self.img_label = ttk.Label(img_row, textvariable=self.image_path_var, foreground="gray")
        self.img_label.pack(side=tk.LEFT, padx=10)

        self.preview_label = ttk.Label(image_frame)
        self.preview_label.pack(pady=2)

        # 提问
        question_frame = ttk.LabelFrame(self.content_frame, text="❓ 提问", padding=5)
        question_frame.pack(fill=tk.X, pady=2)

        self.question_text = tk.Text(question_frame, height=4, width=70, wrap=tk.WORD)
        self.question_text.pack(fill=tk.BOTH, expand=True, pady=2)
        self.question_text.insert("1.0", self.default_question)

        quick_frame = ttk.Frame(question_frame)
        quick_frame.pack(fill=tk.X, pady=2)

        for text, cmd in [
            ("👤 描述人物", "请描述这张图片中的人物，包括：性别、年龄、发型、服装、表情、背景、光线、氛围。用中文回答。"),
            ("🎨 描述风格", "请描述这张图片的艺术风格、构图、色彩搭配和整体氛围。用中文回答。"),
            ("📝 生成提示词", "请为这张图片生成 Stable Diffusion 文生图的提示词（正面提示词和负面提示词）。用中文回答。"),
            ("🔍 详细分析", "请详细分析这张图片，包括：主体、背景、光线、色彩、构图、情感氛围、可能的故事背景。用中文回答。")
        ]:
            ttk.Button(quick_frame, text=text,
                command=lambda q=cmd: self._set_question(q)
            ).pack(side=tk.LEFT, padx=2)

        # 结果 - 带滚动条
        result_frame = ttk.LabelFrame(self.content_frame, text="📝 分析结果", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        text_frame = ttk.Frame(result_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.result_text = tk.Text(text_frame, height=8, width=70, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)

        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_generate_mode(self):
        """生成模式"""
        prompt_frame = ttk.LabelFrame(self.content_frame, text="📝 提示词", padding=5)
        prompt_frame.pack(fill=tk.X, pady=2)

        ttk.Label(prompt_frame, text="正面提示词:").pack(anchor=tk.W, padx=5)
        self.gen_prompt = tk.Text(prompt_frame, height=4, width=70, wrap=tk.WORD)
        self.gen_prompt.pack(fill=tk.BOTH, expand=True, pady=2)
        self.gen_prompt.insert("1.0", "a beautiful Asian woman, wearing elegant dress, full body shot, natural lighting")

        ttk.Label(prompt_frame, text="负面提示词 (可选):").pack(anchor=tk.W, padx=5)
        self.gen_neg = tk.Text(prompt_frame, height=2, width=70, wrap=tk.WORD)
        self.gen_neg.pack(fill=tk.BOTH, expand=True, pady=2)
        self.gen_neg.insert("1.0", "worst quality, low quality, ugly, deformed, blurry")

        quick_frame = ttk.Frame(prompt_frame)
        quick_frame.pack(fill=tk.X, pady=2)

        for text, prompt in [
            ("🌸 亚洲美女", "a beautiful Asian woman, wearing elegant dress, full body shot, natural lighting, detailed face"),
            ("🏯 日本庭院", "a beautiful Japanese woman in kimono, traditional garden, cherry blossoms, full body, soft sunlight"),
            ("🎨 油画风格", "a beautiful woman, oil painting style, renaissance, masterpiece, detailed, rich colors"),
            ("🌅 风景", "beautiful landscape, mountains, lake, sunset, 8k, photorealistic, highly detailed")
        ]:
            ttk.Button(quick_frame, text=text,
                command=lambda p=prompt: self._set_gen_prompt(p)
            ).pack(side=tk.LEFT, padx=2)

        # 结果 - 带滚动条
        result_frame = ttk.LabelFrame(self.content_frame, text="🖼️ 生成结果", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        text_frame = ttk.Frame(result_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.result_text = tk.Text(text_frame, height=8, width=70, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)

        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.result_text.insert("1.0", "💡 输入提示词后点击「生成图片」\n⚠️ Janus 文生图质量有限，建议使用 SD 文生图")

    def _build_chat_mode(self):
        """对话模式"""
        # 对话历史 - 带滚动条
        history_frame = ttk.LabelFrame(self.content_frame, text="💬 对话历史", padding=5)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        text_frame = ttk.Frame(history_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.chat_text = tk.Text(text_frame, height=10, width=70, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=scrollbar.set)

        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.chat_text.insert("1.0", "🤖 Janus 对话助手\n" + "=" * 40 + "\n\n")
        self.chat_text.config(state=tk.DISABLED)

        # 输入
        input_frame = ttk.LabelFrame(self.content_frame, text="✏️ 输入", padding=5)
        input_frame.pack(fill=tk.X, pady=2)

        self.chat_input = tk.Text(input_frame, height=3, width=70, wrap=tk.WORD)
        self.chat_input.pack(fill=tk.BOTH, expand=True, pady=2)
        self.chat_input.bind("<Control-Return>", lambda e: self._execute_action())

        quick_frame = ttk.Frame(input_frame)
        quick_frame.pack(fill=tk.X, pady=2)

        for text, cmd in [
            ("✍️ 写诗", "请写一首关于春天的五言诗"),
            ("📖 写故事", "请写一个关于爱情的短篇故事，约200字"),
            ("💡 写代码", "请用 Python 写一个快速排序算法"),
            ("🌍 翻译", "请将 'Hello, how are you?' 翻译成中文"),
            ("🗑️ 清空历史", "CLEAR_HISTORY")
        ]:
            ttk.Button(quick_frame, text=text,
                command=lambda q=cmd: self._set_chat_input(q)
            ).pack(side=tk.LEFT, padx=2)

    # ==================== 辅助方法 ====================

    def _set_question(self, question: str):
        if hasattr(self, 'question_text'):
            self.question_text.delete("1.0", tk.END)
            self.question_text.insert("1.0", question)

    def _set_gen_prompt(self, prompt: str):
        if hasattr(self, 'gen_prompt'):
            self.gen_prompt.delete("1.0", tk.END)
            self.gen_prompt.insert("1.0", prompt)

    def _set_chat_input(self, text: str):
        if text == "CLEAR_HISTORY":
            self._clear_chat_history()
            return
        if hasattr(self, 'chat_input'):
            self.chat_input.delete("1.0", tk.END)
            self.chat_input.insert("1.0", text)

    def _clear_chat_history(self):
        janus_chat.clear_history()
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.insert("1.0", "🤖 Janus 对话助手\n" + "=" * 40 + "\n\n")
        self.chat_text.insert(tk.END, "💬 对话历史已清空\n\n")
        self.chat_text.config(state=tk.DISABLED)
        self.status_var.set("🗑️ 对话历史已清空")

    def _select_image(self):
        file = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("所有文件", "*.*")]
        )
        if file:
            self.image_path_var.set(os.path.basename(file))
            self._image_path = file
            try:
                img = Image.open(file)
                img.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(img)
                self.preview_label.config(image=photo)
                self.preview_label.image = photo
            except Exception as e:
                self.preview_label.config(image="")
                self.preview_label.image = None
                messagebox.showwarning("提示", f"无法预览图片: {e}")

    def _clear_image(self):
        self.image_path_var.set("")
        self._image_path = None
        self.preview_label.config(image="")
        self.preview_label.image = None

    # ==================== 模型管理 ====================

    def _update_ui_state(self):
        """更新 UI 状态"""
        loaded = janus_loader.is_loaded()
        loading = janus_loader.is_loading()

        if loaded:
            self.model_status.config(text="🟢 已加载", foreground="green")
            self.load_btn.config(state=tk.DISABLED, text="✅ 已加载")
            self.unload_btn.config(state=tk.NORMAL)
            self.action_btn.config(state=tk.NORMAL)
        elif loading:
            self.model_status.config(text="🟡 加载中...", foreground="orange")
            self.load_btn.config(state=tk.DISABLED, text="⏳ 加载中")
            self.unload_btn.config(state=tk.DISABLED)
            self.action_btn.config(state=tk.DISABLED)
        else:
            self.model_status.config(text="🔴 未加载", foreground="red")
            self.load_btn.config(state=tk.NORMAL, text="📦 加载")
            self.unload_btn.config(state=tk.DISABLED)
            self.action_btn.config(state=tk.DISABLED)

    def _on_model_changed(self, event):
        if janus_loader.is_loaded():
            current = janus_loader.get_current_model()
            new_key = "1B" if "1B" in self.model_var.get() else "7B"
            if current != new_key:
                if messagebox.askyesno("切换模型", f"当前已加载 {current}，是否切换到 {new_key}？"):
                    self._load_model()
                else:
                    self.model_var.set(f"{current} (快速, ~4GB)" if current == "1B" else "7B (高质量, ~15GB)")

    def _load_model(self, model_key=None):
        """加载模型"""
        if janus_loader.is_loading():
            return

        if model_key is None:
            model_key = "1B" if "1B" in self.model_var.get() else "7B"

        self._update_ui_state()
        self.status_var.set(f"📦 正在加载 Janus-{model_key}...")

        def load_thread():
            def progress_cb(value, msg):
                self.root.after(0, lambda: self._update_progress(value, msg))

            success = janus_loader.load(model_name=model_key, progress_callback=progress_cb)
            self.root.after(0, lambda: self._on_load_complete(success))

        threading.Thread(target=load_thread, daemon=True).start()

    def _on_load_complete(self, success: bool):
        self._update_ui_state()
        if success:
            self.status_var.set("✅ Janus 模型加载完成")
        else:
            self.status_var.set("❌ 模型加载失败")
            messagebox.showerror("错误", "Janus 模型加载失败，请查看控制台")

    def _unload_model(self):
        if not janus_loader.is_loaded():
            return
        if messagebox.askyesno("确认", "确定要卸载 Janus 模型吗？"):
            janus_loader.unload()
            self._update_ui_state()
            self.status_var.set("✅ Janus 模型已卸载")

    # ==================== 执行操作 ====================

    def _execute_action(self):
        if self._is_generating:
            return

        if not janus_loader.is_loaded():
            messagebox.showwarning("提示", "请先加载 Janus 模型")
            return

        mode = self.mode_var.get()

        if mode == "understand":
            self._execute_understand()
        elif mode == "generate":
            self._execute_generate()
        elif mode == "chat":
            self._execute_chat()

    def _cancel_action(self):
        self._cancel = True
        self._is_generating = False
        self.status_var.set("⏹️ 已取消")
        self.cancel_btn.config(state=tk.DISABLED)
        self.action_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)

    def _start_operation(self, status: str):
        self._cancel = False
        self._is_generating = True
        self.action_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.status_var.set(status)

    def _update_progress(self, value, msg):
        self.progress_var.set(value * 100)
        self.status_var.set(msg)

    def _on_operation_complete(self, result: str):
        self._is_generating = False
        self.action_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.progress_var.set(100)
        self.status_var.set("✅ 完成")

        if hasattr(self, 'result_text') and self.result_text.winfo_exists():
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", result)

    def _on_operation_error(self, error: str):
        self._is_generating = False
        self.action_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_var.set(f"❌ 错误: {error}")

        if hasattr(self, 'result_text') and self.result_text.winfo_exists():
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", f"❌ 操作失败:\n{error}")

    # ==================== 理解模式 ====================

    def _execute_understand(self):
        if not self._image_path:
            messagebox.showwarning("提示", "请先选择一张图片")
            return

        question = self.question_text.get("1.0", tk.END).strip()
        if not question:
            messagebox.showwarning("提示", "请输入问题")
            return

        self._start_operation("🔍 分析图片...")
        threading.Thread(target=self._run_understand, daemon=True).start()

    def _run_understand(self):
        try:
            def progress_cb(value, msg):
                self.root.after(0, lambda: self._update_progress(value, msg))

            result = janus_understand.analyze(
                image_path=self._image_path,
                question=self.question_text.get("1.0", tk.END).strip(),
                temperature=self.temperature_var.get(),
                max_tokens=self.max_tokens_var.get(),
                progress_callback=progress_cb
            )
            self.root.after(0, lambda: self._on_operation_complete(result))
        except Exception as e:
            error_msg = str(e)  # ✅ 保存到变量
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self._on_operation_error(error_msg))

    # ==================== 生成模式 ====================

    def _execute_generate(self):
        prompt = self.gen_prompt.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("提示", "请输入正面提示词")
            return

        negative = self.gen_neg.get("1.0", tk.END).strip()
        self._start_operation("🎨 生成图片...")
        threading.Thread(target=self._run_generate, args=(prompt, negative), daemon=True).start()

    def _run_generate(self, prompt: str, negative: str):
        try:
            def progress_cb(value, msg):
                self.root.after(0, lambda: self._update_progress(value, msg))

            image, metadata = janus_generate.generate(
                prompt=prompt,
                negative_prompt=negative,
                temperature=self.temperature_var.get(),
                max_new_tokens=self.max_tokens_var.get(),
                progress_callback=progress_cb
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_janus_gen.png"
            output_dir = janus_config.paths.get_resolved_output_dir()  # ✅ 正确
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            image.save(filepath)

            self.root.after(0, lambda: self._on_operation_complete(
                f"✅ 图片已生成\n📁 保存到: {filepath}\n⏱️ 耗时: {metadata.get('elapsed', 0):.1f}秒\n\n💡 Janus 文生图质量有限，建议使用 SD 文生图"
            ))
        except Exception as e:
            error_msg = str(e)  # ✅ 保存错误信息
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self._on_operation_error(error_msg))

    # ==================== 对话模式 ====================

    def _execute_chat(self):
        user_input = self.chat_input.get("1.0", tk.END).strip()
        if not user_input:
            messagebox.showwarning("提示", "请输入消息")
            return

        self._append_chat(f"👤 用户: {user_input}\n")
        self.chat_input.delete("1.0", tk.END)
        self._start_operation("💬 思考中...")
        threading.Thread(target=self._run_chat, args=(user_input,), daemon=True).start()

    def _run_chat(self, user_input: str):
        try:
            def progress_cb(value, msg):
                self.root.after(0, lambda: self._update_progress(value, msg))

            reply, metadata = janus_chat.chat(
                user_input=user_input,
                temperature=self.temperature_var.get(),
                max_new_tokens=self.max_tokens_var.get(),
                progress_callback=progress_cb
            )

            self.root.after(0, lambda: self._append_chat(f"🤖 Janus: {reply}\n\n"))
            self.root.after(0, lambda: self._on_operation_complete("✅ 对话完成"))
        except Exception as e:
            error_msg = str(e)  # ✅ 保存到变量
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            self.root.after(0, lambda: self._append_chat(f"❌ 错误: {error_msg}\n\n"))
            self.root.after(0, lambda: self._on_operation_error(error_msg))

    def _append_chat(self, text: str):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, text)
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)

    # ==================== 保存结果 ====================

    def _save_result(self):
        if not hasattr(self, 'result_text') or not self.result_text.winfo_exists():
            messagebox.showwarning("提示", "没有可保存的结果")
            return

        result = self.result_text.get("1.0", tk.END).strip()
        if not result or result.startswith("⏳") or result.startswith("❌") or result.startswith("💡"):
            messagebox.showwarning("提示", "没有有效的结果可保存")
            return

        filepath = filedialog.asksaveasfilename(
            title="保存结果",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=f"janus_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result)
            messagebox.showinfo("成功", f"已保存到:\n{filepath}")

    # ==================== 其他 ====================

    def _show_about(self):
        messagebox.showinfo(
            "关于 Janus-Pro 独立版",
            "🤖 Janus-Pro 独立版\n\n"
            "版本: 1.0\n\n"
            "功能:\n"
            "  🧠 理解模式 - 图生文 (图片分析)\n"
            "  🎨 生成模式 - 文生图 (图片生成)\n"
            "  💬 对话模式 - 文生文 (智能对话)\n\n"
            "快捷键:\n"
            "  Ctrl+R  热重载模块\n"
            "  Ctrl+O  打开图片\n"
            "  Ctrl+S  保存结果\n"
            "  Ctrl+W  关闭窗口\n\n"
            "基于 DeepSeek Janus-Pro 多模态模型"
        )

    def _on_close(self):
        """关闭窗口"""
        if self._is_generating:
            if not messagebox.askyesno("确认退出", "正在执行操作，确定要退出吗？"):
                return

        # 清理滚轮绑定
        try:
            self._canvas.unbind_all("<MouseWheel>")
            self._canvas.unbind_all("<Button-4>")
            self._canvas.unbind_all("<Button-5>")
        except:
            pass

        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    """主入口"""
    print("=" * 60)
    print("  🤖 Janus-Pro 独立版")
    print("  多模态理解与生成 | Ctrl+R 热重载")
    print("=" * 60)
    print()

    try:
        import torch
        print(f"PyTorch: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
    except:
        print("⚠️ PyTorch 未安装")

    print()
    print("启动独立界面...")
    print("=" * 60)

    app = JanusStandalone()
    app.run()


if __name__ == "__main__":
    main()