# gui/tabs/interrogate/ui.py
"""图片反推 UI 构建"""

import tkinter as tk
from tkinter import ttk, filedialog


class InterrogateUI:
    """反推 UI 构建器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.frame = tab.frame
    
    def build(self):
        """构建 UI"""
        frame = self.frame
        row = 0
        
        # 上传图片
        ttk.Label(frame, text="上传图片:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.tab.path_label = ttk.Label(
            frame,
            textvariable=self.tab.path_var,
            foreground="gray",
            background="white",
            relief="sunken"
        )
        self.tab.path_label.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=2, sticky=tk.W)
        ttk.Button(btn_frame, text="浏览", command=self.tab._select_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="清除", command=self.tab._clear_image).pack(side=tk.LEFT, padx=2)
        row += 1
        
        # 预览
        preview_frame = ttk.Frame(frame)
        preview_frame.grid(row=row, column=0, columnspan=3, pady=5, padx=5)
        self.tab.preview_label = ttk.Label(preview_frame)
        self.tab.preview_label.pack()
        row += 1
        
        # 参数
        param_frame = ttk.Frame(frame)
        param_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        self._build_params(param_frame)
        row += 1
        
        # 结果
        ttk.Label(frame, text="反推结果:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.tab.result_text = tk.Text(frame, height=8, width=70)
        self.tab.result_text.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # 操作按钮
        action_frame = ttk.Frame(frame)
        action_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Button(action_frame, text="📋 复制到文生图", command=self.tab._copy_to_txt2img).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📋 复制到图生图", command=self.tab._copy_to_img2img).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📋 复制到图生图(推荐)", command=self.tab._copy_to_img2img_recommended).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="💾 保存到文件", command=self.tab._save_result).pack(side=tk.LEFT, padx=5)
        
        self._update_ui_state()
    
    def _build_params(self, parent):
        """构建参数控件"""
        # 后端选择
        ttk.Label(parent, text="后端:").pack(side=tk.LEFT, padx=5)
        self.tab.backend_combo = ttk.Combobox(
            parent,
            textvariable=self.tab.backend_var,
            values=["tag", "clip", "blip", "combined", "llm"],
            width=8
        )
        self.tab.backend_combo.pack(side=tk.LEFT, padx=5)
        self.tab.backend_combo.bind('<<ComboboxSelected>>', self.tab._on_backend_changed)
        
        # 模型选择
        self.tab.model_label = ttk.Label(parent, text="模型:")
        self.tab.model_combo = ttk.Combobox(
            parent,
            textvariable=self.tab.tag_model_var,
            width=15
        )
        
        # BLIP 模型
        self.tab.blip_model_label = ttk.Label(parent, text="BLIP:")
        self.tab.blip_model_combo = ttk.Combobox(
            parent,
            textvariable=self.tab.blip_model_var,
            values=["BLIP-base (快速)", "BLIP-large (详细)"],
            width=15
        )
        
        # CLIP 模型
        self.tab.clip_model_label = ttk.Label(parent, text="CLIP:")
        self.tab.clip_model_combo = ttk.Combobox(
            parent,
            textvariable=self.tab.clip_model_var,
            values=["ViT-L-14/openai"],
            width=15
        )
        
        # 模式
        ttk.Label(parent, text="模式:").pack(side=tk.LEFT, padx=5)
        self.tab.mode_combo = ttk.Combobox(
            parent,
            textvariable=self.tab.mode_var,
            values=["fast", "classic", "best"],
            width=6
        )
        self.tab.mode_combo.pack(side=tk.LEFT, padx=5)
        
        # 阈值
        ttk.Label(parent, text="阈值:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(
            parent,
            from_=0.01,
            to=0.9,
            textvariable=self.tab.thresh_var,
            width=4,
            increment=0.01
        ).pack(side=tk.LEFT, padx=5)
        
        # 按钮
        self.tab.interrogate_btn = ttk.Button(
            parent,
            text="🔍 开始反推",
            command=self.tab.start_interrogate
        )
        self.tab.interrogate_btn.pack(side=tk.LEFT, padx=10)
        
        self.tab.cancel_interrogate_btn = ttk.Button(
            parent,
            text="⏹️ 取消",
            command=self.tab.cancel_interrogation,
            state=tk.DISABLED
        )
        self.tab.cancel_interrogate_btn.pack(side=tk.LEFT, padx=5)
    
    def _update_ui_state(self):
        """更新 UI 状态"""
        backend = self.tab.backend_var.get()
        
        for widget in [self.tab.model_label, self.tab.model_combo,
                       self.tab.blip_model_label, self.tab.blip_model_combo,
                       self.tab.clip_model_label, self.tab.clip_model_combo,
                       self.tab.mode_combo]:
            try:
                widget.pack_forget()
            except:
                pass
        
        if backend == "tag":
            self.tab.model_label.pack(side=tk.LEFT, padx=5)
            self.tab.model_combo.pack(side=tk.LEFT, padx=5)
            self.tab.model_combo['values'] = ["ViT-Base (快速)", "ViT-Large (准确)", "CLIP-B-32 (推荐)"]
            self.tab.model_combo.set(self.tab.tag_model_var.get())
        elif backend == "clip":
            self.tab.model_label.pack(side=tk.LEFT, padx=5)
            self.tab.model_combo.pack(side=tk.LEFT, padx=5)
            self.tab.model_combo['values'] = ["ViT-L-14/openai"]
            self.tab.model_combo.set("ViT-L-14/openai")
            self.tab.mode_combo.pack(side=tk.LEFT, padx=5)
        elif backend == "combined":
            self.tab.blip_model_label.pack(side=tk.LEFT, padx=5)
            self.tab.blip_model_combo.pack(side=tk.LEFT, padx=5)
            self.tab.clip_model_label.pack(side=tk.LEFT, padx=5)
            self.tab.clip_model_combo.pack(side=tk.LEFT, padx=5)
            self.tab.mode_combo.pack(side=tk.LEFT, padx=5)