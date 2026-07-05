# gui/tabs/janus_tab_v2.py
"""
Janus-Pro 独立界面 - 支持理解/生成/对话三种模式
动态切换模式，统一界面布局
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import datetime
from PIL import Image, ImageTk

from .base_tab import BaseTab
from core.janus import janus_loader, janus_understand, janus_generate, janus_chat
from config.app_config import app_config


class JanusTabV2(BaseTab):
    """Janus-Pro 多功能标签页 - 独立界面"""
    
    MODES = [
        ("understand", "🧠 理解模式", "图生文 - 分析图片"),
        ("generate", "🎨 生成模式", "文生图 - 生成图片"),
        ("chat", "💬 对话模式", "文生文 - 互动聊天"),
    ]
    
    def __init__(self, parent, app, model_manager):
        super().__init__(parent, app)
        self.model_manager = model_manager
        self._image_path = None
        self._is_generating = False
        self._cancel = False
        
        self._init_vars()
        self.setup_ui()
        self._update_ui_state()
    
    def _init_vars(self):
        self.model_var = tk.StringVar(value="1B")
        self.mode_var = tk.StringVar(value="understand")
        self.temperature_var = tk.DoubleVar(value=0.7)
        self.max_tokens_var = tk.IntVar(value=256)
        self.image_path_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="就绪")
        self.progress_var = tk.DoubleVar(value=0.0)
        
        self.default_question = "请描述这张图片中的人物，包括：性别、年龄、发型、服装、表情、背景、光线、氛围。用中文回答。"
        self.chat_history = []
    
    def setup_ui(self):
        frame = self.frame
        row = 0
        
        # ===== 标题 =====
        title = ttk.Label(frame, text="🤖 Janus-Pro 多功能", font=("", 13, "bold"))
        title.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5, padx=5)
        row += 1
        
        # ===== 模型状态栏 =====
        status_frame = ttk.Frame(frame)
        status_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(status_frame, text="模型:").pack(side=tk.LEFT, padx=5)
        
        self.model_combo = ttk.Combobox(
            status_frame,
            textvariable=self.model_var,
            values=["1B (快速, ~4GB)", "7B (高质量, ~15GB)"],
            width=20,
            state="readonly"
        )
        self.model_combo.pack(side=tk.LEFT, padx=5)
        self.model_combo.bind('<<ComboboxSelected>>', self._on_model_changed)
        
        self.model_status = ttk.Label(status_frame, text="🔴 未加载", foreground="red")
        self.model_status.pack(side=tk.LEFT, padx=15)
        
        self.load_btn = ttk.Button(status_frame, text="📦 加载模型", command=self._load_model)
        self.load_btn.pack(side=tk.LEFT, padx=2)
        
        self.unload_btn = ttk.Button(status_frame, text="🔄 卸载", command=self._unload_model, state=tk.DISABLED)
        self.unload_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(status_frame, text="💡 与 SD 互斥", foreground="orange", font=("", 8)).pack(side=tk.LEFT, padx=15)
        row += 1
        
        # ===== 模式切换 =====
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(mode_frame, text="模式:").pack(side=tk.LEFT, padx=5)
        
        self.mode_btns = {}
        for i, (mode_key, mode_label, mode_tip) in enumerate(self.MODES):
            btn = ttk.Button(
                mode_frame,
                text=mode_label,
                command=lambda k=mode_key: self._switch_mode(k),
                width=14
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.mode_btns[mode_key] = btn
        
        ttk.Label(mode_frame, textvariable=self.mode_tip_var, foreground="gray", font=("", 8)).pack(side=tk.LEFT, padx=10)
        row += 1
        
        # ===== 参数栏 =====
        param_frame = ttk.LabelFrame(frame, text="⚙️ 参数", padding=5)
        param_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(param_frame, text="温度:").pack(side=tk.LEFT, padx=5)
        scale = ttk.Scale(
            param_frame,
            from_=0.1, to=2.0,
            variable=self.temperature_var,
            orient=tk.HORIZONTAL,
            length=120
        )
        scale.pack(side=tk.LEFT, padx=5)
        self.temp_label = ttk.Label(param_frame, text="0.7", width=4)
        self.temp_label.pack(side=tk.LEFT, padx=5)
        self.temperature_var.trace('w', lambda *_: self.temp_label.config(text=f"{self.temperature_var.get():.1f}"))
        
        ttk.Label(param_frame, text="最大Token:").pack(side=tk.LEFT, padx=15)
        ttk.Spinbox(
            param_frame,
            from_=64, to=2048,
            textvariable=self.max_tokens_var,
            width=6,
            increment=64
        ).pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # ===== 内容容器（动态切换） =====
        self.content_frame = ttk.Frame(frame)
        self.content_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        
        # ===== 底部控制栏 =====
        bottom_frame = ttk.Frame(frame)
        bottom_frame.grid(row=row+1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.action_btn = ttk.Button(bottom_frame, text="🚀 执行", command=self._execute_action, state=tk.DISABLED)
        self.action_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(bottom_frame, text="⏹️ 取消", command=self._cancel_action, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(bottom_frame, text="📁 保存结果", command=self._save_result).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="🗑️ 清空", command=self._clear_content).pack(side=tk.LEFT, padx=5)
        
        row += 2
        
        # ===== 进度条 =====
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        self.status_label = ttk.Label(frame, textvariable=self.status_var, foreground="blue")
        self.status_label.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5, padx=5)
        row += 1
        
        # ===== 初始构建 =====
        self._build_understand_mode()
        self._update_ui_state()
        
        # 设置行权重，让内容区域可扩展
        frame.rowconfigure(row-3, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=1)
    
    def _switch_mode(self, mode_key: str):
        """切换模式"""
        self.mode_var.set(mode_key)
        self._clear_content()
        
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
        """清空内容区域"""
        for child in self.content_frame.winfo_children():
            child.destroy()
    
    # ==================== 理解模式 UI ====================
    
    def _build_understand_mode(self):
        """构建理解模式 UI"""
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
        
        # 结果
        result_frame = ttk.LabelFrame(self.content_frame, text="📝 分析结果", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        
        self.result_text = tk.Text(result_frame, height=8, width=70, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=2)
    
    # ==================== 生成模式 UI ====================
    
    def _build_generate_mode(self):
        """构建生成模式 UI"""
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
        
        # 快速示例
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
        
        # 结果
        result_frame = ttk.LabelFrame(self.content_frame, text="🖼️ 生成结果", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        
        self.result_text = tk.Text(result_frame, height=8, width=70, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=2)
        self.result_text.insert("1.0", "💡 输入提示词后点击「生成图片」\n⚠️ Janus 文生图质量有限，建议使用 SD 文生图")
    
    # ==================== 对话模式 UI ====================
    
    def _build_chat_mode(self):
        """构建对话模式 UI"""
        # 对话历史
        history_frame = ttk.LabelFrame(self.content_frame, text="💬 对话历史", padding=5)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        
        self.chat_text = tk.Text(history_frame, height=10, width=70, wrap=tk.WORD)
        self.chat_text.pack(fill=tk.BOTH, expand=True, pady=2)
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
            self.load_btn.config(state=tk.DISABLED, text="📦 已加载")
            self.unload_btn.config(state=tk.NORMAL)
            self.action_btn.config(state=tk.NORMAL)
        elif loading:
            self.model_status.config(text="🟡 加载中...", foreground="orange")
            self.load_btn.config(state=tk.DISABLED, text="⏳ 加载中")
            self.unload_btn.config(state=tk.DISABLED)
            self.action_btn.config(state=tk.DISABLED)
        else:
            self.model_status.config(text="🔴 未加载", foreground="red")
            self.load_btn.config(state=tk.NORMAL, text="📦 加载模型")
            self.unload_btn.config(state=tk.DISABLED)
            self.action_btn.config(state=tk.DISABLED)
        
        # 更新主界面状态
        if self.app:
            self.app._update_model_ui()
    
    def _on_model_changed(self, event):
        """模型切换"""
        if janus_loader.is_loaded():
            current = janus_loader.get_current_model()
            new_key = "1B" if "1B" in self.model_var.get() else "7B"
            if current != new_key:
                if messagebox.askyesno("切换模型", f"当前已加载 {current}，是否切换到 {new_key}？"):
                    self._load_model()
                else:
                    self.model_var.set(f"{current} (快速, ~4GB)" if current == "1B" else "7B (高质量, ~15GB)")
    
    def _load_model(self):
        """加载模型"""
        if janus_loader.is_loading():
            return
        
        # 检查是否与 SD 互斥
        if self.model_manager and self.model_manager.is_sd_loaded:
            if not messagebox.askyesno("切换模型", "加载 Janus 将自动卸载 SD 模型，继续吗？"):
                return
        
        self._update_ui_state()
        self.status_var.set("📦 正在加载 Janus 模型...")
        
        def load_thread():
            def progress_cb(value, msg):
                self.app.root.after(0, lambda: self._update_progress(value, msg))
            
            model_key = "1B" if "1B" in self.model_var.get() else "7B"
            success = janus_loader.load(model_name=model_key, progress_callback=progress_cb)
            self.app.root.after(0, lambda: self._on_load_complete(success))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def _on_load_complete(self, success: bool):
        self._update_ui_state()
        if success:
            self.status_var.set("✅ Janus 模型加载完成")
            if self.model_manager:
                self.model_manager._janus_loaded = True
                self.model_manager._current_type = type('ModelType', (), {'JANUS': 'janus'})()
                self.model_manager._current_type = 'janus'
                self.app._update_model_ui()
        else:
            self.status_var.set("❌ 模型加载失败")
            messagebox.showerror("错误", "Janus 模型加载失败，请查看控制台")
    
    def _unload_model(self):
        """卸载模型"""
        if not janus_loader.is_loaded():
            return
        if messagebox.askyesno("确认", "确定要卸载 Janus 模型吗？"):
            janus_loader.unload()
            if self.model_manager:
                self.model_manager._janus_loaded = False
                self.model_manager._current_type = 'none'
                self.app._update_model_ui()
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
    
    # ==================== 理解模式执行 ====================
    
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
                self.app.root.after(0, lambda: self._update_progress(value, msg))
            
            result = janus_understand.analyze(
                image_path=self._image_path,
                question=self.question_text.get("1.0", tk.END).strip(),
                temperature=self.temperature_var.get(),
                max_tokens=self.max_tokens_var.get(),
                progress_callback=progress_cb
            )
            self.app.root.after(0, lambda: self._on_operation_complete(result))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.app.root.after(0, lambda: self._on_operation_error(str(e)))
    
    # ==================== 生成模式执行 ====================
    
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
                self.app.root.after(0, lambda: self._update_progress(value, msg))
            
            image, metadata = janus_generate.generate(
                prompt=prompt,
                negative_prompt=negative,
                temperature=self.temperature_var.get(),
                max_new_tokens=self.max_tokens_var.get(),
                progress_callback=progress_cb
            )
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_janus_gen.png"
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            image.save(filepath)
            
            self.app.root.after(0, lambda: self.app.add_to_preview(filepath, image))
            self.app.root.after(0, lambda: self._on_operation_complete(
                f"✅ 图片已生成\n📁 保存到: {filepath}\n⏱️ 耗时: {metadata.get('elapsed', 0):.1f}秒\n\n💡 Janus 文生图质量有限，建议使用 SD 文生图"
            ))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.app.root.after(0, lambda: self._on_operation_error(str(e)))
    
    # ==================== 对话模式执行 ====================
    
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
                self.app.root.after(0, lambda: self._update_progress(value, msg))
            
            reply, metadata = janus_chat.chat(
                user_input=user_input,
                temperature=self.temperature_var.get(),
                max_new_tokens=self.max_tokens_var.get(),
                progress_callback=progress_cb
            )
            
            self.app.root.after(0, lambda: self._append_chat(f"🤖 Janus: {reply}\n\n"))
            self.app.root.after(0, lambda: self._on_operation_complete("✅ 对话完成"))
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            self.app.root.after(0, lambda: self._append_chat(f"❌ 错误: {error_msg}\n\n"))
            self.app.root.after(0, lambda: self._on_operation_error(error_msg))
    
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
    
    def get_frame(self):
        return self.frame