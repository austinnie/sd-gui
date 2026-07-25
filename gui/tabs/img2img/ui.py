# gui/tabs/img2img/ui.py
"""图生图 UI 构建"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

from .mask_editor import MaskEditor
from .controlnet import ControlNetHandler


class Img2ImgUI:
    """图生图 UI 构建器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.frame = tab.frame
    
    def build(self):
        """构建 UI"""
        frame = self.frame
        row = 0
        
        self._build_mode_selector(frame, row)
        row += 1
        
        self._build_image_selector(frame, row)
        row += 1
        
        self._build_template_selector(frame, row)
        row += 1
        
        self._build_preview(frame, row)
        row += 1
        
        self._build_prompt_area(frame, row)
        row += 2
        
        self._build_hint(frame, row)
        row += 1
        
        self._build_params(frame, row)
        row += 1
        
        self._build_buttons(frame, row)
    
    def _build_mode_selector(self, frame, row):
        """选择模式"""
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(mode_frame, text="选择模式:").pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(mode_frame, text="📷 单张", variable=self.tab.image_mode_var,
                        value="single", command=self.tab._on_mode_changed).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="📚 多张", variable=self.tab.image_mode_var,
                        value="multiple", command=self.tab._on_mode_changed).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="📁 目录", variable=self.tab.image_mode_var,
                        value="directory", command=self.tab._on_mode_changed).pack(side=tk.LEFT, padx=5)
        
        self.tab.image_count_label = ttk.Label(mode_frame, text="", foreground="blue")
        self.tab.image_count_label.pack(side=tk.RIGHT, padx=10)
    
    def _build_image_selector(self, frame, row):
        """图片选择区域"""
        self.tab.image_select_frame = ttk.Frame(frame)
        self.tab.image_select_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # 单张模式
        self.tab.single_path_frame = ttk.Frame(self.tab.image_select_frame)
        ttk.Label(self.tab.single_path_frame, text="图片:").pack(side=tk.LEFT, padx=5)
        self.tab.path_label = ttk.Label(self.tab.single_path_frame, textvariable=self.tab.img_paths_var,
                                        foreground="gray", background="white", relief="sunken")
        self.tab.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(self.tab.single_path_frame, text="选择图片", command=self.tab._select_single_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.tab.single_path_frame, text="清空", command=self.tab._clear_images).pack(side=tk.LEFT, padx=2)
        self.tab.single_path_frame.pack(fill=tk.X)
        
        # 多张模式
        self.tab.multiple_path_frame = ttk.Frame(self.tab.image_select_frame)
        self.tab.multiple_path_frame.pack(fill=tk.X)
        self.tab.multiple_path_frame.pack_forget()
        
        ttk.Label(self.tab.multiple_path_frame, text="已选:").pack(side=tk.LEFT, padx=5)
        self.tab.multiple_count_label = ttk.Label(self.tab.multiple_path_frame, text="未选择",
                                                   foreground="gray", background="white", relief="sunken")
        self.tab.multiple_count_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(self.tab.multiple_path_frame, text="选择多张", command=self.tab._select_multiple_images).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.tab.multiple_path_frame, text="清空", command=self.tab._clear_images).pack(side=tk.LEFT, padx=2)
        
        # 目录模式
        self.tab.directory_path_frame = ttk.Frame(self.tab.image_select_frame)
        self.tab.directory_path_frame.pack(fill=tk.X)
        self.tab.directory_path_frame.pack_forget()
        
        ttk.Label(self.tab.directory_path_frame, text="目录:").pack(side=tk.LEFT, padx=5)
        self.tab.directory_path_label = ttk.Label(self.tab.directory_path_frame, textvariable=self.tab.img_paths_var,
                                                   foreground="gray", background="white", relief="sunken")
        self.tab.directory_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(self.tab.directory_path_frame, text="选择目录", command=self.tab._select_directory).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.tab.directory_path_frame, text="清空", command=self.tab._clear_images).pack(side=tk.LEFT, padx=2)
    
    def _build_template_selector(self, frame, row):
        """模板选择器"""
        from gui.components.template_selector import TemplateSelector
        
        template_row = ttk.Frame(frame)
        template_row.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        self.tab.template_selector = TemplateSelector(
            template_row,
            on_select=self.tab._on_template_selected,
            show_apply_button=False
        )
        self.tab.template_selector.pack(fill=tk.X)
        
        ttk.Button(template_row, text="✖ 清空", command=self.tab._clear_template_prompt, width=6).pack(side=tk.RIGHT, padx=2)
    
    def _build_preview(self, frame, row):
        """预览"""
        preview_frame = ttk.Frame(frame)
        preview_frame.grid(row=row, column=0, columnspan=3, pady=5, padx=5)
        self.tab.preview_label = ttk.Label(preview_frame)
        self.tab.preview_label.pack()
    
    def _build_prompt_area(self, frame, row):
        """提示词区域"""
        ttk.Label(frame, text="目标提示词:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.tab.prompt_text = tk.Text(frame, height=4, width=70)
        self.tab.prompt_text.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(frame, text="负面提示词:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.tab.neg_text = tk.Text(frame, height=3, width=70)
        self.tab.neg_text.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
    
    def _build_hint(self, frame, row):
        """参数提示"""
        hint_frame = ttk.Frame(frame)
        hint_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2, padx=5)
        ttk.Label(hint_frame, text="💡 参数（步数、CFG、种子、尺寸等）请在顶部的「共享参数面板」调整",
                  foreground="gray", font=("", 8)).pack(side=tk.LEFT, padx=5)
    
    def _build_params(self, frame, row):
        """图生图参数"""
        param_frame = ttk.Frame(frame)
        param_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # 局部重绘
        inpaint_row = ttk.Frame(param_frame)
        inpaint_row.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(inpaint_row, text="🩲 启用局部重绘（去除衣物区域）",
                        variable=self.tab.use_inpaint_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(inpaint_row, text="🖱️ 涂抹遮罩", command=self.tab._open_mask_editor).pack(side=tk.LEFT, padx=5)
        
        # ControlNet
        controlnet_row = ttk.Frame(param_frame)
        controlnet_row.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(controlnet_row, text="🧠 启用 ControlNet",
                        variable=self.tab.use_controlnet_var,
                        command=self.tab._on_controlnet_toggle).pack(side=tk.LEFT, padx=5)
        
        from utils.controlnet import get_recommended_multi_controlnet_combos
        ttk.Label(controlnet_row, text="模式:").pack(side=tk.LEFT, padx=5)
        
        combos = get_recommended_multi_controlnet_combos()
        self.tab.controlnet_combo = ttk.Combobox(controlnet_row,
                                                  textvariable=self.tab.controlnet_combo_var,
                                                  values=list(combos.keys()), width=18, state="readonly")
        self.tab.controlnet_combo.pack(side=tk.LEFT, padx=5)
        
        self.tab.controlnet_hint = ttk.Label(controlnet_row, text="💡 多层锁定：姿态+边缘+深度",
                                              foreground="gray", font=("", 8))
        self.tab.controlnet_hint.pack(side=tk.LEFT, padx=5)
        self.tab.controlnet_combo.bind('<<ComboboxSelected>>', self.tab._on_controlnet_combo_changed)
        
        # 重绘强度
        param_row1 = ttk.Frame(param_frame)
        param_row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(param_row1, text="重绘强度:").pack(side=tk.LEFT, padx=5)
        scale = ttk.Scale(param_row1, from_=0.05, to=0.99, variable=self.tab.strength_var,
                          orient=tk.HORIZONTAL, length=120)
        scale.pack(side=tk.LEFT, padx=5)
        self.tab.strength_label = ttk.Label(param_row1, text="0.05", width=5)
        self.tab.strength_label.pack(side=tk.LEFT, padx=5)
        self.tab.strength_var.trace('w', lambda *_: self.tab.strength_label.config(
            text=f"{self.tab.strength_var.get():.2f}"))
        
        # 每张生成变体数
        param_row2 = ttk.Frame(param_frame)
        param_row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(param_row2, text="每张生成:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(param_row2, from_=1, to=4, textvariable=self.tab.per_image_var, width=4).pack(side=tk.LEFT, padx=5)
        ttk.Label(param_row2, textvariable=self.tab.per_image_var, width=3).pack(side=tk.LEFT, padx=5)
    
    def _build_buttons(self, frame, row):
        """按钮"""
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        self.tab.generate_btn = ttk.Button(btn_frame, text="🎨 图生图", command=self.tab.start_generate)
        self.tab.generate_btn.pack(side=tk.LEFT, padx=10)
        
        self.tab.cancel_btn = ttk.Button(btn_frame, text="⏹️ 取消", command=self.tab.cancel_generation, state=tk.DISABLED)
        self.tab.cancel_btn.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(btn_frame, text="📁 打开输出文件夹", command=self.app.open_output_folder).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="🎯 强度测试", command=self.tab._run_strength_test).pack(side=tk.LEFT, padx=5)