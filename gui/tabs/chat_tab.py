#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能会话标签页 - 自然语言生图
支持文生图、图生图、多轮对话
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import re
import time
from datetime import datetime
from PIL import Image, ImageTk
import torch

# ===== Hugging Face 缓存配置 =====
CACHE_ROOT = r"E:\hf_cache\.cache"
os.makedirs(CACHE_ROOT, exist_ok=True)

os.environ["HF_HOME"] = CACHE_ROOT
os.environ["HF_HUB_CACHE"] = os.path.join(CACHE_ROOT, "hub")
os.environ["U2NET_HOME"] = os.path.join(CACHE_ROOT, "u2net")
os.environ["DEEPFACE_HOME"] = os.path.join(CACHE_ROOT, "deepface")

for env_var in ['HF_HOME', 'HF_HUB_CACHE', 'U2NET_HOME', 'DEEPFACE_HOME']:
    path = os.environ.get(env_var)
    if path:
        os.makedirs(path, exist_ok=True)
        print(f"   ✅ {env_var} = {path}")

from .base_tab import BaseTab
from gui.components.memory_monitor import force_memory_cleanup
import tempfile


class ChatTab(BaseTab):
    """智能会话标签页"""

    # ===== 默认加载的 LoRA 列表 =====
    DEFAULT_LORAS = [
        "busty_slider.safetensors",
        "beauty_masters.safetensors",
        "boobs.safetensors",
        "chunli.safetensors",
    ]

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.params = app.params_panel
        self._init_vars()
        self.setup_ui()

        # ✅ 延迟加载 LoRA（等待模型就绪）
        self.app.root.after(2000, self._auto_load_default_lora)

        # ✅ 延迟检测 LLM
        self.app.root.after(3000, self._check_ollama)

        self._append_message("assistant", "👋 你好！我是智能生图助手\n\n我可以帮你：\n• 📝 文生图 - 输入描述生成图片\n• 🖼️ 图生图 - 上传图片并修改\n• 💬 自由对话 - 回答你的问题\n\n试试输入：\"生成一张美女在沙滩上的图片\"")

        # 绑定快捷键
        self.input_text.bind("<Control-Return>", self._on_send)
        self.input_text.bind("<Return>", self._on_send_shift_check)

    def _init_vars(self):
        """初始化变量"""
        self.is_generating = False
        self.cancel_generation = False

        self.uploaded_image_paths = []
        self.uploaded_images = []
        self.uploaded_image = None
        self.uploaded_image_path = None

        self.messages = []
        self.chat_context = {}
        self._is_loading_model = False
        self.chat_steps_var = tk.IntVar(value=20)
        self.chat_cfg_var = tk.DoubleVar(value=7.5)
        self._last_negative = None
        self._pending_intent = None

        # 上下文记忆
        self.last_generated_image = None
        self.last_prompt = None
        self.last_intent_type = None
        self.conversation_history = []
        self.user_preferences = {
            "style": None,
            "scene": None,
            "gender": None,
            "quality": "high",
        }

        # 本地 LLM 配置
        self.llm_enabled = tk.BooleanVar(value=True)
        self.llm_model = tk.StringVar(value="qwen2.5:1.5b")
        self.llm_available = False
        self.llm_installing = False
        self.llm_model_size = "1GB"

        # ===== LoRA 相关变量 =====
        self.lora_enabled = tk.BooleanVar(value=True)
        self.lora_var = tk.StringVar(value="")
        self.lora_paths = {}
        self.current_lora_path = None
        self.lora_loaded = False

        # 缓存
        self._enhanced_prompt_cache = {}

        # 负面提示词模板（新增动物专用）
        self._negative_templates = {
            "default": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, extra limbs, bad proportions, bad hands, missing fingers, extra fingers",
            "portrait": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, extra limbs, bad proportions, bad hands, bad face, distorted face",
            "landscape": "worst quality, low quality, ugly, deformed, blurry, watermark, text, bad composition, cluttered",
            "nude": "clothes, fabric, dress, shirt, pants, underwear, bra, panties, bikini, swimsuit, covering, censorship, mosaic",
            # ✅ 新增动物专用
            "animal": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, extra legs, missing limbs, deformed body, watermark, text, human, person, man, woman, people, clothes, clothing, accessories, jewelry, hat, glasses",
        }        

    # ==================== LoRA 管理 ====================

    def _scan_lora_files(self):
        """扫描 sd15-lora 目录下的 LoRA 文件"""
        lora_dir = r"..\models\sd15-lora"
        if not os.path.exists(lora_dir):
            print(f"⚠️ LoRA 目录不存在: {lora_dir}")
            return []

        lora_files = []
        self.lora_paths = {}

        for f in os.listdir(lora_dir):
            if f.endswith('.safetensors'):
                # 检查是否在默认列表中
                is_default = f in self.DEFAULT_LORAS
                display_name = f"{'⭐ ' if is_default else ''}{f}"
                lora_files.append(display_name)
                self.lora_paths[display_name] = os.path.join(lora_dir, f)

        # 按默认优先排序
        lora_files.sort(key=lambda x: 0 if x.startswith('⭐') else 1)
        return lora_files


    def _load_lora_to_pipe(self, lora_path: str, lora_name: str):
        """加载 LoRA - 通过重新加载主模型"""
        if not self.app.model_manager.is_sd_loaded:
            self._append_message("system", "⚠️ 模型未加载，请先加载模型")
            return False

        try:
            self._append_message("system", f"📦 重新加载模型并加载 LoRA: {lora_name}")
            
            model_name = self.app.model_var.get()
            model_path = self.app._get_model_path(model_name)
            
            if not model_path:
                self._append_message("system", "❌ 找不到模型文件")
                return False
            
            # ✅ 重新加载模型带上 LoRA
            success = self.app.model_manager.load_sd(
                model_path, model_name, None,
                lora_path=lora_path,
                lora_weight=1.0
            )
            
            if success:
                self.lora_loaded = True
                self.current_lora_path = lora_path
                self.lora_var.set(lora_name)
                self._append_message("system", f"✅ LoRA 加载成功: {lora_name}")
                self._update_lora_status()
                return True
            else:
                self._append_message("system", f"❌ LoRA 加载失败")
                return False
                
        except Exception as e:
            self._append_message("system", f"❌ LoRA 加载失败: {str(e)}")
            return False
        
    def _unload_lora(self):
        """卸载 LoRA"""
        if not self.lora_loaded:
            self._append_message("system", "ℹ️ 没有已加载的 LoRA")
            return

        pipe = self.app.model_manager._sd_pipe
        if pipe is None:
            return

        try:
            pipe.unload_lora_weights()
            self.lora_loaded = False
            self.current_lora_path = None
            self._append_message("system", "🗑️ LoRA 已卸载")
            self._update_lora_status()
        except Exception as e:
            self._append_message("system", f"❌ 卸载失败: {str(e)}")

    def _auto_load_default_lora(self):
        """自动加载默认 LoRA"""
        # 检查模型是否已加载
        if not self.app.model_manager.is_sd_loaded:
            self._append_message("system", "⏳ 等待模型加载后自动加载 LoRA...")
            # 延迟重试
            self.app.root.after(3000, self._auto_load_default_lora)
            return

        if not self.lora_enabled.get():
            return

        # 获取 LoRA 列表
        lora_files = self._scan_lora_files()
        if not lora_files:
            return

        # 优先加载默认 LoRA（第一个）
        default_lora = lora_files[0]
        lora_path = self.lora_paths.get(default_lora)

        if lora_path and os.path.exists(lora_path):
            self._append_message("system", f"📦 自动加载 LoRA: {default_lora.replace('⭐ ', '')}")
            self._load_lora_to_pipe(lora_path, default_lora)
        else:
            self._append_message("system", "⚠️ 未找到默认 LoRA")

    def _on_lora_selected(self, event=None):
        """LoRA 下拉选择事件"""
        selected = self.lora_var.get()
        if not selected:
            return

        lora_path = self.lora_paths.get(selected)
        if not lora_path:
            self._append_message("system", "❌ 找不到 LoRA 文件")
            return

        if not self.app.model_manager.is_sd_loaded:
            self._append_message("system", "⚠️ 请先加载模型")
            return

        self._load_lora_to_pipe(lora_path, selected)

    def _toggle_lora(self):
        """切换 LoRA 启用/禁用"""
        if self.lora_enabled.get():
            self._auto_load_default_lora()
        else:
            self._unload_lora()

    def _update_lora_status(self):
        """更新 LoRA 状态显示"""
        if self.lora_loaded and self.current_lora_path:
            name = os.path.basename(self.current_lora_path)
            self.lora_status_label.config(text=f"🟢 {name}", foreground="green")
        else:
            self.lora_status_label.config(text="🔴 未加载", foreground="red")

    # ==================== UI 设置 ====================

    def setup_ui(self):
        """设置 UI"""
        frame = self.frame

        # ===== 主容器 =====
        main_frame = ttk.Frame(frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ===== 工具栏 =====
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=2)

        # ===== LoRA 控制区域 =====
        lora_frame = ttk.Frame(toolbar)
        lora_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(lora_frame, text="🔗 LoRA:").pack(side=tk.LEFT, padx=2)

        # LoRA 下拉选择
        lora_files = self._scan_lora_files()
        self.lora_combo = ttk.Combobox(
            lora_frame,
            textvariable=self.lora_var,
            values=lora_files,
            width=25,
            state="readonly"
        )
        self.lora_combo.pack(side=tk.LEFT, padx=2)
        self.lora_combo.bind('<<ComboboxSelected>>', self._on_lora_selected)

        # 启用开关
        self.lora_check = ttk.Checkbutton(
            lora_frame,
            text="启用",
            variable=self.lora_enabled,
            command=self._toggle_lora
        )
        self.lora_check.pack(side=tk.LEFT, padx=5)

        # 状态标签
        self.lora_status_label = ttk.Label(
            lora_frame,
            text="🔴 未加载",
            foreground="red",
            font=("", 8)
        )
        self.lora_status_label.pack(side=tk.LEFT, padx=5)

        # 刷新按钮
        ttk.Button(
            lora_frame,
            text="🔄",
            width=2,
            command=self._refresh_lora_list
        ).pack(side=tk.LEFT, padx=2)

        # 分隔线
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # ===== 原有工具栏控件 =====
        self.clear_images_btn = ttk.Button(
            toolbar,
            text="🗑️ 清除图片",
            command=self._clear_upload,
            width=10
        )
        self.clear_images_btn.pack(side=tk.LEFT, padx=2)

        self.image_status = ttk.Label(toolbar, text="", foreground="green")
        self.image_status.pack(side=tk.LEFT, padx=10)

        # 安全模式切换
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.safe_mode_var = tk.BooleanVar(value=True)

        self.safe_mode_btn = tk.Button(
            toolbar,
            text="🛡️ 安全模式",
            command=self._toggle_safe_mode,
            relief="sunken" if self.safe_mode_var.get() else "raised",
            bg="#e8f5e9" if self.safe_mode_var.get() else "#f5f5f5",
            font=("微软雅黑", 8),
            width=10,
            height=1
        )
        self.safe_mode_btn.pack(side=tk.LEFT, padx=5)

        self.safe_mode_label = ttk.Label(
            toolbar,
            text="🟢 已启用",
            foreground="green",
            font=("", 8)
        )
        self.safe_mode_label.pack(side=tk.LEFT, padx=2)

        ttk.Button(toolbar, text="🔧 测试 LLM", command=self.debug_test_llm, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ 清除对话", command=self._clear_chat, width=12).pack(side=tk.LEFT, padx=2)

        # ControlNet 缓存状态
        if hasattr(self, '_check_controlnet_cached') and self._check_controlnet_cached():
            size = self._get_controlnet_size()
            cache_status = f"🦴 ControlNet 已缓存 ({size})"
            ttk.Label(toolbar, text=cache_status, foreground="green").pack(side=tk.LEFT, padx=10)
        else:
            ttk.Label(toolbar, text="🦴 ControlNet 未缓存", foreground="orange").pack(side=tk.LEFT, padx=10)

        self.upload_btn = ttk.Button(toolbar, text="📎 上传图片", command=self._upload_image, width=12)
        self.upload_btn.pack(side=tk.LEFT, padx=2)

        self.image_status = ttk.Label(toolbar, text="", foreground="green")
        self.image_status.pack(side=tk.LEFT, padx=10)

        self.preview_label = ttk.Label(toolbar)
        self.preview_label.pack(side=tk.LEFT, padx=5)

        # ===== 参数控制栏 =====
        param_bar = ttk.Frame(main_frame)
        param_bar.pack(fill=tk.X, pady=2)

        ttk.Label(param_bar, text="步数:").pack(side=tk.LEFT, padx=5)

        self.steps_spinbox = ttk.Spinbox(
            param_bar,
            from_=4,
            to=50,
            textvariable=self.chat_steps_var,
            width=5,
            increment=1
        )
        self.steps_spinbox.pack(side=tk.LEFT, padx=2)

        for steps in [8, 12, 20, 30]:
            btn = ttk.Button(
                param_bar,
                text=str(steps),
                width=3,
                command=lambda s=steps: self.chat_steps_var.set(s)
            )
            btn.pack(side=tk.LEFT, padx=1)

        ttk.Label(param_bar, text="CFG:").pack(side=tk.LEFT, padx=15)

        self.cfg_spinbox = ttk.Spinbox(
            param_bar,
            from_=1.0,
            to=20.0,
            textvariable=self.chat_cfg_var,
            width=5,
            increment=0.5
        )
        self.cfg_spinbox.pack(side=tk.LEFT, padx=2)

        for cfg in [5, 7, 7.5, 9]:
            btn = ttk.Button(
                param_bar,
                text=str(cfg),
                width=3,
                command=lambda c=cfg: self.chat_cfg_var.set(c)
            )
            btn.pack(side=tk.LEFT, padx=1)

        ttk.Label(param_bar, text="💡 步数越高质量越好", foreground="gray", font=("", 8)).pack(side=tk.LEFT, padx=15)

        # ===== 速度/质量模式切换 =====
        ttk.Separator(param_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.quality_mode_var = tk.StringVar(value="快速")

        mode_frame = ttk.Frame(param_bar)
        mode_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(mode_frame, text="模式:", font=("", 9)).pack(side=tk.LEFT)

        self.fast_btn = tk.Button(
            mode_frame,
            text="⚡ 快速",
            command=lambda: self._set_quality_mode("快速"),
            relief="sunken" if self.quality_mode_var.get() == "快速" else "raised",
            bg="#e8f5e9" if self.quality_mode_var.get() == "快速" else "#f5f5f5",
            font=("微软雅黑", 8),
            width=6,
            height=1
        )
        self.fast_btn.pack(side=tk.LEFT, padx=2)

        self.balance_btn = tk.Button(
            mode_frame,
            text="⚖️ 平衡",
            command=lambda: self._set_quality_mode("平衡"),
            relief="sunken" if self.quality_mode_var.get() == "平衡" else "raised",
            bg="#e3f2fd" if self.quality_mode_var.get() == "平衡" else "#f5f5f5",
            font=("微软雅黑", 8),
            width=6,
            height=1
        )
        self.balance_btn.pack(side=tk.LEFT, padx=2)

        self.quality_btn = tk.Button(
            mode_frame,
            text="🌟 高质量",
            command=lambda: self._set_quality_mode("高质量"),
            relief="sunken" if self.quality_mode_var.get() == "高质量" else "raised",
            bg="#fff3e0" if self.quality_mode_var.get() == "高质量" else "#f5f5f5",
            font=("微软雅黑", 8),
            width=6,
            height=1
        )
        self.quality_btn.pack(side=tk.LEFT, padx=2)

        self.ultra_btn = tk.Button(
            mode_frame,
            text="🌟 超高质量",
            command=lambda: self._set_quality_mode("超高质量"),
            relief="sunken" if self.quality_mode_var.get() == "超高质量" else "raised",
            bg="#fce4ec" if self.quality_mode_var.get() == "超高质量" else "#f5f5f5",
            font=("微软雅黑", 8),
            width=6,
            height=1
        )
        self.ultra_btn.pack(side=tk.LEFT, padx=2)

        self.mode_hint = ttk.Label(param_bar, text="⚡ 快速模式", foreground="green", font=("", 8))
        self.mode_hint.pack(side=tk.LEFT, padx=10)

        # LLM 开关
        ttk.Separator(param_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.llm_check = ttk.Checkbutton(
            param_bar,
            text="🧠 LLM增强",
            variable=self.llm_enabled,
            command=self._on_llm_toggle
        )
        self.llm_check.pack(side=tk.LEFT, padx=5)

        self.llm_install_btn = ttk.Button(
            param_bar,
            text="📦 安装 LLM",
            command=self._manual_install_llm,
            width=10
        )
        self.llm_install_btn.pack(side=tk.LEFT, padx=5)

        self.llm_status = ttk.Label(
            param_bar,
            text="●",
            foreground="gray",
            font=("", 10)
        )
        self.llm_status.pack(side=tk.LEFT, padx=2)

        # ===== 对话区域 =====
        chat_container = ttk.Frame(main_frame)
        chat_container.pack(fill=tk.BOTH, expand=True, pady=5)

        self.chat_text = tk.Text(
            chat_container,
            height=20,
            wrap=tk.WORD,
            font=("微软雅黑", 10),
            bg="#f5f5f5",
            relief="flat",
            padx=10,
            pady=10
        )
        scrollbar = ttk.Scrollbar(chat_container, orient=tk.VERTICAL, command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=scrollbar.set)

        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.chat_text.config(state=tk.DISABLED)

        # ===== 底部输入区 =====
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)

        self.input_text = tk.Text(
            input_frame,
            height=4,
            wrap=tk.WORD,
            font=("微软雅黑", 10),
            relief="sunken",
            borderwidth=1
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        self.send_btn = tk.Button(
            btn_frame,
            text="🚀 发送\n(Ctrl+Enter)",
            command=self._on_send,
            width=12,
            height=2,
            relief="raised",
            bg="#e3f2fd",
            font=("微软雅黑", 9)
        )
        self.send_btn.pack(side=tk.TOP, pady=2)

        self.cancel_btn = tk.Button(
            btn_frame,
            text="⏹️ 取消",
            command=self._cancel_generation,
            state=tk.DISABLED,
            width=12,
            height=1,
            relief="raised",
            font=("微软雅黑", 9)
        )
        self.cancel_btn.pack(side=tk.TOP, pady=2)

        # ===== 状态栏 =====
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=2)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var, foreground="blue").pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(status_frame, length=200, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, padx=5)

    def _refresh_lora_list(self):
        """刷新 LoRA 列表"""
        lora_files = self._scan_lora_files()
        self.lora_combo['values'] = lora_files
        if lora_files and not self.lora_var.get():
            # 如果当前没有选择，默认选第一个（默认 LoRA）
            self.lora_var.set(lora_files[0])
        self._append_message("system", f"🔄 LoRA 列表已刷新 ({len(lora_files)} 个)")

    # ==================== 原有方法（保持不变） ====================

    def _detect_couple_intent(self, text: str) -> bool:
        keywords = ['和', '与', '一起', '两人', '双人', '情侣', 'couple', 'together',
                    '拥抱', '牵手', '接吻', '依偎', '并肩', '合成', '合并', '合并成一张']
        return any(k in text for k in keywords)

    def _detect_action_from_text(self, text: str) -> str:
        action_map = {
            '拥抱': 'hugging each other',
            '牵手': 'holding hands',
            '接吻': 'kissing',
            '依偎': 'cuddling',
            '并肩': 'standing side by side',
            '背靠背': 'back to back',
            '跳舞': 'dancing together',
            '对视': 'looking at each other',
        }
        text_lower = text.lower()
        for cn, en in action_map.items():
            if cn in text_lower:
                return en
        return "standing together"

    def _handle_couple_generation(self, intent: dict):
        if len(self.uploaded_images) < 2:
            self._append_message("assistant", "❌ 请上传两张图片（一男一女）")
            return

        self._append_message("system", "👫 正在合成双人图片...")

        try:
            prompt = intent["prompt"]
            action = intent.get("action", "standing together")

            pose_image = self._extract_couple_pose(
                self.uploaded_image_paths[0],
                self.uploaded_image_paths[1]
            )

            if pose_image:
                self._append_message("system", "🦴 已提取双人姿态图")
                params = intent.get("params", {})
                self._handle_controlnet_generation(prompt, pose_image, intent, params)
                return
            else:
                self._append_message("system", "⚠️ 姿态提取失败，使用普通图生图")
                self._handle_couple_img2img(intent)

        except Exception as e:
            self._append_message("assistant", f"❌ 双人合成失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def _extract_couple_pose(self, img1_path: str, img2_path: str) -> Image.Image:
        try:
            import cv2
            import numpy as np
            from PIL import Image

            try:
                from controlnet_aux import OpenPoseDetector
                detector = OpenPoseDetector.from_pretrained("lllyasviel/ControlNet")

                img1 = cv2.imread(img1_path)
                img2 = cv2.imread(img2_path)

                pose1 = detector(img1, output_type="pil")
                pose2 = detector(img2, output_type="pil")

                combined = self._merge_pose_images(pose1, pose2)
                return combined

            except ImportError:
                print("   ⚠️ controlnet_aux 未安装，使用备用方案")
                pass

            try:
                import mediapipe as mp

                img1 = cv2.imread(img1_path)
                img2 = cv2.imread(img2_path)
                h, w = img1.shape[:2]

                mp_pose = mp.solutions.pose
                with mp_pose.Pose(static_image_mode=True) as pose:
                    results1 = pose.process(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
                    results2 = pose.process(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB))

                    combined_img = np.zeros((h, w * 2, 3), dtype=np.uint8)

                    if results1.pose_landmarks:
                        pass
                    if results2.pose_landmarks:
                        pass

                    return Image.fromarray(combined_img)

            except ImportError:
                print("   ⚠️ mediapipe 未安装")
                pass

            img1 = cv2.imread(img1_path)
            img2 = cv2.imread(img2_path)

            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            edges1 = cv2.Canny(gray1, 50, 150)
            edges2 = cv2.Canny(gray2, 50, 150)

            combined_edges = np.hstack([edges1, edges2])
            return Image.fromarray(combined_edges)

        except Exception as e:
            print(f"⚠️ 双人姿态提取失败: {e}")
            return None

    def _merge_pose_images(self, pose1: Image.Image, pose2: Image.Image) -> Image.Image:
        import numpy as np
        from PIL import Image

        w1, h1 = pose1.size
        w2, h2 = pose2.size

        if h1 != h2:
            if h1 > h2:
                pose2 = pose2.resize((int(w2 * h1 / h2), h1))
            else:
                pose1 = pose1.resize((int(w1 * h2 / h1), h2))

        combined = Image.new('RGB', (pose1.width + pose2.width, pose1.height))
        combined.paste(pose1, (0, 0))
        combined.paste(pose2, (pose1.width, 0))

        return combined

    def _handle_couple_img2img(self, intent: dict):
        try:
            from utils.pipeline_pool import pipeline_pool
            from datetime import datetime
            import random

            prompt = intent["prompt"]
            params = intent.get("params", {})

            model_name = self.app.model_var.get()
            model_path = self.app._get_model_path(model_name)

            # 获取 LoRA
            lora_path = self.current_lora_path if self.lora_loaded else None
            lora_weight = 1.0

            task_id = f"couple_{datetime.now().strftime('%H%M%S')}"

            pipe, is_new = pipeline_pool.get_pipeline(
                model_path=model_path,
                model_name=model_name,
                lora_path=lora_path,
                lora_weight=lora_weight,
                task_id=task_id
            )

            if pipe is None:
                self._append_message("assistant", "❌ 无法获取 Pipeline")
                return

            img1 = self.uploaded_images[0].convert('RGB')
            img2 = self.uploaded_images[1].convert('RGB')

            h1, w1 = img1.size
            h2, w2 = img2.size
            target_h = min(h1, h2, 512)

            img1 = img1.resize((int(w1 * target_h / h1), target_h))
            img2 = img2.resize((int(w2 * target_h / h2), target_h))

            combined_img = Image.new('RGB', (img1.width + img2.width, target_h))
            combined_img.paste(img1, (0, 0))
            combined_img.paste(img2, (img1.width, 0))

            steps = params.get("steps", 20)
            cfg = params.get("cfg", 7.5)
            strength = 0.5

            seed = random.randint(1, 2**32 - 1)
            generator = torch.Generator("cpu").manual_seed(seed)

            result = pipe(
                prompt=prompt,
                negative_prompt=self._negative_templates["default"],
                image=combined_img,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
                num_images_per_prompt=1
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_couple_{intent.get('action', 'together')}.png"

            from config.app_config import app_config
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            result.images[0].save(filepath)

            self._append_image_result(filepath)
            self._append_message("assistant", f"✅ 双人合成完成！\n📁 {os.path.basename(filepath)}")
            self.app.add_to_preview(filepath, result.images[0])

        except Exception as e:
            self._append_message("assistant", f"❌ 双人合成失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def _check_ollama_installed(self) -> bool:
        import subprocess
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def _check_ollama_running(self) -> bool:
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False

    def _check_model_available(self, model: str) -> bool:
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                return model in models or model.split(":")[0] in str(models)
            return False
        except:
            return False

    def _install_ollama(self):
        import subprocess

        self.llm_installing = True
        self.app.root.after(0, lambda: self._append_message("system", "📦 正在下载并安装 Ollama... (可能需要几分钟)"))
        self.app.root.after(0, lambda: self._update_status("📦 安装 Ollama..."))

        def install_thread():
            try:
                cmd = 'powershell -Command "irm https://ollama.com/install.ps1 | iex"'
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0                )

                for line in process.stdout:
                    if "Downloading" in line or "Installing" in line:
                        self.app.root.after(0, lambda l=line: self._update_status(f"📦 {l.strip()[:50]}..."))
                        print(line.strip())

                process.wait()

                if process.returncode == 0:
                    self.app.root.after(0, lambda: self._append_message("system", "✅ Ollama 安装完成！正在启动..."))
                    threading.Thread(target=self._start_ollama_service, daemon=True).start()
                else:
                    self.app.root.after(0, lambda: self._append_message("system", "❌ Ollama 安装失败，请手动安装"))
                    self.llm_installing = False

            except Exception as e:
                self.app.root.after(0, lambda: self._append_message("system", f"❌ 安装失败: {e}"))
                self.llm_installing = False

        threading.Thread(target=install_thread, daemon=True).start()

    def _start_ollama_service(self):
        import subprocess
        import time

        self._append_message("system", "🔄 正在启动 Ollama 服务...")

        try:
            subprocess.Popen(
                ["ollama", "serve"],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            time.sleep(3)

            if self._check_ollama_running():
                self.app.root.after(0, lambda: self._append_message("system", "✅ Ollama 服务已启动"))
                threading.Thread(target=self._download_model, daemon=True).start()
            else:
                self.app.root.after(0, lambda: self._append_message("system", "⚠️ 服务启动失败，请手动运行: ollama serve"))
                self.llm_installing = False
        except Exception as e:
            self.app.root.after(0, lambda: self._append_message("system", f"❌ 启动失败: {e}"))
            self.llm_installing = False

    def _download_model(self):
        import subprocess

        model = self.llm_model.get()
        self.app.root.after(0, lambda: self._append_message("system", f"📦 正在下载模型: {model} (约 {self.llm_model_size})..."))
        self.app.root.after(0, lambda: self._append_message("system", "⏳ 这可能需要 10-30 分钟，请耐心等待..."))
        self.app.root.after(0, lambda: self._update_status(f"📦 下载模型 {model}..."))

        def download_thread():
            try:
                process = subprocess.Popen(
                    ["ollama", "pull", model],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )

                for line in process.stdout:
                    line = line.strip()
                    if "downloading" in line.lower() or "downloading" in line:
                        if "%" in line:
                            self.app.root.after(0, lambda l=line: self._update_status(f"📦 {l[:60]}..."))
                        print(line)

                process.wait()

                if process.returncode == 0:
                    self.app.root.after(0, lambda: self._on_llm_ready())
                else:
                    self.app.root.after(0, lambda: self._append_message("system", f"❌ 模型下载失败"))
                    self.app.root.after(0, lambda: self._append_message("system", f"💡 请手动下载: ollama pull {model}"))
                    self.llm_installing = False

            except Exception as e:
                self.app.root.after(0, lambda: self._append_message("system", f"❌ 下载失败: {e}"))
                self.llm_installing = False

        threading.Thread(target=download_thread, daemon=True).start()

    def _on_llm_ready(self):
        self.llm_available = True
        self.llm_installing = False
        self.llm_status.config(text="●", foreground="green")
        self._append_message("system", f"✅ LLM 已就绪！模型: {self.llm_model.get()}")
        self._append_message("assistant", "🧠 本地 LLM 已启用，可以智能理解你的需求了！")
        self._update_status("✅ LLM 就绪", 1.0)

    def _check_ollama(self):
        if not self._check_ollama_installed():
            self.llm_status.config(text="●", foreground="orange")
            self._append_message("system", "⚠️ Ollama 未安装，点击「安装 LLM」按钮自动安装")
            return

        if not self._check_ollama_running():
            self.llm_status.config(text="●", foreground="orange")
            self._append_message("system", "⏳ Ollama 服务未启动，正在自动启动...")
            threading.Thread(target=self._start_ollama_service, daemon=True).start()
            return

        model = self.llm_model.get()
        if not self._check_model_available(model):
            self.llm_status.config(text="●", foreground="orange")
            self._append_message("system", f"📦 模型 {model} 未下载，正在自动下载...")
            threading.Thread(target=self._download_model, daemon=True).start()
            return

        self.llm_available = True
        self.llm_status.config(text="●", foreground="green")
        self._append_message("system", f"✅ LLM 已就绪 (模型: {model})")

    # ==================== LLM 提示词增强 ====================

    def _call_ollama(self, prompt: str, timeout: int = 30, max_tokens: int = 512, stream: bool = False) -> str:
        """
        调用 Ollama API
        
        参数:
            prompt: 提示词
            timeout: 超时时间（秒）
            max_tokens: 最大生成 token 数
            stream: 是否启用流式输出（边生成边返回）
        """
        if not self.llm_available:
            return None

        try:
            import requests
            
            if stream:
                print(f"   📤 流式调用 LLM (超时: {timeout}s)...")
            else:
                print(f"   📤 调用 LLM (超时: {timeout}s, max_tokens: {max_tokens})...")
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.llm_model.get(),
                    "prompt": prompt,
                    "temperature": 0.7,
                    "stream": stream,
                    "max_tokens": max_tokens,
                    "top_p": 0.9,
                },
                timeout=timeout,
                stream=stream
            )
            
            if response.status_code != 200:
                print(f"   ❌ LLM 返回错误: {response.status_code}")
                return None
            
            if stream:
                # ===== 流式模式：逐块接收 =====
                result = ""
                chunk_count = 0
                for line in response.iter_lines():
                    if line:
                        try:
                            import json
                            data = json.loads(line)
                            if "response" in data:
                                chunk = data["response"]
                                result += chunk
                                chunk_count += 1
                                # 每 5 个块打印一次进度
                                if chunk_count % 5 == 0:
                                    print(f"\r   📥 接收中: {len(result)} 字符", end="")
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                
                # 换行
                print()
                print(f"   📥 流式接收完成: {len(result)} 字符")
                
                # 清理结果（去除可能的特殊标记）
                result = result.strip()
                # 如果结果包含特殊标记，尝试清理
                if result.startswith('"') and result.endswith('"'):
                    try:
                        import json
                        result = json.loads(result)
                    except:
                        pass
                
                return result
            else:
                # ===== 非流式模式：一次性返回 =====
                result = response.json().get("response", "").strip()
                print(f"   📥 LLM 响应长度: {len(result)} 字符")
                return result
                
        except requests.exceptions.Timeout:
            print("⚠️ Ollama 超时")
            return None
        except Exception as e:
            print(f"⚠️ Ollama 调用失败: {e}")
            return None
        
        
    def _build_preserve_parts_from_features(self, image_features: dict, user_text: str = "") -> list:
        preserve_parts = ["same person", "same face", "same identity"]

        face_count = image_features.get("face_count", 0)
        has_multiple = image_features.get("has_multiple_subjects", False)

        is_realistic = image_features.get("is_realistic", True)

        if user_text and any(k in user_text.lower() for k in ['动漫', '二次元', 'anime', '卡通']):
            is_realistic = False

        if self.uploaded_image_path:
            filename = os.path.basename(self.uploaded_image_path).lower()
            if 'anime' in filename or 'cartoon' in filename or '动漫' in filename:
                is_realistic = False

        if face_count == 1:
            if user_text and any(k in user_text.lower() for k in ['男', '帅哥', '男孩', '男性', '小哥哥', '男神']):
                preserve_parts.append("1boy" if is_realistic else "1boy")
            else:
                if is_realistic:
                    preserve_parts.append("1woman")
                else:
                    preserve_parts.append("1girl")
        elif face_count >= 2 or has_multiple:
            if user_text and any(k in user_text.lower() for k in ['男', '帅哥', '男孩', '男性']):
                preserve_parts.append("2boys")
            else:
                preserve_parts.append("2women" if is_realistic else "2girls")

        preserve_parts.append("same pose")
        preserve_parts.append("same body language")

        if image_features.get("is_full_body", True):
            preserve_parts.append("full body")
        else:
            preserve_parts.append("half body")

        return preserve_parts

    def _merge_llm_prompt_with_features(self, llm_prompt: str, preserve_parts: list) -> str:
        prompt_lower = llm_prompt.lower()

        has_preserve = "same person" in prompt_lower and "same face" in prompt_lower
        has_user_pose = "same pose" not in preserve_parts

        parts_to_add = []
        for part in preserve_parts:
            if part.lower() not in prompt_lower:
                if has_user_pose and part == "same pose":
                    continue
                parts_to_add.append(part)

        if has_preserve:
            if parts_to_add:
                gender_parts = [p for p in parts_to_add if p in ["1girl", "1boy", "2girls", "2boys"]]
                other_parts = [p for p in parts_to_add if p not in ["1girl", "1boy", "2girls", "2boys"]]
                result_parts = gender_parts + [llm_prompt] + other_parts
                return ", ".join(result_parts)
            return llm_prompt
        else:
            gender_parts = [p for p in preserve_parts if p in ["1girl", "1boy", "2girls", "2boys"]]
            other_parts = [p for p in preserve_parts if p not in ["1girl", "1boy", "2girls", "2boys"]]
            result_parts = gender_parts + other_parts + [llm_prompt]
            return ", ".join(result_parts)

    def _enhance_prompt_with_features(self, prompt: str, intent: dict, image_features: dict) -> str:
        user_text = intent.get("original_text", "")
        keywords = intent.get("keywords", {})
        user_poses = keywords.get("poses", [])

        preserve_parts = self._build_preserve_parts_from_features(image_features, user_text)

        if user_poses:
            preserve_parts = [p for p in preserve_parts if p != "same pose"]
            print(f"   🧍 用户指定姿势: {user_poses}，已移除 'same pose'")

        prompt_lower = prompt.lower()
        sentence_indicators = ['maintain', 'exchange', 'retain', 'keep', 'change', 'feature', 'outfit', 'gown']
        is_natural = any(ind in prompt_lower for ind in sentence_indicators)
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in prompt)

        has_preserve = "same person" in prompt_lower and "same face" in prompt_lower

        if has_preserve:
            parts_to_add = [p for p in preserve_parts if p.lower() not in prompt_lower]
            if parts_to_add:
                return prompt + ", " + ", ".join(parts_to_add)
            return prompt

        if is_natural or has_chinese:
            clothes = []
            clothes_map = {
                '旗袍': 'qipao',
                '汉服': 'hanfu',
                '礼服': 'evening gown',
                '裙子': 'dress',
                '西装': 'suit',
                '制服': 'uniform',
                '泳衣': 'swimsuit',
                '比基尼': 'bikini',
                'dress': 'dress',
                'gown': 'evening gown',
                'qipao': 'qipao',
            }
            for cn, en in clothes_map.items():
                if cn in prompt_lower or cn in user_text.lower():
                    if en not in clothes:
                        clothes.append(en)

            result_parts = []
            gender = next((p for p in preserve_parts if p in ["1girl", "1boy", "2girls", "2boys"]), "1girl")
            result_parts.append(gender)
            other_parts = [p for p in preserve_parts if p not in ["1girl", "1boy", "2girls", "2boys"]]
            result_parts.extend(other_parts)
            if user_poses:
                result_parts.append(" ".join(user_poses) + " pose")
            if clothes:
                result_parts.append("wearing " + ", ".join(clothes))
            result_parts.append("masterpiece")
            result_parts.append("best quality")
            result_parts.append("photorealistic")
            result_parts.append("8k")
            result_parts.append("highly detailed")

            return ", ".join(result_parts)

        return self._merge_llm_prompt_with_features(prompt, preserve_parts)

    def debug_test_llm(self):
        import requests

        self._append_message("system", "🔍 开始测试 LLM...")

        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                self._append_message("system", f"✅ Ollama 运行中，已安装: {models}")
            else:
                self._append_message("system", f"❌ Ollama 异常: {response.status_code}")
                return
        except Exception as e:
            self._append_message("system", f"❌ 连接失败: {e}")
            return

        test_prompt = "请用一句话介绍你自己"
        self._append_message("system", f"🧠 测试模型: {self.llm_model.get()}")
        self._append_message("system", f"📝 提示词: {test_prompt}")

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.llm_model.get(),
                    "prompt": test_prompt,
                    "temperature": 0.7,
                    "stream": False,
                    "max_tokens": 100
                },
                timeout=30
            )

            if response.status_code == 200:
                reply = response.json().get("response", "").strip()
                self._append_message("assistant", f"🧠 LLM 回复: {reply}")
                self._append_message("system", "✅ LLM 测试通过！")
            else:
                self._append_message("system", f"❌ 测试失败: {response.status_code}")

        except Exception as e:
            self._append_message("system", f"❌ 测试失败: {e}")

    def _llm_enhance_prompt(self, text: str, is_img2img: bool = False) -> dict:
        if not self.llm_available or not self.llm_enabled.get():
            return None

        cache_key = f"{text}_{is_img2img}"
        if cache_key in self._enhanced_prompt_cache:
            return self._enhanced_prompt_cache[cache_key]

        # ===== 自动检测主题类型 =====
        text_lower = text.lower()
        
        # 动物关键词
        animal_keywords = ['猫', '狗', '兔', '鸟', '鱼', '马', '鹿', '熊', '熊猫', '老虎', '狮子', 
                           '豹', '大象', '长颈鹿', '鹰', '猫头鹰', '孔雀', '鲸鱼', '海豚', '鲨鱼', 
                           '蝴蝶', '蛇', '狐狸', '狼', '仓鼠', '鹦鹉', '鸽子', '天鹅', '鹤', '鸳鸯',
                           'cat', 'dog', 'rabbit', 'bird', 'fish', 'horse', 'panda', 'tiger', 'lion',
                           'elephant', 'giraffe', 'eagle', 'owl', 'whale', 'dolphin', 'shark', 'fox', 'wolf']
        
        # 风景关键词
        landscape_keywords = ['风景', '山水', '日落', '日出', '大海', '山川', '森林', '花园', '草原', 
                              '沙漠', '瀑布', '湖泊', '溪流', '山谷', '天空', '云海', '极光', '星空',
                              'landscape', 'scenery', 'mountain', 'ocean', 'forest', 'garden', 'desert',
                              'waterfall', 'lake', 'river', 'valley', 'sky', 'aurora', 'starry']
        
        # 植物关键词
        plant_keywords = ['花', '树', '草', '玫瑰', '樱花', '荷花', '薰衣草', '枫叶', '竹林', '森林',
                          'flower', 'rose', 'cherry blossom', 'lotus', 'lavender', 'maple', 'bamboo']
        
        # 物体/建筑关键词
        object_keywords = ['建筑', '房屋', '城堡', '宫殿', '寺庙', '教堂', '桥梁', '塔', '摩天轮', 
                           '汽车', '火车', '飞机', '船', '自行车', '相机', '钢琴', '吉他', '书籍',
                           'building', 'castle', 'palace', 'temple', 'church', 'bridge', 'tower',
                           'car', 'train', 'airplane', 'boat', 'bicycle', 'piano', 'guitar']
        
        # 判断主题类型
        is_animal = any(k in text_lower for k in animal_keywords)
        is_landscape = any(k in text_lower for k in landscape_keywords)
        is_plant = any(k in text_lower for k in plant_keywords)
        is_object = any(k in text_lower for k in object_keywords)
        
        # 确定主题类型
        if is_animal:
            subject_type = "动物"
            extra_rules = "使用具体动物名称作为主体标签（如 cat, dog, bird 等），不要使用 1girl/1boy"
        elif is_landscape:
            subject_type = "风景"
            extra_rules = "使用 landscape, scenery, nature 等标签，描述整体场景和氛围"
        elif is_plant:
            subject_type = "植物"
            extra_rules = "使用具体植物名称（如 rose, cherry blossom, lotus 等）"
        elif is_object:
            subject_type = "物体/建筑"
            extra_rules = "使用具体物体或建筑名称，描述其外观、材质和细节"
        else:
            subject_type = "人物"
            extra_rules = "根据性别和人数选择合适的标签（1girl, 1boy, 1woman, 1man, couple 等）"

        # ===== 使用简洁的提示词模板 =====
        if is_img2img:
            prompt_template = f"""SD提示词专家。用户修改图片：{{text}}

    主题：{subject_type}
    规则：{extra_rules}。保留原图特征(same person/animal/scene)，只改用户要求的部分。英文，逗号分隔。

    正面提示词：
    负面提示词："""
        else:
            prompt_template = f"""SD提示词专家。根据描述生成提示词：{{text}}

    主题：{subject_type}
    规则：{extra_rules}。包含主体、场景、光线。英文，逗号分隔。不要重复。

    正面提示词：
    负面提示词："""

        prompt = prompt_template.format(text=text)
        
        # ✅ 使用流式输出，提高响应速度
        result = self._call_ollama(prompt, timeout=60, max_tokens=200, stream=True)

        if not result:
            return None

        parsed = self._parse_llm_response_simple(result)
        parsed = self._parse_llm_response_stream(result)

        if parsed and parsed.get('prompt'):
            parsed['prompt'] = self._clean_prompt(parsed['prompt'])
            # 如果是动物主题，使用动物负面提示词
            if is_animal and not parsed.get('negative'):
                parsed['negative'] = self._negative_templates["animal"]
            self._enhanced_prompt_cache[cache_key] = parsed
            return parsed

        return None
    
    def _parse_llm_response(self, response: str) -> dict:
        """
        解析 LLM 响应，提取正面和负面提示词
        支持多种格式，更健壮
        """
        result = {
            "prompt": "",
            "negative": "",
        }
        
        if not response:
            return result
        
        lines = response.strip().split('\n')
        
        # ===== 尝试提取正面提示词 =====
        prompt_found = False
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 匹配中文或英文的"正面提示词"
            if any(k in line for k in ['正面提示词', '正面', 'Positive prompt', 'Prompt']):
                # 提取冒号后的内容
                if '：' in line:
                    content = line.split('：', 1)[-1].strip()
                elif ':' in line:
                    content = line.split(':', 1)[-1].strip()
                else:
                    # 如果只有标记没有内容，看下一行
                    if i + 1 < len(lines):
                        content = lines[i + 1].strip()
                    else:
                        content = ""
                
                if content:
                    result['prompt'] = content
                    prompt_found = True
                    break
        
        # ===== 尝试提取负面提示词 =====
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if any(k in line for k in ['负面提示词', '负面', 'Negative prompt', 'Negative']):
                if '：' in line:
                    content = line.split('：', 1)[-1].strip()
                elif ':' in line:
                    content = line.split(':', 1)[-1].strip()
                else:
                    content = ""
                
                if content:
                    result['negative'] = content
                    break
        
        # ===== 如果还是没有提取到，尝试整段提取 =====
        if not result['prompt']:
            # 移除常见的标记
            clean = response
            clean = re.sub(r'正面提示词[：:]\s*', '', clean)
            clean = re.sub(r'负面提示词[：:]\s*', '', clean)
            clean = re.sub(r'Positive prompt[：:]\s*', '', clean, flags=re.IGNORECASE)
            clean = re.sub(r'Negative prompt[：:]\s*', '', clean, flags=re.IGNORECASE)
            
            # 如果还有 "负面" 标记，分割
            if '负面' in clean or 'Negative' in clean:
                parts = re.split(r'负面|Negative', clean, flags=re.IGNORECASE)
                if len(parts) >= 2:
                    result['prompt'] = parts[0].strip()
                    result['negative'] = parts[1].strip()
                else:
                    result['prompt'] = clean.strip()
            else:
                result['prompt'] = clean.strip()
        
        # ===== 清理提示词 =====
        if result['prompt']:
            result['prompt'] = self._clean_prompt_text(result['prompt'])
        
        # ===== 如果没有负面提示词，使用默认 =====
        if not result['negative']:
            result['negative'] = self._negative_templates["default"]
        else:
            result['negative'] = self._clean_prompt_text(result['negative'])
        
        # ===== 确保质量词存在 =====
        if result['prompt']:
            prompt_lower = result['prompt'].lower()
            if 'masterpiece' not in prompt_lower and 'best quality' not in prompt_lower:
                result['prompt'] = f"masterpiece, best quality, photorealistic, 8k, {result['prompt']}"
        
        return result
    
    def _parse_llm_response_simple(self, response: str) -> dict:
        """简化版解析 LLM 响应 - 支持更多格式"""
        result = {
            "prompt": "",
            "negative": "",
        }
        
        if not response:
            return result
        
        lines = response.strip().split('\n')
        
        # ===== 方法1: 按行解析 =====
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 检测正面提示词
            if any(k in line for k in ['正面提示词', '正面', 'Positive prompt', 'Prompt']):
                content = self._extract_content(line, lines, i)
                if content:
                    result['prompt'] = content
                    continue
            
            # 检测负面提示词
            if any(k in line for k in ['负面提示词', '负面', 'Negative prompt', 'Negative']):
                content = self._extract_content(line, lines, i)
                if content:
                    result['negative'] = content
                    continue
            
            # 如果没有检测到标记，但行内容看起来像提示词（英文逗号分隔）
            if not result['prompt'] and ',' in line and len(line) > 10:
                # 检查是否包含质量词
                if any(q in line.lower() for q in ['masterpiece', 'best quality', 'photorealistic']):
                    result['prompt'] = line
        
        # ===== 方法2: 如果还没解析到，从整个响应提取 =====
        if not result['prompt']:
            clean = response
            clean = re.sub(r'(正面|正面提示词|Positive prompt)[：:]\s*', '', clean, flags=re.IGNORECASE)
            clean = re.sub(r'(负面|负面提示词|Negative prompt)[：:]\s*', '', clean, flags=re.IGNORECASE)
            clean = clean.strip()
            
            if clean:
                # 如果包含负面标记，分割
                if any(k in clean for k in ['负面', 'Negative']):
                    parts = re.split(r'负面|Negative', clean, flags=re.IGNORECASE)
                    result['prompt'] = parts[0].strip()
                    if len(parts) > 1:
                        result['negative'] = parts[1].strip()
                else:
                    result['prompt'] = clean
        
        # ===== 清理 =====
        if result['prompt']:
            result['prompt'] = self._clean_prompt(result['prompt'])
        
        if not result['negative']:
            result['negative'] = self._negative_templates["default"]
        else:
            result['negative'] = self._clean_prompt(result['negative'])
        
        return result

    def _extract_content(self, line: str, lines: list, index: int) -> str:
        """提取冒号后的内容"""
        # 尝试从当前行提取
        if '：' in line:
            content = line.split('：', 1)[-1].strip()
        elif ':' in line:
            content = line.split(':', 1)[-1].strip()
        else:
            content = line.replace('正面提示词', '').replace('正面', '').replace('Negative prompt', '').replace('负面', '').strip()
        
        # 如果内容为空，尝试从下一行获取
        if not content and index + 1 < len(lines):
            next_line = lines[index + 1].strip()
            # 确保下一行不是标记行
            if next_line and not any(k in next_line for k in ['正面', '负面', 'Prompt', 'Negative']):
                content = next_line
        
        return content
    
    def _parse_llm_response_stream(self, response: str) -> dict:
        """解析流式 LLM 响应，实时提取提示词"""
        result = {
            "prompt": "",
            "negative": "",
        }
        
        if not response:
            return result
        
        # 按行分割
        lines = response.strip().split('\n')
        
        # 状态机
        current_section = None
        prompt_buffer = []
        negative_buffer = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测节标题
            if '正面提示词' in line or '正面' in line:
                current_section = 'prompt'
                # 如果有冒号，提取内容
                if '：' in line or ':' in line:
                    content = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                    if content:
                        prompt_buffer.append(content)
                continue
            elif '负面提示词' in line or '负面' in line:
                current_section = 'negative'
                if '：' in line or ':' in line:
                    content = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                    if content:
                        negative_buffer.append(content)
                continue
            
            # 根据当前节添加内容
            if current_section == 'prompt':
                prompt_buffer.append(line)
            elif current_section == 'negative':
                negative_buffer.append(line)
            else:
                # 没有节标题，尝试智能判断
                if '负面' in line or 'negative' in line.lower():
                    continue
                prompt_buffer.append(line)
        
        # 组合结果
        if prompt_buffer:
            result['prompt'] = ', '.join(prompt_buffer)
        if negative_buffer:
            result['negative'] = ', '.join(negative_buffer)
        
        # 如果没有负面提示词，使用默认
        if not result['negative']:
            result['negative'] = self._negative_templates["default"]
        
        return result

    
    def _clean_prompt(self, prompt: str) -> str:
        """清理提示词：去重、去标点、保留关键信息"""
        if not prompt:
            return prompt
        
        # 1. 移除多余的句号和感叹号，替换为逗号
        prompt = prompt.replace('。', ', ').replace('！', ', ').replace('?', ', ')
        prompt = prompt.replace('.', ', ').replace('!', ', ').replace('?', ', ')
        
        # 2. 拆分并去重
        parts = [p.strip() for p in prompt.split(',') if p.strip()]
        seen = set()
        unique_parts = []
        for p in parts:
            # 只取前50个字符，避免过长
            if len(p) > 50:
                p = p[:50]
            if p.lower() not in seen:
                seen.add(p.lower())
                unique_parts.append(p)
        
        # 3. 确保质量词在最前面
        quality_words = ['masterpiece', 'best quality', 'photorealistic', '8k', 'highly detailed']
        quality_used = []
        for q in quality_words:
            if q not in seen:
                unique_parts.insert(0, q)
                seen.add(q)
        
        # 4. 限制总长度（最多200字符，避免提示词过长）
        result = ", ".join(unique_parts)
        if len(result) > 200:
            # 保留前150字符 + ...
            result = result[:200]
            last_comma = result.rfind(',')
            if last_comma > 150:
                result = result[:last_comma]
        
        return result
        
    def _enhance_prompt_with_context(self, base_prompt: str, keywords: dict) -> str:
        quality_parts = ["masterpiece", "best quality", "photorealistic", "8k", "highly detailed", "ultra detailed"]
        prompt_parts = quality_parts.copy()
        
        # ===== 检测是否是动物主题 =====
        is_animal = keywords.get("is_animal", False)
        animals = keywords.get("animals", [])
        animal_features = keywords.get("animal_features", [])
        
        if is_animal and animals:
            # ===== 动物主题：构建动物提示词 =====
            animal_str = ", ".join(animals)
            prompt_parts = quality_parts.copy()
            prompt_parts.append(animal_str)
            
            # 添加动物特征
            if animal_features:
                prompt_parts.extend(animal_features)
            
            # 添加数量描述
            count_keywords = ['一只', '两只', '三只', '一群', 'a', 'two', 'three', 'a group of']
            for kw in count_keywords:
                if kw in base_prompt.lower():
                    prompt_parts.append(kw)
                    break
            
            # 添加场景（如果有）
            if keywords.get("scenes"):
                prompt_parts.append("in " + ", ".join(keywords["scenes"]))
            
            # 添加姿势（如果有）
            if keywords.get("poses"):
                prompt_parts.append(", ".join(keywords["poses"]))
            
            # 添加风格（如果有）
            if keywords.get("styles"):
                prompt_parts.extend(keywords["styles"])
            
            # 添加颜色描述（如果有）
            if keywords.get("colors"):
                prompt_parts.append("with " + ", ".join(keywords["colors"]) + " fur")
            
            # 添加灯光（如果有）
            if keywords.get("lighting"):
                prompt_parts.append("with " + ", ".join(keywords["lighting"]))
            
            # 构建最终提示词
            full_prompt = ", ".join(prompt_parts)
            
            # 如果用户输入包含中文描述，尝试保留一些核心描述
            if any('\u4e00' <= char <= '\u9fff' for char in base_prompt):
                # 提取中文描述中的核心词（去除动物名本身）
                core_desc = base_prompt
                for animal_name in ['猫', '猫咪', '小猫', '狗', '小狗', '兔子']:
                    core_desc = core_desc.replace(animal_name, '')
                core_desc = core_desc.strip()
                if core_desc and len(core_desc) < 30:
                    # 将中文描述翻译成英文（简单映射）
                    desc_map = {
                        '躺在床上': 'lying on bed',
                        '在沙发上': 'on the sofa',
                        '在花园里': 'in the garden',
                        '在草地上': 'on the grass',
                        '在阳光下': 'in the sunlight',
                        '在窗台上': 'on the windowsill',
                        '在笼子里': 'in the cage',
                        '在树上': 'in the tree',
                        '在水里': 'in the water',
                        '在雪地里': 'in the snow',
                        '在花丛中': 'among flowers',
                        '在森林里': 'in the forest',
                        '在山顶上': 'on the mountaintop',
                        '在沙滩上': 'on the beach',
                        '在屋顶上': 'on the roof',
                        '在雨中': 'in the rain',
                        '在风中': 'in the wind',
                        '在月光下': 'under the moonlight',
                    }
                    for cn, en in desc_map.items():
                        if cn in core_desc:
                            if en not in full_prompt:
                                full_prompt += f", {en}"
                            break
            
            return full_prompt
        
        # ===== 人物主题：原有逻辑 =====
        genders = keywords.get("genders", [])
        if not genders:
            if self.uploaded_image_path:
                image_features = self._analyze_image_features(self.uploaded_image_path)
                face_count = image_features.get("face_count", 0)
                if face_count == 1:
                    genders = ["1girl"]
                elif face_count >= 2:
                    genders = ["2girls"]
                else:
                    genders = ["1girl"]
            else:
                genders = ["1girl"]
            keywords["genders"] = genders

        existing_genders = [p for p in prompt_parts if p in ["1girl", "1boy", "2girls", "2boys", "1girl, 1boy"]]
        if not existing_genders:
            prompt_parts = genders + prompt_parts
        elif existing_genders and genders and existing_genders[0] != genders[0]:
            for g in existing_genders:
                prompt_parts.remove(g)
            prompt_parts = genders + prompt_parts

        current_prompt = ", ".join(prompt_parts)
        if base_prompt and base_prompt not in current_prompt:
            prompt_parts.append(base_prompt)

        if keywords.get("styles"):
            for style in keywords["styles"]:
                if style not in prompt_parts:
                    prompt_parts.append(style)

        subject_parts = []
        if keywords.get("scenes"):
            subject_parts.append("background: " + ", ".join(keywords["scenes"]))
        if keywords.get("lighting"):
            subject_parts.append("lighting: " + ", ".join(keywords["lighting"]))
        if keywords.get("poses"):
            subject_parts.append("pose: " + ", ".join(keywords["poses"]))
        if keywords.get("expressions"):
            subject_parts.append("expression: " + ", ".join(keywords["expressions"]))
        if keywords.get("body"):
            subject_parts.extend(keywords["body"])
        if keywords.get("clothes"):
            subject_parts.append("wearing " + ", ".join(keywords["clothes"]))
        if keywords.get("colors"):
            subject_parts.append("with " + ", ".join(keywords["colors"]) + " color scheme")

        full_prompt = ", ".join(prompt_parts)
        if subject_parts:
            full_prompt += ", " + ", ".join(subject_parts)

        if self.user_preferences.get("style"):
            style = self.user_preferences["style"]
            if style not in full_prompt:
                full_prompt += f", {style} style"

        return full_prompt

    # ==================== UI 事件处理 ====================

    def _toggle_safe_mode(self):
        current = self.safe_mode_var.get()
        self.safe_mode_var.set(not current)

        if self.safe_mode_var.get():
            self.safe_mode_btn.config(
                relief="sunken",
                bg="#e8f5e9",
                text="🛡️ 安全模式"
            )
            self.safe_mode_label.config(text="🟢 已启用", foreground="green")
            self._append_message("system", "🛡️ 安全模式已启用 - 将过滤不当内容")
        else:
            self.safe_mode_btn.config(
                relief="raised",
                bg="#ffebee",
                text="⚠️ 自由模式"
            )
            self.safe_mode_label.config(text="🔴 已禁用", foreground="red")
            self._append_message("system", "⚠️ 安全模式已禁用 - 内容不受限制")

    def _update_safe_mode_status(self):
        if self.safe_mode_var.get():
            self.safe_mode_label.config(text="🟢 已启用", foreground="green")
            self.safe_mode_btn.config(
                relief="sunken",
                bg="#e8f5e9",
                text="🛡️ 安全模式"
            )
        else:
            self.safe_mode_label.config(text="🔴 已禁用", foreground="red")
            self.safe_mode_btn.config(
                relief="raised",
                bg="#ffebee",
                text="⚠️ 自由模式"
            )

    def _check_unsafe_content(self, text: str) -> tuple:
        unsafe_keywords = [
            '阴茎', '阴道', '插入', '性交', '做爱', '操', '干', '肏',
            '射精', '高潮', '精液', '阴蒂', '口交', '肛交', '自慰',
            '手淫', '淫荡', '色情', '全裸', '一丝不挂',
            '乳交', '足交', '性虐', 'sm', '捆绑', '性爱', '性行为',
            'penis', 'vagina', 'insert', 'intercourse', 'sexual', 'fuck',
            'sperm', 'ejaculate', 'orgasm', 'clitoris', 'oral sex',
            'anal sex', 'masturbate', 'porn', 'naked', 'nude',
            'hardcore', 'explicit', 'xxx', 'sex scene', 'sex',
        ]

        text_lower = text.lower()
        matched = []

        for keyword in unsafe_keywords:
            if keyword in text_lower:
                matched.append(keyword)

        return len(matched) > 0, matched

    def _get_safe_alternatives(self, text: str) -> list:
        text_lower = text.lower()

        alternatives = {
            "romantic": [
                "couple hugging in sunset, romantic atmosphere, artistic photography, masterpiece, best quality",
                "lovers embracing, intimate moment, soft lighting, elegant, 8k, highly detailed",
                "romantic kiss in the rain, cinematic style, beautiful composition, masterpiece",
                "two people cuddling, cozy bedroom, warm tones, tender moment, photorealistic"
            ],
            "passionate": [
                "passionate embrace, intense emotion, dramatic lighting, artistic photography",
                "lovers in bed, morning light, intimate atmosphere, artistic nude, soft focus",
                "romantic dance, elegant pose, dreamy background, masterpiece",
                "intimate couple, sensual atmosphere, warm colors, artistic composition"
            ],
            "dancing": [
                "couple dancing, elegant movement, beautiful dress, romantic atmosphere",
                "ballroom dance, passionate tango, dramatic lighting, stunning composition"
            ],
            "portrait": [
                "couple portrait, close up, intimate gaze, soft lighting, masterpiece",
                "romantic portrait, affectionate couple, beautiful bokeh, professional photography"
            ]
        }

        if '拥抱' in text_lower or 'hug' in text_lower:
            category = "romantic"
        elif '接吻' in text_lower or 'kiss' in text_lower:
            category = "passionate"
        elif '跳舞' in text_lower or 'dance' in text_lower:
            category = "dancing"
        elif '肖像' in text_lower or 'portrait' in text_lower:
            category = "portrait"
        else:
            category = "romantic"

        return alternatives.get(category, alternatives["romantic"])

    def _clear_upload(self):
        self.uploaded_images = []
        self.uploaded_image_paths = []
        self.uploaded_image = None
        self.uploaded_image_path = None
        self.image_status.config(text="")
        self.preview_label.config(image="")
        self.preview_label.image = None
        self._append_message("system", "🗑️ 已清除所有图片")

    def _set_quality_mode(self, mode: str):
        self.quality_mode_var.set(mode)

        buttons = {
            "快速": self.fast_btn,
            "平衡": self.balance_btn,
            "高质量": self.quality_btn,
        }

        colors = {
            "快速": {"bg": "#e8f5e9", "hint": "⚡ 快速模式 (8步, 小尺寸)", "fg": "green"},
            "平衡": {"bg": "#e3f2fd", "hint": "⚖️ 平衡模式 (12步, 中等尺寸)", "fg": "blue"},
            "高质量": {"bg": "#fff3e0", "hint": "🌟 高质量模式 (20步, 大尺寸)", "fg": "orange"},
            "超高质量": {"bg": "#fce4ec", "hint": "✨ 超高质量模式 (30步, 超大尺寸, 建议16GB+内存)", "fg": "red"},
        }

        for name, btn in buttons.items():
            if name == mode:
                btn.config(relief="sunken", bg=colors[name]["bg"])
            else:
                btn.config(relief="raised", bg="#f5f5f5")

        self.mode_hint.config(text=colors[mode]["hint"], foreground=colors[mode]["fg"])

        if mode == "快速":
            self.chat_steps_var.set(8)
        elif mode == "平衡":
            self.chat_steps_var.set(12)
        else:
            self.chat_steps_var.set(20)

        self._append_message("system", f"📊 切换到 {mode} 模式")

    def _manual_install_llm(self):
        if self.llm_installing:
            self._append_message("system", "⏳ 正在安装中...")
            return

        if self.llm_available:
            self._append_message("system", "✅ LLM 已就绪")
            return

        if messagebox.askyesno("安装 LLM",
            "将自动安装 Ollama 并下载模型。\n\n"
            f"1. 下载 Ollama (约 100MB)\n"
            f"2. 下载模型 {self.llm_model.get()} (约 {self.llm_model_size})\n"
            f"3. 自动启动服务\n\n"
            "整个过程可能需要 10-30 分钟，确定继续吗？"
        ):
            threading.Thread(target=self._install_ollama, daemon=True).start()

    def _on_llm_toggle(self):
        if self.llm_enabled.get():
            if self.llm_installing:
                self._append_message("system", "⏳ 正在安装中，请稍候...")
                return

            if not self.llm_available:
                self._append_message("system", "🔍 正在检测 LLM 环境...")

                if not self._check_ollama_installed():
                    if messagebox.askyesno("安装 LLM",
                        "检测到 Ollama 未安装。\n"
                        "是否自动下载并安装 Ollama？\n\n"
                        f"下载大小: ~{self.llm_model_size}\n"
                        "安装后需要下载模型，请确保网络畅通。"
                    ):
                        self._install_ollama()
                    else:
                        self.llm_enabled.set(False)
                        self.llm_status.config(text="●", foreground="gray")
                    return

                self._check_ollama()
            else:
                self.llm_status.config(text="●", foreground="green")
                self._append_message("system", "🧠 LLM 增强已启用")
        else:
            self._append_message("system", "🧠 LLM 增强已禁用")
            self.llm_status.config(text="●", foreground="gray")

    def _update_context(self, intent: dict, result: dict = None):
        self.last_intent_type = intent.get("type")
        self.last_prompt = intent.get("prompt")

        if result and result.get("image_path"):
            self.last_generated_image = result.get("image_path")

        keywords = intent.get("keywords", {})
        if keywords.get("styles"):
            self.user_preferences["style"] = keywords["styles"][0]
        if keywords.get("scenes"):
            self.user_preferences["scene"] = keywords["scenes"][0]
        if keywords.get("genders"):
            gender = keywords["genders"][0]
            if "girl" in gender:
                self.user_preferences["gender"] = "女性"
            elif "boy" in gender:
                self.user_preferences["gender"] = "男性"

        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "result": result
        })

    def _get_context_summary(self) -> str:
        if not self.conversation_history:
            return ""

        summary_parts = []

        prefs = []
        if self.user_preferences.get("style"):
            prefs.append(f"风格偏好: {self.user_preferences['style']}")
        if self.user_preferences.get("scene"):
            prefs.append(f"场景偏好: {self.user_preferences['scene']}")
        if self.user_preferences.get("gender"):
            prefs.append(f"性别偏好: {self.user_preferences['gender']}")

        if prefs:
            summary_parts.append("📌 用户偏好: " + ", ".join(prefs))

        if self.last_prompt:
            summary_parts.append(f"📝 上次提示词: {self.last_prompt[:50]}...")

        user_msgs = [m for m in self.messages if m.get("role") == "user"]
        if user_msgs:
            summary_parts.append(f"💬 已对话 {len(user_msgs)} 轮")

        return "\n".join(summary_parts) if summary_parts else "无上下文"

    def _has_context(self) -> bool:
        return len(self.conversation_history) > 0 or self.last_prompt is not None

    def _on_send_shift_check(self, event):
        if event.state & 0x1:
            return
        self._on_send()
        return "break"

    def _on_send(self, event=None):
        if self.is_generating:
            return

        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return

        self.input_text.delete("1.0", tk.END)
        self._append_message("user", user_input)

        threading.Thread(target=self._process_message, args=(user_input,), daemon=True).start()

    def _upload_image(self):
        file = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("所有文件", "*.*")]
        )
        if file:
            self.uploaded_image_paths.append(file)
            img = Image.open(file)
            self.uploaded_images.append(img)

            if not self.uploaded_image:
                self.uploaded_image = img
                self.uploaded_image_path = file

            count = len(self.uploaded_images)
            self.image_status.config(text=f"📎 {count} 张图片")

            thumb = img.copy()
            thumb.thumbnail((40, 40))
            photo = ImageTk.PhotoImage(thumb)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo

            self._append_message("system", f"📎 已上传图片 ({count}/2): {os.path.basename(file)}")

            if count >= 2:
                self._append_message("system", "✅ 已上传2张图片！输入 '合成'、'在一起'、'拥抱' 等指令生成双人图")

    def _cancel_generation(self):
        self.cancel_generation = True
        self.is_generating = False
        self.cancel_btn.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.NORMAL)
        self.status_var.set("⏹️ 已取消")

    def _clear_chat(self):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.config(state=tk.DISABLED)
        self.messages = []
        self.chat_context = {}
        self.uploaded_image = None
        self.uploaded_image_path = None
        self.image_status.config(text="")
        self.preview_label.config(image="")
        self.preview_label.image = None
        self._enhanced_prompt_cache = {}
        self._append_message("assistant", "🗑️ 对话已清空，有什么可以帮你的？")

    def _append_message(self, role: str, content: str):
        self.chat_text.config(state=tk.NORMAL)

        timestamp = datetime.now().strftime("%H:%M")

        if role == "user":
            prefix = f"👤 你 ({timestamp})\n"
            tag = "user_msg"
            bg = "#e3f2fd"
        elif role == "assistant":
            prefix = f"🤖 助手 ({timestamp})\n"
            tag = "assistant_msg"
            bg = "#f5f5f5"
        elif role == "system":
            prefix = f"📌 系统 ({timestamp})\n"
            tag = "system_msg"
            bg = "#fff3e0"
        elif role == "image":
            prefix = f"🖼️ 生成 ({timestamp})\n"
            tag = "image_msg"
            bg = "#e8f5e9"
        else:
            prefix = f"📝 ({timestamp})\n"
            tag = "normal_msg"
            bg = "#ffffff"

        self.chat_text.insert(tk.END, f"\n{prefix}", f"{tag}_prefix")
        self.chat_text.insert(tk.END, f"{content}\n", tag)

        self.chat_text.tag_config(f"{tag}_prefix", foreground="gray", font=("", 8))
        self.chat_text.tag_config(tag, background=bg, font=("微软雅黑", 10), spacing1=2, spacing2=2, lmargin1=10, lmargin2=10, rmargin=10)

        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)

        self.messages.append({"role": role, "content": content, "timestamp": timestamp})

    def _append_image_result(self, filepath: str):
        self.chat_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M")

        try:
            img = Image.open(filepath)
            img.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(img)

            self.chat_text.insert(tk.END, f"\n🖼️ 生成 ({timestamp})\n", "image_prefix")
            self.chat_text.image_create(tk.END, image=photo)
            self.chat_text.insert(tk.END, f"\n📁 {os.path.basename(filepath)}\n", "image_info")

            if not hasattr(self, '_image_refs'):
                self._image_refs = []
            self._image_refs.append(photo)

            self.chat_text.tag_config("image_prefix", foreground="gray", font=("", 8))
            self.chat_text.tag_config("image_info", foreground="blue", font=("", 8))

        except Exception as e:
            self.chat_text.insert(tk.END, f"\n🖼️ 生成 ({timestamp})\n", "image_prefix")
            self.chat_text.insert(tk.END, f"✅ 已保存: {filepath}\n", "image_info")

        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)

    def _update_status(self, msg: str, progress: float = None):
        self.status_var.set(msg)
        if progress is not None:
            self.progress_bar.config(value=progress * 100)

    # ==================== 消息处理 ====================

    def _process_message(self, user_input: str):
        self.is_generating = True
        self.cancel_generation = False
        self.send_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)

        try:
            intent = self._analyze_intent(user_input)

            self._append_message("system", f"🔍 分析意图: {intent['type']}")

            mode = self.quality_mode_var.get() if hasattr(self, 'quality_mode_var') else "平衡"
            is_ultra = mode == "超高质量"

            if intent["type"] == "text_to_image" and is_ultra:
                self._handle_large_scale_generation(intent)
            elif intent["type"] == "couple_generation":
                self._handle_couple_generation(intent)
            elif intent["type"] == "text_to_image":
                self._handle_text_to_image(intent)
            elif intent["type"] == "image_to_image":
                self._handle_image_to_image(intent)
            elif intent["type"] == "chat":
                self._handle_chat(intent)
            else:
                self._append_message("assistant", "❌ 抱歉，我没理解你的意思。请试试：\n• \"生成一张...\"\n• \"把这张图改成...\"\n• 直接和我聊天")

        except Exception as e:
            self._append_message("assistant", f"❌ 处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_generating = False
            self.send_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.progress_bar.config(value=0)

    # ==================== ControlNet 相关 ====================

    def _setup_controlnet(self):
        if hasattr(self, 'controlnet_available') and self.controlnet_available:
            print("✅ ControlNet 已就绪（使用缓存）")
            return

        try:
            from diffusers import ControlNetModel, StableDiffusionControlNetPipeline

            print("📦 正在加载 ControlNet...")

            hf_cache_dir = os.environ.get("HF_HOME", r"E:\hf_cache\.cache")
            controlnet_cache_dir = os.path.join(hf_cache_dir, "hub")
            os.makedirs(controlnet_cache_dir, exist_ok=True)

            print(f"   📁 缓存目录: {controlnet_cache_dir}")

            model_path = os.path.join(controlnet_cache_dir, "models--lllyasviel--sd-controlnet-openpose")
            if os.path.exists(model_path):
                print(f"   ✅ 找到本地缓存")
                controlnet = ControlNetModel.from_pretrained(
                    "lllyasviel/sd-controlnet-openpose",
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                    cache_dir=controlnet_cache_dir,
                    local_files_only=True,
                )
            else:
                print("   📦 首次使用，下载 ControlNet (1.45GB)...")
                controlnet = ControlNetModel.from_pretrained(
                    "lllyasviel/sd-controlnet-openpose",
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                    cache_dir=controlnet_cache_dir,
                    resume_download=True,
                )
                print("   ✅ 下载完成，已缓存到本地")

            from utils.pipeline_pool import pipeline_pool

            model_name = self.app.model_var.get() if hasattr(self.app, 'model_var') else None
            if not model_name:
                print("   ⚠️ 未选择模型")
                self.controlnet_available = False
                return

            model_path = self.app._get_model_path(model_name)
            if not model_path:
                print(f"   ⚠️ 找不到模型: {model_name}")
                self.controlnet_available = False
                return

            # 获取 LoRA
            lora_path = self.current_lora_path if self.lora_loaded else None
            lora_weight = 1.0

            task_id = f"controlnet_{datetime.now().strftime('%H%M%S')}"
            pipe, is_new = pipeline_pool.get_pipeline(
                model_path=model_path,
                model_name=model_name,
                lora_path=lora_path,
                lora_weight=lora_weight,
                task_id=task_id
            )

            if pipe:
                self.controlnet_pipe = StableDiffusionControlNetPipeline(
                    vae=pipe.vae,
                    text_encoder=pipe.text_encoder,
                    tokenizer=pipe.tokenizer,
                    unet=pipe.unet,
                    controlnet=controlnet,
                    scheduler=pipe.scheduler,
                    safety_checker=None,
                    feature_extractor=None,
                    requires_safety_checker=False,
                )
                self.controlnet_available = True
                print(f"✅ ControlNet 已加载")
            else:
                print("⚠️ 无法获取 Pipeline，ControlNet 加载失败")
                self.controlnet_available = False

        except Exception as e:
            print(f"⚠️ ControlNet 加载失败: {e}")
            self.controlnet_available = False

    def _check_controlnet_cached(self) -> bool:
        hf_cache_dir = os.environ.get("HF_HOME", r"E:\hf_cache\.cache")
        controlnet_cache_dir = os.path.join(hf_cache_dir, "hub")
        model_path = os.path.join(controlnet_cache_dir, "models--lllyasviel--sd-controlnet-openpose")
        return os.path.exists(model_path)

    def _get_controlnet_size(self) -> str:
        hf_cache_dir = os.environ.get("HF_HOME", r"E:\hf_cache\.cache")
        controlnet_cache_dir = os.path.join(hf_cache_dir, "hub")
        if not os.path.exists(controlnet_cache_dir):
            return "未缓存"

        total_size = 0
        for dirpath, dirnames, filenames in os.walk(controlnet_cache_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)

        if total_size > 1024**3:
            return f"{total_size / 1024**3:.1f} GB"
        elif total_size > 1024**2:
            return f"{total_size / 1024**2:.1f} MB"
        else:
            return f"{total_size / 1024:.1f} KB"

    def _extract_pose_from_image(self, image_path: str) -> Image.Image:
        try:
            import cv2
            import numpy as np
            from PIL import Image

            img = cv2.imread(image_path)
            if img is None:
                return None

            h, w = img.shape[:2]

            try:
                from controlnet_aux import OpenPoseDetector
                detector = OpenPoseDetector.from_pretrained("lllyasviel/ControlNet")
                pose_img = detector(img, output_type="pil")
                return pose_img
            except:
                pass

            try:
                import mediapipe as mp
                mp_pose = mp.solutions.pose
                with mp_pose.Pose(static_image_mode=True) as pose:
                    results = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                    if results.pose_landmarks:
                        pose_img = np.zeros_like(img)
                        return Image.fromarray(pose_img)
            except:
                pass

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            return Image.fromarray(edges)

        except Exception as e:
            print(f"⚠️ 姿态提取失败: {e}")
            return None

    def _analyze_intent(self, text: str) -> dict:
        print("\n" + "=" * 60)
        print("🔍 [智能意图分析]")
        print(f"   用户输入: {text}")

        text_lower = text.lower()
        has_image = self.uploaded_image is not None
        has_multiple_images = len(self.uploaded_images) >= 2

        is_unsafe, unsafe_keywords = self._check_unsafe_content(text)

        if is_unsafe:
            safe_alternatives = self._get_safe_alternatives(text)

            if self.safe_mode_var.get():
                self._append_message("system", f"🛡️ 检测到不当内容: {', '.join(unsafe_keywords[:3])}")
                self._append_message("assistant",
                    f"💡 建议使用更艺术的表达方式：\n\n"
                    f"📝 已替换为：\n{safe_alternatives[0]}\n\n"
                    f"💡 如需生成原内容，请关闭安全模式"
                )

                return {
                    "type": "text_to_image",
                    "prompt": safe_alternatives[0],
                    "keywords": self._extract_keywords(safe_alternatives[0]),
                    "original_text": text,
                    "is_continuation": False,
                    "llm_enhanced": False,
                    "params": self._optimize_parameters(safe_alternatives[0], "text_to_image", None),
                    "content_filtered": True,
                    "safe_alternatives": safe_alternatives,
                }
            else:
                self._append_message("system", f"⚠️ 检测到敏感内容: {', '.join(unsafe_keywords[:3])}")
                self._append_message("assistant",
                    f"⚠️ 当前为自由模式，将尝试生成您的请求。\n\n"
                    f"💡 建议使用更艺术的表达方式：\n"
                    f"• {safe_alternatives[0]}\n"
                    f"• {safe_alternatives[1]}\n"
                    f"• {safe_alternatives[2]}\n\n"
                    f"🛡️ 点击「安全模式」启用自动过滤"
                )
                self._unsafe_content_detected = True

        is_couple_intent = has_multiple_images and self._detect_couple_intent(text)

        if is_couple_intent:
            print(f"   👫 检测到双人合成意图")
            action = self._detect_action_from_text(text)
            print(f"   🎬 动作: {action}")

            genders = []
            for img in self.uploaded_images[:2]:
                pass

            gender1 = "1woman"
            gender2 = "1man"

            if any(k in text_lower for k in ['男', '帅哥', '男孩', '男性', 'man', 'boy']):
                gender2 = "1man"
            if any(k in text_lower for k in ['女', '美女', '女孩', '女性', 'woman', 'girl']):
                gender1 = "1woman"

            smart_prompt = f"{gender1} and {gender2}, {action}, couple, romantic, masterpiece, best quality, photorealistic"

            use_llm = self.llm_enabled.get() and self.llm_available
            if use_llm:
                llm_result = self._llm_enhance_prompt(text, is_img2img=True)
                if llm_result and llm_result.get('prompt'):
                    smart_prompt = llm_result['prompt']

            result = {
                "type": "couple_generation",
                "prompt": smart_prompt,
                "action": action,
                "keywords": self._extract_keywords(text),
                "original_text": text,
                "is_continuation": False,
                "llm_enhanced": llm_result is not None if use_llm else False,
                "params": self._optimize_parameters(smart_prompt, "image_to_image", None),
            }
            print(f"   分析结果: {result['type']}")
            print(f"   提示词: {result['prompt'][:150]}...")
            print("=" * 60 + "\n")
            return result

        classification = self._classify_intent(text, has_image)
        intent_type = classification["type"]
        print(f"   📋 意图分类: {intent_type} (置信度: {classification.get('confidence', 'medium')})")

        keywords = self._extract_keywords(text)
        print(f"   提取的关键词: {keywords}")

        continuation_keywords = ['再来', '继续', '换一个', '换一张', '再生成', 'another', 'continue']
        is_continuation = any(k in text_lower for k in continuation_keywords)

        use_llm = self.llm_enabled.get() and self.llm_available
        is_img2img = intent_type == "image_to_image"

        llm_result = None
        if use_llm:
            print("   🧠 正在调用 LLM 增强...")
            self._append_message("system", "🧠 正在智能分析需求...")

            llm_result = self._llm_enhance_prompt(text, is_img2img)
            if llm_result:
                print(f"   ✅ LLM 增强成功")
                print(f"   📝 增强后提示词: {llm_result.get('prompt', '')[:100]}...")
                self._append_message("system", f"🧠 LLM 增强完成")

        if llm_result and llm_result.get('prompt'):
            smart_prompt = llm_result['prompt']
            self._last_negative = llm_result.get('negative', self._negative_templates["default"])
            print(f"   ✅ 使用 LLM 生成的提示词")
        elif is_continuation and self.last_prompt:
            smart_prompt = self.last_prompt
            self._append_message("system", f"🔄 复用上次提示词")
            print(f"   🔄 复用上次提示词")
        else:
            smart_prompt = self._enhance_prompt_with_context(text, keywords)
            self._last_negative = self._negative_templates["default"]
            print(f"   📝 使用关键词构建提示词")

        image_features = None
        if has_image and self.uploaded_image_path:
            image_features = self._analyze_image_features(self.uploaded_image_path)

        params = self._optimize_parameters(smart_prompt, intent_type, image_features)
        print(f"   ⚙️ 优化参数: 步数={params['steps']}, CFG={params['cfg']}, 强度={params.get('strength', 'N/A')}")

        if intent_type == "image_to_image":
            if llm_result and llm_result.get('prompt'):
                smart_prompt = llm_result['prompt']
                print(f"   ✅ 保留 LLM 生成的提示词（不覆盖）")
            else:
                actions = keywords.get("actions", [])
                genders = keywords.get("genders", [])
                gender = genders[0] if genders else "1woman"

                if "change_clothes" in actions and keywords.get("clothes"):
                    clothes_str = ", ".join(keywords["clothes"])
                    smart_prompt = f"same person, same face, same pose, {gender}, wearing {clothes_str}"
                    self._append_message("system", f"👗 检测到换装指令: {clothes_str}")
                elif keywords.get("poses"):
                    pose_str = ", ".join(keywords["poses"])
                    smart_prompt = f"same person, same face, {gender}, {pose_str} pose"
                    self._append_message("system", f"🧍 检测到姿势指令: {pose_str}")
                elif "change_background" in actions and keywords.get("scenes"):
                    scene_str = ", ".join(keywords["scenes"])
                    smart_prompt = f"same person, same face, same pose, {gender}, {scene_str} background"
                    self._append_message("system", f"🏠 检测到换背景指令: {scene_str}")
                elif "change_style" in actions or any(k in text_lower for k in ['风格', '油画', '水彩', '动漫']):
                    style = self._detect_style_from_text(text)
                    smart_prompt = f"same person, same face, same pose, {gender}, {style} style"
                    self._append_message("system", f"🎨 检测到风格转换: {style}")
                else:
                    smart_prompt = f"same person, same face, same pose, {gender}, {smart_prompt}"

            result = {
                "type": "image_to_image",
                "prompt": smart_prompt,
                "keywords": keywords,
                "original_text": text,
                "is_continuation": is_continuation,
                "llm_enhanced": llm_result is not None,
                "params": params,
            }
            print(f"   分析结果: {result['type']}")
            print(f"   提示词: {result['prompt'][:150]}...")
            print(f"   LLM增强: {result['llm_enhanced']}")
            print("=" * 60 + "\n")
            return result

        elif intent_type == "text_to_image":
            quality_prefix = "masterpiece, best quality"
            if "photorealistic" not in smart_prompt:
                quality_prefix += ", photorealistic"
            smart_prompt = f"{quality_prefix}, {smart_prompt}"

            result = {
                "type": "text_to_image",
                "prompt": smart_prompt,
                "keywords": keywords,
                "original_text": text,
                "is_continuation": is_continuation,
                "llm_enhanced": llm_result is not None,
                "params": params,
            }
            print(f"   分析结果: {result['type']}")
            print(f"   提示词: {result['prompt'][:150]}...")
            print(f"   LLM增强: {result['llm_enhanced']}")
            print("=" * 60 + "\n")
            return result

        else:
            if use_llm:
                reply = self._call_ollama(f"用户说：{text}\n请简短友好地回复（一句话）：", timeout=15, max_tokens=128)
                if reply:
                    result = {
                        "type": "chat",
                        "original_text": text,
                        "llm_reply": reply
                    }
                    return result

            result = {
                "type": "chat",
                "original_text": text
            }
            return result

    def _detect_style_from_text(self, text: str) -> str:
        text_lower = text.lower()

        style_map = {
            '油画': 'oil painting',
            '水彩': 'watercolor',
            '素描': 'sketch',
            '动漫': 'anime',
            '卡通': 'cartoon',
            '写实': 'photorealistic',
            '国风': 'chinese traditional',
            '古风': 'ancient chinese',
            '赛博朋克': 'cyberpunk',
            '蒸汽朋克': 'steampunk',
            '哥特': 'gothic',
            '暗黑': 'dark',
            '唯美': 'aesthetic',
            '梦幻': 'dreamy',
            '复古': 'vintage',
            '现代': 'modern',
            '抽象': 'abstract',
        }

        for cn, en in style_map.items():
            if cn in text_lower:
                return en

        return "realistic"

    def _classify_intent(self, text: str, has_image: bool) -> dict:
        text_lower = text.lower()

        image_descriptors = [
            '在沙滩', '在海边', '在花园', '在森林', '在城市', '在街道', '在卧室', '在浴室',
            '在舞台', '在宫殿', '在城堡', '在雨中', '在雪地', '在日落', '在星空下',
            '站着', '坐着', '躺着', '蹲着', '跪着', '弯腰', '回头', '侧身',
            '奔跑', '走路', '跳舞', '拥抱', '接吻', '睡觉',
            '动漫风格', '油画风格', '水彩风格', '写实风格', '赛博朋克', '古风', '复古',
            '穿着', '戴着', '披着', '身着', '礼服', '婚纱', '旗袍', '汉服',
            '微笑', '严肃', '忧郁', '诱惑', '可爱', '性感', '优雅', '梦幻',
        ]

        edit_indicators = [
            '变成', '改为', '换成', '改成', '换', '改', '修改', '调整',
            '穿', '戴上', '脱下', '去掉', '去除',
            '更', '更加', '多一点', '少一点',
        ]

        style_indicators = [
            '风格', '画风', '质感', '样式', 'styl',
            '油画', '水彩', '素描', '动漫', '写实', '国风', '卡通',
            '赛博朋克', '蒸汽朋克', '哥特', '暗黑', '唯美',
        ]

        has_edit = any(k in text_lower for k in edit_indicators)
        has_style = any(k in text_lower for k in style_indicators)
        has_description = any(k in text_lower for k in image_descriptors)

        explicit_gen = any(k in text_lower for k in ['生成', '画', '创建', 'create', 'generate', 'draw'])

        if has_image and (has_edit or has_style):
            return {"type": "image_to_image", "confidence": "high"}

        if has_image and has_description:
            return {"type": "image_to_image", "confidence": "medium"}

        if explicit_gen or has_description or len(text) > 5:
            return {"type": "text_to_image", "confidence": "high"}

        return {"type": "chat", "confidence": "low"}


    def _build_llm_parser_prompt(self, text: str, is_img2img: bool, has_image: bool, 
                                  has_multiple_images: bool, context: str = "") -> str:
        """构建 LLM 解析提示词（包含上下文）"""
        
        text_lower = text.lower()
        
        # 检测主题类型
        is_animal = any(k in text_lower for k in ['猫', '狗', '兔', '鸟', '鱼', '马', '鹿', '熊', '熊猫', '老虎', '狮子', '豹', '大象', '长颈鹿', '鹰', '猫头鹰', '孔雀', '鲸鱼', '海豚', '鲨鱼', '蝴蝶', '蛇', '狐狸', '狼'])
        is_landscape = any(k in text_lower for k in ['风景', '山水', '日落', '日出', '大海', '山川', '森林', '花园', '草原'])
        is_portrait = any(k in text_lower for k in ['肖像', '头像', '特写', '半身'])
        
        subject_type = "人物"
        if is_animal:
            subject_type = "动物"
        elif is_landscape:
            subject_type = "风景"
        
        # ===== 【新增】检测是否是延续性指令 =====
        is_continuation = self._is_continuation(text)
        continuation_hint = ""
        if is_continuation and self.last_prompt:
            continuation_hint = f"""
    【延续性提示】
    用户可能在延续之前的对话。之前的主题是：{self.last_prompt[:100]}...
    请保持主题一致性，如果用户只是简单说"再来一张"或"换一个"，请基于之前的主题生成新的变体。
    """
        
        # 上下文信息
        context_info = ""
        if context and context != "无历史对话":
            context_info = f"""
    【对话上下文】
    {context}
    """
        
        # 图生图特殊规则
        img2img_rules = ""
        if is_img2img:
            img2img_rules = """
    【图生图特殊规则】
    - 必须包含 "same person, same face, same pose" 保持人物一致性
    - 只修改用户明确要求的部分
    - 不要添加用户未提及的风格词
    """
        
        return f"""你是一个专业的 Stable Diffusion 提示词专家。请根据用户的自然语言描述，生成高质量的 SD 提示词。

    用户描述：{text}
    {context_info}
    {continuation_hint}

    【主题识别】
    当前主题类型：{subject_type}

    【重要规则】
    1. 提示词使用英文，用逗号分隔
    2. 包含：主体描述、场景、光线、风格、构图、色彩、情绪
    3. 添加高质量修饰词：masterpiece, best quality, photorealistic, 8k, highly detailed
    4. 根据主题类型选择合适的标签：
       - 人物：1girl, 1boy, 1woman, 1man, couple 等
       - 动物：cat, dog, rabbit, bird, fish 等具体动物名称
       - 风景：landscape, scenery, nature 等
    5. 如果是延续性对话，保持主题一致性
    6. 提取所有可识别的元素：颜色、姿势、场景、风格、情绪
    {img2img_rules}

    【输出格式】
    请严格按以下格式输出，每行一个部分：

    主题类型：[人物/动物/风景/其他]
    主体标签：[1girl/1boy/cat/dog/landscape 等]
    场景：[场景描述]
    光线：[光线描述]
    风格：[风格描述]
    构图：[构图描述]
    色彩：[色彩描述]
    情绪：[情绪描述]
    正面提示词：[完整的英文提示词]
    负面提示词：[完整的英文负面提示词]

    注意：正面提示词必须包含所有相关元素，用逗号分隔。"""

    def _parse_llm_unified_response(self, response: str, original_text: str) -> dict:
        """解析 LLM 统一格式的响应"""
        result = {
            "prompt": "",
            "negative": self._negative_templates["default"],
            "subject_type": "人物",
            "subject_tag": "1girl",
        }
        
        lines = response.strip().split('\n')
        current_section = None
        prompt_lines = []
        negative_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 解析各个字段
            if '主题类型：' in line or '主题类型:' in line:
                result["subject_type"] = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
            elif '主体标签：' in line or '主体标签:' in line:
                result["subject_tag"] = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
            elif '正面提示词：' in line or '正面提示词:' in line:
                content = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                if content:
                    result["prompt"] = content
            elif '负面提示词：' in line or '负面提示词:' in line:
                content = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                if content:
                    result["negative"] = content
            elif line.startswith('场景：') or line.startswith('场景:'):
                continue
            elif line.startswith('光线：') or line.startswith('光线:'):
                continue
            elif line.startswith('风格：') or line.startswith('风格:'):
                continue
            elif line.startswith('构图：') or line.startswith('构图:'):
                continue
            elif line.startswith('色彩：') or line.startswith('色彩:'):
                continue
            elif line.startswith('情绪：') or line.startswith('情绪:'):
                continue
        
        # 如果没有解析到提示词，尝试从整个响应中提取
        if not result["prompt"]:
            # 尝试找包含提示词的行
            for line in lines:
                if '正面提示词' in line:
                    content = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                    if content:
                        result["prompt"] = content
                        break
            
            # 如果还是没有，尝试从其他字段组合
            if not result["prompt"]:
                # 收集所有有用的描述
                parts = []
                for line in lines:
                    if line.startswith('主体标签：') or line.startswith('主体标签:'):
                        tag = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                        if tag:
                            parts.append(tag)
                    elif line.startswith('场景：') or line.startswith('场景:'):
                        scene = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                        if scene:
                            parts.append(scene)
                    elif line.startswith('光线：') or line.startswith('光线:'):
                        light = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                        if light:
                            parts.append(light)
                    elif line.startswith('风格：') or line.startswith('风格:'):
                        style = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                        if style:
                            parts.append(style)
                    elif line.startswith('情绪：') or line.startswith('情绪:'):
                        mood = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                        if mood:
                            parts.append(mood)
                
                if parts:
                    result["prompt"] = "masterpiece, best quality, photorealistic, 8k, highly detailed, " + ", ".join(parts)
        
        # 确保有负面提示词
        if not result["negative"]:
            # 根据主题类型选择合适的负面提示词
            subject_type = result.get("subject_type", "人物")
            if subject_type == "动物":
                result["negative"] = self._negative_templates["animal"]
            else:
                result["negative"] = self._negative_templates["default"]
        
        return result
    
    def _optimize_parameters(self, prompt: str, intent_type: str, image_features: dict = None) -> dict:
        prompt_lower = prompt.lower()
        params = {}

        # ===== 【新增】动物主题参数优化 =====
        is_animal = any(k in prompt_lower for k in ['cat', 'dog', 'rabbit', 'fox', 'wolf', 'deer', 
                                                      'bear', 'panda', 'tiger', 'lion', 'elephant', 
                                                      'giraffe', 'bird', 'eagle', 'owl', 'fish', 
                                                      'whale', 'dolphin', 'shark', 'horse', 'butterfly', 
                                                      'snake', 'animal', 'kitten', 'puppy'])
        
        if is_animal:
            # 动物主题：步数可以稍少，CFG稍低
            if any(k in prompt_lower for k in ['快速', '快', '预览', 'quick', 'fast']):
                params["steps"] = 10
            elif any(k in prompt_lower for k in ['高质量', '精美', '细致', 'high quality', 'detailed']):
                params["steps"] = 25
            else:
                params["steps"] = 16  # 动物默认步数
            
            params["cfg"] = 6.5  # 动物主题用稍低CFG更自然
            
            # 动物主题尺寸（修复：使用中文关键词检测）
            if any(k in prompt_lower for k in ['肖像', '头像', '特写', 'close-up', 'portrait', 'face']):
                params["width"] = 512
                params["height"] = 512
                params["size_msg"] = "动物肖像（方图）"
            elif any(k in prompt_lower for k in ['全身', '站立', 'full body', 'standing', 'full-length']):
                params["width"] = 512
                params["height"] = 768
                params["size_msg"] = "动物全身（竖图）"
            elif any(k in prompt_lower for k in ['风景', '场景', 'landscape', 'scenery', 'scene']):
                params["width"] = 768
                params["height"] = 512
                params["size_msg"] = "动物与风景（横图）"
            else:
                params["width"] = 512
                params["height"] = 512
                params["size_msg"] = "动物默认（方图）"
            
            # 添加默认的 negative（如果是动物主题，使用动物专用负面提示词）
            if not params.get("negative"):
                params["negative"] = self._negative_templates.get("animal", self._negative_templates["default"])
            
            return params
        
        # ===== 人物主题：原有参数优化逻辑 =====
        if any(k in prompt_lower for k in ['快速', '快', '预览', '草稿', 'quick', 'fast', 'draft']):
            params["steps"] = 8
        elif any(k in prompt_lower for k in ['高质量', '精美', '细致', '大师', '杰作', 'high quality', 'masterpiece']):
            params["steps"] = 30
        elif any(k in prompt_lower for k in ['动漫', '卡通', '二次元', 'anime', 'cartoon']):
            params["steps"] = 16
        elif any(k in prompt_lower for k in ['写实', '真实', '照片', 'realistic', 'photorealistic', 'photo']):
            params["steps"] = 24
        else:
            params["steps"] = 12

        if any(k in prompt_lower for k in ['抽象', '梦幻', '随意', 'abstract', 'dreamy']):
            params["cfg"] = 5.0
        elif any(k in prompt_lower for k in ['写实', '真实', '照片', 'realistic', 'photorealistic']):
            params["cfg"] = 8.0
        elif any(k in prompt_lower for k in ['动漫', '卡通', 'anime', 'cartoon']):
            params["cfg"] = 6.5
        else:
            params["cfg"] = 7.5

        if any(k in prompt_lower for k in ['肖像', '头像', '特写', '脸部', 'portrait', 'headshot', 'close-up', 'face']):
            params["width"], params["height"] = 512, 640
            params["size_msg"] = "肖像模式（竖图）"
        elif any(k in prompt_lower for k in ['全身', '站立', '整体', 'full body', 'standing']):
            params["width"], params["height"] = 512, 768
            params["size_msg"] = "全身照（竖图）"
        elif any(k in prompt_lower for k in ['风景', '场景', '全景', '横', 'landscape', 'scenery', 'panorama']):
            params["width"], params["height"] = 896, 512
            params["size_msg"] = "风景模式（横图）"
        elif any(k in prompt_lower for k in ['双人', '多人', '情侣', 'couple', 'two', 'group']):
            params["width"], params["height"] = 640, 896
            params["size_msg"] = "双人照（竖图）"
        else:
            params["width"], params["height"] = 512, 768
            params["size_msg"] = "默认竖图"

        if intent_type == "image_to_image":
            if any(k in prompt_lower for k in ['微调', '轻微', '稍微', 'slight', 'minor']):
                params["strength"] = 0.25
            elif any(k in prompt_lower for k in ['大幅', '完全', '改变', 'major', 'full', 'change']):
                params["strength"] = 0.55
            elif any(k in prompt_lower for k in ['风格', '风格转换', 'style', 'style transfer']):
                params["strength"] = 0.50
            elif any(k in prompt_lower for k in ['换装', '换衣服', '换背景', 'change clothes', 'change background']):
                params["strength"] = 0.35
            else:
                params["strength"] = 0.40

            if image_features and image_features.get("has_face"):
                params["strength"] = min(params["strength"], 0.35)

        return params
    
    def _extract_keywords(self, text: str) -> dict:
        text_lower = text.lower()

        # ===== 动物检测（扩展版） =====
        animals = []
        animal_map = {
            # 常见宠物
            '猫': 'cat', '猫咪': 'cat', '小猫': 'kitten', 'cat': 'cat',
            '狗': 'dog', '小狗': 'puppy', 'dog': 'dog', '狗狗': 'dog',
            '兔子': 'rabbit', '兔兔': 'rabbit', 'rabbit': 'rabbit',
            '仓鼠': 'hamster', 'hamster': 'hamster',
            # 野生动物
            '狐狸': 'fox', 'fox': 'fox',
            '狼': 'wolf', 'wolf': 'wolf',
            '鹿': 'deer', 'deer': 'deer',
            '熊': 'bear', 'bear': 'bear',
            '熊猫': 'panda', 'panda': 'panda',
            '老虎': 'tiger', 'tiger': 'tiger',
            '狮子': 'lion', 'lion': 'lion',
            '豹': 'leopard', 'leopard': 'leopard',
            '大象': 'elephant', 'elephant': 'elephant',
            '长颈鹿': 'giraffe', 'giraffe': 'giraffe',
            # 鸟类
            '鸟': 'bird', '小鸟': 'bird', 'bird': 'bird',
            '鹰': 'eagle', 'eagle': 'eagle',
            '猫头鹰': 'owl', 'owl': 'owl',
            '孔雀': 'peacock', 'peacock': 'peacock',
            # 海洋动物
            '鱼': 'fish', 'fish': 'fish',
            '鲸鱼': 'whale', 'whale': 'whale',
            '海豚': 'dolphin', 'dolphin': 'dolphin',
            '鲨鱼': 'shark', 'shark': 'shark',
            # 其他
            '马': 'horse', 'horse': 'horse',
            '蝴蝶': 'butterfly', 'butterfly': 'butterfly',
            '蛇': 'snake', 'snake': 'snake',
        }
        
        # 检测动物并记录具体种类
        detected_animals = []
        animal_types = []
        for cn, en in animal_map.items():
            if cn in text_lower:
                if en not in animal_types:
                    animal_types.append(en)
                    detected_animals.append(en)
        
        # 检测是否是动物主题
        is_animal = len(detected_animals) > 0
        
        # 检测动物特征描述
        animal_features = []
        feature_map = {
            '可爱': 'cute',
            '毛茸茸': 'fluffy',
            '胖': 'chubby',
            '萌': 'adorable',
            '优雅': 'elegant',
            '威风': 'majestic',
            '凶猛': 'fierce',
            '温顺': 'gentle',
            '活泼': 'lively',
            '慵懒': 'lazy',
            '调皮': 'playful',
            '高贵': 'noble',
            '野性': 'wild',
            '灵动': 'agile',
        }
        for cn, en in feature_map.items():
            if cn in text_lower:
                animal_features.append(en)
                
        # ===== 性别检测（仅非动物主题） =====
        genders = []
        if not is_animal:
            if any(k in text_lower for k in ['女', '美女', '女孩', '女性', '姑娘', '小姐姐', '女神']):
                genders.append("1girl")
            elif any(k in text_lower for k in ['男', '帅哥', '男孩', '男性', '小哥哥', '男神']):
                genders.append("1boy")
            elif any(k in text_lower for k in ['情侣', '双人', '两人', '夫妻', 'couple', '恋人']):
                genders.append("1girl, 1boy")
            
        # ===== 【新增】如果检测到动物，添加 animal 关键词 =====
        subject_parts = []
        if is_animal:
            subject_parts.extend(animals)
        
        clothes_map = {
            '裙子': 'dress',
            '连衣裙': 'dress',
            '礼服': 'evening gown',
            '旗袍': 'qipao',
            '汉服': 'hanfu',
            '和服': 'kimono',
            '上衣': 'top',
            '衬衫': 'shirt',
            'T恤': 't-shirt',
            '外套': 'jacket',
            '大衣': 'coat',
            '牛仔裤': 'jeans',
            '裤子': 'pants',
            '短裤': 'shorts',
            '泳衣': 'swimsuit',
            '比基尼': 'bikini',
            '内衣': 'lingerie',
            '蕾丝': 'lace',
            '丝袜': 'stockings',
            '高跟鞋': 'high heels',
            '运动服': 'sportswear',
            '婚纱': 'wedding dress',
            '晚礼服': 'evening dress',
            '制服': 'uniform',
            '校服': 'school uniform',
            '军装': 'military uniform',
            '护士服': 'nurse uniform',
            '女仆装': 'maid outfit',
        }
        clothes = []
        for cn, en in clothes_map.items():
            if cn in text_lower:
                clothes.append(en)

        colors_map = {
            '白色': 'white',
            '黑色': 'black',
            '红色': 'red',
            '蓝色': 'blue',
            '绿色': 'green',
            '粉色': 'pink',
            '紫色': 'purple',
            '黄色': 'yellow',
            '金色': 'golden',
            '银色': 'silver',
            '透明': 'transparent',
            '裸色': 'nude',
            '橙色': 'orange',
            '灰色': 'gray',
            '棕色': 'brown',
            '彩色': 'colorful',
            '渐变': 'gradient',
        }
        colors = []
        for cn, en in colors_map.items():
            if cn in text_lower:
                colors.append(en)

        scenes_map = {
            '沙滩': 'beach',
            '海滩': 'beach',
            '海边': 'ocean',
            '卧室': 'bedroom',
            '浴室': 'bathroom',
            '花园': 'garden',
            '森林': 'forest',
            '城市': 'city',
            '街道': 'street',
            '咖啡厅': 'cafe',
            '餐厅': 'restaurant',
            '办公室': 'office',
            '公园': 'park',
            '泳池': 'swimming pool',
            '舞台': 'stage',
            '宫殿': 'palace',
            '城堡': 'castle',
            '雪山': 'snow mountain',
            '日落': 'sunset',
            '星空': 'starry sky',
            '雨中': 'rainy',
            '雪地': 'snowy',
            '花海': 'flower field',
        }
        scenes = []
        for cn, en in scenes_map.items():
            if cn in text_lower:
                scenes.append(en)

        styles_map = {
            '动漫': 'anime style',
            '油画': 'oil painting style',
            '水彩': 'watercolor style',
            '素描': 'sketch style',
            '写实': 'photorealistic',
            '赛博朋克': 'cyberpunk style',
            '暗黑': 'dark style',
            '梦幻': 'dreamy style',
            '复古': 'vintage style',
            '古风': 'traditional Chinese style',
            '唯美': 'aesthetic style',
            '可爱': 'cute style',
            '性感': 'sexy style',
            '优雅': 'elegant style',
            '科幻': 'sci-fi style',
            '哥特': 'gothic style',
            '蒸汽朋克': 'steampunk style',
            '极简': 'minimalist style',
            '浮世绘': 'ukiyo-e style',
            '水墨': 'ink wash style',
            '工笔': 'gongbi style',
        }
        styles = []
        for cn, en in styles_map.items():
            if cn in text_lower:
                styles.append(en)

        poses_map = {
            '站立': 'standing',
            '坐': 'sitting',
            '躺': 'lying',
            '蹲': 'squatting',
            '跪': 'kneeling',
            '弯腰': 'bending over',
            '回头': 'looking back',
            '侧身': 'side view',
            '趴': 'lying on stomach',
            '睡': 'sleeping',
            '奔跑': 'running',
            '走路': 'walking',
            '跳舞': 'dancing',
            '拥抱': 'hugging',
            '接吻': 'kissing',
            '仰头': 'looking up',
            '低头': 'looking down',
            '托腮': 'hand on chin',
            '叉腰': 'hands on hips',
            '比心': 'heart shape hand',
        }
        poses = []
        for cn, en in poses_map.items():
            if cn in text_lower:
                poses.append(en)

        expressions_map = {
            '微笑': 'smiling',
            '大笑': 'laughing',
            '严肃': 'serious',
            '忧郁': 'melancholy',
            '诱惑': 'seductive',
            '性感': 'seductive expression',
            '可爱': 'cute expression',
            '害羞': 'shy',
            '惊讶': 'surprised',
            '愤怒': 'angry',
            '悲伤': 'sad',
            '深情': 'affectionate',
            '冷漠': 'cold expression',
            '灿烂': 'bright smile',
            '温柔': 'gentle expression',
        }
        expressions = []
        for cn, en in expressions_map.items():
            if cn in text_lower:
                expressions.append(en)

        body_map = {
            '大胸': 'large breasts',
            '巨乳': 'huge breasts',
            '丰满': 'curvy figure',
            '苗条': 'slim figure',
            '匀称': 'fit body',
            '肌肉': 'muscular',
            '修长': 'long legs',
            '美腿': 'beautiful legs',
            '纤细': 'slender',
        }
        body = []
        for cn, en in body_map.items():
            if cn in text_lower:
                body.append(en)

        lighting_map = {
            '自然光': 'natural lighting',
            '暖光': 'warm lighting',
            '冷光': 'cold lighting',
            '柔光': 'soft lighting',
            '逆光': 'backlighting',
            '阳光': 'sunlight',
            '月光': 'moonlight',
            '烛光': 'candlelight',
            '霓虹': 'neon lighting',
            '黄昏': 'golden hour',
            '黎明': 'dawn light',
            '阴天': 'overcast lighting',
            '舞台光': 'stage lighting',
            '聚光灯': 'spotlight',
        }
        lighting = []
        for cn, en in lighting_map.items():
            if cn in text_lower:
                lighting.append(en)

        materials_map = {
            '大理石': 'marble',
            '石膏': 'plaster',
            '青铜': 'bronze',
            '铜': 'bronze',
            '金': 'gold',
            '银': 'silver',
            '水晶': 'crystal',
            '玻璃': 'glass',
            '陶瓷': 'ceramic',
            '粘土': 'clay',
            '木头': 'wood',
            '木雕': 'wood carving',
            '石雕': 'stone carving',
            '玉石': 'jade',
            '翡翠': 'jade',
            '金属': 'metal',
            '铁': 'iron',
            '钢铁': 'steel',
            '蜡': 'wax',
            '塑料': 'plastic',
            '树脂': 'resin',
            '织物': 'fabric',
            '丝绸': 'silk',
            '天鹅绒': 'velvet',
            '皮革': 'leather',
            '纸质': 'paper',
        }
        materials = []
        for cn, en in materials_map.items():
            if cn in text_lower:
                materials.append(en)

        is_statue = any(k in text_lower for k in ['雕像', '雕塑', '石刻', '石像', '塑像', 'statue', 'sculpture'])
        if is_statue and not materials:
            materials.append('marble')

        actions = []
        if any(k in text_lower for k in ['去掉衣服', '脱衣服', '脱光', '去衣', '裸体', 'nude', 'naked']):
            actions.append("remove_clothes")
        elif any(k in text_lower for k in ['换衣服', '换装', '改衣服', '换成']):
            actions.append("change_clothes")
        if any(k in text_lower for k in ['换颜色', '改颜色', '变色']):
            actions.append("change_color")
        if any(k in text_lower for k in ['换背景', '改背景', '背景换成']):
            actions.append("change_background")
        if any(k in text_lower for k in ['换风格', '改风格', '风格换成']):
            actions.append("change_style")
        if any(k in text_lower for k in ['做成', '变成', '转换为', '转化', '制作', 'turn into', 'convert to']):
            actions.append("transform_material")

        return {
            "genders": genders,
            "animals": detected_animals,  # 检测到的动物列表
            "is_animal": is_animal,        # 是否为动物主题
            "animal_features": animal_features,  # 动物特征描述
            "animal_type": detected_animals[0] if detected_animals else None,  # 主要动物          
            "clothes": clothes,
            "colors": colors,
            "scenes": scenes,
            "styles": styles,
            "poses": poses,
            "expressions": expressions,
            "body": body,
            "lighting": lighting,
            "materials": materials,
            "is_statue": is_statue,
            "actions": actions,
        }

    def _estimate_params(self, prompt: str, is_image: bool = False) -> dict:
        prompt_lower = prompt.lower()

        is_portrait = any(k in prompt_lower for k in ['portrait', 'headshot', 'close up', 'face', '头像', '特写', '自拍'])
        is_full_body = any(k in prompt_lower for k in ['full body', 'standing', '全身', '站立', 'full-length'])
        is_half_body = any(k in prompt_lower for k in ['half body', '半身', 'from waist up', 'upper body'])
        is_landscape = any(k in prompt_lower for k in ['landscape', 'scenery', '风景', '山水', 'cityscape'])
        is_couple = any(k in prompt_lower for k in ['couple', 'two people', '双人', '情侣', '两人'])
        is_group = any(k in prompt_lower for k in ['group', 'three people', '多人', '三人', '人群'])
        is_square = any(k in prompt_lower for k in ['square', '1:1', '方图'])

        mode = getattr(self, 'quality_mode_var', tk.StringVar(value="平衡")).get()

        if mode == "超高质量":
            size_config = {
                "portrait": (768, 1024),
                "full_body": (768, 1152),
                "half_body": (896, 1024),
                "landscape": (1344, 768),
                "couple": (896, 1344),
                "group": (1152, 896),
                "square": (1024, 1024),
                "default": (768, 1024),
            }
            steps_override = 30
            max_size = 1536

        elif mode == "快速":
            size_config = {
                "portrait": (256, 384),
                "full_body": (256, 384),
                "half_body": (320, 384),
                "landscape": (448, 256),
                "couple": (320, 448),
                "group": (384, 320),
                "square": (320, 320),
                "default": (256, 384),
            }
            steps_override = 8
            size_suffix = "（快速模式）"
        elif mode == "平衡":
            size_config = {
                "portrait": (384, 512),
                "full_body": (384, 576),
                "half_body": (448, 576),
                "landscape": (640, 384),
                "couple": (448, 640),
                "group": (576, 448),
                "square": (448, 448),
                "default": (384, 576),
            }
            steps_override = 12
            size_suffix = "（平衡模式）"
        else:
            size_config = {
                "portrait": (512, 640),
                "full_body": (512, 768),
                "half_body": (640, 768),
                "landscape": (896, 512),
                "couple": (640, 896),
                "group": (768, 640),
                "square": (640, 640),
                "default": (512, 768),
            }
            steps_override = 20
            size_suffix = "（高质量模式）"

        if is_image and self.uploaded_image_path:
            try:
                from PIL import Image
                img = Image.open(self.uploaded_image_path)
                w, h = img.size

                max_size = {
                    "快速": 384,
                    "平衡": 512,
                    "高质量": 768,
                }.get(mode, 512)

                if max(w, h) > max_size:
                    scale = max_size / max(w, h)
                    w = int(w * scale)
                    h = int(h * scale)

                width = ((w + 31) // 64) * 64
                height = ((h + 31) // 64) * 64

                if width < 256:
                    width = 256
                if height < 256:
                    height = 256

                steps = self.chat_steps_var.get()
                if steps > 30:
                    steps = steps_override

                cfg = self.chat_cfg_var.get()

                return {
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg": cfg,
                    "strength": 0.4,
                    "num_images": 1,
                    "mode": mode,
                }
            except:
                pass

        if is_portrait:
            width, height = size_config["portrait"]
        elif is_full_body:
            width, height = size_config["full_body"]
        elif is_half_body:
            width, height = size_config["half_body"]
        elif is_landscape:
            width, height = size_config["landscape"]
        elif is_couple:
            width, height = size_config["couple"]
        elif is_group:
            width, height = size_config["group"]
        elif is_square:
            width, height = size_config["square"]
        else:
            width, height = size_config["default"]

        steps = self.chat_steps_var.get()
        cfg = self.chat_cfg_var.get()

        return {
            "width": width,
            "height": height,
            "steps": steps,
            "cfg": cfg,
            "strength": 0.4 if is_image else None,
            "num_images": 1,
            "mode": mode,
        }

    # ==================== 文生图处理 ====================

    def _handle_large_scale_generation(self, intent: dict):
        try:
            prompt = intent.get("prompt", "")
            original_text = intent.get("original_text", "")
            params = intent.get("params", {})

            self._append_message("system", "📐 正在生成大尺度图片（两阶段）...")

            self._append_message("system", "📝 阶段1: 生成预览图...")

            from utils.pipeline_pool import pipeline_pool
            import random
            from datetime import datetime

            model_name = self.app.model_var.get()
            model_path = self.app._get_model_path(model_name)

            # 获取 LoRA
            lora_path = self.current_lora_path if self.lora_loaded else None
            lora_weight = 1.0

            task_id = f"large_scale_{datetime.now().strftime('%H%M%S')}"

            pipe, is_new = pipeline_pool.get_pipeline(
                model_path=model_path,
                model_name=model_name,
                lora_path=lora_path,
                lora_weight=lora_weight,
                task_id=task_id
            )

            if pipe is None:
                self._append_message("assistant", "❌ 无法获取 Pipeline")
                return

            seed = random.randint(1, 2**32 - 1)
            generator = torch.Generator("cpu").manual_seed(seed)

            small_result = pipe(
                prompt=prompt,
                negative_prompt=self._negative_templates["default"],
                num_inference_steps=20,
                guidance_scale=7.5,
                height=768,
                width=512,
                generator=generator,
                num_images_per_prompt=1
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = os.path.join(tempfile.gettempdir(), f"temp_{timestamp}_small.png")
            small_result.images[0].save(temp_path)

            pipeline_pool.release_pipeline(model_path, lora_path, task_id)

            self._append_message("system", "✅ 阶段1完成，正在放大...")

            output_path = self._upscale_image(temp_path, scale=2)

            if output_path == temp_path:
                self._append_message("system", "⚠️ 使用 PIL 简单放大...")
                img = Image.open(temp_path)
                new_size = (img.width * 2, img.height * 2)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                output_dir = app_config.paths.output_dir
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{timestamp}_large_{original_text[:20]}.png")
                img.save(output_path)

            try:
                os.remove(temp_path)
            except:
                pass

            self._append_image_result(output_path)
            self._append_message("assistant", f"✅ 大尺度图片生成完成！\n📁 {os.path.basename(output_path)}\n📐 尺寸: {Image.open(output_path).size}")
            self.app.add_to_preview(output_path, Image.open(output_path))

        except Exception as e:
            self._append_message("assistant", f"❌ 大尺度生成失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def _upscale_image(self, image_path: str, scale: int = 2) -> str:
        from datetime import datetime
        from config.app_config import app_config

        try:
            try:
                import cv2
                from basicsr.archs.rrdbnet_arch import RRDBNet
                from realesrgan import RealESRGANer

                img = cv2.imread(image_path)
                if img is None:
                    return image_path

                model_path = "models/realesrgan_x4plus.pth"
                if not os.path.exists(model_path):
                    print(f"⚠️ Real-ESRGAN 模型不存在: {model_path}")
                    raise FileNotFoundError("模型文件不存在")

                model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=scale)
                upsampler = RealESRGANer(
                    scale=scale,
                    model_path=model_path,
                    model=model,
                    tile=0,
                    tile_pad=10,
                    pre_pad=0,
                    half=False
                )

                output, _ = upsampler.enhance(img, outscale=scale)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = app_config.paths.output_dir
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{timestamp}_upscaled_{scale}x.png")
                cv2.imwrite(output_path, output)

                print(f"✅ 超分辨率完成: {output_path}")
                return output_path

            except ImportError as e:
                print(f"⚠️ Real-ESRGAN 未安装: {e}")

            except FileNotFoundError as e:
                print(f"⚠️ {e}")

            from PIL import Image

            print("📦 使用 PIL LANCZOS 放大...")
            img = Image.open(image_path)

            new_width = img.width * scale
            new_height = img.height * scale

            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{timestamp}_upscaled_{scale}x_pil.png")
            img_resized.save(output_path)

            print(f"✅ PIL 放大完成: {output_path}")
            return output_path

        except Exception as e:
            print(f"⚠️ 超分辨率失败: {e}")
            return image_path

    def _handle_text_to_image(self, intent: dict):
        if self._is_loading_model:
            self._append_message("assistant", "⏳ 模型正在加载中，请稍候...")
            return

        if not self.app.model_manager.is_sd_loaded:
            self._append_message("assistant", "📦 正在自动加载模型...")
            self._pending_intent = intent
            if not self._ensure_model_loaded():
                return
            self._append_message("assistant", "⏳ 模型加载中，请稍候再试...")
            return

        # ===== 获取提示词 =====
        if intent.get("llm_generated", False):
            # LLM 生成的提示词
            prompt = intent["prompt"]
            negative = intent.get("negative", self._negative_templates["default"])
            print(f"\n📝 [LLM 生成的提示词]")
            print(f"   {prompt}")
            
            # ===== 【新增】如果检测到延续性，提示用户 =====
            if intent.get("is_continuation", False) and self.last_prompt:
                print(f"   🔄 [延续模式] 基于之前的主题: {self.last_prompt[:60]}...")
                self._append_message("system", f"🔄 延续之前的话题，生成新变体...")
        else:
            # 降级方案：使用原有的构建逻辑
            prompt = intent.get("prompt", "")
            negative = intent.get("negative", self._negative_templates["default"])
            
            # 如果是延续性，添加上下文增强
            if intent.get("is_continuation", False) and self.last_prompt:
                prompt = self._enhance_with_context(prompt)
                print(f"   🔄 [延续模式] 增强后: {prompt[:100]}...")

        original_text = intent.get("original_text", "")

        print("\n" + "=" * 60)
        print("📊 [文生图调试]")
        print(f"   用户输入: {original_text}")
        print(f"   提示词: {prompt}")
        if intent.get("llm_enhanced"):
            print(f"   🧠 已启用 LLM 增强")
        if intent.get("is_continuation", False):
            print(f"   🔄 延续模式")
        print("=" * 60 + "\n")

        params = self._estimate_params(prompt)

        self._append_message("system", f"⚙️ 参数: 步数={params['steps']}, CFG={params['cfg']}, 尺寸={params['width']}x{params['height']}")

        if intent.get("llm_enhanced"):
            self._append_message("system", f"🧠 已使用 LLM 增强提示词")

        self._append_message("assistant", f"🎨 正在生成图片...\n\n📝 提示词:\n{prompt[:200]}{'...' if len(prompt) > 200 else ''}")

        self._update_status(f"🎨 生成中... (尺寸: {params['width']}x{params['height']})", 0.1)

        try:
            # ... 原有的生成代码保持不变 ...
            from utils.pipeline_pool import pipeline_pool
            from datetime import datetime
            import random

            model_name = self.app.model_var.get()
            model_path = self.app._get_model_path(model_name)

            # 获取 LoRA
            lora_path = self.current_lora_path if self.lora_loaded else None
            lora_weight = 1.0

            task_id = f"chat_{datetime.now().strftime('%H%M%S')}"

            pipe, is_new = pipeline_pool.get_pipeline(
                model_path=model_path,
                model_name=model_name,
                lora_path=lora_path,
                lora_weight=lora_weight,
                task_id=task_id
            )

            if pipe is None:
                self._append_message("assistant", "❌ 无法获取 Pipeline")
                return

            seed = random.randint(1, 2**32 - 1)
            generator = torch.Generator("cpu").manual_seed(seed)

            self._update_status(f"🎨 生成中... 步骤: {params['steps']}", 0.3)

            # 检测是否是动物主题，使用对应的负面提示词
            keywords = intent.get("keywords", {})
            is_animal = keywords.get("is_animal", False)
            
            if is_animal:
                negative = self._negative_templates["animal"]
            elif not negative:
                negative = getattr(self, '_last_negative', self._negative_templates["default"])

            result = pipe(
                prompt=prompt,
                negative_prompt=negative,
                num_inference_steps=params["steps"],
                guidance_scale=params["cfg"],
                height=params["height"],
                width=params["width"],
                generator=generator,
                num_images_per_prompt=1  # ✅ 改为1张，避免过多
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prompt_preview = "".join(c for c in prompt[:30] if c.isalnum() or c in " _-") or "image"
            filename = f"{timestamp}_chat_{prompt_preview}.png"

            from config.app_config import app_config
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            result.images[0].save(filepath)

            # ===== 图片后处理 =====
            try:
                from utils.image_post_processor import post_process_image
                final_path = post_process_image(
                    filepath,
                    self.params,
                    prompt=prompt,
                    log_prefix="[会话生图]"
                )
                if final_path != filepath:
                    try:
                        os.remove(filepath)
                    except:
                        pass
                    filepath = final_path
            except:
                pass

            pipeline_pool.release_pipeline(model_path, lora_path, task_id)

            self._append_image_result(filepath)
            self._append_message("assistant", f"✅ 图片已生成！\n📁 {os.path.basename(filepath)}\n\n💡 提示: 继续发送描述可以生成更多图片")

            # ===== 【新增】保存上下文 =====
            self._update_context(intent, {"image_path": filepath, "prompt": prompt})
            self._save_to_context({
                "last_prompt": prompt,
                "last_negative": negative,
                "last_intent": "text_to_image",
            })
            
            self._update_status("✅ 生成完成", 1.0)
            self.app.add_to_preview(filepath, result.images[0])
            self._pending_intent = None

        except Exception as e:
            self._append_message("assistant", f"❌ 生成失败: {str(e)}")
            self._update_status("❌ 生成失败", 0)
            import traceback
            traceback.print_exc()
            self._pending_intent = None
        
    def _enhance_with_context(self, prompt: str) -> str:
        """使用上下文增强提示词（降级方案）"""
        if not self.last_prompt:
            return prompt
        
        # 如果当前提示词太短，可能是在延续
        if len(prompt.split(',')) < 3:
            # 从上次的提示词中提取主体标签
            parts = self.last_prompt.split(',')
            subject_tag = parts[0] if parts else "1girl"
            
            # 保留主题，添加当前描述
            enhanced = f"{subject_tag}, {prompt}"
            return enhanced
        
        return prompt
    
    def _get_conversation_context(self) -> str:
        """获取对话上下文摘要"""
        if not self.conversation_history:
            return "无历史对话"
        
        # 获取最近 5 轮对话
        recent = self.conversation_history[-5:] if len(self.conversation_history) > 5 else self.conversation_history
        
        context_parts = []
        for item in recent:
            intent = item.get("intent", {})
            result = item.get("result", {})
            
            if intent.get("type") == "text_to_image":
                prompt = intent.get("prompt", "")
                if prompt:
                    context_parts.append(f"用户要求生成: {prompt[:100]}...")
            elif intent.get("type") == "image_to_image":
                prompt = intent.get("prompt", "")
                if prompt:
                    context_parts.append(f"用户要求修改图片: {prompt[:100]}...")
            elif intent.get("type") == "chat":
                original = intent.get("original_text", "")
                if original:
                    context_parts.append(f"用户说: {original[:50]}...")
        
        if result and result.get("image_path"):
            context_parts.append(f"已生成图片: {os.path.basename(result['image_path'])}")
        
        if not context_parts:
            return "无历史对话"
        
        return "\n".join(context_parts)

    def _is_continuation(self, text: str) -> bool:
        """检测是否是延续性指令"""
        continuation_keywords = ['再来', '继续', '换一个', '换一张', '再生成', 'another', 'continue', '再', '又']
        text_lower = text.lower()
        
        # 检查是否包含延续关键词
        if any(k in text_lower for k in continuation_keywords):
            return True
        
        # 检查是否包含"也"、"和"等连接词（表示延续）
        if any(k in text_lower for k in ['也', '和', '以及', '还有', '另外', '同样']):
            # 如果之前有生成记录，可能是延续
            if self.last_prompt:
                return True
        
        # 检查是否是简短指令（少于5个字且没有明确主题）
        if len(text) < 5 and self.last_prompt:
            return True
        
        return False
    
    def _save_to_context(self, data: dict):
        """保存上下文信息"""
        if data.get("last_prompt"):
            self.last_prompt = data["last_prompt"]
        if data.get("last_negative"):
            self._last_negative = data["last_negative"]
        if data.get("last_intent"):
            self.last_intent_type = data["last_intent"]
        if data.get("subject"):
            self.user_preferences["subject"] = data["subject"]
            
    # ==================== 图生图处理 ====================

    def _handle_image_to_image(self, intent: dict):
        if self.uploaded_image is None:
            self._append_message("assistant", "❌ 请先上传一张图片")
            return

        if self._is_loading_model:
            self._append_message("assistant", "⏳ 模型正在加载中，请稍候...")
            return

        if not self.app.model_manager.is_sd_loaded:
            self._append_message("assistant", "📦 正在自动加载模型...")
            self._pending_intent = intent
            if not self._ensure_model_loaded():
                return
            self._append_message("assistant", "⏳ 模型加载中，请稍候再试...")
            return

        prompt = intent["prompt"]
        image_features = self._analyze_image_features(self.uploaded_image_path)

        params = intent.get("params", {})
        if not params:
            params = self._optimize_parameters(prompt, "image_to_image", image_features)

        self._setup_controlnet()

        user_text = intent.get("original_text", "").lower()
        pose_keywords = ['站立', '坐', '躺', '蹲', '跪', '弯腰', '回头', '侧身',
                         '奔跑', '走路', '跳舞', '拥抱', '接吻', '仰头', '低头']
        needs_pose_control = any(k in user_text for k in pose_keywords)

        keywords = intent.get("keywords", {})
        user_poses = keywords.get("poses", [])

        use_controlnet = needs_pose_control and hasattr(self, 'controlnet_available') and self.controlnet_available

        if use_controlnet and user_poses:
            pose_image = self._extract_pose_from_image(self.uploaded_image_path)
            if pose_image:
                self._append_message("system", "🦴 已提取姿态图，使用 ControlNet 控制")
                self._handle_controlnet_generation(prompt, pose_image, intent, params)
                return
            else:
                self._append_message("system", "⚠️ 姿态提取失败，使用普通图生图")

        steps = params.get("steps", 20)
        cfg = params.get("cfg", 7.5)
        strength = params.get("strength", 0.35)

        width = params.get("width", 512)
        height = params.get("height", 768)

        self._append_message("system", f"⚙️ 自动参数: 步数={steps}, CFG={cfg}, 强度={strength}")

        if intent.get("llm_enhanced"):
            style_removals = ['elegant', 'modern', 'professional', 'fashionable', 'professional style']
            for word in style_removals:
                prompt = prompt.replace(word, '')
            prompt = re.sub(r',\s*,', ',', prompt)
            prompt = prompt.strip(', ')
            intent["prompt"] = prompt
            print(f"   ✂️ 精简风格词后: {prompt[:100]}...")

        enhanced_prompt = self._enhance_prompt_with_features(prompt, intent, image_features)
        if enhanced_prompt != prompt:
            prompt = enhanced_prompt
            intent["prompt"] = prompt
            print(f"   ✅ 已结合原图特征增强提示词: {prompt[:150]}...")

        if not intent.get("llm_enhanced"):
            enhanced_prompt = self._enhance_prompt_with_context(prompt, keywords)
            if enhanced_prompt:
                prompt = enhanced_prompt
                print(f"   📝 使用备用增强提示词: {prompt[:150]}...")

        keywords = intent.get("keywords", {})

        if keywords.get("is_statue") or "transform_material" in keywords.get("actions", []):
            materials = keywords.get("materials", [])
            if materials:
                material = materials[0]
                prompt = f"made of {material}, {material} statue, sculpture, {material} texture, polished, classical style, masterpiece, best quality"
                self._append_message("system", f"🗿 检测到材质转换: {material}")

        print("\n" + "=" * 60)
        print("📊 [图生图调试]")
        print(f"   用户输入: {intent.get('original_text', '')}")
        print(f"   提示词: {prompt}")
        if intent.get("llm_enhanced"):
            print(f"   🧠 已启用 LLM 增强")
        print("=" * 60 + "\n")

        prompt_lower = prompt.lower()
        has_preserve = "same person" in prompt_lower and "same face" in prompt_lower

        if has_preserve:
            full_prompt = prompt
        else:
            preserve_parts = ["same person", "same face", "same identity"]
            face_count = image_features.get("face_count", 0)

            user_text = intent.get("original_text", "").lower()
            mentioned_multiple = any(k in user_text for k in ['双人', '多人', '两人', '情侣', 'couple', 'two', 'group'])

            if face_count >= 2 and mentioned_multiple:
                preserve_parts.append("same two people")
                preserve_parts.append("same couple")
                self._append_message("system", f"👥 检测到双人/多人 ({face_count} 张人脸)")
            elif face_count >= 2 and not mentioned_multiple:
                self._append_message("system", f"⚠️ 检测到 {face_count} 张人脸，但用户未提及多人，按单人处理")
                face_count = 1

            preserve_parts.append("same pose")
            preserve_parts.append("same body language")

            if image_features.get("is_full_body", True):
                preserve_parts.append("full body")
            else:
                preserve_parts.append("half body")

            preserve_str = ", ".join(preserve_parts)

            for part in preserve_parts:
                if part in prompt_lower:
                    preserve_parts.remove(part)

            if preserve_parts:
                full_prompt = f"{', '.join(preserve_parts)}, {prompt}"
            else:
                full_prompt = prompt

        print(f"📝 [调试] 最终提示词: {full_prompt}")

        self._append_message("system", f"📝 完整提示词:\n{full_prompt[:200]}{'...' if len(full_prompt) > 200 else ''}")

        params = self._estimate_params(prompt, is_image=True)
        orig_w = image_features.get("width", 512)
        orig_h = image_features.get("height", 768)
        params["width"] = ((orig_w + 31) // 64) * 64
        params["height"] = ((orig_h + 31) // 64) * 64
        if params["width"] > 1024:
            params["width"] = 1024
        if params["height"] > 1024:
            params["height"] = 1024

        strength = 0.2
        if image_features.get("is_bright"):
            strength = 0.18
        elif image_features.get("is_dark"):
            strength = 0.25
        if image_features.get("has_face"):
            strength = min(strength, 0.2)
            self._append_message("system", f"🛡️ 检测到面部，降低强度保护面部: {strength:.2f}")

        params["strength"] = strength

        self._append_message("system", f"⚙️ 参数: 步数={params['steps']}, CFG={params['cfg']}, 强度={params['strength']}")

        self._append_message("assistant", f"🔄 正在修改图片...\n\n📝 指令:\n{prompt[:100]}{'...' if len(prompt) > 100 else ''}")

        self._update_status(f"🔄 修改中... (强度: {params['strength']})", 0.1)

        try:
            from utils.pipeline_pool import pipeline_pool
            from datetime import datetime
            import random

            model_name = self.app.model_var.get()
            model_path = self.app._get_model_path(model_name)

            # 获取 LoRA
            lora_path = self.current_lora_path if self.lora_loaded else None
            lora_weight = 1.0

            task_id = f"chat_img2img_{datetime.now().strftime('%H%M%S')}"

            pipe, is_new = pipeline_pool.get_pipeline(
                model_path=model_path,
                model_name=model_name,
                lora_path=lora_path,
                lora_weight=lora_weight,
                task_id=task_id
            )

            if pipe is None:
                self._append_message("assistant", "❌ 无法获取 Pipeline")
                return

            init_image = self.uploaded_image.copy().convert('RGB')
            w, h = init_image.size

            new_w = ((w + 31) // 64) * 64
            new_h = ((h + 31) // 64) * 64
            if new_w != w or new_h != h:
                init_image = init_image.resize((new_w, new_h))

            max_size = 1024
            if max(new_w, new_h) > max_size:
                scale = max_size / max(new_w, new_h)
                new_w = int(new_w * scale)
                new_h = int(new_h * scale)
                new_w = ((new_w + 31) // 64) * 64
                new_h = ((new_h + 31) // 64) * 64
                init_image = init_image.resize((new_w, new_h))

            self._update_status(f"🔄 修改中... 尺寸: {new_w}x{new_h}", 0.3)

            seed = random.randint(1, 2**32 - 1)
            generator = torch.Generator("cpu").manual_seed(seed)

            negative_prompt = getattr(self, '_last_negative', self._negative_templates["default"])

            result = pipe(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                image=init_image,
                strength=params["strength"],
                num_inference_steps=params["steps"],
                guidance_scale=params["cfg"],
                generator=generator,
                num_images_per_prompt=1
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prompt_preview = "".join(c for c in prompt[:30] if c.isalnum() or c in " _-") or "edit"
            filename = f"{timestamp}_chat_edit_{prompt_preview}.png"

            from config.app_config import app_config
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            result.images[0].save(filepath)

            pipeline_pool.release_pipeline(model_path, lora_path, task_id)

            self._append_image_result(filepath)
            self._append_message("assistant", f"✅ 图片已修改完成！\n📁 {os.path.basename(filepath)}")

            self._update_context(intent, {"image_path": filepath, "prompt": prompt})
            self._update_status("✅ 修改完成", 1.0)
            self.app.add_to_preview(filepath, result.images[0])
            self._pending_intent = None

        except Exception as e:
            self._append_message("assistant", f"❌ 修改失败: {str(e)}")
            self._update_status("❌ 修改失败", 0)
            import traceback
            traceback.print_exc()
            self._pending_intent = None

    def _handle_controlnet_generation(self, prompt: str, pose_image: Image.Image,
                                      intent: dict, params: dict):
        try:
            from diffusers import StableDiffusionControlNetPipeline
            import torch

            if not hasattr(self, 'controlnet_pipe') or self.controlnet_pipe is None:
                self._setup_controlnet()
                if not self.controlnet_available:
                    self._append_message("assistant", "❌ ControlNet 不可用，使用普通图生图")
                    self._handle_image_to_image(intent)
                    return

            model_name = self.app.model_var.get()
            model_path = self.app._get_model_path(model_name)

            steps = params.get("steps", 20)
            cfg = params.get("cfg", 7.5)

            result = self.controlnet_pipe(
                prompt=prompt,
                image=pose_image,
                num_inference_steps=steps,
                guidance_scale=cfg,
                height=512,
                width=512,
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_controlnet_{intent.get('original_text', 'pose')[:20]}.png"

            from config.app_config import app_config
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            result.images[0].save(filepath)

            self._append_image_result(filepath)
            self._append_message("assistant", f"✅ ControlNet 生成完成！\n📁 {os.path.basename(filepath)}")
            self.app.add_to_preview(filepath, result.images[0])

        except Exception as e:
            self._append_message("assistant", f"❌ ControlNet 生成失败: {str(e)}")
            self._handle_image_to_image(intent)

    def _generate_pose_image(self, image_path: str) -> str:
        try:
            temp_path = os.path.join(tempfile.gettempdir(), f"pose_{datetime.now().strftime('%H%M%S')}.png")
            pose_img = self._extract_pose_from_image(image_path)
            if pose_img:
                pose_img.save(temp_path)
                return temp_path
        except:
            pass
        return None

    def _analyze_image_features(self, image_path: str) -> dict:
        try:
            import cv2
            import numpy as np

            img = cv2.imread(image_path)
            if img is None:
                return {}

            h, w = img.shape[:2]

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (h * w)

            is_realistic = edge_density > 0.03

            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )

            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=8,
                minSize=(30, 30)
            )

            valid_faces = []
            for (x, y, fw, fh) in faces:
                if fw > 40 and fh > 40:
                    valid_faces.append((x, y, fw, fh))
            faces = valid_faces

            if len(faces) >= 2:
                filtered_faces = []
                for i, (x1, y1, fw1, fh1) in enumerate(faces):
                    is_duplicate = False
                    for j, (x2, y2, fw2, fh2) in enumerate(faces):
                        if i == j:
                            continue
                        x_left = max(x1, x2)
                        y_top = max(y1, y2)
                        x_right = min(x1 + fw1, x2 + fw2)
                        y_bottom = min(y1 + fh1, y2 + fh2)
                        if x_right > x_left and y_bottom > y_top:
                            inter_area = (x_right - x_left) * (y_bottom - y_top)
                            area1 = fw1 * fh1
                            area2 = fw2 * fh2
                            iou = inter_area / min(area1, area2)
                            if iou > 0.3:
                                is_duplicate = True
                                break
                    if not is_duplicate:
                        filtered_faces.append((x1, y1, fw1, fh1))
                faces = filtered_faces

            is_full_body = True
            is_portrait = False
            face_ratio = 0

            if len(faces) > 0:
                x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                face_ratio = (fw * fh) / (w * h)
                if face_ratio > 0.15:
                    is_full_body = False
                    is_portrait = True
                else:
                    is_full_body = True
            else:
                aspect = w / h
                if aspect > 0.8:
                    is_full_body = True

            brightness = np.mean(gray)
            is_bright = brightness > 150
            is_dark = brightness < 80

            has_multiple_subjects = len(faces) >= 2

            return {
                "has_face": len(faces) > 0,
                "has_person": len(faces) > 0,
                "face_count": len(faces),
                "is_full_body": is_full_body,
                "is_portrait": is_portrait,
                "is_landscape": w > h * 1.2,
                "face_ratio": face_ratio,
                "has_multiple_subjects": has_multiple_subjects,
                "width": w,
                "height": h,
                "is_bright": is_bright,
                "is_dark": is_dark,
                "aspect_ratio": w / h,
                "is_realistic": is_realistic,
            }
        except Exception as e:
            print(f"⚠️ 分析图片失败: {e}")
            return {}

    # ==================== 对话处理 ====================

    def _handle_chat(self, intent: dict):
        text = intent["original_text"]
        text_lower = text.lower()

        if intent.get("llm_reply"):
            self._append_message("assistant", intent["llm_reply"])
            return

        if self.uploaded_image is not None:
            if any(k in text_lower for k in ['这是什么', '这是什么图片', '描述', '分析']):
                image_features = self._analyze_image_features(self.uploaded_image_path)
                if image_features.get("has_face"):
                    self._append_message("assistant",
                        f"📷 这张图片包含 {image_features.get('face_count', 0)} 张人脸\n"
                        f"📐 尺寸: {image_features.get('width')}x{image_features.get('height')}\n"
                        f"{'📱 竖图' if image_features.get('is_portrait') else '🖥️ 横图'}\n\n"
                        f"💡 如果你想修改它，请说：\n"
                        f"• \"把这张图改成...\"\n"
                        f"• \"换成...风格\""
                    )
                else:
                    self._append_message("assistant",
                        f"📷 已上传图片: {os.path.basename(self.uploaded_image_path)}\n"
                        f"📐 尺寸: {image_features.get('width')}x{image_features.get('height')}\n\n"
                        f"💡 如果你想修改它，请说：\"把这张图改成...\""
                    )
                return

        if '上下文' in text_lower or 'context' in text_lower:
            summary = self._get_context_summary()
            self._append_message("assistant", f"📊 当前上下文:\n{summary}")
            return

        if '偏好' in text_lower or 'preference' in text_lower:
            prefs = []
            if self.user_preferences.get("style"):
                prefs.append(f"风格: {self.user_preferences['style']}")
            if self.user_preferences.get("scene"):
                prefs.append(f"场景: {self.user_preferences['scene']}")
            if self.user_preferences.get("gender"):
                prefs.append(f"性别: {self.user_preferences['gender']}")

            if prefs:
                self._append_message("assistant", f"📌 你的偏好:\n• " + "\n• ".join(prefs))
            else:
                self._append_message("assistant", "📌 还没有记录你的偏好。生成图片时我会自动学习！")
            return

        responses = {
            '你好': '你好！有什么可以帮你的吗？',
            '你是谁': '我是智能生图助手，可以帮助你生成和修改图片。试试说 "生成一张..."！',
            '功能': '我可以：\n• 📝 文生图 - 输入描述生成图片\n• 🖼️ 图生图 - 上传图片并修改\n• 💬 自由对话 - 回答你的问题',
            '帮助': '💡 使用提示：\n• 说 "生成一张..." 来文生图\n• 先上传图片，再说 "改成..." 来图生图\n• 直接聊天也可以',
            '谢谢': '不客气！还有需要帮忙的吗？',
            '再见': '再见！随时回来找我生成图片 😊'
        }

        reply = None
        for key, value in responses.items():
            if key in text_lower:
                reply = value
                break

        if reply:
            self._append_message("assistant", reply)
        else:
            if self.llm_enabled.get() and self.llm_available:
                self._append_message("system", "🧠 正在思考...")
                llm_reply = self._call_ollama(
                    f"用户说：{text}\n请简短友好地回复（一句话，不要超过20字）：",
                    timeout=15,
                    max_tokens=128
                )
                if llm_reply:
                    self._append_message("assistant", llm_reply)
                    return

            self._append_message("assistant", f"🤔 我理解你想说：\"{text}\"\n\n如果你想生成图片，可以试试说：\n• \"生成一张...\" (文生图)\n• 先上传图片，然后说 \"改成...\" (图生图)\n\n或者直接告诉我你的需求！")

    def _ensure_model_loaded(self) -> bool:
        if self.app.model_manager.is_sd_loaded:
            return True

        self._append_message("system", "📦 检测到模型未加载，正在自动加载...")
        self._update_status("📦 正在加载模型...")

        checkpoints = getattr(self.app, 'checkpoints', [])
        if not checkpoints:
            self._append_message("assistant", "❌ 没有找到可用的 SD 模型文件\n\n请将模型文件放到 models 目录下，然后在主界面加载。")
            self._update_status("❌ 未找到模型", 0)
            return False

        model_name = checkpoints[0]
        model_path = self.app._get_model_path(model_name)

        if not model_path:
            self._append_message("assistant", f"❌ 找不到模型文件: {model_name}")
            self._update_status("❌ 模型文件不存在", 0)
            return False

        if self.app.model_manager.is_janus_loaded:
            self._append_message("system", "🔄 正在切换 Janus → SD...")

        self._is_loading_model = True

        def load_thread():
            def progress_cb(value, msg):
                self.app.root.after(0, lambda: self._update_status(f"🔄 {msg}", value))

            success = self.app.model_manager.load_sd(model_path, model_name, progress_cb)
            self.app.root.after(0, lambda: self._on_model_loaded(success, model_name))

        threading.Thread(target=load_thread, daemon=True).start()
        return True

    def _on_model_loaded(self, success: bool, model_name: str):
        self._is_loading_model = False

        if success:
            self._append_message("system", f"✅ 模型加载完成: {model_name[:40]}...")
            self._update_status("✅ 模型就绪", 1.0)
            self.progress_bar.config(value=0)

            # ✅ 模型加载完成后自动加载 LoRA
            if self.lora_enabled.get():
                lora_files = self._scan_lora_files()
                if lora_files:
                    default_lora = lora_files[0]
                    lora_path = self.lora_paths.get(default_lora)
                    if lora_path:
                        self._append_message("system", f"📦 自动加载 LoRA: {default_lora.replace('⭐ ', '')}")
                        self._load_lora_to_pipe(lora_path, default_lora)

            if self._pending_intent is not None:
                intent = self._pending_intent
                self._pending_intent = None
                self._append_message("system", "🔄 继续执行之前的请求...")

                if intent["type"] == "text_to_image":
                    self._handle_text_to_image(intent)
                elif intent["type"] == "image_to_image":
                    self._handle_image_to_image(intent)
            else:
                self._append_message("assistant", "✅ 模型已就绪，可以开始生图了！")
        else:
            self._append_message("assistant", "❌ 模型加载失败\n\n请在主界面手动加载模型后重试。")
            self._update_status("❌ 加载失败", 0)
            self._pending_intent = None

    def get_frame(self):
        return self.frame