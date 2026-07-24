# gui/tabs/pipeline_ui.py
"""Pipeline UI 构建 - 从 pipeline_tab.py 移出"""

import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pipeline_tab import PipelineTab


class PipelineUI:
    """Pipeline UI 构建器"""
    
    def __init__(self, tab: 'PipelineTab'):
        self.tab = tab
        self.app = tab.app
    
    def build(self):
        """构建完整 UI"""
        frame = self.tab.frame
        row = 0
        
        # ===== 标题 =====
        title = ttk.Label(frame, text="🔧 流水线处理", font=("", 14, "bold"))
        title.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=10, padx=5)
        row += 1
        
        # ===== 流水线选择 =====
        row = self._build_pipeline_selector(frame, row)
        
        # ===== 流水线信息 =====
        row = self._build_info_panel(frame, row)
        
        # ===== 图片选择 =====
        row = self._build_image_selector(frame, row)
        
        # ===== 参数覆盖 =====
        row = self._build_params_panel(frame, row)
        
        # ===== 批量处理 =====
        row = self._build_batch_panel(frame, row)
        
        # ===== 控制按钮 =====
        row = self._build_controls(frame, row)
        
        # ===== 进度条 =====
        row = self._build_progress(frame, row)
        
        # ===== 日志 =====
        row = self._build_log(frame, row)
        
        # ===== 底部提示 =====
        ttk.Label(
            frame,
            text="💡 选择流水线后点击运行，参数覆盖会应用到对应的 step",
            foreground="gray",
            font=("", 8)
        ).grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # 设置行权重
        frame.rowconfigure(row-2, weight=1)
        frame.columnconfigure(1, weight=1)
    
    def _build_pipeline_selector(self, frame, row: int) -> int:
        """构建流水线选择器"""
        ttk.Label(frame, text="选择流水线:").grid(row=row, column=0, sticky=tk.W, padx=5)
        
        self.tab.pipeline_combo = ttk.Combobox(
            frame,
            textvariable=self.tab.pipeline_var,
            width=35,
            state="readonly"
        )
        self.tab.pipeline_combo.grid(row=row, column=1, sticky=tk.W, padx=5)
        self.tab.pipeline_combo.bind('<<ComboboxSelected>>', lambda e: self.tab._update_info())
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=2, sticky=tk.W, padx=5)
        ttk.Button(btn_frame, text="🔄 刷新", command=self.tab._reload_pipelines).pack(side=tk.LEFT, padx=2)
        row += 1
        
        return row
    
    def _build_info_panel(self, frame, row: int) -> int:
        """构建信息面板"""
        info_frame = ttk.LabelFrame(frame, text="📋 流水线信息", padding=5)
        info_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.tab.info_text = tk.Text(info_frame, height=4, width=80, bg='#f0f0f0', wrap=tk.WORD)
        self.tab.info_text.pack(fill=tk.BOTH, expand=True)
        row += 1
        
        return row
    
    def _build_image_selector(self, frame, row: int) -> int:
        """构建图片选择器"""
        image_frame = ttk.LabelFrame(frame, text="📷 输入图片", padding=5)
        image_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        img_row = ttk.Frame(image_frame)
        img_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(img_row, text="图片:").pack(side=tk.LEFT, padx=5)
        
        self.tab.path_label = ttk.Label(
            img_row,
            textvariable=self.tab.image_path_var,
            foreground="gray",
            background="white",
            relief="sunken"
        )
        self.tab.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(img_row, text="浏览", command=self.tab._select_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(img_row, text="清除", command=self.tab._clear_image).pack(side=tk.LEFT, padx=5)
        
        self.tab.preview_label = ttk.Label(image_frame)
        self.tab.preview_label.pack(pady=5)
        row += 1
        
        return row
    
    # gui/tabs/pipeline_ui.py - _build_params_panel 方法
    def _build_params_panel(self, frame, row: int) -> int:
        """构建参数覆盖面板"""
        param_frame = ttk.LabelFrame(frame, text="⚙️ 参数覆盖 (可选)", padding=5)
        param_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # ===== 强度 =====
        strength_row = ttk.Frame(param_frame)
        strength_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(strength_row, text="强度:").pack(side=tk.LEFT, padx=5)
        scale = ttk.Scale(
            strength_row,
            from_=0.1, to=0.8,
            variable=self.tab.strength_var,
            orient=tk.HORIZONTAL,
            length=150
        )
        scale.pack(side=tk.LEFT, padx=5)
        self.tab.strength_label = ttk.Label(strength_row, text="0.35", width=5)
        self.tab.strength_label.pack(side=tk.LEFT, padx=5)
        self.tab.strength_var.trace('w', lambda *_: self.tab.strength_label.config(
            text=f"{self.tab.strength_var.get():.2f}"
        ))
        
        # ===== 步数 + CFG =====
        steps_row = ttk.Frame(param_frame)
        steps_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(steps_row, text="步数:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(steps_row, from_=5, to=60, textvariable=self.tab.steps_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(steps_row, text="CFG:").pack(side=tk.LEFT, padx=15)
        ttk.Spinbox(steps_row, from_=5.0, to=12.0, textvariable=self.tab.cfg_var, width=5, increment=0.5).pack(side=tk.LEFT, padx=5)
        
        # ================================================================
        # ✅ 场景数信息显示（只读，显示当前流水线的场景总数）
        # ================================================================
        scenes_info_row = ttk.Frame(param_frame)
        scenes_info_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(scenes_info_row, text="📊 场景数:").pack(side=tk.LEFT, padx=5)
        
        self.tab.scenes_info_var = tk.StringVar(value="检测中...")
        self.tab.scenes_info_label = ttk.Label(
            scenes_info_row,
            textvariable=self.tab.scenes_info_var,
            foreground="blue"
        )
        self.tab.scenes_info_label.pack(side=tk.LEFT, padx=5)
        
        # 刷新场景数按钮
        ttk.Button(
            scenes_info_row,
            text="🔄",
            width=2,
            command=self.tab._update_scenes_info
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(
            scenes_info_row,
            text="💡 显示当前流水线所有步骤的场景总数",
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=10)
        
        # ================================================================
        # ✅ 场景数限制（用户可控制，对所有步骤生效）
        # ================================================================
        scenes_limit_row = ttk.Frame(param_frame)
        scenes_limit_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(scenes_limit_row, text="🎯 场景数限制:").pack(side=tk.LEFT, padx=5)
        
        self.tab.scenes_limit_combo = ttk.Combobox(
            scenes_limit_row,
            textvariable=self.tab.scenes_limit_var,
            values=["全部", "1", "2", "3", "4", "5", "6", "7", "8", "10", "12", "14", "16", "20"],
            width=8,
            state="readonly"
        )
        self.tab.scenes_limit_combo.pack(side=tk.LEFT, padx=5)
        self.tab.scenes_limit_combo.set("全部")
        
        ttk.Label(
            scenes_limit_row,
            text="💡 选择数字限制场景数量，留空=全部",
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=10)
        
        # ================================================================
        # ControlNet
        # ================================================================
        controlnet_frame = ttk.LabelFrame(param_frame, text="🧠 ControlNet 控制", padding=3)
        controlnet_frame.pack(fill=tk.X, pady=3)
        
        cn_row1 = ttk.Frame(controlnet_frame)
        cn_row1.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(
            cn_row1,
            text="启用 ControlNet",
            variable=self.tab.use_controlnet_var
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(cn_row1, text="类型:").pack(side=tk.LEFT, padx=15)
        
        cn_type_combo = ttk.Combobox(
            cn_row1,
            textvariable=self.tab.controlnet_type_var,
            values=["canny", "hed", "lineart", "scribble", "openpose", "depth", "normal", "mlsd"],
            width=10,
            state="readonly"
        )
        cn_type_combo.pack(side=tk.LEFT, padx=5)
        cn_type_combo.set("canny")
        
        cn_row2 = ttk.Frame(controlnet_frame)
        cn_row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(cn_row2, text="ControlNet 强度:").pack(side=tk.LEFT, padx=5)
        cn_scale = ttk.Scale(
            cn_row2,
            from_=0.1, to=1.0,
            variable=self.tab.controlnet_strength_var,
            orient=tk.HORIZONTAL,
            length=120
        )
        cn_scale.pack(side=tk.LEFT, padx=5)
        self.tab.cn_strength_label = ttk.Label(cn_row2, text="0.60", width=5)
        self.tab.cn_strength_label.pack(side=tk.LEFT, padx=5)
        self.tab.controlnet_strength_var.trace('w', lambda *_: self.tab.cn_strength_label.config(
            text=f"{self.tab.controlnet_strength_var.get():.2f}"
        ))
        
        row += 1
        return row
    
    def _build_batch_panel(self, frame, row: int) -> int:
        """构建批量处理面板"""
        batch_frame = ttk.LabelFrame(frame, text="📁 批量处理模式", padding=5)
        batch_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        row += 1
        
        batch_row1 = ttk.Frame(batch_frame)
        batch_row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(batch_row1, text="图片目录:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(batch_row1, textvariable=self.tab.batch_dir_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(batch_row1, text="浏览", command=self.tab._select_batch_dir).pack(side=tk.LEFT, padx=5)
        
        batch_row2 = ttk.Frame(batch_frame)
        batch_row2.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(batch_row2, text="跳过已存在的图片", variable=self.tab.batch_skip_existing_var).pack(side=tk.LEFT, padx=5)
        
        batch_row3 = ttk.Frame(batch_frame)
        batch_row3.pack(fill=tk.X, pady=5)
        
        self.tab.batch_run_btn = ttk.Button(batch_row3, text="📦 批量处理目录", command=self.tab._run_batch_pipeline)
        self.tab.batch_run_btn.pack(side=tk.LEFT, padx=5)
        
        self.tab.batch_cancel_btn = ttk.Button(batch_row3, text="⏹️ 取消", command=self.tab._cancel_batch, state=tk.DISABLED)
        self.tab.batch_cancel_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(batch_row3, textvariable=self.tab.batch_status_var, foreground="blue").pack(side=tk.LEFT, padx=15)
        
        row += 1
        return row
    
    def _build_controls(self, frame, row: int) -> int:
        """构建控制按钮"""
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        self.tab.run_btn = ttk.Button(btn_frame, text="🚀 运行流水线", command=self.tab._run_pipeline)
        self.tab.run_btn.pack(side=tk.LEFT, padx=5)
        
        self.tab.cancel_btn = ttk.Button(btn_frame, text="⏹️ 取消", command=self.tab._cancel_pipeline, state=tk.DISABLED)
        self.tab.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="📁 打开输出", command=self.tab._open_output).pack(side=tk.LEFT, padx=5)
        row += 1
        
        return row
    
    def _build_progress(self, frame, row: int) -> int:
        """构建进度条"""
        progress_frame = ttk.Frame(frame)
        progress_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.tab.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.tab.progress_var,
            maximum=100,
            length=400
        )
        self.tab.progress_bar.pack(fill=tk.X, pady=2)
        
        self.tab.status_label = ttk.Label(progress_frame, textvariable=self.tab.progress_text_var, foreground="blue")
        self.tab.status_label.pack(anchor=tk.W, pady=2)
        row += 1
        
        return row
    
    def _build_log(self, frame, row: int) -> int:
        """构建日志"""
        log_frame = ttk.LabelFrame(frame, text="📝 运行日志", padding=5)
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.tab.log_text = tk.Text(log_frame, height=8, width=80, state=tk.DISABLED, wrap=tk.WORD)
        self.tab.log_text.pack(fill=tk.BOTH, expand=True)
        row += 1
        
        return row
    
    def update_info(self, name: str, pipeline: dict):
        """更新流水线信息"""
        from core.pipeline.scene_counter import get_total_scenes
        
        info = f"📌 {name}\n"
        info += f"📝 {pipeline.get('description', '无描述')}\n"
        steps = pipeline.get("steps", [])
        info += f"📊 共 {len(steps)} 步\n"
        
        for i, step in enumerate(steps, 1):
            step_type = step.get("type", "unknown")
            config = step.get("config", {})
            config_str = ", ".join(f"{k}={v}" for k, v in config.items() if k != "model_path")
            info += f"   {i}. {step_type} ({config_str})\n"
        
        # 场景统计
        total_scenes, scene_details = get_total_scenes(steps)
        if scene_details:
            info += f"\n📊 场景统计:\n"
            for detail in scene_details:
                info += f"   • {detail}\n"
            info += f"   📝 总计: {total_scenes} 个场景\n"
        
        self.tab.info_text.delete("1.0", tk.END)
        self.tab.info_text.insert("1.0", info)
    
    def show_preview(self, filepath: str):
        """显示图片预览"""
        try:
            img = Image.open(filepath)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.tab.preview_label.config(image=photo)
            self.tab.preview_label.image = photo
        except Exception as e:
            print(f"⚠️ 预览失败: {e}")
    
    def clear_preview(self):
        """清除预览"""
        self.tab.preview_label.config(image='')
        self.tab.preview_label.image = None