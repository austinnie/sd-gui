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

from .base_tab import BaseTab
from gui.components.memory_monitor import force_memory_cleanup


class ChatTab(BaseTab):
    """智能会话标签页"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.params = app.params_panel
        self._init_vars()
        self.setup_ui()
        self._append_message("assistant", "👋 你好！我是智能生图助手\n\n我可以帮你：\n• 📝 文生图 - 输入描述生成图片\n• 🖼️ 图生图 - 上传图片并修改\n• 💬 自由对话 - 回答你的问题\n\n试试输入：\"生成一张美女在沙滩上的图片\"")
        
        # 绑定快捷键
        self.input_text.bind("<Control-Return>", self._on_send)
        self.input_text.bind("<Return>", self._on_send_shift_check)
    
    def _init_vars(self):
        """初始化变量"""
        self.is_generating = False
        self.cancel_generation = False
        self.uploaded_image_path = None
        self.uploaded_image = None
        self.messages = []  # 对话历史
        self.chat_context = {}  # 上下文信息
        self._is_loading_model = False  # ✅ 新增：防止重复加载
        # ✅ 新增：会话生图参数
        self.chat_steps_var = tk.IntVar(value=12)  # 默认 12 步
        self.chat_cfg_var = tk.DoubleVar(value=7.5)  
        # ✅ 新增：缓存待处理的意图
        self._pending_intent = None
    
    
    def setup_ui(self):
        """设置 UI"""
        frame = self.frame
        
        # ===== 主容器 =====
        main_frame = ttk.Frame(frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ===== 工具栏 =====
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=2)
        
        # 清除对话
        ttk.Button(toolbar, text="🗑️ 清除对话", command=self._clear_chat, width=12).pack(side=tk.LEFT, padx=2)
        
        # 上传图片
        self.upload_btn = ttk.Button(toolbar, text="📎 上传图片", command=self._upload_image, width=12)
        self.upload_btn.pack(side=tk.LEFT, padx=2)
        
        # 图片状态
        self.image_status = ttk.Label(toolbar, text="", foreground="green")
        self.image_status.pack(side=tk.LEFT, padx=10)
        
        # 图片预览（缩略图）
        self.preview_label = ttk.Label(toolbar)
        self.preview_label.pack(side=tk.LEFT, padx=5)

        # ===== 【新增】参数控制栏（第二行） =====
        param_bar = ttk.Frame(main_frame)
        param_bar.pack(fill=tk.X, pady=2)
        
        ttk.Label(param_bar, text="步数:").pack(side=tk.LEFT, padx=5)
        
        # 步数 Spinbox
        self.steps_spinbox = ttk.Spinbox(
            param_bar,
            from_=4,
            to=50,
            textvariable=self.chat_steps_var,
            width=5,
            increment=1
        )
        self.steps_spinbox.pack(side=tk.LEFT, padx=2)
        
        # 快速步数按钮
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
        
        # 快速 CFG 按钮
        for cfg in [5, 7, 7.5, 9]:
            btn = ttk.Button(
                param_bar,
                text=str(cfg),
                width=3,
                command=lambda c=cfg: self.chat_cfg_var.set(c)
            )
            btn.pack(side=tk.LEFT, padx=1)
        
        ttk.Label(param_bar, text="💡 步数越低越快，8-12步快速预览", foreground="gray", font=("", 8)).pack(side=tk.LEFT, padx=15)
        
        # ===== 对话区域 =====
        chat_container = ttk.Frame(main_frame)
        chat_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 对话显示
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
        
        # 禁用编辑
        self.chat_text.config(state=tk.DISABLED)
        
        # ===== 底部输入区 =====
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        # 输入框
        self.input_text = tk.Text(
            input_frame,
            height=4,
            wrap=tk.WORD,
            font=("微软雅黑", 10),
            relief="sunken",
            borderwidth=1
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # 右侧按钮
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
    
    def _on_send_shift_check(self, event):
        """检查是否按了 Shift+Enter"""
        if event.state & 0x1:  # Shift 键
            return
        self._on_send()
        return "break"
    
    def _on_send(self, event=None):
        """发送消息"""
        if self.is_generating:
            return
        
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return
        
        # 清空输入框
        self.input_text.delete("1.0", tk.END)
        
        # 显示用户消息
        self._append_message("user", user_input)
        
        # 处理消息
        threading.Thread(target=self._process_message, args=(user_input,), daemon=True).start()
    
    def _upload_image(self):
        """上传图片"""
        file = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("所有文件", "*.*")]
        )
        if file:
            self.uploaded_image_path = file
            self.uploaded_image = Image.open(file)
            
            # 显示状态
            self.image_status.config(text=f"📎 {os.path.basename(file)}")
            
            # 显示缩略图
            thumb = self.uploaded_image.copy()
            thumb.thumbnail((40, 40))
            photo = ImageTk.PhotoImage(thumb)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
            
            self._append_message("system", f"📎 已上传图片: {os.path.basename(file)}")
    
    def _cancel_generation(self):
        """取消生成"""
        self.cancel_generation = True
        self.is_generating = False
        self.cancel_btn.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.NORMAL)
        self.status_var.set("⏹️ 已取消")
    
    def _clear_chat(self):
        """清除对话"""
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
        self._append_message("assistant", "🗑️ 对话已清空，有什么可以帮你的？")
    
    def _append_message(self, role: str, content: str):
        """添加消息到对话"""
        self.chat_text.config(state=tk.NORMAL)
        
        # 时间戳
        timestamp = datetime.now().strftime("%H:%M")
        
        # 角色样式
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
        
        # 插入消息
        self.chat_text.insert(tk.END, f"\n{prefix}", f"{tag}_prefix")
        self.chat_text.insert(tk.END, f"{content}\n", tag)
        
        # 设置样式
        self.chat_text.tag_config(f"{tag}_prefix", foreground="gray", font=("", 8))
        self.chat_text.tag_config(tag, background=bg, font=("微软雅黑", 10), spacing1=2, spacing2=2, lmargin1=10, lmargin2=10, rmargin=10)
        
        # 滚动到底部
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
        # 保存到历史
        self.messages.append({"role": role, "content": content, "timestamp": timestamp})
    
    def _append_image_result(self, filepath: str):
        """添加图片生成结果"""
        self.chat_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M")
        
        # 插入图片（显示缩略图）
        try:
            img = Image.open(filepath)
            img.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(img)
            
            self.chat_text.insert(tk.END, f"\n🖼️ 生成 ({timestamp})\n", "image_prefix")
            
            # 插入图片（通过标签）
            self.chat_text.image_create(tk.END, image=photo)
            self.chat_text.insert(tk.END, f"\n📁 {os.path.basename(filepath)}\n", "image_info")
            
            # 保存引用防止被垃圾回收
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
        """更新状态"""
        self.status_var.set(msg)
        if progress is not None:
            self.progress_bar.config(value=progress * 100)
    
    # ==================== 消息处理 ====================
    
    def _process_message(self, user_input: str):
        """处理用户消息"""
        self.is_generating = True
        self.cancel_generation = False
        self.send_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        
        try:
            # 1. 分析意图
            intent = self._analyze_intent(user_input)
            
            self._append_message("system", f"🔍 分析意图: {intent['type']}")
            
            # 2. 执行对应操作
            if intent["type"] == "text_to_image":
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
    

    def _analyze_intent(self, text: str) -> dict:
        """分析用户意图 - 使用智能提示词"""
        text_lower = text.lower()
        has_image = self.uploaded_image is not None
        
        # 提取关键词
        keywords = self._extract_keywords(text)
        smart_prompt = self._build_smart_prompt(text, keywords)
        
        # 文生图关键词
        gen_keywords = ['生成', '画', '创建', 'create', 'generate', '画一张', '生成一张']
        edit_keywords = ['修改', '改', '换', '变成', '改成', 'edit', 'change', 'modify', '替换', '去除', '去掉']
        
        is_gen = any(k in text_lower for k in gen_keywords)
        is_edit = any(k in text_lower for k in edit_keywords)
        
        if has_image and is_edit:
            # 图生图：如果有"换"或"改成"，但用户没有指定颜色/服装，保留原样
            if not keywords.get("clothes") and not keywords.get("colors") and not keywords.get("styles"):
                smart_prompt = f"same person, same pose, {smart_prompt}"
            
            return {
                "type": "image_to_image",
                "prompt": smart_prompt,
                "keywords": keywords,
                "original_text": text
            }
        elif is_gen or (not is_edit and len(text) > 10):
            return {
                "type": "text_to_image",
                "prompt": smart_prompt,
                "keywords": keywords,
                "original_text": text
            }
        else:
            return {
                "type": "chat",
                "original_text": text
            }
        
    def _extract_prompt(self, text: str) -> str:
        """从文本中提取提示词"""
        # 移除常见前缀
        prefixes = ['生成', '画', '创建', '帮我生成', '帮我画', '我想生成', '我想画',
                    'create', 'generate', 'draw', 'make', '请生成', '请画']
        
        prompt = text
        for prefix in prefixes:
            if text.lower().startswith(prefix):
                prompt = text[len(prefix):].strip()
                break
        
        # 如果提示词太短，使用原文
        if len(prompt) < 3:
            prompt = text
        
        # 如果提示词没有质量词，自动添加
        quality_keywords = ['masterpiece', 'best quality', 'photorealistic', '8k', 'high quality']
        if not any(k in prompt.lower() for k in quality_keywords):
            prompt = f"masterpiece, best quality, photorealistic, 8k, {prompt}"
        
        return prompt
    
    def _estimate_params(self, prompt: str, is_image: bool = False) -> dict:
        """根据提示词估算参数"""
        prompt_lower = prompt.lower()
        
        # 检测场景
        is_portrait = any(k in prompt_lower for k in ['portrait', 'headshot', 'close up', 'face', '头像', '特写'])
        is_full_body = any(k in prompt_lower for k in ['full body', 'standing', '全身', '站立'])
        is_landscape = any(k in prompt_lower for k in ['landscape', 'scenery', '风景', '山水'])
        is_couple = any(k in prompt_lower for k in ['couple', 'two people', '双人', '情侣'])
        
        # 尺寸
        if is_portrait:
            width, height = 512, 768
        elif is_full_body:
            width, height = 512, 768
        elif is_landscape:
            width, height = 896, 512
        elif is_couple:
            width, height = 640, 896
        else:
            width, height = 512, 768
            
        # ===== 使用用户设置的步数和 CFG =====
        steps = self.chat_steps_var.get()
        cfg = self.chat_cfg_var.get()
        
        # 图生图强度
        strength = 0.45 if is_image else None
        
        return {
            "width": width,
            "height": height,
            "steps": steps,
            "cfg": cfg,
            "strength": strength,
            "num_images": 1
        }
    
    # ==================== 文生图处理 ====================
    
    def _handle_text_to_image(self, intent: dict):
        """处理文生图"""
        # ✅ 检查并自动加载模型
        if self._is_loading_model:
            self._append_message("assistant", "⏳ 模型正在加载中，请稍候...")
            return
        
        if not self.app.model_manager.is_sd_loaded:
            self._append_message("assistant", "📦 正在自动加载模型...")
            # ✅ 缓存意图，加载完成后自动重试
            self._pending_intent = intent            
            if not self._ensure_model_loaded():
                return
            # 等待加载完成
            self._append_message("assistant", "⏳ 模型加载中，请稍候再试...")
            return
        
        prompt = intent["prompt"]
        params = self._estimate_params(prompt)
        
        # ✅ 显示当前参数
        self._append_message(
            "system", 
            f"⚙️ 参数: 步数={params['steps']}, CFG={params['cfg']}, 尺寸={params['width']}x{params['height']}"
        )    
        
        self._append_message("assistant", f"🎨 正在生成图片...\n\n📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        
        # 估算参数

        self._update_status(f"🎨 生成中... (尺寸: {params['width']}x{params['height']})", 0.1)
        
        # 检查模型
        if not self.app.model_manager.is_sd_loaded:
            self._append_message("assistant", "❌ 请先在主界面加载 SD 模型")
            return
        
        # 执行生成
        try:
            from utils.pipeline_pool import pipeline_pool
            from datetime import datetime
            import random
            
            # 获取模型
            model_name = self.app.model_var.get()
            model_path = self.app._get_model_path(model_name)
            
            # 获取 LoRA
            lora_path = None
            lora_weight = 1.0
            if hasattr(self.app, 'lora_var') and hasattr(self.app, 'lora_paths'):
                lora_display = self.app.lora_var.get()
                if lora_display:
                    lora_path = self.app.lora_paths.get(lora_display)
                    lora_weight = self.app.lora_weight_var.get()
            
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
            
            # 生成
            seed = random.randint(1, 2**32 - 1)
            generator = torch.Generator("cpu").manual_seed(seed)
            
            self._update_status(f"🎨 生成中... 步骤: {params['steps']}", 0.3)
            
            result = pipe(
                prompt=prompt,
                negative_prompt="worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text",
                num_inference_steps=params["steps"],
                guidance_scale=params["cfg"],
                height=params["height"],
                width=params["width"],
                generator=generator,
                num_images_per_prompt=1
            )
            
            # 保存图片
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prompt_preview = "".join(c for c in prompt[:30] if c.isalnum() or c in " _-") or "image"
            filename = f"{timestamp}_chat_{prompt_preview}.png"
            
            from config.app_config import app_config
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            result.images[0].save(filepath)
            
            # 图片后处理
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
            
            # 释放 Pipeline
            pipeline_pool.release_pipeline(model_path, lora_path, task_id)
            
            # 显示结果
            self._append_image_result(filepath)
            self._append_message("assistant", f"✅ 图片已生成！\n📁 {os.path.basename(filepath)}\n\n💡 提示: 继续发送描述可以生成更多图片")
            
            self._update_status("✅ 生成完成", 1.0)
            
            # 添加到预览
            self.app.add_to_preview(filepath, result.images[0])
            # ✅ 清除缓存
            self._pending_intent = None
            
            
        except Exception as e:
            self._append_message("assistant", f"❌ 生成失败: {str(e)}")
            self._update_status("❌ 生成失败", 0)
            import traceback
            traceback.print_exc()
            # ✅ 清除缓存，防止卡住
            self._pending_intent = None            
    
    # ==================== 图生图处理 ====================
    
    def _handle_image_to_image(self, intent: dict):
        """处理图生图"""
        if self.uploaded_image is None:
            self._append_message("assistant", "❌ 请先上传一张图片")
            return
        
        # ✅ 检查并自动加载模型
        if self._is_loading_model:
            self._append_message("assistant", "⏳ 模型正在加载中，请稍候...")
            return
        
        if not self.app.model_manager.is_sd_loaded:
            self._append_message("assistant", "📦 正在自动加载模型...")
            # ✅ 缓存意图，加载完成后自动重试
            self._pending_intent = intent
        
            if not self._ensure_model_loaded():
                return
            self._append_message("assistant", "⏳ 模型加载中，请稍候再试...")
            return
        
        prompt = intent["prompt"]
        keywords = intent.get("keywords", {})  # ✅ 添加这一行
        params = self._estimate_params(prompt, is_image=True)
        
        
        # ===== 分析原图特征 =====
        image_features = self._analyze_image_features(self.uploaded_image_path)
        
        # ===== 根据原图特征调整参数 =====
        if image_features.get("has_face"):
            self._append_message("system", f"👤 检测到人脸 ({image_features.get('face_count', 0)} 张)")
        
        if image_features.get("is_portrait"):
            self._append_message("system", "📐 检测到竖图")
            # 竖图保持竖图
        elif image_features.get("is_landscape"):
            self._append_message("system", "📐 检测到横图")
        
        # ===== 根据原图特征调整强度 =====
        strength = 0.45
        if image_features.get("is_bright"):
            strength = 0.40  # 亮图用低强度保持质感
        elif image_features.get("is_dark"):
            strength = 0.55  # 暗图用高强度改变更多
        
        # 如果有脸部，降低强度保护面部
        if image_features.get("has_face"):
            strength = min(strength, 0.45)
            self._append_message("system", f"🛡️ 检测到面部，降低强度保护面部: {strength:.2f}")
        
        params = self._estimate_params(prompt, is_image=True)
        params["strength"] = strength
    
        # ✅ 显示当前参数
        self._append_message(
            "system", 
            f"⚙️ 参数: 步数={params['steps']}, CFG={params['cfg']}, 强度={params['strength']}"
        )

        # ===== 构建优化的图生图提示词 =====
        # 保留原图核心特征
        if not keywords.get("clothes") and not keywords.get("colors"):
            # 用户没有指定换装或换色，强调保留原图
            prompt = f"same person, same face, same expression, {prompt}"
        
        self._append_message("assistant", f"🔄 正在修改图片...\n\n📝 指令: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        
        # 估算参数

        self._update_status(f"🔄 修改中... (强度: {params['strength']})", 0.1)
        
        # 检查模型
        if not self.app.model_manager.is_sd_loaded:
            self._append_message("assistant", "❌ 请先在主界面加载 SD 模型")
            return
        
        try:
            from utils.pipeline_pool import pipeline_pool
            from datetime import datetime
            import random
            
            model_name = self.app.model_var.get()
            model_path = self.app._get_model_path(model_name)
            
            lora_path = None
            lora_weight = 1.0
            if hasattr(self.app, 'lora_var') and hasattr(self.app, 'lora_paths'):
                lora_display = self.app.lora_var.get()
                if lora_display:
                    lora_path = self.app.lora_paths.get(lora_display)
                    lora_weight = self.app.lora_weight_var.get()
            
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
            
            # 准备图片
            init_image = self.uploaded_image.copy().convert('RGB')
            w, h = init_image.size
            
            # 对齐尺寸
            new_w = ((w + 31) // 64) * 64
            new_h = ((h + 31) // 64) * 64
            if new_w != w or new_h != h:
                init_image = init_image.resize((new_w, new_h))
            
            # 限制最大尺寸
            max_size = 1024
            if max(new_w, new_h) > max_size:
                scale = max_size / max(new_w, new_h)
                new_w = int(new_w * scale)
                new_h = int(new_h * scale)
                new_w = ((new_w + 31) // 64) * 64
                new_h = ((new_h + 31) // 64) * 64
                init_image = init_image.resize((new_w, new_h))
            
            self._update_status(f"🔄 修改中... 尺寸: {new_w}x{new_h}", 0.3)
            
            # 生成
            seed = random.randint(1, 2**32 - 1)
            generator = torch.Generator("cpu").manual_seed(seed)
            
            result = pipe(
                prompt=prompt,
                negative_prompt="worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text",
                image=init_image,
                strength=params["strength"],
                num_inference_steps=params["steps"],
                guidance_scale=params["cfg"],
                generator=generator,
                num_images_per_prompt=1
            )
            
            # 保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prompt_preview = "".join(c for c in prompt[:30] if c.isalnum() or c in " _-") or "edit"
            filename = f"{timestamp}_chat_edit_{prompt_preview}.png"
            
            from config.app_config import app_config
            output_dir = app_config.paths.output_dir
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            result.images[0].save(filepath)
            
            # 释放 Pipeline
            pipeline_pool.release_pipeline(model_path, lora_path, task_id)
            
            # 显示结果
            self._append_image_result(filepath)
            self._append_message("assistant", f"✅ 图片已修改完成！\n📁 {os.path.basename(filepath)}")
            
            self._update_status("✅ 修改完成", 1.0)
            
            # 添加到预览
            self.app.add_to_preview(filepath, result.images[0])
            # ✅ 清除缓存
            self._pending_intent = None            
            
            # 清空上传的图片（可选）
            # self._clear_upload()
            
        except Exception as e:
            self._append_message("assistant", f"❌ 修改失败: {str(e)}")
            self._update_status("❌ 修改失败", 0)
            import traceback
            traceback.print_exc()
            # ✅ 清除缓存，防止卡住
            self._pending_intent = None            

    # 在 _init_vars 后添加以下方法

    def _extract_keywords(self, text: str) -> dict:
        """提取关键词"""
        text_lower = text.lower()
        
        # 性别
        genders = []
        if any(k in text_lower for k in ['女', '美女', '女孩', '女性', '姑娘', '小姐姐']):
            genders.append("1girl")
        elif any(k in text_lower for k in ['男', '帅哥', '男孩', '男性', '小哥哥']):
            genders.append("1boy")
        elif any(k in text_lower for k in ['情侣', '双人', '两人', '夫妻', 'couple']):
            genders.append("1girl, 1boy")
        
        # 服装
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
        }
        clothes = []
        for cn, en in clothes_map.items():
            if cn in text_lower:
                clothes.append(en)
        
        # 颜色
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
        }
        colors = []
        for cn, en in colors_map.items():
            if cn in text_lower:
                colors.append(en)
        
        # 场景
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
        }
        scenes = []
        for cn, en in scenes_map.items():
            if cn in text_lower:
                scenes.append(en)
        
        # 风格
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
        }
        styles = []
        for cn, en in styles_map.items():
            if cn in text_lower:
                styles.append(en)
        
        # 姿势
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
        }
        poses = []
        for cn, en in poses_map.items():
            if cn in text_lower:
                poses.append(en)
        
        # 表情
        expressions_map = {
            '微笑': 'smiling',
            '大笑': 'laughing',
            '严肃': 'serious',
            '忧郁': 'melancholy',
            '诱惑': 'seductive',
            '性感': 'seductive',
            '可爱': 'cute expression',
            '害羞': 'shy',
            '惊讶': 'surprised',
            '愤怒': 'angry',
            '悲伤': 'sad',
            '深情': 'affectionate',
        }
        expressions = []
        for cn, en in expressions_map.items():
            if cn in text_lower:
                expressions.append(en)
        
        # 身体特征
        body_map = {
            '大胸': 'large breasts',
            '巨乳': 'huge breasts',
            '丰满': 'curvy figure',
            '苗条': 'slim figure',
            '匀称': 'fit body',
            '肌肉': 'muscular',
        }
        body = []
        for cn, en in body_map.items():
            if cn in text_lower:
                body.append(en)
        
        # 光线
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
        }
        lighting = []
        for cn, en in lighting_map.items():
            if cn in text_lower:
                lighting.append(en)
        
        return {
            "genders": genders,
            "clothes": clothes,
            "colors": colors,
            "scenes": scenes,
            "styles": styles,
            "poses": poses,
            "expressions": expressions,
            "body": body,
            "lighting": lighting,
            "has_clothes": len(clothes) > 0,
            "has_scene": len(scenes) > 0,
        }


    def _build_smart_prompt(self, text: str, keywords: dict) -> str:
        """根据关键词构建提示词"""
        # 质量词
        prompt_parts = ["masterpiece", "best quality", "photorealistic", "8k", "highly detailed"]
        
        # 性别
        if keywords.get("genders"):
            prompt_parts.extend(keywords["genders"])
        
        # 身体特征
        if keywords.get("body"):
            prompt_parts.extend(keywords["body"])
        
        # 颜色
        if keywords.get("colors"):
            prompt_parts.append(" ".join(keywords["colors"]))
        
        # 服装
        if keywords.get("clothes"):
            prompt_parts.append("wearing " + ", ".join(keywords["clothes"]))
        
        # 表情
        if keywords.get("expressions"):
            prompt_parts.extend(keywords["expressions"])
        
        # 姿势
        if keywords.get("poses"):
            prompt_parts.extend(keywords["poses"])
        
        # 场景
        if keywords.get("scenes"):
            prompt_parts.extend(keywords["scenes"])
        
        # 光线
        if keywords.get("lighting"):
            prompt_parts.extend(keywords["lighting"])
        
        # 风格（加到最前面，紧接质量词）
        if keywords.get("styles"):
            prompt_parts.insert(2, ", ".join(keywords["styles"]))
        
        # 去重
        seen = set()
        unique_parts = []
        for p in prompt_parts:
            if p not in seen:
                seen.add(p)
                unique_parts.append(p)
        
        return ", ".join(unique_parts)

    def _analyze_image_features(self, image_path: str) -> dict:
        """分析图片特征"""
        try:
            import cv2
            import numpy as np
            
            img = cv2.imread(image_path)
            if img is None:
                return {}
            
            h, w = img.shape[:2]
            
            # 检测人脸
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            # 检测人体（简化：通过轮廓）
            has_person = len(faces) > 0
            
            # 判断横竖图
            is_landscape = w > h * 1.2
            is_portrait = h > w * 1.2
            
            # 检测亮度
            brightness = np.mean(gray)
            is_bright = brightness > 150
            is_dark = brightness < 80
            
            return {
                "has_face": len(faces) > 0,
                "has_person": has_person,
                "face_count": len(faces),
                "width": w,
                "height": h,
                "is_landscape": is_landscape,
                "is_portrait": is_portrait,
                "is_bright": is_bright,
                "is_dark": is_dark,
                "aspect_ratio": w / h
            }
        except Exception as e:
            print(f"⚠️ 分析图片失败: {e}")
            return {}
        

    # ==================== 对话处理 ====================
    
    def _handle_chat(self, intent: dict):
        """处理对话"""
        text = intent["original_text"]
        
        # 简单规则对话
        text_lower = text.lower()
        
        # 检查是否有上传图片但用户没有明确说要修改
        if self.uploaded_image is not None:
            if any(k in text_lower for k in ['这是什么', '这是什么图片', '描述']):
                self._append_message("assistant", "📷 我检测到你有上传图片。如果你想修改它，请说：\n• \"把这张图改成...\"\n• \"换成...风格\"\n• \"去除...\"\n\n或者直接描述你想要的效果。")
                return
        
        # 简单问答
        responses = {
            '你好': '你好！有什么可以帮你的吗？',
            '你是谁': '我是智能生图助手，可以帮助你生成和修改图片。试试说 "生成一张..."！',
            '功能': '我可以：\n• 📝 文生图 - 输入描述生成图片\n• 🖼️ 图生图 - 上传图片并修改\n• 💬 自由对话 - 回答你的问题',
            '帮助': '💡 使用提示：\n• 说 "生成一张..." 来文生图\n• 先上传图片，再说 "改成..." 来图生图\n• 直接聊天也可以',
            '谢谢': '不客气！还有需要帮忙的吗？',
            '再见': '再见！随时回来找我生成图片 😊'
        }
        
        # 匹配关键词
        reply = None
        for key, value in responses.items():
            if key in text_lower:
                reply = value
                break
        
        if reply:
            self._append_message("assistant", reply)
        else:
            self._append_message("assistant", f"🤔 我理解你想说：\"{text}\"\n\n如果你想生成图片，可以试试说：\n• \"生成一张...\" (文生图)\n• 先上传图片，然后说 \"改成...\" (图生图)\n\n或者直接告诉我你的需求！")
            
    def _ensure_model_loaded(self) -> bool:
        """确保模型已加载，如果没有则自动加载"""
        if self.app.model_manager.is_sd_loaded:
            return True
        
        # 自动加载
        self._append_message("system", "📦 检测到模型未加载，正在自动加载...")
        self._update_status("📦 正在加载模型...")
        
        # 获取第一个可用模型
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
        
        # 检查是否已加载 Janus（需要先卸载）
        if self.app.model_manager.is_janus_loaded:
            self._append_message("system", "🔄 正在切换 Janus → SD...")
        
        # 同步标记正在加载，防止重复
        self._is_loading_model = True
        
        def load_thread():
            def progress_cb(value, msg):
                self.app.root.after(0, lambda: self._update_status(f"🔄 {msg}", value))
            
            success = self.app.model_manager.load_sd(model_path, model_name, progress_cb)
            self.app.root.after(0, lambda: self._on_model_loaded(success, model_name))
        
        threading.Thread(target=load_thread, daemon=True).start()
        return True

    def _on_model_loaded(self, success: bool, model_name: str):
        """模型加载完成回调"""
        self._is_loading_model = False
        
        if success:
            self._append_message("system", f"✅ 模型加载完成: {model_name[:40]}...")
            self._update_status("✅ 模型就绪", 1.0)
            self.progress_bar.config(value=0)
            
            # ✅ 如果有缓存的意图，自动执行
            if self._pending_intent is not None:
                intent = self._pending_intent
                self._pending_intent = None
                self._append_message("system", "🔄 继续执行之前的请求...")
                
                # 重新执行
                if intent["type"] == "text_to_image":
                    self._handle_text_to_image(intent)
                elif intent["type"] == "image_to_image":
                    self._handle_image_to_image(intent)
            else:
                self._append_message("assistant", "✅ 模型已就绪，可以开始生图了！")
        else:
            self._append_message("assistant", "❌ 模型加载失败\n\n请在主界面手动加载模型后重试。")
            self._update_status("❌ 加载失败", 0)
            self._pending_intent = None  # 清除缓存
            
    def _clear_upload(self):
        """清除上传的图片"""
        self.uploaded_image = None
        self.uploaded_image_path = None
        self.image_status.config(text="")
        self.preview_label.config(image="")
        self.preview_label.image = None
    
    def get_frame(self):
        return self.frame