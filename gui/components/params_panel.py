#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
共享参数面板 - 所有 Tab 共用的生成参数控件
"""

import tkinter as tk
from tkinter import ttk


class ParamsPanel:
    """共享参数面板 - 单例模式，所有 Tab 共享同一组参数"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, parent=None):
        # 防止重复初始化
        if ParamsPanel._initialized:
            return
        ParamsPanel._initialized = True
        
        self.parent = parent
        self.frame = None
        
        # ===== 参数变量 =====
        # ✅ 修改：在 __init__ 时加载配置
        from config.app_config import app_config
        gen_cfg = app_config.generation
        
        # ===== 参数变量 =====
        self.steps_var = tk.IntVar(value=gen_cfg.steps["default"])  # 改成 default: 10
        self.cfg_var = tk.DoubleVar(value=gen_cfg.cfg["default"])   # 改成 default: 7.5
        self.seed_var = tk.IntVar(value=-1)
        self.width_var = tk.IntVar(value=gen_cfg.size["default_width"])  # ✅ 顺便改尺寸默认值
        self.height_var = tk.IntVar(value=gen_cfg.size["default_height"]) # ✅ 顺便改尺寸默认值
        self.num_images_var = tk.IntVar(value=1)

        # 👇 【在此处新增高清修复变量】 👇
        self.hires_fix_var = tk.BooleanVar(value=False)        # 是否开启高清修复
        self.hires_scale_var = tk.DoubleVar(value=1.5)         # 放大倍数
        self.hires_denoise_var = tk.DoubleVar(value=0.4)       # 重绘幅度
        # 👆 新增结束 👆
        

        # ===== 水印去除参数 =====
        # ✅ 把 True 改为从配置读取（如果 JSON 里没有，默认也是 True）
        # 使用 getattr 确保安全
        default_wm = getattr(app_config.generation, "default_remove_watermark", True)
        
        self.remove_watermark_var = tk.BooleanVar(value=default_wm)
        self.watermark_strength_var = tk.StringVar(value="strong")
        self.watermark_methods_var = tk.StringVar(value="all")
        self.watermark_auto_detect_var = tk.BooleanVar(value=True)
        self.watermark_post_process_var = tk.BooleanVar(value=True)

        # ===== 调度器选择 =====
        self.scheduler_var = tk.StringVar(value="euler")
        
        # ===== 预设尺寸 (名称, 宽度, 高度, 描述显示) =====
        self.preset_sizes = [
            ("📐 标全(512x768)", 512, 768),
            ("📏 细全(512x1024)", 512, 1024),
            ("🖼️ 高全(640x960)", 640, 960),
            ("💎 极全(640x1024)", 640, 1024),
            ("🌉 超长(576x1024)", 576, 1024),
            ("⬜ 方图(768x768)", 768, 768),
            ("🌅 横图(896x512)", 896, 512),
            ("🟥 HD 方图(1024x1024)", 1024, 1024),  # ✅ 新增，适合 SDXL 或 CPU 高清
            ("📺 宽屏(1024x512)", 1024, 512),      # ✅ 新增，适合宽幅背景
        ]

        # ===== 图片后期处理参数 =====
        self.clear_metadata_var = tk.BooleanVar(value=False)
        self.inject_exif_var = tk.BooleanVar(value=False)
        self.realistic_var = tk.BooleanVar(value=False)
        self.camera_var = tk.StringVar(value="sony_a7iv")
        self.realistic_strength_var = tk.StringVar(value="medium")
    
        if parent:
            self.create_widgets(parent)
    
    def create_widgets(self, parent):
        """创建控件"""
        self.parent = parent
        self.frame = ttk.Frame(parent)
        
        row = 0
        
        # ===== 第一模块：基础参数 =====
        param_row1 = ttk.Frame(self.frame)
        param_row1.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        # 在函数里加载配置
        from config.app_config import app_config
        gen_cfg = app_config.generation

        # ✅ 修改步数 Spinbox
        ttk.Label(param_row1, text="步数:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(param_row1, 
                    from_=gen_cfg.steps["min"],       # 动态读取最小值
                    to=gen_cfg.steps["max"],          # 动态读取最大值
                    textvariable=self.steps_var, 
                    width=5).pack(side=tk.LEFT)

        # ✅ 修改 CFG Spinbox
        ttk.Label(param_row1, text="CFG:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(param_row1, 
                    from_=gen_cfg.cfg["min"],         # 动态读取最小值
                    to=gen_cfg.cfg["max"],            # 动态读取最大值
                    textvariable=self.cfg_var, 
                    width=5, 
                    increment=0.5).pack(side=tk.LEFT)
        
        ttk.Label(param_row1, text="种子:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(param_row1, from_=-1, to=999999, textvariable=self.seed_var, width=8).pack(side=tk.LEFT)
        
        ttk.Label(param_row1, text="尺寸:").pack(side=tk.LEFT, padx=5)
        # ✅ 修改：宽度从配置读取
        ttk.Spinbox(param_row1, 
                    from_=gen_cfg.size["min_width"], 
                    to=gen_cfg.size["max_width"], 
                    textvariable=self.width_var, 
                    width=5, 
                    increment=64).pack(side=tk.LEFT)
        ttk.Label(param_row1, text="x").pack(side=tk.LEFT)
        # ✅ 修改：高度从配置读取
        ttk.Spinbox(param_row1, 
                    from_=gen_cfg.size["min_height"], 
                    to=gen_cfg.size["max_height"], 
                    textvariable=self.height_var, 
                    width=5, 
                    increment=64).pack(side=tk.LEFT)
        
        # ✅ 【修改】数量 Spinbox 从配置读取最大值
        ttk.Label(param_row1, text="数量:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(param_row1, 
                    from_=1, 
                    to=gen_cfg.max_images,      # ✅ 从 JSON 读取最大数量 (4)
                    textvariable=self.num_images_var, 
                    width=3).pack(side=tk.LEFT)
        
        row += 1

        # ✅ 调度器选择（放在数量后面）
        ttk.Label(param_row1, text="调度器:").pack(side=tk.LEFT, padx=5)
        
        # ✅ 定义切换事件（必须在 bind 之前）
        def on_scheduler_change(event):
            from utils.scheduler_factory import get_scheduler_recommended_steps
            scheduler = self.scheduler_var.get()
            recommended = get_scheduler_recommended_steps(scheduler)
            # 更新步数为推荐值
            self.steps_var.set(recommended)
            print(f"🔄 切换到 {scheduler}，推荐步数: {recommended}")
    
        scheduler_combo = ttk.Combobox(
            param_row1,
            textvariable=self.scheduler_var,
            values=[
                "euler",           # EulerDiscreteScheduler - 稳定写实
                "euler_ancestral", # EulerAncestralDiscreteScheduler - 创造性强
                "dpm",             # DPMSolverMultistepScheduler - 速度快
                "dpm++",           # DPMSolver++ - 更优版本
                "lms",             # LMSDiscreteScheduler - 艺术风格
                "heun",            # HeunDiscreteScheduler - 高精度
                "pndm",            # PNDMScheduler - 经典稳定
                "unipc",           # UniPCMultistepScheduler - 极速
                "deis",            # DEISMultistepScheduler - 快速高质量
                "ddim",            # DDIMScheduler - 确定性
                "ddpm",            # DDPMScheduler - 标准扩散
                "kdpm2",           # KDPM2DiscreteScheduler - Karras 高画质
                "kdpm2_ancestral", # KDPM2AncestralDiscreteScheduler - Karras 创意
            ],
            width=10,
            state="readonly"
        )
        scheduler_combo.pack(side=tk.LEFT, padx=5)
        scheduler_combo.set("euler")  # 默认
        scheduler_combo.bind('<<ComboboxSelected>>', on_scheduler_change)
        
        # ===== 第二模块：预设尺寸 =====
        param_row2 = ttk.Frame(self.frame)
        param_row2.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        # ✅ 第 1 步：把文字放在最左边（不再占用整行）
        ttk.Label(param_row2, text="预设尺寸:").pack(side=tk.LEFT, padx=5)
        
        # ✅ 第 2 步：创建一个专门装按钮的容器，放在文字的右边
        btn_container = ttk.Frame(param_row2)
        btn_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # ✅ 第 3 步：在这个容器里分三行放按钮
        
        # 第一行：标全、细全、高全
        row2_top = ttk.Frame(btn_container)
        row2_top.pack(side=tk.TOP, fill=tk.X, pady=1)
        for label, w, h in self.preset_sizes[0:3]:
            btn = ttk.Button(row2_top, text=label, width=16, command=lambda w=w, h=h: self._set_size(w, h))
            btn.pack(side=tk.LEFT, padx=2)
        
        # 第二行：极全、超长、方图
        row2_mid = ttk.Frame(btn_container)
        row2_mid.pack(side=tk.TOP, fill=tk.X, pady=1)
        for label, w, h in self.preset_sizes[3:6]:
            btn = ttk.Button(row2_mid, text=label, width=16, command=lambda w=w, h=h: self._set_size(w, h))
            btn.pack(side=tk.LEFT, padx=2)
        
        # 第三行：横图、HD方图、宽屏
        row2_bottom = ttk.Frame(btn_container)
        row2_bottom.pack(side=tk.TOP, fill=tk.X, pady=1)
        for label, w, h in self.preset_sizes[6:9]:
            btn = ttk.Button(row2_bottom, text=label, width=16, command=lambda w=w, h=h: self._set_size(w, h))
            btn.pack(side=tk.LEFT, padx=2)
        
        row += 1

        # 第三模块：👇 【在此处新增高清修复的UI】 👇
        hires_frame = ttk.LabelFrame(self.frame, text="🔍 高清修复 (Hires. fix)", padding=5)
        hires_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2, padx=5)
        row += 1
        
        ttk.Checkbutton(hires_frame, text="启用高清修复", variable=self.hires_fix_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(hires_frame, text="放大倍数:").pack(side=tk.LEFT, padx=5)
        ttk.Combobox(hires_frame, textvariable=self.hires_scale_var, values=[1.5, 2.0, 3.0], width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(hires_frame, text="重绘幅度:").pack(side=tk.LEFT, padx=5)
        ttk.Combobox(hires_frame, textvariable=self.hires_denoise_var, values=[0.3, 0.4, 0.5, 0.6], width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(hires_frame, text="💡 放大后重绘细节，适合全身照", foreground="gray", font=("", 8)).pack(side=tk.LEFT, padx=5)
        # 👆 新增结束 👆  
        
        # ===== 第四模块：水印去除 =====
        param_row3 = ttk.Frame(self.frame)
        param_row3.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        ttk.Checkbutton(
            param_row3,
            text="🚫 启用水印去除",
            variable=self.remove_watermark_var
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(param_row3, text="强度:").pack(side=tk.LEFT, padx=5)
        ttk.Combobox(
            param_row3,
            textvariable=self.watermark_strength_var,
            values=["light", "medium", "strong", "extreme"],
            width=8
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(
            param_row3,
            text="后处理",
            variable=self.watermark_post_process_var
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(
            param_row3,
            text="自动检测",
            variable=self.watermark_auto_detect_var
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            param_row3,
            text="💡 组合使用有效去除水印",
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=5)
        
        row += 1

        # ===== 【新增】第五模块：图片后期处理 =====
        post_frame = ttk.LabelFrame(self.frame, text="🖼️ 图片后期处理", padding=5)
        post_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2, padx=5)

        # ===== 功能1：清除元数据 =====
        pp_row1 = ttk.Frame(post_frame)
        pp_row1.pack(fill=tk.X, pady=2)

        ttk.Checkbutton(
            pp_row1,
            text="🧹 清除元数据",
            variable=self.clear_metadata_var
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            pp_row1,
            text="清除 PNG tEXt / EXIF 等元数据，转换为 JPG",
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=15)

        # ===== 功能2：注入 EXIF 信息 =====
        pp_row2 = ttk.Frame(post_frame)
        pp_row2.pack(fill=tk.X, pady=2)

        ttk.Checkbutton(
            pp_row2,
            text="📷 注入 EXIF 信息",
            variable=self.inject_exif_var
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(pp_row2, text="相机:").pack(side=tk.LEFT, padx=15)
        ttk.Combobox(
            pp_row2,
            textvariable=self.camera_var,
            values=[
                "sony_a7iv", "sony_a7iii", "canon_r5", "canon_r6",
                "nikon_z8", "fuji_x100v", "iphone_15", "pixel_8"
            ],
            width=12
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            pp_row2,
            text="💡 添加相机元数据，让图片更像真实照片",
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=15)

        # ===== 功能3：照片真实化 =====
        pp_row3 = ttk.Frame(post_frame)
        pp_row3.pack(fill=tk.X, pady=2)

        ttk.Checkbutton(
            pp_row3,
            text="🎯 照片真实化",
            variable=self.realistic_var
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(pp_row3, text="强度:").pack(side=tk.LEFT, padx=15)
        ttk.Combobox(
            pp_row3,
            textvariable=self.realistic_strength_var,
            values=["light", "medium", "strong"],
            width=8
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            pp_row3,
            text="💡 添加噪点/暗角/锐化，模拟真实相机效果",
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=15)
        
        row += 1
        
        return self.frame

    def get_scheduler_type(self) -> str:
        """获取当前选择的调度器类型"""
        return self.scheduler_var.get()

    from utils.scheduler_factory import get_scheduler_description, get_scheduler_recommended_steps

    def get_scheduler_info(self) -> dict:
        """获取当前调度器的信息"""
        scheduler = self.scheduler_var.get()
        return {
            "name": scheduler,
            "description": get_scheduler_description(scheduler),
            "recommended_steps": get_scheduler_recommended_steps(scheduler),
        }
        
    def get_postprocess_params(self) -> dict:
        """获取图片后期处理参数"""
        return {
            "clear_metadata": self.clear_metadata_var.get(),
            "inject_exif": self.inject_exif_var.get(),
            "realistic": self.realistic_var.get(),
            "camera": self.camera_var.get(),
            "realistic_strength": self.realistic_strength_var.get()
        }
    
    def _set_size(self, width: int, height: int):
        """设置尺寸"""
        self.width_var.set(width)
        self.height_var.set(height)
    
    def get_frame(self):
        """获取框架"""
        return self.frame
    
    def get_params(self) -> dict:
        """获取所有参数"""
        return {
            "steps": self.steps_var.get(),
            "cfg": self.cfg_var.get(),
            "seed": self.seed_var.get(),
            "width": self.width_var.get(),
            "height": self.height_var.get(),
            "num_images": self.num_images_var.get()
        }
    
    def set_params(self, **kwargs):
        """设置参数"""
        if "steps" in kwargs:
            self.steps_var.set(kwargs["steps"])
        if "cfg" in kwargs:
            self.cfg_var.set(kwargs["cfg"])
        if "seed" in kwargs:
            self.seed_var.set(kwargs["seed"])
        if "width" in kwargs:
            self.width_var.set(kwargs["width"])
        if "height" in kwargs:
            self.height_var.set(kwargs["height"])
        if "num_images" in kwargs:
            self.num_images_var.set(kwargs["num_images"])
    
    def get_watermark_params(self) -> dict:
        """获取水印去除参数"""
        return {
            "enabled": self.remove_watermark_var.get(),
            "strength": self.watermark_strength_var.get(),
            "methods": self.watermark_methods_var.get(),
            "auto_detect": self.watermark_auto_detect_var.get(),
            "post_process": self.watermark_post_process_var.get()
        }
            
    def rebuild(self, parent):
        """销毁当前面板并重新创建"""
        # 1. 销毁当前的 UI 框架
        if self.frame:
            self.frame.destroy()
            self.frame = None

        # ✅ 2. 在重建之前，把变量更新为最新的配置默认值
        from config.app_config import app_config
        gen_cfg = app_config.generation
        
        # 更新基础参数变量（这样重建后界面上的数值就是最新的默认值）
        self.steps_var.set(gen_cfg.steps["default"])
        self.cfg_var.set(gen_cfg.cfg["default"])
        self.width_var.set(gen_cfg.size["default_width"])
        self.height_var.set(gen_cfg.size["default_height"])

        # ✅ 3. 【修复】直接访问属性，而不是使用 .get()
        default_wm = gen_cfg.default_remove_watermark
        self.remove_watermark_var.set(default_wm)
        
        # 4. 重新创建控件
        self.parent = parent
        self.create_widgets(parent)     