#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LoRA 管理标签页 - 集成分析、批量测试、筛选、重命名、同步功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import shutil
import re
import json
from datetime import datetime
from collections import defaultdict
from PIL import Image, ImageDraw
import torch
import gc

from .base_tab import BaseTab
from gui.components.memory_monitor import force_memory_cleanup


class LoraManagerTab(BaseTab):
    """LoRA 管理标签页"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._init_vars()
        self.setup_ui()
        self._scan_lora_files()
    
    def _init_vars(self):
        """初始化变量"""
        # ===== 路径配置 =====
        self.image_dir_var = tk.StringVar(value="output/all_images")
        self.output_file_var = tk.StringVar(value="output/high_sex_lora_list.txt")
        self.extract_dir_var = tk.StringVar(value="output/selected_high_loras")
        self.top_k_var = tk.IntVar(value=30)
        
        # 模型目录
        self.models_root_var = tk.StringVar(value=r"E:\SD_OpenVINO\models")
        self.test_lora_dir_var = tk.StringVar(value=r"E:\SD_OpenVINO\models\test_lora")
        self.sd15_lora_dir_var = tk.StringVar(value=r"E:\SD_OpenVINO\models\sd15-lora")
        self.sdxl_lora_dir_var = tk.StringVar(value=r"E:\SD_OpenVINO\models\sdxl-lora")
        
        # ===== 批量测试配置 =====
        self.sd15_model_path_var = tk.StringVar(value=r"../models/sd-v1-5/aiiiiii01_v10.safetensors")
        self.sdxl_model_path_var = tk.StringVar(value=r"../models/sdxl/perfectionAsianILXL_v10.safetensors")
        self.output_previews_dir_var = tk.StringVar(value="./output/lora_previews")
        self.test_steps_sd15_var = tk.IntVar(value=12)
        self.test_steps_sdxl_var = tk.IntVar(value=20)
        self.test_prompt_sd15_var = tk.StringVar(
            value="masterpiece, best quality, 1girl, solo, white background, sharp focus, <lora:NAME:1>"
        )
        self.test_prompt_sdxl_var = tk.StringVar(
            value="masterpiece, best quality, 1girl, solo, white background, studio lighting, highly detailed, sharp focus, <lora:NAME:1>"
        )
        self.test_negative_sd15_var = tk.StringVar(
            value="worst quality, low quality, deformed, blurry, bad anatomy"
        )
        self.test_negative_sdxl_var = tk.StringVar(
            value="worst quality, low quality, deformed, blurry, bad anatomy, extra limbs, missing limbs, text"
        )

        # ===== 尺寸配置 =====
        self.test_size_sd15_var = tk.StringVar(value="512x768")   # SD 1.5 当前选中的尺寸
        self.test_size_sdxl_var = tk.StringVar(value="1024x1024") # SDXL 当前选中的尺寸
        
        # ===== 多尺寸测试（新增） =====
        self.test_multi_size_var = tk.BooleanVar(value=False)  # 是否启用多尺寸
        self.test_sizes_sd15_var = tk.StringVar(value="512x768,640x960,576x1024")  # SD 1.5 尺寸列表
        self.test_sizes_sdxl_var = tk.StringVar(value="1024x1024,896x1152,768x1344")  # SDXL 尺寸列表
        
        # 测试选项
        self.test_filter_var = tk.StringVar(value="all")  # all, small, medium, large
        self.test_model_type_var = tk.StringVar(value="both")  # sd15, sdxl, both
        self.test_re_run_var = tk.BooleanVar(value=False)
        
        # ===== 测试模式（多选） =====
        self.test_mode_basic_var = tk.BooleanVar(value=True)   # v1: 基础 SD1.5 + SDXL
        self.test_mode_multi_model_var = tk.BooleanVar(value=False)  # v2: 多模型
        self.test_mode_multi_weight_var = tk.BooleanVar(value=False) # v3: 多权重
        self.test_mode_combine_var = tk.BooleanVar(value=False)      # v3: LoRA 叠加
        
        # ===== v2/v3 高级参数 =====
        self.test_model_scope_var = tk.StringVar(value="default")
        self.custom_models_var = tk.StringVar(value="")
        self.test_weights_var = tk.StringVar(value="0.5,0.8,1.0,1.2")
        self.test_prompts_var = tk.StringVar(value="portrait")
        self.test_group_var = tk.StringVar(value="")
        self.test_recent_var = tk.IntVar(value=0)
        self.test_combine_var = tk.StringVar(value="")
        self.test_max_loras_var = tk.IntVar(value=0)


        # ===== 多维度风格（新增） =====
        self.dimensions = {
            "prompt": ["portrait", "full_body", "close_up", "cinematic", "anime"],
            "background": ["white", "studio", "outdoor", "beach", "forest"],
            "lighting": ["natural", "dramatic", "soft", "golden_hour"],
            "quality": ["standard", "photorealistic", "artistic"],
            "clothing": ["casual", "elegant", "swimsuit", "lingerie"],
            "expression": ["smiling", "seductive", "serious", "happy"],
            "pose": ["standing", "sitting", "lying", "dancing"],
        }
        
        # 每个维度的启用开关和选中值
        self.dim_vars = {}  # {dimension: BooleanVar}
        self.dim_options_vars = {}  # {dimension: {option: BooleanVar}}
        
        # 默认启用的维度
        self._init_dimension_vars()        
    
        # ===== 测试范围（新增） =====
        self.test_scope_var = tk.StringVar(value="all")  # all, single, keyword
        self.test_single_lora_var = tk.StringVar(value="")  # 选中的单个 LoRA
    
        # ===== 状态 =====
        self.is_scanning = False
        self.is_testing = False
        self.is_processing = False
        self.cancel_operation = False
        
        # ===== 数据 =====
        self.lora_scores = []
        self.top_loras = []
        self.lora_files = []
        self.test_run_log = {}

    def _init_dimension_vars(self):
        """初始化维度变量"""
        for dim, options in self.dimensions.items():
            # 维度启用开关
            self.dim_vars[dim] = tk.BooleanVar(value=(dim == "prompt"))
            
            # 每个选项的开关（默认选中第一个）
            self.dim_options_vars[dim] = {}
            for opt in options:
                self.dim_options_vars[dim][opt] = tk.BooleanVar(value=(opt == options[0]))
            
    def setup_ui(self):
        """设置 UI"""
        frame = self.frame
        
        # 创建 Notebook 子标签页
        self.notebook = ttk.Notebook(frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ===== 子标签页1: 批量测试 =====
        self.test_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.test_frame, text="🚀 批量测试")
        self._setup_test_tab()
        
        # ===== 子标签页2: 分析管理 =====
        self.analyze_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analyze_frame, text="📊 分析管理")
        self._setup_analyze_tab()
    
    # ==================== 子标签页1: 批量测试 ====================

    def _setup_test_tab(self):
        """设置批量测试子标签页"""
        frame = self.test_frame
        row = 0
        
        # ===== 标题 =====
        title = ttk.Label(frame, text="🚀 LoRA 批量预览测试", font=("", 12, "bold"))
        title.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5, padx=5)
        row += 1
        
        # ===== 模型路径配置 =====
        model_frame = ttk.LabelFrame(frame, text="📦 模型配置", padding=5)
        model_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(model_frame, text="SD 1.5 模型:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.sd15_model_path_var, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(model_frame, text="浏览", command=lambda: self._browse_file(self.sd15_model_path_var)).grid(row=0, column=2, padx=5)
        
        ttk.Label(model_frame, text="SDXL 模型:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.sdxl_model_path_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(model_frame, text="浏览", command=lambda: self._browse_file(self.sdxl_model_path_var)).grid(row=1, column=2, padx=5)
        
        ttk.Label(model_frame, text="LoRA 目录:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.test_lora_dir_var, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(model_frame, text="浏览", command=lambda: self._browse_dir(self.test_lora_dir_var)).grid(row=2, column=2, padx=5)
        
        ttk.Label(model_frame, text="输出目录:").grid(row=3, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.output_previews_dir_var, width=50).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(model_frame, text="浏览", command=lambda: self._browse_dir(self.output_previews_dir_var)).grid(row=3, column=2, padx=5)
        
        row += 1
        
        # ===== 基础参数 =====
        param_frame = ttk.LabelFrame(frame, text="⚙️ 基础参数", padding=5)
        param_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        param_row1 = ttk.Frame(param_frame)
        param_row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(param_row1, text="SD 1.5 步数:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(param_row1, from_=1, to=50, textvariable=self.test_steps_sd15_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(param_row1, text="SDXL 步数:").pack(side=tk.LEFT, padx=15)
        ttk.Spinbox(param_row1, from_=1, to=50, textvariable=self.test_steps_sdxl_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(param_row1, text="筛选:").pack(side=tk.LEFT, padx=15)
        ttk.Combobox(param_row1, textvariable=self.test_filter_var, 
                     values=["all", "small", "medium", "large"], width=8, state="readonly").pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(param_row1, text="强制重跑", variable=self.test_re_run_var).pack(side=tk.LEFT, padx=15)

        # ===== 尺寸配置（新增） =====
        size_row = ttk.Frame(param_frame)
        size_row.pack(fill=tk.X, pady=2)

        ttk.Label(size_row, text="SD 1.5 尺寸:").pack(side=tk.LEFT, padx=5)
        size_combo_sd15 = ttk.Combobox(
            size_row,
            textvariable=self.test_size_sd15_var,
            values=["512x768", "512x1024", "576x1024", "640x960", "640x1024", "768x768", "768x1024"],
            width=10,
            state="readonly"
        )
        size_combo_sd15.pack(side=tk.LEFT, padx=5)

        ttk.Label(size_row, text="SDXL 尺寸:").pack(side=tk.LEFT, padx=15)
        size_combo_sdxl = ttk.Combobox(
            size_row,
            textvariable=self.test_size_sdxl_var,
            values=["1024x1024", "896x1152", "832x1216", "768x1344", "1152x896", "1216x832"],
            width=10,
            state="readonly"
        )
        size_combo_sdxl.pack(side=tk.LEFT, padx=5)

        # ===== 多尺寸测试模式（新增） =====
        multi_size_frame = ttk.LabelFrame(param_frame, text="📐 多尺寸测试", padding=3)
        multi_size_frame.pack(fill=tk.X, pady=3)

        multi_row1 = ttk.Frame(multi_size_frame)
        multi_row1.pack(fill=tk.X, pady=2)

        ttk.Checkbutton(
            multi_row1,
            text="☑ 启用多尺寸测试",
            variable=self.test_multi_size_var
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(multi_row1, text="💡 勾选后，每个 LoRA 会生成所有指定尺寸的图片", foreground="gray", font=("", 8)).pack(side=tk.LEFT, padx=15)

        multi_row2 = ttk.Frame(multi_size_frame)
        multi_row2.pack(fill=tk.X, pady=2)

        ttk.Label(multi_row2, text="SD 1.5 尺寸列表:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(multi_row2, textvariable=self.test_sizes_sd15_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Label(multi_row2, text="(逗号分隔)", foreground="gray", font=("", 8)).pack(side=tk.LEFT)

        multi_row3 = ttk.Frame(multi_size_frame)
        multi_row3.pack(fill=tk.X, pady=2)

        ttk.Label(multi_row3, text="SDXL 尺寸列表:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(multi_row3, textvariable=self.test_sizes_sdxl_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Label(multi_row3, text="(逗号分隔)", foreground="gray", font=("", 8)).pack(side=tk.LEFT)
                
        # ===== 提示词模板 =====
        param_row2 = ttk.Frame(param_frame)
        param_row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(param_row2, text="SD 1.5 提示词:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(param_row2, textvariable=self.test_prompt_sd15_var, width=45).pack(side=tk.LEFT, padx=5)
        
        param_row3 = ttk.Frame(param_frame)
        param_row3.pack(fill=tk.X, pady=2)
        
        ttk.Label(param_row3, text="SDXL 提示词:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(param_row3, textvariable=self.test_prompt_sdxl_var, width=45).pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # ===== 测试模式 (核心：用户选择要测试的维度) =====
        mode_frame = ttk.LabelFrame(frame, text="🔧 测试模式 (选择要测试的维度)", padding=5)
        mode_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1


                
        
        # 第一行：基础模式
        mode_row1 = ttk.Frame(mode_frame)
        mode_row1.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(mode_row1, text="☑ 基础测试 (SD1.5 + SDXL)", 
                        variable=self.test_mode_basic_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(mode_row1, text="v1", foreground="gray", font=("", 8)).pack(side=tk.LEFT)
        
        ttk.Checkbutton(mode_row1, text="☑ 多模型测试 (扫描所有模型)", 
                        variable=self.test_mode_multi_model_var).pack(side=tk.LEFT, padx=15)
        ttk.Label(mode_row1, text="v2", foreground="gray", font=("", 8)).pack(side=tk.LEFT)
        
        # 第二行：v3 高级模式
        mode_row2 = ttk.Frame(mode_frame)
        mode_row2.pack(fill=tk.X, pady=2)

        ttk.Checkbutton(mode_row2, text="☑ 多权重测试", 
                        variable=self.test_mode_multi_weight_var).pack(side=tk.LEFT, padx=5)
        ttk.Entry(mode_row2, textvariable=self.test_weights_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(mode_row2, text="v3", foreground="gray", font=("", 8)).pack(side=tk.LEFT)

        # 第三行：LoRA 叠加
        mode_row3 = ttk.Frame(mode_frame)
        mode_row3.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(mode_row3, text="☑ LoRA 叠加测试", 
                        variable=self.test_mode_combine_var).pack(side=tk.LEFT, padx=5)
        ttk.Entry(mode_row3, textvariable=self.test_combine_var, width=25).pack(side=tk.LEFT, padx=5)
        ttk.Label(mode_row3, text="(逗号分隔)", foreground="gray", font=("", 8)).pack(side=tk.LEFT)
        ttk.Label(mode_row3, text="v3", foreground="gray", font=("", 8)).pack(side=tk.LEFT, padx=5)
        
        row += 1

        # ===== 多维度风格（新增） =====
        dim_frame = ttk.LabelFrame(frame, text="🎨 多维度风格 (选择要测试的维度)", padding=5)
        dim_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1

        # 维度映射（中文显示）
        dim_labels = {
            "prompt": "📝 构图风格",
            "background": "🏠 背景",
            "lighting": "💡 光照",
            "quality": "🎯 画质",
            "clothing": "👗 服装",
            "expression": "😊 表情",
            "pose": "🧘 姿势",
        }

        for dim, options in self.dimensions.items():
            dim_row = ttk.Frame(dim_frame)
            dim_row.pack(fill=tk.X, pady=2)  # pady 改为 2 增加间距
            
            cb = ttk.Checkbutton(
                dim_row,
                text=dim_labels.get(dim, dim),
                variable=self.dim_vars[dim]
            )
            cb.pack(side=tk.LEFT, padx=5)
            
            # 选项使用更紧凑的布局
            for opt in options:
                var = self.dim_options_vars[dim][opt]
                ttk.Checkbutton(
                    dim_row,
                    text=opt,
                    variable=var
                ).pack(side=tk.LEFT, padx=2)
                
        
        # ===== 高级筛选 (v2/v3) =====
        filter_frame = ttk.LabelFrame(frame, text="📊 高级筛选", padding=5)
        filter_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        filter_row1 = ttk.Frame(filter_frame)
        filter_row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(filter_row1, text="模型范围:").pack(side=tk.LEFT, padx=5)
        ttk.Combobox(filter_row1, textvariable=self.test_model_scope_var,
                     values=["default", "all", "sd15", "sdxl"], width=8, state="readonly").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_row1, text="自定义模型:").pack(side=tk.LEFT, padx=15)
        ttk.Entry(filter_row1, textvariable=self.custom_models_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(filter_row1, text="(逗号分隔)", foreground="gray", font=("", 8)).pack(side=tk.LEFT)
        
        filter_row2 = ttk.Frame(filter_frame)
        filter_row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(filter_row2, text="关键词分组:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(filter_row2, textvariable=self.test_group_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_row2, text="最近 N 个:").pack(side=tk.LEFT, padx=15)
        ttk.Spinbox(filter_row2, from_=0, to=100, textvariable=self.test_recent_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_row2, text="最多测试:").pack(side=tk.LEFT, padx=15)
        ttk.Spinbox(filter_row2, from_=0, to=100, textvariable=self.test_max_loras_var, width=5).pack(side=tk.LEFT, padx=5)
        
        row += 1


        # ===== 测试范围（新增） =====
        scope_frame = ttk.LabelFrame(frame, text="🎯 测试范围", padding=5)
        scope_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1

        scope_row1 = ttk.Frame(scope_frame)
        scope_row1.pack(fill=tk.X, pady=2)

        ttk.Radiobutton(
            scope_row1,
            text="📦 全部 LoRA",
            variable=self.test_scope_var,
            value="all",
            command=self._on_scope_changed
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            scope_row1,
            text="📌 单个 LoRA",
            variable=self.test_scope_var,
            value="single",
            command=self._on_scope_changed
        ).pack(side=tk.LEFT, padx=15)

        scope_row2 = ttk.Frame(scope_frame)
        scope_row2.pack(fill=tk.X, pady=2)

        # 单个 LoRA 下拉选择
        ttk.Label(scope_row2, text="选择 LoRA:").pack(side=tk.LEFT, padx=5)
        self.single_lora_combo = ttk.Combobox(
            scope_row2,
            textvariable=self.test_single_lora_var,
            width=40,
            state="readonly"
        )
        self.single_lora_combo.pack(side=tk.LEFT, padx=5)
        self._refresh_single_lora_list()

        # 状态提示
        self.scope_status_label = ttk.Label(
            scope_row2,
            text="💡 将测试所有 LoRA",
            foreground="gray",
            font=("", 8)
        )
        self.scope_status_label.pack(side=tk.LEFT, padx=15)

        row += 1
        
        # ===== 操作按钮 =====
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=10)
        row += 1
        
        self.test_btn = ttk.Button(btn_frame, text="🚀 开始测试", command=self._start_batch_test)
        self.test_btn.pack(side=tk.LEFT, padx=5)
        
        self.test_cancel_btn = ttk.Button(btn_frame, text="⏹️ 取消", command=self._cancel_operation, state=tk.DISABLED)
        self.test_cancel_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="📁 打开输出", command=self._open_previews_output).pack(side=tk.LEFT, padx=5)
        
        # ===== 状态和日志 =====
        status_frame = ttk.Frame(frame)
        status_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        self.test_status_var = tk.StringVar(value="就绪")
        self.test_status_label = ttk.Label(status_frame, textvariable=self.test_status_var, foreground="blue")
        self.test_status_label.pack(side=tk.LEFT)
        
        self.test_progress_bar = ttk.Progressbar(status_frame, length=300, mode='determinate')
        self.test_progress_bar.pack(side=tk.RIGHT, padx=5)
        
        log_frame = ttk.LabelFrame(frame, text="📝 测试日志", padding=5)
        log_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        row += 1

        self._refresh_single_lora_list()
        self._on_scope_changed()  # 初始化状态
        
        self.test_log_text = tk.Text(log_frame, height=10, width=70, wrap=tk.WORD, state=tk.DISABLED)
        self.test_log_text.pack(fill=tk.BOTH, expand=True)
        
        # 设置行权重
        frame.rowconfigure(row, weight=1)
        frame.columnconfigure(1, weight=1)

    def _build_prompt_with_dimensions(self, base_prompt, negative):
        """根据选中的维度构建提示词
        Args:
            base_prompt: 基础提示词
            negative: 负面提示词
            combo: 指定的维度组合 (dict: {dim: option})，如果为 None 则使用所有选中的第一个
        """
    
        prompt_parts = [base_prompt]
        negative_parts = [negative]
        
        # 维度关键词映射
        dim_keywords = {
            "prompt": {
                "portrait": "portrait, headshot, face focused",
                "full_body": "full body shot, entire body visible, full length",
                "close_up": "close up shot, detailed view",
                "cinematic": "cinematic lighting, dramatic, movie still",
                "anime": "anime style, manga, vibrant colors",
            },
            "background": {
                "white": "white background, plain background",
                "studio": "studio photography, professional backdrop",
                "outdoor": "outdoor, natural setting",
                "beach": "on the beach, ocean background",
                "forest": "in the forest, trees, nature",
            },
            "lighting": {
                "natural": "natural lighting, soft daylight",
                "dramatic": "dramatic lighting, strong shadows",
                "soft": "soft lighting, diffused, gentle",
                "golden_hour": "golden hour, warm sunset light",
            },
            "quality": {
                "standard": "high quality, detailed",
                "photorealistic": "photorealistic, 8k, ultra HD",
                "artistic": "artistic, masterpiece, beautiful composition",
            },
            "clothing": {
                "casual": "casual clothes, everyday wear",
                "elegant": "elegant dress, formal wear",
                "swimsuit": "wearing swimsuit, bikini",
                "lingerie": "wearing lingerie, lace",
            },
            "expression": {
                "smiling": "smiling, happy expression",
                "seductive": "seductive gaze, sultry expression",
                "serious": "serious expression, intense look",
                "happy": "happy, joyful expression",
            },
            "pose": {
                "standing": "standing pose, upright",
                "sitting": "sitting pose, seated",
                "lying": "lying down, reclining",
                "dancing": "dancing, in motion",
            },
        }
        
        if combo is not None:
            # 使用指定的组合
            for dim, opt in combo.items():
                keyword = dim_keywords.get(dim, {}).get(opt, opt)
                prompt_parts.append(keyword)
        else:
            # 兼容旧逻辑：使用每个维度的第一个选中项
            for dim, options in self.dimensions.items():
                if not self.dim_vars[dim].get():
                    continue
                for opt in options:
                    if self.dim_options_vars[dim][opt].get():
                        keyword = dim_keywords.get(dim, {}).get(opt, opt)
                        prompt_parts.append(keyword)
                        break  # 只取第一个
        
        full_prompt = ", ".join(prompt_parts)
        full_negative = ", ".join(negative_parts)
        return full_prompt, full_negative
    
    def _refresh_single_lora_list(self):
        """刷新单个 LoRA 下拉列表"""
        test_dir = self.test_lora_dir_var.get()
        if os.path.exists(test_dir):
            files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
            files.sort()
            self.single_lora_combo['values'] = files
            if files and not self.test_single_lora_var.get():
                self.test_single_lora_var.set(files[0])
                # 如果当前是 single 模式，更新状态标签
                if self.test_scope_var.get() == "single":
                    self.scope_status_label.config(text=f"💡 将只测试: {files[0]}")

    def _on_scope_changed(self):
        """测试范围切换"""
        scope = self.test_scope_var.get()
        
        if scope == "all":
            self.single_lora_combo.config(state=tk.DISABLED)
            self.scope_status_label.config(text="💡 将测试所有 LoRA")
        elif scope == "single":
            self.single_lora_combo.config(state="readonly")
            selected = self.test_single_lora_var.get()
            if selected:
                self.scope_status_label.config(text=f"💡 将只测试: {selected}")
            else:
                self.scope_status_label.config(text="💡 请选择一个 LoRA")
            self._refresh_single_lora_list()
            
    # ==================== 子标签页2: 分析管理 ====================
    
    def _setup_analyze_tab(self):
        """设置分析管理子标签页"""
        frame = self.analyze_frame
        row = 0
        
        # ===== 标题 =====
        title = ttk.Label(frame, text="📊 LoRA 分析管理", font=("", 12, "bold"))
        title.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5, padx=5)
        row += 1
        
        # ===== 路径配置 =====
        path_frame = ttk.LabelFrame(frame, text="📁 路径配置", padding=5)
        path_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(path_frame, text="图片目录:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(path_frame, textvariable=self.image_dir_var, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(path_frame, text="浏览", command=lambda: self._browse_dir(self.image_dir_var)).grid(row=0, column=2, padx=5)
        
        ttk.Label(path_frame, text="输出列表:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(path_frame, textvariable=self.output_file_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Label(path_frame, text="Top K:").grid(row=1, column=2, sticky=tk.E, padx=5)
        ttk.Spinbox(path_frame, from_=10, to=100, textvariable=self.top_k_var, width=8).grid(row=1, column=3, padx=5)
        
        ttk.Label(path_frame, text="提取目录:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(path_frame, textvariable=self.extract_dir_var, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        
        row += 1
        
        # ===== 模型目录配置 =====
        model_frame = ttk.LabelFrame(frame, text="📂 模型目录配置", padding=5)
        model_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(model_frame, text="test_lora 目录:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.test_lora_dir_var, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(model_frame, text="浏览", command=lambda: self._browse_dir(self.test_lora_dir_var)).grid(row=0, column=2, padx=5)
        
        ttk.Label(model_frame, text="sd15-lora 目录:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.sd15_lora_dir_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Label(model_frame, text="sdxl-lora 目录:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.sdxl_lora_dir_var, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        
        row += 1
        
        # ===== 操作按钮 =====
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=10)
        row += 1
        
        ttk.Button(btn_frame, text="🔍 扫描分析", command=self._start_scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📋 显示排行", command=self._show_ranking).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📂 提取高分", command=self._extract_high_loras).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 过滤删除", command=self._filter_low_loras).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📝 重命名", command=self._rename_loras).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 同步目录", command=self._sync_loras).pack(side=tk.LEFT, padx=5)
        
        self.analyze_cancel_btn = ttk.Button(btn_frame, text="⏹️ 取消", command=self._cancel_operation, state=tk.DISABLED)
        self.analyze_cancel_btn.pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # ===== 状态 =====
        status_frame = ttk.Frame(frame)
        status_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        self.analyze_status_var = tk.StringVar(value="就绪")
        self.analyze_status_label = ttk.Label(status_frame, textvariable=self.analyze_status_var, foreground="blue")
        self.analyze_status_label.pack(side=tk.LEFT)
        
        self.analyze_progress_bar = ttk.Progressbar(status_frame, length=300, mode='determinate')
        self.analyze_progress_bar.pack(side=tk.RIGHT, padx=5)
        
        # ===== LoRA 列表 =====
        list_frame = ttk.LabelFrame(frame, text="📋 LoRA 列表", padding=5)
        list_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        row += 1
        
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(
            list_container,
            columns=("rank", "name", "score", "size_mb", "status"),
            show="headings",
            height=12
        )
        
        self.tree.heading("rank", text="排名")
        self.tree.heading("name", text="LoRA 名称")
        self.tree.heading("score", text="评分")
        self.tree.heading("size_mb", text="大小 (MB)")
        self.tree.heading("status", text="状态")
        
        self.tree.column("rank", width=50, anchor=tk.CENTER)
        self.tree.column("name", width=300, anchor=tk.W)
        self.tree.column("score", width=80, anchor=tk.CENTER)
        self.tree.column("size_mb", width=80, anchor=tk.CENTER)
        self.tree.column("status", width=80, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右键菜单
        self._create_context_menu()
        
        # ===== 日志 =====
        log_frame = ttk.LabelFrame(frame, text="📝 操作日志", padding=5)
        log_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        self.analyze_log_text = tk.Text(log_frame, height=6, width=70, wrap=tk.WORD, state=tk.DISABLED)
        self.analyze_log_text.pack(fill=tk.BOTH, expand=True)
        
        # 设置行权重
        frame.rowconfigure(row, weight=1)
        frame.columnconfigure(1, weight=1)
    
    # ==================== 辅助方法 ====================
    
    def _create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="📋 复制名称", command=self._copy_selected_name)
        self.context_menu.add_command(label="📂 打开所在目录", command=self._open_selected_dir)
        self.tree.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _copy_selected_name(self):
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0], "values")
            if values and len(values) > 1:
                self.app.root.clipboard_clear()
                self.app.root.clipboard_append(values[1])
                self._append_analyze_log(f"📋 已复制: {values[1]}")
    
    def _open_selected_dir(self):
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0], "values")
            if values and len(values) > 1:
                name = values[1]
                test_dir = self.test_lora_dir_var.get()
                if os.path.exists(test_dir):
                    for f in os.listdir(test_dir):
                        if name in f and f.endswith('.safetensors'):
                            path = os.path.join(test_dir, f)
                            if os.path.exists(path):
                                try:
                                    os.startfile(os.path.dirname(path))
                                except:
                                    pass
                                return
    
    def _browse_dir(self, var):
        dir_path = filedialog.askdirectory(title="选择目录")
        if dir_path:
            var.set(dir_path)
            # 如果是 test_lora_dir_var，刷新列表
            if var == self.test_lora_dir_var:
                self._refresh_single_lora_list()
    
    def _browse_file(self, var):
        file_path = filedialog.askopenfilename(
            title="选择模型文件",
            filetypes=[("模型文件", "*.safetensors *.ckpt"), ("所有文件", "*.*")]
        )
        if file_path:
            var.set(file_path)
    
    def _scan_lora_files(self):
        test_dir = self.test_lora_dir_var.get()
        if os.path.exists(test_dir):
            self.lora_files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
    
    def _open_previews_output(self):
        output_dir = self.output_previews_dir_var.get()
        if os.path.exists(output_dir):
            try:
                os.startfile(output_dir)
            except:
                pass
        else:
            messagebox.showinfo("提示", f"输出目录不存在: {output_dir}")
        
    def _get_filtered_lora_list(self):
        """获取筛选后的 LoRA 列表（支持全部/单个）"""
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            return []
        
        files = []
        for f in os.listdir(test_dir):
            if f.endswith('.safetensors'):
                path = os.path.join(test_dir, f)
                size_mb = os.path.getsize(path) / (1024 * 1024)
                mtime = os.path.getmtime(path)
                files.append({
                    "name": f,
                    "path": path,
                    "size_mb": size_mb,
                    "mtime": mtime
                })
        
        files.sort(key=lambda x: x["size_mb"])
        
        # ===== 应用大小筛选 =====
        filter_type = self.test_filter_var.get()
        if filter_type == "small":
            files = [f for f in files if f['size_mb'] < 50]
        elif filter_type == "medium":
            files = [f for f in files if 50 <= f['size_mb'] < 200]
        elif filter_type == "large":
            files = [f for f in files if f['size_mb'] >= 200]
        
        # ===== 应用范围筛选（新增） =====
        scope = self.test_scope_var.get()
        if scope == "single":
            single_name = self.test_single_lora_var.get()
            if single_name:
                files = [f for f in files if f["name"] == single_name]
        
        return files
    
    # ==================== 日志方法 ====================
    
    def _append_test_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        def update():
            try:
                self.test_log_text.config(state=tk.NORMAL)
                self.test_log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
                self.test_log_text.see(tk.END)
                self.test_log_text.config(state=tk.DISABLED)
            except:
                pass
        self.app.root.after(0, update)
    
    def _append_analyze_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        def update():
            try:
                self.analyze_log_text.config(state=tk.NORMAL)
                self.analyze_log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
                self.analyze_log_text.see(tk.END)
                self.analyze_log_text.config(state=tk.DISABLED)
            except:
                pass
        self.app.root.after(0, update)
    
    def _clear_test_log(self):
        def update():
            try:
                self.test_log_text.config(state=tk.NORMAL)
                self.test_log_text.delete("1.0", tk.END)
                self.test_log_text.config(state=tk.DISABLED)
            except:
                pass
        self.app.root.after(0, update)
    
    def _clear_analyze_log(self):
        def update():
            try:
                self.analyze_log_text.config(state=tk.NORMAL)
                self.analyze_log_text.delete("1.0", tk.END)
                self.analyze_log_text.config(state=tk.DISABLED)
            except:
                pass
        self.app.root.after(0, update)
    
    # ==================== 批量测试功能 ====================
    

    def _start_batch_test(self):
        """开始批量测试"""
        if self.is_testing:
            return
        
        # 检查是否至少选择了一种测试模式
        if not (self.test_mode_basic_var.get() or 
                self.test_mode_multi_model_var.get() or
                self.test_mode_multi_weight_var.get() or
                self.test_mode_combine_var.get()):
            messagebox.showwarning("提示", "请至少选择一种测试模式")
            return
        
        # ===== 检查 LoRA 目录 =====
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            messagebox.showwarning("提示", f"LoRA 目录不存在: {test_dir}")
            return
        
        # ===== 获取 LoRA 列表并应用筛选 =====
        lora_files = self._get_filtered_lora_list()
        lora_files = self._apply_advanced_filters(lora_files)
        
        if not lora_files:
            messagebox.showwarning("提示", "没有找到符合条件的 LoRA 文件")
            return
        
        # ===== 检查模型是否存在 =====
        if self.test_mode_basic_var.get() or self.test_mode_multi_model_var.get():
            if self.test_mode_basic_var.get():
                sd15_model = self.sd15_model_path_var.get()
                sdxl_model = self.sdxl_model_path_var.get()
                if not os.path.exists(sd15_model):
                    messagebox.showwarning("提示", f"SD 1.5 模型不存在: {sd15_model}")
                    return
                if not os.path.exists(sdxl_model):
                    messagebox.showwarning("提示", f"SDXL 模型不存在: {sdxl_model}")
                    return
            
            if self.test_mode_multi_model_var.get():
                models = self._get_model_list()
                if not models:
                    messagebox.showwarning("提示", "没有找到任何模型")
                    return
        
        # ===== 计算预计任务数 =====
        estimated_tasks = self._estimate_tasks(lora_files)
        
        # ===== 确认对话框 =====
        if not messagebox.askyesno("确认测试",
            f"将测试 {len(lora_files)} 个 LoRA\n"
            f"预计任务数: {estimated_tasks}\n"
            f"输出目录: {self.output_previews_dir_var.get()}\n\n"
            f"确定继续吗？"
        ):
            return
        
        # ===== 启动测试 =====
        self.is_testing = True
        self.cancel_operation = False
        self.test_btn.config(state=tk.DISABLED)
        self.test_cancel_btn.config(state=tk.NORMAL)
        self.test_progress_bar.config(value=0, maximum=100)
        self._clear_test_log()
        self._append_test_log(f"🚀 开始批量测试，共 {len(lora_files)} 个 LoRA")
        
        # 打印模式信息
        modes = []
        if self.test_mode_basic_var.get():
            modes.append("基础(v1)")
        if self.test_mode_multi_model_var.get():
            modes.append("多模型(v2)")
        if self.test_mode_multi_weight_var.get():
            modes.append("多权重(v3)")
        if self.test_mode_combine_var.get():
            modes.append("叠加(v3)")
        self._append_test_log(f"📋 测试模式: {', '.join(modes)}")
        self._append_test_log(f"📊 预计任务数: {estimated_tasks}")
        
        threading.Thread(target=self._run_batch_test, args=(lora_files,), daemon=True).start()

    def _apply_advanced_filters(self, lora_files):
        """应用高级筛选 (v3)"""
        if not lora_files:
            return lora_files
        
        # 关键词分组
        group_keyword = self.test_group_var.get().strip()
        if group_keyword:
            lora_files = [f for f in lora_files if group_keyword.lower() in f["name"].lower()]
        
        # 最近修改
        recent_n = self.test_recent_var.get()
        if recent_n > 0:
            lora_files.sort(key=lambda x: x.get("mtime", 0), reverse=True)
            lora_files = lora_files[:recent_n]
        
        # 最多测试
        max_loras = self.test_max_loras_var.get()
        if max_loras > 0:
            lora_files = lora_files[:max_loras]
        
        return lora_files

    def _get_dimension_combinations(self):
        """获取所有维度的选项组合"""
        import itertools
        
        # 获取每个维度选中的选项列表
        selected_options = []
        dim_names = []
        
        for dim, options in self.dimensions.items():
            if not self.dim_vars[dim].get():
                continue
            selected = [opt for opt in options if self.dim_options_vars[dim][opt].get()]
            if selected:
                selected_options.append(selected)
                dim_names.append(dim)
        
        if not selected_options:
            return [{}]
        
        # 生成所有组合
        combinations = []
        for combo in itertools.product(*selected_options):
            combo_dict = dict(zip(dim_names, combo))
            combinations.append(combo_dict)
        
        return combinations
        
    def _estimate_tasks(self, lora_files):
        """估算任务数"""
        base_count = len(lora_files)
        tasks = 0
        
        # 获取尺寸数量
        if self.test_multi_size_var.get():
            sd15_sizes = [s.strip() for s in self.test_sizes_sd15_var.get().split(',') if s.strip()]
            sdxl_sizes = [s.strip() for s in self.test_sizes_sdxl_var.get().split(',') if s.strip()]
        else:
            sd15_sizes = [self.test_size_sd15_var.get()]
            sdxl_sizes = [self.test_size_sdxl_var.get()]
        
        # ===== 计算维度组合数 =====
        dim_count = 1
        for dim, options in self.dimensions.items():
            if not self.dim_vars[dim].get():
                continue
            count = sum(1 for opt in options if self.dim_options_vars[dim][opt].get())
            if count > 0:
                dim_count *= count
        
        # 基础测试 (v1)
        if self.test_mode_basic_var.get():
            tasks += (base_count * len(sd15_sizes) + base_count * len(sdxl_sizes)) * dim_count
        
        # 多模型测试 (v2)
        if self.test_mode_multi_model_var.get():
            models = self._get_model_list()
            for model in models:
                if model["type"] == "sd15":
                    tasks += base_count * len(sd15_sizes) * dim_count
                else:
                    tasks += base_count * len(sdxl_sizes) * dim_count
        
        # 多权重测试 (v3)
        if self.test_mode_multi_weight_var.get():
            weights = self._get_weights_list()
            weight_count = len(weights)
            if self.test_mode_basic_var.get():
                tasks += (base_count * len(sd15_sizes) * weight_count + 
                         base_count * len(sdxl_sizes) * weight_count) * dim_count
        
        return tasks
    
    
    def _get_model_list(self):
        """获取模型列表 (v2)"""
        models = []
        scope = self.test_model_scope_var.get()
        
        # 扫描 SD 1.5 模型
        sd15_dir = os.path.dirname(self.sd15_model_path_var.get())
        if os.path.exists(sd15_dir):
            for f in os.listdir(sd15_dir):
                if f.endswith(('.safetensors', '.ckpt')):
                    models.append({
                        "name": f,
                        "path": os.path.join(sd15_dir, f),
                        "type": "sd15"
                    })
        
        # 扫描 SDXL 模型
        sdxl_dir = os.path.dirname(self.sdxl_model_path_var.get())
        if os.path.exists(sdxl_dir):
            for f in os.listdir(sdxl_dir):
                if f.endswith(('.safetensors', '.ckpt')):
                    models.append({
                        "name": f,
                        "path": os.path.join(sdxl_dir, f),
                        "type": "sdxl"
                    })
        
        # 根据范围筛选
        if scope == "sd15":
            models = [m for m in models if m["type"] == "sd15"]
        elif scope == "sdxl":
            models = [m for m in models if m["type"] == "sdxl"]
        elif scope == "default":
            # 使用默认模型
            default_names = [
                "aiiiiiii01_v10.safetensors",
                "realisticmix_iiV12Version12.safetensors",
                "anycharactermixBaked_v20BakedVae.safetensors",
                "asianrealisticSdlife_v40.safetensors",
                "t3_sdVer3.safetensors",
                "perfectionAsianILXL_v10.safetensors",
                "xlAsianRealisticMixNhiPNhChU_v10.safetensors"
            ]
            models = [m for m in models if m["name"] in default_names]
        
        # 自定义模型
        custom = self.custom_models_var.get().strip()
        if custom:
            custom_names = [n.strip() for n in custom.split(",")]
            custom_models = [m for m in models if any(n in m["name"] for n in custom_names)]
            if custom_models:
                models = custom_models
        
        return models


    def _get_weights_list(self):
        """获取权重列表 (v3)"""
        weights_str = self.test_weights_var.get().strip()
        if not weights_str:
            return [1.0]
        try:
            return [float(w.strip()) for w in weights_str.split(",") if w.strip()]
        except:
            return [1.0]


    def _get_combine_list(self):
        """获取 LoRA 叠加列表 (v3)"""
        combine_str = self.test_combine_var.get().strip()
        if not combine_str:
            return []
        return [s.strip() for s in combine_str.split(",") if s.strip()]
    
    def _run_batch_test(self, lora_files):
        """后台运行批量测试"""
        from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, EulerDiscreteScheduler
        
        output_dir = self.output_previews_dir_var.get()
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载运行日志
        run_log_path = os.path.join(output_dir, "run_log.json")
        if self.test_re_run_var.get():
            run_log = {}
            self._append_test_log("💥 强制重跑模式")
        else:
            run_log = self._load_run_log(run_log_path)
        
        model_type = self.test_model_type_var.get()
        total = len(lora_files)
        if model_type == "both":
            total *= 2
        
        pipe_sd15 = None
        pipe_sdxl = None
        processed = 0
        
        try:
            # ===== SD 1.5 阶段 =====
            if model_type in ["sd15", "both"]:
                sd15_model = self.sd15_model_path_var.get()
                self._append_test_log(f"📦 加载 SD 1.5: {os.path.basename(sd15_model)}")
                
                pipe_sd15 = StableDiffusionPipeline.from_single_file(
                    sd15_model,
                    torch_dtype=torch.float32,
                    safety_checker=None,
                    requires_safety_checker=False,
                    use_safetensors=True,
                    low_cpu_mem_usage=True
                )
                pipe_sd15.to("cpu")
                pipe_sd15.enable_vae_slicing()
                pipe_sd15.enable_attention_slicing()
                pipe_sd15.scheduler = EulerDiscreteScheduler.from_config(pipe_sd15.scheduler.config)
                
                self._append_test_log("✅ SD 1.5 加载完成")
                
                for idx, lora_info in enumerate(lora_files):
                    if self.cancel_operation:
                        break
                    self._test_single_lora(
                        pipe_sd15, lora_info, output_dir, 
                        is_sdxl=False, run_log=run_log, 
                        idx=idx, total=len(lora_files)
                    )
                    processed += 1
                    self._update_test_progress(processed, total)
                
                del pipe_sd15
                gc.collect()
                self._append_test_log("🗑️ SD 1.5 已卸载")
            
            # ===== SDXL 阶段 =====
            if model_type in ["sdxl", "both"] and not self.cancel_operation:
                sdxl_model = self.sdxl_model_path_var.get()
                self._append_test_log(f"📦 加载 SDXL: {os.path.basename(sdxl_model)}")
                
                pipe_sdxl = StableDiffusionXLPipeline.from_single_file(
                    sdxl_model,
                    torch_dtype=torch.float32,
                    safety_checker=None,
                    requires_safety_checker=False,
                    use_safetensors=True,
                    low_cpu_mem_usage=True
                )
                pipe_sdxl.to("cpu")
                pipe_sdxl.enable_vae_slicing()
                pipe_sdxl.enable_attention_slicing()
                pipe_sdxl.scheduler = EulerDiscreteScheduler.from_config(pipe_sdxl.scheduler.config)
                
                self._append_test_log("✅ SDXL 加载完成")
                
                for idx, lora_info in enumerate(lora_files):
                    if self.cancel_operation:
                        break
                    self._test_single_lora(
                        pipe_sdxl, lora_info, output_dir,
                        is_sdxl=True, run_log=run_log,
                        idx=idx, total=len(lora_files)
                    )
                    processed += 1
                    self._update_test_progress(processed, total)
                
                del pipe_sdxl
                gc.collect()
                self._append_test_log("🗑️ SDXL 已卸载")
            
            # ===== 生成对比图 =====
            if not self.cancel_operation and model_type == "both":
                self._append_test_log("🔄 生成对比图...")
                self._generate_comparison_images(lora_files, output_dir)
            
            # 保存运行日志
            self._save_run_log(run_log_path, run_log)
            
            if self.cancel_operation:
                self._append_test_log("⏹️ 测试已取消")
            else:
                self._append_test_log(f"✅ 测试完成！共处理 {processed} 个任务")

            # ===== 收集图片（可选） =====
            if messagebox.askyesno("收集图片", 
                "测试完成！是否将生成的预览图收集到 all_images 目录？\n\n"
                "这将在 LoRA 分析中使用。"):
                self._append_test_log("📦 正在收集图片...")
                self._collect_preview_images()
        
        except Exception as e:
            self._append_test_log(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_testing = False
            self.app.root.after(0, self._reset_test_ui)
    


    def _test_single_lora(self, pipe, lora_info, output_dir, is_sdxl=False, 
                          run_log=None, idx=0, total=1):
        """测试单个 LoRA（支持多尺寸和多维度风格组合）"""
        lora_name = lora_info["name"]
        lora_code = lora_name.replace('.safetensors', '')
        
        # 构建基础提示词
        if is_sdxl:
            base_prompt = self.test_prompt_sdxl_var.get().replace("NAME", lora_code)
            base_negative = self.test_negative_sdxl_var.get()
            steps = self.test_steps_sdxl_var.get()
            if self.test_multi_size_var.get():
                size_str = self.test_sizes_sdxl_var.get()
                sizes = [tuple(map(int, s.strip().split('x'))) for s in size_str.split(',') if s.strip()]
            else:
                size_str = self.test_size_sdxl_var.get()
                sizes = [tuple(map(int, size_str.split('x')))]
        else:
            base_prompt = self.test_prompt_sd15_var.get().replace("NAME", lora_code)
            base_negative = self.test_negative_sd15_var.get()
            steps = self.test_steps_sd15_var.get()
            if self.test_multi_size_var.get():
                size_str = self.test_sizes_sd15_var.get()
                sizes = [tuple(map(int, s.strip().split('x'))) for s in size_str.split(',') if s.strip()]
            else:
                size_str = self.test_size_sd15_var.get()
                sizes = [tuple(map(int, size_str.split('x')))]
        
        # ===== 获取所有维度组合 =====
        combinations = self._get_dimension_combinations()
        
        # 输出路径
        lora_dir = os.path.join(output_dir, lora_code)
        os.makedirs(lora_dir, exist_ok=True)
        
        stage_key_base = "sdxl" if is_sdxl else "sd15"
        
        # ===== 遍历所有组合 =====
        for combo in combinations:
            # 构建组合名称（用于文件名）
            combo_name = "_".join([f"{dim}_{opt}" for dim, opt in combo.items()])
            
            # 构建提示词
            prompt, negative = self._build_prompt_with_dimensions(base_prompt, base_negative, combo)
            
            # 对每个尺寸生成图片
            for size_idx, size in enumerate(sizes):
                size_label = f"{size[0]}x{size[1]}"
                
                # 生成唯一文件名
                if len(sizes) > 1:
                    out_path = os.path.join(lora_dir, f"{stage_key_base.upper()}_{combo_name}_{size_label}.png")
                    stage_key = f"{stage_key_base}_{combo_name}_{size_label}"
                else:
                    out_path = os.path.join(lora_dir, f"{stage_key_base.upper()}_{combo_name}.png")
                    stage_key = f"{stage_key_base}_{combo_name}"
                
                # 检查是否需要跳过
                if not self.test_re_run_var.get():
                    if run_log.get(lora_name, {}).get(stage_key, False):
                        continue
                    if os.path.exists(out_path):
                        if lora_name not in run_log:
                            run_log[lora_name] = {}
                        run_log[lora_name][stage_key] = True
                        self._save_run_log(os.path.join(self.output_previews_dir_var.get(), "run_log.json"), run_log)
                        continue
                
                try:
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    
                    generator = torch.Generator("cpu").manual_seed(42 + size_idx)
                    result = pipe(
                        prompt=prompt,
                        negative_prompt=negative,
                        num_inference_steps=steps,
                        guidance_scale=7.5,
                        height=size[1],
                        width=size[0],
                        generator=generator,
                        num_images_per_prompt=1
                    )
                    result.images[0].save(out_path)
                    
                    if lora_name not in run_log:
                        run_log[lora_name] = {}
                    run_log[lora_name][stage_key] = True
                    self._save_run_log(os.path.join(self.output_previews_dir_var.get(), "run_log.json"), run_log)
                    
                    self._append_test_log(f"   ✅ [{idx+1}/{total}] 已保存: {os.path.basename(out_path)}")
                    
                except Exception as e:
                    self._append_test_log(f"   ❌ [{idx+1}/{total}] 生成失败: {e}")
                
                gc.collect()
            

    def _generate_comparison_images(self, lora_files, output_dir):
        """生成对比图"""
        for lora_info in lora_files:
            lora_code = lora_info["name"].replace('.safetensors', '')
            lora_dir = os.path.join(output_dir, lora_code)
            
            sd15_path = os.path.join(lora_dir, "SD15.png")
            sdxl_path = os.path.join(lora_dir, "SDXL.png")
            combined_out = os.path.join(lora_dir, "对比图.png")
            
            if os.path.exists(sd15_path) and os.path.exists(sdxl_path):
                if not os.path.exists(combined_out) or self.test_re_run_var.get():
                    try:
                        img1 = Image.open(sd15_path)
                        img2 = Image.open(sdxl_path)
                        max_height = max(img1.height, img2.height)
                        if img1.height < max_height:
                            img1 = img1.resize((img1.width, max_height))
                        if img2.height < max_height:
                            img2 = img2.resize((img2.width, max_height))
                        total_width = img1.width + img2.width
                        new_img = Image.new('RGB', (total_width, max_height + 40))
                        new_img.paste(img1, (0, 20))
                        new_img.paste(img2, (img1.width, 20))
                        draw = ImageDraw.Draw(new_img)
                        draw.line([(img1.width, 0), (img1.width, max_height + 40)], fill="white", width=2)
                        draw.text((20, 4), "⬅️ SD 1.5", fill="black")
                        draw.text((img1.width + 20, 4), "SDXL ➡️", fill="black")
                        new_img.save(combined_out)
                        self._append_test_log(f"   ✅ {lora_code} 对比图已生成")
                    except Exception as e:
                        self._append_test_log(f"   ⚠️ {lora_code} 对比图生成失败: {e}")
    
    def _load_run_log(self, log_path):
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_run_log(self, log_path, log_data):
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            pass
    
    def _update_test_progress(self, current, total):
        progress = (current / total) * 100
        self.app.root.after(0, lambda: self.test_progress_bar.config(value=progress))
        self.app.root.after(0, lambda: self.test_status_var.set(f"测试中... {current}/{total}"))
    
    def _reset_test_ui(self):
        self.test_btn.config(state=tk.NORMAL)
        self.test_cancel_btn.config(state=tk.DISABLED)
        self.test_progress_bar.config(value=0)
        self.test_status_var.set("就绪")

    def _collect_preview_images(self):
        """收集预览图到 all_images 目录"""
        source_dir = self.output_previews_dir_var.get()
        target_dir = "output/all_images"
        
        if not os.path.exists(source_dir):
            self._append_test_log("❌ 源目录不存在")
            return
        
        try:
            #from PIL import Image
            import shutil
            from pathlib import Path
            
            os.makedirs(target_dir, exist_ok=True)
            used_names = set()
            copied = 0
            
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    ext = Path(file).suffix.lower()
                    if ext in {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}:
                        source_path = Path(root) / file
                        
                        # 生成唯一文件名
                        rel_path = Path(root).relative_to(source_dir)
                        folder_name = '_'.join(rel_path.parts) + '_' if rel_path != Path('.') else ''
                        original_name = Path(file).stem
                        new_filename = f"{folder_name}{original_name}.jpg"
                        
                        # 处理重名
                        counter = 1
                        final_filename = new_filename
                        while final_filename in used_names:
                            final_filename = f"{folder_name}{original_name}_{counter}.jpg"
                            counter += 1
                        
                        used_names.add(final_filename)
                        target_path = Path(target_dir) / final_filename
                        
                        # 转换并保存
                        try:
                            img = Image.open(source_path)
                            if img.mode in ('RGBA', 'LA', 'P'):
                                background = Image.new('RGB', img.size, (255, 255, 255))
                                if img.mode == 'P':
                                    img = img.convert('RGBA')
                                if img.mode == 'RGBA':
                                    background.paste(img, mask=img.split()[-1])
                                else:
                                    background.paste(img)
                                img = background
                            elif img.mode != 'RGB':
                                img = img.convert('RGB')
                            img.save(target_path, 'JPEG', quality=90, optimize=True)
                            copied += 1
                        except Exception as e:
                            self._append_test_log(f"   ⚠️ 转换失败: {file} - {e}")
            
            self._append_test_log(f"✅ 图片收集完成！共 {copied} 张图片")
            self._append_test_log(f"📁 保存到: {target_dir}")
            
        except Exception as e:
            self._append_test_log(f"❌ 图片收集失败: {e}")
        
    # ==================== 分析功能（从之前的代码迁移） ====================
    
    def _start_scan(self):
        """开始扫描分析"""
        if self.is_scanning:
            return
        
        image_dir = self.image_dir_var.get()
        if not os.path.exists(image_dir):
            messagebox.showwarning("提示", f"图片目录不存在: {image_dir}")
            return
        
        self.is_scanning = True
        self.cancel_operation = False
        self._set_analyze_buttons_state(tk.DISABLED)
        self.analyze_cancel_btn.config(state=tk.NORMAL)
        self.analyze_progress_bar.config(value=0, maximum=100)
        
        self._clear_analyze_log()
        self._append_analyze_log("🔍 开始扫描分析...")
        self.analyze_status_var.set("扫描中...")
        
        threading.Thread(target=self._run_scan, daemon=True).start()
    
    def _run_scan(self):
        """后台运行扫描"""
        try:
            import open_clip
            #from PIL import Image
            
            image_dir = self.image_dir_var.get()
            top_k = self.top_k_var.get()
            
            self._append_analyze_log("📦 正在加载 CLIP 模型...")
            
            model, _, preprocess = open_clip.create_model_and_transforms(
                'ViT-B-32', pretrained='laion2b_s34b_b79k'
            )
            tokenizer = open_clip.get_tokenizer('ViT-B-32')
            
            positive_texts = [
                "a sexy woman", "a beautiful woman", "large breasts", 
                "seductive pose", "hot female"
            ]
            negative_texts = [
                "a man", "a boy", "a child", "ugly", "clothed in heavy coat"
            ]
            
            with torch.no_grad():
                pos_tokens = tokenizer(positive_texts)
                pos_embeddings = model.encode_text(pos_tokens)
                pos_embeddings /= pos_embeddings.norm(dim=-1, keepdim=True)
                positive_score = pos_embeddings.mean(dim=0)
                
                neg_tokens = tokenizer(negative_texts)
                neg_embeddings = model.encode_text(neg_tokens)
                neg_embeddings /= neg_embeddings.norm(dim=-1, keepdim=True)
                negative_score = neg_embeddings.mean(dim=0)
            
            self._append_analyze_log(f"📁 扫描目录: {image_dir}")
            
            files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            total = len(files)
            
            lora_scores = defaultdict(list)
            
            for idx, filename in enumerate(files):
                if self.cancel_operation:
                    self._append_analyze_log("⏹️ 已取消扫描")
                    break
                
                progress = (idx + 1) / total * 100
                self.app.root.after(0, lambda p=progress: self.analyze_progress_bar.config(value=p))
                
                if idx % 10 == 0:
                    self.app.root.after(0, lambda i=idx, t=total: 
                        self.analyze_status_var.set(f"扫描中... {i+1}/{t}"))
                
                try:
                    image_path = os.path.join(image_dir, filename)
                    image = preprocess(Image.open(image_path).convert('RGB')).unsqueeze(0)
                    
                    with torch.no_grad():
                        image_features = model.encode_image(image)
                        image_features /= image_features.norm(dim=-1, keepdim=True)
                        score = (image_features @ positive_score).item() - (image_features @ negative_score).item()
                        
                        lora_name = filename.split('_')[0] if '_' in filename else filename
                        lora_scores[lora_name].append(score)
                except Exception as e:
                    continue
            
            if self.cancel_operation:
                return
            
            avg_scores = {k: sum(v)/len(v) for k, v in lora_scores.items()}
            sorted_loras = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
            
            self.lora_scores = sorted_loras
            self.top_loras = [name for name, _ in sorted_loras[:top_k]]
            
            output_file = self.output_file_var.get()
            os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== 高分 LoRA 排行 ===\n\n")
                for i, (lora, score) in enumerate(sorted_loras[:top_k], 1):
                    f.write(f"{i:02d}. {lora} (评分: {score:.4f})\n")
            
            self._append_analyze_log(f"✅ 扫描完成！共 {len(sorted_loras)} 个 LoRA")
            self._append_analyze_log(f"📄 列表已保存: {output_file}")
            
            self.app.root.after(0, self._update_tree)
            
        except Exception as e:
            self._append_analyze_log(f"❌ 扫描失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_scanning = False
            self.app.root.after(0, self._reset_analyze_ui)
    
    def _update_tree(self):
        """更新树形列表"""
        self.tree.delete(*self.tree.get_children())
        
        test_dir = self.test_lora_dir_var.get()
        test_files = set(os.listdir(test_dir)) if os.path.exists(test_dir) else set()
        
        for i, (name, score) in enumerate(self.lora_scores[:100], 1):
            size_mb = 0
            status = "❌ 未找到"
            
            for f in test_files:
                if name in f and f.endswith('.safetensors'):
                    size_mb = os.path.getsize(os.path.join(test_dir, f)) / (1024 * 1024)
                    status = "✅ 存在"
                    break
            
            if i <= self.top_k_var.get():
                status = "⭐ " + status
            
            self.tree.insert("", tk.END, values=(i, name[:60], f"{score:.4f}", f"{size_mb:.1f}", status))
    
    def _show_ranking(self):
        if not self.lora_scores:
            messagebox.showinfo("提示", "请先运行扫描分析")
            return
        self._update_tree()
        self._append_analyze_log(f"📋 显示排行，共 {len(self.lora_scores)} 个 LoRA")
    
    def _extract_high_loras(self):
        if not self.top_loras:
            messagebox.showinfo("提示", "请先运行扫描分析")
            return
        
        if not messagebox.askyesno("确认提取",
            f"将复制前 {self.top_k_var.get()} 个 LoRA 的图片到:\n{self.extract_dir_var.get()}\n\n确定继续吗？"
        ):
            return
        
        self._start_analyze_operation("📂 提取高分 LoRA...")
        threading.Thread(target=self._run_extract, daemon=True).start()
    
    def _run_extract(self):
        try:
            image_dir = self.image_dir_var.get()
            extract_dir = self.extract_dir_var.get()
            
            os.makedirs(extract_dir, exist_ok=True)
            
            files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            copied = 0
            
            for idx, filename in enumerate(files):
                if self.cancel_operation:
                    break
                
                candidate_name = filename.split('_')[0]
                if candidate_name in self.top_loras:
                    src = os.path.join(image_dir, filename)
                    dst = os.path.join(extract_dir, filename)
                    shutil.copy2(src, dst)
                    copied += 1
                
                if idx % 10 == 0:
                    self.app.root.after(0, lambda i=idx, t=len(files): 
                        self.analyze_progress_bar.config(value=(i+1)/t*100))
            
            self._append_analyze_log(f"✅ 提取完成！共复制 {copied} 张图片到 {extract_dir}")
        except Exception as e:
            self._append_analyze_log(f"❌ 提取失败: {e}")
        finally:
            self._reset_analyze_ui()
    
    def _filter_low_loras(self):
        if not self.lora_scores:
            messagebox.showinfo("提示", "请先运行扫描分析")
            return
        
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            messagebox.showwarning("提示", f"目录不存在: {test_dir}")
            return
        
        keep_names = set(self.top_loras)
        files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
        to_delete = []
        
        for filename in files:
            kept = False
            for name in keep_names:
                if name in filename:
                    kept = True
                    break
            if not kept:
                to_delete.append(filename)
        
        if not to_delete:
            messagebox.showinfo("提示", "没有需要删除的文件")
            return
        
        if not messagebox.askyesno("确认删除",
            f"将删除 {len(to_delete)} 个低分 LoRA 文件\n\n"
            f"保留: {len(keep_names)} 个\n"
            f"删除: {len(to_delete)} 个\n\n"
            f"确定继续吗？"
        ):
            return
        
        self._start_analyze_operation("🗑️ 过滤低分 LoRA...")
        threading.Thread(target=self._run_filter, args=(to_delete,), daemon=True).start()
    
    def _run_filter(self, to_delete):
        try:
            test_dir = self.test_lora_dir_var.get()
            deleted = 0
            
            for idx, filename in enumerate(to_delete):
                if self.cancel_operation:
                    break
                
                filepath = os.path.join(test_dir, filename)
                try:
                    os.remove(filepath)
                    deleted += 1
                    if idx % 5 == 0:
                        self._append_analyze_log(f"   🗑️ 已删除: {filename}")
                except Exception as e:
                    self._append_analyze_log(f"   ❌ 删除失败 {filename}: {e}")
                
                self.app.root.after(0, lambda i=idx, t=len(to_delete): 
                    self.analyze_progress_bar.config(value=(i+1)/t*100))
            
            self._append_analyze_log(f"✅ 过滤完成！共删除 {deleted} 个文件")
        except Exception as e:
            self._append_analyze_log(f"❌ 过滤失败: {e}")
        finally:
            self._reset_analyze_ui()
            self._scan_lora_files()
            self._update_tree()
    
    def _rename_loras(self):
        if not self.top_loras:
            messagebox.showinfo("提示", "请先运行扫描分析")
            return
        
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            messagebox.showwarning("提示", f"目录不存在: {test_dir}")
            return
        
        if not messagebox.askyesno("确认重命名",
            f"将按排名重命名 test_lora 目录中的文件\n\n"
            f"共 {len(self.top_loras)} 个文件\n"
            f"格式: 01_xxx.safetensors\n\n"
            f"确定继续吗？"
        ):
            return
        
        self._start_analyze_operation("📝 重命名 LoRA...")
        threading.Thread(target=self._run_rename, daemon=True).start()
    
    def _run_rename(self):
        try:
            test_dir = self.test_lora_dir_var.get()
            files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
            
            renamed = 0
            skipped = 0
            
            for idx, target_name in enumerate(self.top_loras, 1):
                if self.cancel_operation:
                    break
                
                clean_name = re.sub(r'[\\/*?:"<>|]', '_', target_name)
                new_filename = f"{idx:02d}_{clean_name}.safetensors"
                new_path = os.path.join(test_dir, new_filename)
                
                if os.path.exists(new_path):
                    skipped += 1
                    continue
                
                found = False
                for old_filename in files:
                    if old_filename.startswith(f"{idx:02d}_"):
                        found = True
                        break
                    if target_name in old_filename:
                        old_path = os.path.join(test_dir, old_filename)
                        try:
                            os.rename(old_path, new_path)
                            renamed += 1
                            found = True
                            files.remove(old_filename)
                            self._append_analyze_log(f"   ✅ [{idx:02d}] {old_filename} -> {new_filename}")
                            break
                        except Exception as e:
                            self._append_analyze_log(f"   ❌ 重命名失败: {e}")
                
                if not found:
                    self._append_analyze_log(f"   ⚠️ [{idx:02d}] 未找到匹配: {target_name}")
                    skipped += 1
                
                self.app.root.after(0, lambda i=idx, t=len(self.top_loras): 
                    self.analyze_progress_bar.config(value=(i+1)/t*100))
            
            self._append_analyze_log(f"✅ 重命名完成！成功: {renamed}, 跳过: {skipped}")
        except Exception as e:
            self._append_analyze_log(f"❌ 重命名失败: {e}")
        finally:
            self._reset_analyze_ui()
            self._scan_lora_files()
            self._update_tree()
    
    def _sync_loras(self):
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            messagebox.showwarning("提示", f"test_lora 目录不存在: {test_dir}")
            return
        
        if not messagebox.askyesno("确认同步",
            "将按文件大小判断架构，分别同步到 sd15-lora 和 sdxl-lora 目录\n\n确定继续吗？"
        ):
            return
        
        self._start_analyze_operation("🔄 同步 LoRA...")
        threading.Thread(target=self._run_sync, daemon=True).start()
    
    def _run_sync(self):
        try:
            test_dir = self.test_lora_dir_var.get()
            sd15_dir = self.sd15_lora_dir_var.get()
            sdxl_dir = self.sdxl_lora_dir_var.get()
            
            os.makedirs(sd15_dir, exist_ok=True)
            os.makedirs(sdxl_dir, exist_ok=True)
            
            files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
            
            sd15_copied = 0
            sdxl_copied = 0
            unknown = 0
            
            for idx, filename in enumerate(files):
                if self.cancel_operation:
                    break
                
                filepath = os.path.join(test_dir, filename)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                
                if size_mb < 200:
                    dst_dir = sd15_dir
                    sd15_copied += 1
                elif size_mb >= 200:
                    dst_dir = sdxl_dir
                    sdxl_copied += 1
                else:
                    unknown += 1
                    continue
                
                dst_path = os.path.join(dst_dir, filename)
                if not os.path.exists(dst_path):
                    shutil.copy2(filepath, dst_path)
                
                if idx % 10 == 0:
                    self.app.root.after(0, lambda i=idx, t=len(files): 
                        self.analyze_progress_bar.config(value=(i+1)/t*100))
            
            self._append_analyze_log(f"✅ 同步完成！")
            self._append_analyze_log(f"   SD 1.5: {sd15_copied} 个 → {sd15_dir}")
            self._append_analyze_log(f"   SDXL: {sdxl_copied} 个 → {sdxl_dir}")
            if unknown:
                self._append_analyze_log(f"   ⚠️ 无法判断: {unknown} 个")
        except Exception as e:
            self._append_analyze_log(f"❌ 同步失败: {e}")
        finally:
            self._reset_analyze_ui()
    
    # ==================== UI 控制方法 ====================
    
    def _start_analyze_operation(self, status):
        self.is_processing = True
        self.cancel_operation = False
        self._set_analyze_buttons_state(tk.DISABLED)
        self.analyze_cancel_btn.config(state=tk.NORMAL)
        self.analyze_progress_bar.config(value=0, maximum=100)
        self.analyze_status_var.set(status)
        self._append_analyze_log(status)
    
    def _reset_analyze_ui(self):
        self.is_scanning = False
        self.is_processing = False
        self._set_analyze_buttons_state(tk.NORMAL)
        self.analyze_cancel_btn.config(state=tk.DISABLED)
        self.analyze_progress_bar.config(value=0)
        self.analyze_status_var.set("就绪")
    
    def _set_analyze_buttons_state(self, state):
        for child in self.analyze_frame.winfo_children():
            if isinstance(child, ttk.Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, ttk.Button) and btn != self.analyze_cancel_btn:
                        try:
                            btn.config(state=state)
                        except:
                            pass
    
    def _cancel_operation(self):
        self.cancel_operation = True
        self._append_test_log("⏹️ 正在取消...")
        self._append_analyze_log("⏹️ 正在取消...")
        self.test_cancel_btn.config(state=tk.DISABLED)
        self.analyze_cancel_btn.config(state=tk.DISABLED)