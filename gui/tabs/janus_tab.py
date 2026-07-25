#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Janus-Pro 多功能标签页 - 使用 ModelManager 管理模型
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import datetime
from PIL import Image, ImageTk

from .base_tab import BaseTab
from core.janus_analyzer import janus_analyzer
from core.janus_generator import janus_generator
from gui.components.memory_monitor import force_memory_cleanup
from config.app_config import app_config
from core.janus_chat import janus_chat

class JanusTab(BaseTab):
    """Janus-Pro 多功能标签页"""
    
    MODE_OPTIONS = {
        "understand": "🧠 理解模式 (图生文)",
        "generate": "🎨 生成模式 (文生图)",
        "chat": "💬 对话模式 (文生文)"
    }
    
    def __init__(self, parent, app, model_manager):
        super().__init__(parent, app)
        self.model_manager = model_manager
        self.params = self.app.params_panel  # ✅ 添加这行
        self._image_path = None
        self._init_vars()
        self.setup_ui()
        #self._update_model_status()
    
    def _init_vars(self):
        self.model_var = tk.StringVar(value="1B")
        self.mode_var = tk.StringVar(value="understand")
        self.image_path_var = tk.StringVar(value="")
        self.default_question = "请描述这张图片中的人物，包括：性别、年龄、发型、服装、表情、背景、光线、氛围。用中文回答。"
        
        self.cancel_generation = False
        self.is_generating = False
        self.temperature_var = tk.DoubleVar(value=0.8)
        self.max_tokens_var = tk.IntVar(value=512)

        # ✅ 新增：取消回调（用于中断模型执行）
        self._cancel_callbacks = []
        

    # ============================================================
    # ✅ 新增：注册取消回调
    # ============================================================
    def register_cancel_callback(self, callback):
        """注册取消回调函数"""
        if callback not in self._cancel_callbacks:
            self._cancel_callbacks.append(callback)
    
    def _trigger_cancel_callbacks(self):
        """触发所有取消回调"""
        for cb in self._cancel_callbacks:
            try:
                cb()
            except Exception as e:
                print(f"⚠️ 取消回调执行失败: {e}")

    # ============================================================
    # ✅ 修改：取消命令
    # ============================================================
    def cancel_generation_cmd(self):
        """取消生成"""
        self.cancel_generation = True
        self.is_generating = False
        self.status_label.config(text="⏹️ 已取消")
        self.cancel_btn.config(state=tk.DISABLED)
        
        # ✅ 触发取消回调（中断模型执行）
        self._trigger_cancel_callbacks()
        
        # ✅ 如果有模型正在执行，尝试中断
        import core.janus_analyzer
        if hasattr(core.janus_analyzer, 'janus_analyzer'):
            core.janus_analyzer.janus_analyzer._cancel = True
            
    def setup_ui(self):
        # 创建滚动容器
        canvas = tk.Canvas(self.frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 之后所有控件创建在 self.scrollable_frame 上
        frame = self.scrollable_frame  # 替换原来的 self.frame
    
        row = 0
        
        title = ttk.Label(frame, text="🤖 Janus-Pro 多功能", font=("", 12, "bold"))
        title.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5, padx=5)
        row += 1
        
        # ===== 模型状态 =====
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
        self.model_combo.set("1B (快速, ~4GB)")
        self.model_combo.bind('<<ComboboxSelected>>', self._on_model_changed)
        
        self.model_status = ttk.Label(
            status_frame,
            text="🔴 未加载",
            foreground="red"
        )
        self.model_status.pack(side=tk.LEFT, padx=15)
        
        self.load_btn = ttk.Button(
            status_frame,
            text="📦 加载 Janus",
            command=self._load_janus
        )
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        self.unload_btn = ttk.Button(
            status_frame,
            text="🔄 卸载",
            command=self._unload_janus
        )
        self.unload_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            status_frame,
            text="💡 加载 Janus 会自动卸载 SD 模型",
            foreground="orange",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=15)
        row += 1
        
        # ===== 模式选择 =====
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(mode_frame, text="模式:").pack(side=tk.LEFT, padx=5)
        
        self.mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            values=list(self.MODE_OPTIONS.values()),
            width=25,
            state="readonly"
        )
        self.mode_combo.pack(side=tk.LEFT, padx=5)
        self.mode_combo.set(self.MODE_OPTIONS["understand"])
        self.mode_combo.bind('<<ComboboxSelected>>', self._on_mode_changed)
        row += 1
        
        # ===== 内容容器 =====
        self.content_frame = ttk.Frame(frame)
        self.content_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        self._build_understand_mode()
        row += 1
        
        # ===== 参数 =====
        param_frame = ttk.LabelFrame(frame, text="⚙️ 参数", padding=5)
        param_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(param_frame, text="温度:").pack(side=tk.LEFT, padx=5)
        scale = ttk.Scale(
            param_frame,
            from_=0.1, to=2.0,
            variable=self.temperature_var,
            orient=tk.HORIZONTAL,
            length=150
        )
        scale.pack(side=tk.LEFT, padx=5)
        self.temp_label = ttk.Label(param_frame, text="0.8", width=4)
        self.temp_label.pack(side=tk.LEFT, padx=5)
        self.temperature_var.trace('w', lambda *_: self.temp_label.config(
            text=f"{self.temperature_var.get():.1f}"
        ))
        
        ttk.Label(param_frame, text="最大Token:").pack(side=tk.LEFT, padx=15)
        ttk.Spinbox(
            param_frame,
            from_=128, to=4096,
            textvariable=self.max_tokens_var,
            width=6,
            increment=128
        ).pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # ===== 操作按钮 =====
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=10)
        
        self.action_btn = ttk.Button(
            btn_frame,
            text="🚀 执行",
            command=self._execute_action
        )
        self.action_btn.pack(side=tk.LEFT, padx=10)
        
        self.cancel_btn = ttk.Button(
            btn_frame,
            text="⏹️ 取消",
            command=self.cancel_generation_cmd,
            state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            btn_frame,
            text="📁 保存结果",
            command=self._save_result
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            btn_frame,
            text="🗑️ 清空",
            command=self._clear_result
        ).pack(side=tk.LEFT, padx=10)
        
        row += 1
        
        # ===== 进度 =====
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        self.status_label = ttk.Label(frame, text="就绪", foreground="blue")
        self.status_label.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5, padx=5)
        
        #self._update_model_status()
    
    def _get_model_key(self) -> str:
        selected = self.model_var.get()
        if "7B" in selected:
            return "7B"
        return "1B"
    
    def _on_model_changed(self, event):
        """模型切换事件 - 仅更新 UI 提示，实际加载由按钮触发"""
        pass
    
    def update_model_status(self):
        """更新模型状态 - 由外部调用"""
        self._update_model_status()
    
    def _update_model_status(self):
        """更新模型状态"""
        if self.model_manager.is_janus_loaded:
            self.model_status.config(
                text="🟢 已加载",
                foreground="green"
            )
            self.action_btn.config(state=tk.NORMAL)
            self.load_btn.config(text="🔄 切换模型")
            self.unload_btn.config(state=tk.NORMAL)
        elif self.model_manager.is_loading:
            self.model_status.config(
                text="🟡 加载中...",
                foreground="orange"
            )
            self.action_btn.config(state=tk.DISABLED)
            self.load_btn.config(state=tk.DISABLED)
            self.unload_btn.config(state=tk.DISABLED)
        else:
            self.model_status.config(
                text="🔴 未加载",
                foreground="red"
            )
            self.action_btn.config(state=tk.DISABLED)
            self.load_btn.config(state=tk.NORMAL)
            self.unload_btn.config(state=tk.DISABLED)
        
        # 检查是否已有 SD 模型加载（提示用户切换）
        if self.model_manager.is_sd_loaded and not self.model_manager.is_janus_loaded:
            self.load_btn.config(text="📦 加载 Janus (将卸载 SD)")
        elif not self.model_manager.is_janus_loaded:
            self.load_btn.config(text="📦 加载 Janus")
    
    def _load_janus(self):
        """加载 Janus 模型"""
        if self.model_manager.is_loading:
            return
        
        # 如果 Janus 已加载，询问是否切换模型
        if self.model_manager.is_janus_loaded:
            if not messagebox.askyesno("切换模型", f"当前已加载 Janus，是否切换到 {self._get_model_key()}？"):
                return
        
        # 如果有 SD 模型加载，提示
        if self.model_manager.is_sd_loaded:
            if not messagebox.askyesno("切换模型", "加载 Janus 将自动卸载 SD 模型，继续吗？"):
                return
        
        self._start_operation("📦 加载 Janus 模型...")
        self.load_btn.config(state=tk.DISABLED)
        
        def load_thread():
            def progress_cb(value, msg):
                self.app.root.after(0, lambda: self._update_progress(value, msg))
            
            model_key = self._get_model_key()
            success = self.model_manager.load_janus(model_key, progress_cb)
            
            self.app.root.after(0, lambda: self._on_load_complete(success))
        
        threading.Thread(target=load_thread, daemon=True).start()
        
    def _on_load_complete(self, success: bool):
        self.load_btn.config(state=tk.NORMAL)
        self._update_model_status()
        
        if success:
            self.app.update_status("✅ Janus-Pro 模型加载完成")
            self.app._update_model_ui()
            
            # 安全更新 UI
            self.is_generating = False
            self.action_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.progress_var.set(100)
            self.status_label.config(text="✅ Janus 模型加载完成")
            
            # 安全更新结果文本框
            try:
                if hasattr(self, 'result_text') and self.result_text.winfo_exists():
                    self.result_text.delete("1.0", tk.END)
                    self.result_text.insert("1.0", "✅ Janus 模型加载完成\n\n现在可以使用 Janus 功能了！")
            except Exception as e:
                print(f"⚠️ 更新结果文本框失败: {e}")
        else:
            self._on_operation_error("Janus 模型加载失败")
            messagebox.showerror("错误", "Janus 模型加载失败，请查看控制台输出")
        
    def _unload_janus(self):
        """卸载 Janus"""
        if not self.model_manager.is_janus_loaded:
            return
        
        if messagebox.askyesno("确认", "确定要卸载 Janus 模型吗？"):
            self.model_manager.unload_janus()
            self._update_model_status()
            self.app._update_model_ui()
            self.app.update_status("✅ Janus 模型已卸载")
            self._on_operation_complete("✅ Janus 模型已卸载")
    
    # ===== 模式构建 =====
    def _on_mode_changed(self, event):
        try:
            for child in self.content_frame.winfo_children():
                child.destroy()
            
            mode = self.mode_var.get()
            if mode == self.MODE_OPTIONS["understand"]:
                self._build_understand_mode()
                self.action_btn.config(text="🔍 分析图片")
            elif mode == self.MODE_OPTIONS["generate"]:
                self._build_generate_mode()
                self.action_btn.config(text="🎨 生成图片")
            elif mode == self.MODE_OPTIONS["chat"]:
                self._build_chat_mode()
                self.action_btn.config(text="💬 发送")
            
            #self._update_model_status()
            
        except Exception as e:
            print(f"⚠️ 模式切换失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _build_understand_mode(self):
        image_frame = ttk.LabelFrame(self.content_frame, text="📷 上传图片", padding=5)
        image_frame.pack(fill=tk.X, pady=5)
        
        img_select_frame = ttk.Frame(image_frame)
        img_select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(img_select_frame, text="📁 选择图片", command=self._select_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(img_select_frame, text="🗑️ 清除", command=self._clear_image).pack(side=tk.LEFT, padx=5)
        
        self.image_label = ttk.Label(img_select_frame, textvariable=self.image_path_var, foreground="gray")
        self.image_label.pack(side=tk.LEFT, padx=10)
        
        self.preview_label = ttk.Label(image_frame)
        self.preview_label.pack(pady=5)
        
        question_frame = ttk.LabelFrame(self.content_frame, text="❓ 提问", padding=5)
        question_frame.pack(fill=tk.X, pady=5)
        
        self.question_text = tk.Text(question_frame, height=4, width=70, wrap=tk.WORD)
        self.question_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.question_text.insert("1.0", self.default_question)
        
        quick_frame = ttk.Frame(question_frame)
        quick_frame.pack(fill=tk.X, pady=5)
        
        for text, cmd in [
            ("👤 描述人物", "请描述这张图片中的人物，包括：性别、年龄、发型、服装、表情、背景、光线、氛围。用中文回答。"),
            ("🎨 描述风格", "请描述这张图片的艺术风格、构图、色彩搭配和整体氛围。用中文回答。"),
            ("📝 生成提示词", "请为这张图片生成 Stable Diffusion 文生图的提示词（正面提示词和负面提示词）。用中文回答。"),
            ("🔍 详细分析", "请详细分析这张图片，包括：主体、背景、光线、色彩、构图、情感氛围、可能的故事背景。用中文回答。")
        ]:
            ttk.Button(quick_frame, text=text, 
                command=lambda q=cmd: self._set_question(q)
            ).pack(side=tk.LEFT, padx=2)
        
        result_frame = ttk.LabelFrame(self.content_frame, text="📝 分析结果", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = tk.Text(result_frame, height=8, width=70, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _build_generate_mode(self):
        prompt_frame = ttk.LabelFrame(self.content_frame, text="📝 提示词", padding=5)
        prompt_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(prompt_frame, text="正面提示词:").pack(anchor=tk.W, padx=5)
        self.gen_prompt_text = tk.Text(prompt_frame, height=4, width=70, wrap=tk.WORD)
        self.gen_prompt_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.gen_prompt_text.insert("1.0", "a beautiful Asian woman, wearing elegant dress, full body shot, natural lighting")
        
        ttk.Label(prompt_frame, text="负面提示词 (可选):").pack(anchor=tk.W, padx=5)
        self.gen_neg_text = tk.Text(prompt_frame, height=2, width=70, wrap=tk.WORD)
        self.gen_neg_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.gen_neg_text.insert("1.0", "worst quality, low quality, ugly, deformed, blurry, bad anatomy")
        
        quick_frame = ttk.Frame(prompt_frame)
        quick_frame.pack(fill=tk.X, pady=5)
        
        for text, prompt in [
            ("🌸 亚洲美女", "a beautiful Asian woman, wearing elegant dress, full body shot, natural lighting, detailed face"),
            ("🏯 日本庭院", "a beautiful Japanese woman in kimono, traditional garden, cherry blossoms, full body, soft sunlight"),
            ("🎨 油画风格", "a beautiful woman, oil painting style, renaissance, masterpiece, detailed, rich colors"),
            ("🌅 风景", "beautiful landscape, mountains, lake, sunset, 8k, photorealistic, highly detailed")
        ]:
            ttk.Button(quick_frame, text=text, 
                command=lambda p=prompt: self._set_gen_prompt(p)
            ).pack(side=tk.LEFT, padx=2)
        
        result_frame = ttk.LabelFrame(self.content_frame, text="🖼️ 生成结果", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = tk.Text(result_frame, height=8, width=70, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.result_text.insert("1.0", "💡 输入提示词后点击「生成图片」\n\n注意: Janus 文生图质量有限，建议使用 SD 文生图获得更好效果。")
    
    def _build_chat_mode(self):
        history_frame = ttk.LabelFrame(self.content_frame, text="💬 对话历史", padding=5)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.chat_text = tk.Text(history_frame, height=10, width=70, wrap=tk.WORD)
        self.chat_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.chat_text.insert("1.0", "🤖 Janus 对话助手\n" + "=" * 40 + "\n\n")
        self.chat_text.config(state=tk.DISABLED)
        
        input_frame = ttk.LabelFrame(self.content_frame, text="✏️ 输入", padding=5)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.chat_input = tk.Text(input_frame, height=3, width=70, wrap=tk.WORD)
        self.chat_input.pack(fill=tk.BOTH, expand=True, pady=5)
        self.chat_input.bind("<Control-Return>", lambda e: self._execute_action())
        
        quick_frame = ttk.Frame(input_frame)
        quick_frame.pack(fill=tk.X, pady=5)
        
        for text, cmd in [
            ("✍️ 写诗", "请写一首关于春天的五言诗"),
            ("📖 写故事", "请写一个关于爱情的短篇故事，约200字"),
            ("💡 写代码", "请用 Python 写一个快速排序算法"),
            ("🌍 翻译", "请将 'Hello, how are you?' 翻译成中文")
        ]:
            ttk.Button(quick_frame, text=text, 
                command=lambda q=cmd: self._set_chat_input(q)
            ).pack(side=tk.LEFT, padx=2)
    
    # ===== 辅助方法 =====
    def _set_question(self, question: str):
        if hasattr(self, 'question_text'):
            self.question_text.delete("1.0", tk.END)
            self.question_text.insert("1.0", question)
    
    def _set_gen_prompt(self, prompt: str):
        if hasattr(self, 'gen_prompt_text'):
            self.gen_prompt_text.delete("1.0", tk.END)
            self.gen_prompt_text.insert("1.0", prompt)
    
    def _set_chat_input(self, text: str):
        if hasattr(self, 'chat_input'):
            self.chat_input.delete("1.0", tk.END)
            self.chat_input.insert("1.0", text)
    
    def _get_mode_key(self) -> str:
        selected = self.mode_var.get()
        for key, value in self.MODE_OPTIONS.items():
            if value == selected:
                return key
        return "understand"
    
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
    
    # ===== 执行操作 =====
    def _execute_action(self):
        if self.is_generating:
            return
        
        if not self.model_manager.is_janus_loaded:
            if messagebox.askyesno("提示", "Janus 模型未加载，是否立即加载？"):
                self._load_janus()
            return
        
        mode = self._get_mode_key()
        
        if mode == "understand":
            if not hasattr(self, '_image_path') or not self._image_path:
                messagebox.showwarning("提示", "请先选择一张图片")
                return
            if not hasattr(self, 'question_text'):
                messagebox.showwarning("提示", "请先切换模式后再试")
                return
            self._execute_understand()
        elif mode == "generate":
            if not hasattr(self, 'gen_prompt_text'):
                messagebox.showwarning("提示", "请先切换模式后再试")
                return
            self._execute_generate()
        elif mode == "chat":
            if not hasattr(self, 'chat_input'):
                messagebox.showwarning("提示", "请先切换模式后再试")
                return
            self._execute_chat()
    
    def _execute_understand(self):
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

                # ✅ 检查取消
                if self.cancel_generation:
                    raise Exception("用户取消")       
                    
            result = janus_analyzer.analyze(
                image_path=self._image_path,
                question=self.question_text.get("1.0", tk.END).strip(),
                temperature=self.temperature_var.get(),
                max_tokens=self.max_tokens_var.get(),
                progress_callback=progress_cb
            )

            # ✅ 检查取消
            if self.cancel_generation:
                raise Exception("用户取消")
                
            self.app.root.after(0, lambda: self._on_operation_complete(result))
        except Exception as e:
            error_msg = str(e)
            if "取消" in error_msg or "cancelled" in error_msg.lower():
                self.app.root.after(0, lambda: self._on_operation_cancelled())
            else:
                import traceback
                traceback.print_exc()
                self.app.root.after(0, lambda: self._on_operation_error(error_msg))

    # ============================================================
    # ✅ 新增：取消完成处理
    # ============================================================
    def _on_operation_cancelled(self):
        """操作被取消"""
        self.is_generating = False
        self.action_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_label.config(text="⏹️ 已取消")

        # 清理取消回调
        self._cancel_callbacks.clear()
        
        if hasattr(self, 'result_text'):
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", "⏹️ 操作已取消")
    
    def _execute_generate(self):
        prompt = self.gen_prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("提示", "请输入正面提示词")
            return
        
        negative = self.gen_neg_text.get("1.0", tk.END).strip()
        self._start_operation("🎨 生成图片...")
        threading.Thread(target=self._run_generate, args=(prompt, negative), daemon=True).start()

    # ============================================================
    # ✅ 修改：生成模式 - 添加取消检查
    # ============================================================    
    def _run_generate(self, prompt: str, negative: str):
        try:
            def progress_cb(value, msg):
                # ✅ 检查取消
                if self.cancel_generation:
                    raise Exception("用户取消")
                self.app.root.after(0, lambda: self._update_progress(value, msg))
            
            image, metadata = janus_generator.generate(
                prompt=prompt,
                negative_prompt=negative,
                temperature=self.temperature_var.get(),
                max_new_tokens=self.max_tokens_var.get(),
                progress_callback=progress_cb
            )

            # ✅ 检查取消
            if self.cancel_generation:
                raise Exception("用户取消")
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_janus_gen.png"
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            image.save(filepath)

            # ===== 【新增】图片后期处理 =====
            from utils.image_post_processor import post_process_image
            
            final_path = post_process_image(
                filepath,
                self.params,  # 需要传入 params
                prompt=prompt,
                log_prefix="[Janus-Pro]"
            )
            
            if final_path != filepath:
                try:
                    os.remove(filepath)
                except:
                    pass
                filepath = final_path            
            
            self.app.root.after(0, lambda: self.app.add_to_preview(filepath, image))
            self.app.root.after(0, lambda: self._on_operation_complete(
                f"✅ 图片已生成\n📁 保存到: {filepath}\n⏱️ 耗时: {metadata.get('elapsed', 0):.1f}秒\n\n💡 Janus 文生图质量有限，建议使用 SD 文生图获得更好效果。"
            ))
        except Exception as e:
            error_msg = str(e)
            if "取消" in error_msg or "cancelled" in error_msg.lower():
                self.app.root.after(0, lambda: self._on_operation_cancelled())
            else:
                import traceback
                traceback.print_exc()
                self.app.root.after(0, lambda: self._on_operation_error(error_msg))
    
    def _execute_chat(self):
        user_input = self.chat_input.get("1.0", tk.END).strip()
        if not user_input:
            messagebox.showwarning("提示", "请输入消息")
            return
        
        self._append_chat(f"👤 用户: {user_input}\n")
        self.chat_input.delete("1.0", tk.END)
        self._start_operation("💬 思考中...")
        threading.Thread(target=self._run_chat, args=(user_input,), daemon=True).start()

    # ============================================================
    # ✅ 修改：对话模式 - 添加取消检查
    # ============================================================        
    def _run_chat(self, user_input: str):
        """后台运行对话 - 使用 janus_chat"""
        try:
            def progress_cb(value, msg):
                # ✅ 检查取消
                if self.cancel_generation:
                    raise Exception("用户取消")
                self.app.root.after(0, lambda: self._update_progress(value, msg))
            
            # ✅ 使用专门的 janus_chat 模块
            reply, metadata = janus_chat.chat(
                user_input=user_input,
                temperature=self.temperature_var.get(),
                max_new_tokens=self.max_tokens_var.get(),
                progress_callback=progress_cb
            )

            # ✅ 检查取消
            if self.cancel_generation:
                raise Exception("用户取消")
                
            self.app.root.after(0, lambda: self._append_chat(f"🤖 Janus: {reply}\n\n"))
            self.app.root.after(0, lambda: self._on_operation_complete("✅ 对话完成"))
            
        except Exception as e:
            error_msg = str(e)
            if "取消" in error_msg or "cancelled" in error_msg.lower():
                self.app.root.after(0, lambda: self._append_chat(f"⏹️ 对话已取消\n\n"))
                self.app.root.after(0, lambda: self._on_operation_cancelled())
            else:
                import traceback
                traceback.print_exc()
                self.app.root.after(0, lambda: self._append_chat(f"❌ 错误: {error_msg}\n\n"))
                self.app.root.after(0, lambda: self._on_operation_error(error_msg))
            
    def _append_chat(self, text: str):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, text)
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    # ===== 通用方法 =====
    # ============================================================
    # ✅ 修改：启动操作时重置取消标志
    # ============================================================    
    def _start_operation(self, status: str):
        self.cancel_generation = False  # ✅ 重置取消标志
        self._cancel_callbacks.clear()  # ✅ 清空取消回调
        self.is_generating = True
        self.action_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.status_label.config(text=status)
    
    def _update_progress(self, value, msg):
        self.progress_var.set(value * 100)
        self.status_label.config(text=msg)

    # ============================================================
    # ✅ 修改：操作完成 - 清理取消回调
    # ============================================================    
    def _on_operation_complete(self, result: str):
        self.is_generating = False
        self.action_btn.config(state=tk.NORMAL if self.model_manager.is_janus_loaded else tk.DISABLED)
        self.cancel_btn.config(state=tk.DISABLED)
        self.progress_var.set(100)
        self.status_label.config(text="✅ 完成")
        
        # 清理取消回调
        self._cancel_callbacks.clear()
        
        # ✅ 安全检查 result_text 是否存在且有效
        try:
            if hasattr(self, 'result_text') and self.result_text.winfo_exists():
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", result)
        except Exception as e:
            print(f"⚠️ 更新结果文本框失败: {e}")

    # ============================================================
    # ✅ 修改：操作错误 - 清理取消回调
    # ============================================================    
    def _on_operation_error(self, error: str):
        self.is_generating = False
        self.action_btn.config(state=tk.NORMAL if self.model_manager.is_janus_loaded else tk.DISABLED)
        self.cancel_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_label.config(text=f"❌ 错误: {error}")

        # 清理取消回调
        self._cancel_callbacks.clear()
        
        # ✅ 安全检查 result_text 是否存在且有效
        try:
            if hasattr(self, 'result_text') and self.result_text.winfo_exists():
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", f"❌ 操作失败:\n{error}")
        except Exception as e:
            print(f"⚠️ 更新结果文本框失败: {e}")
        
    def cancel_generation_cmd(self):
        self.cancel_generation = True
        self.is_generating = False
        self.status_label.config(text="⏹️ 已取消")
        self.cancel_btn.config(state=tk.DISABLED)
    
    def _save_result(self):
        if not hasattr(self, 'result_text'):
            return
        
        result = self.result_text.get("1.0", tk.END).strip()
        if not result or result.startswith("⏳") or result.startswith("❌"):
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
    
    def _clear_result(self):
        if hasattr(self, 'result_text'):
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", "已清空")
        
        if hasattr(self, 'chat_text'):
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.delete("1.0", tk.END)
            self.chat_text.insert("1.0", "🤖 Janus 对话助手\n" + "=" * 40 + "\n\n")
            self.chat_text.config(state=tk.DISABLED)
    
    def get_frame(self):
        return self.frame