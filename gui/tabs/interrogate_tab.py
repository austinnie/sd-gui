#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片反推标签页 - 直接集成反推功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import os
import threading
import subprocess
import sys
from datetime import datetime

from .base_tab import BaseTab

# ✅ 抑制 transformers 和 huggingface 的警告日志
import logging
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    
# ===== 全局缓存 =====
_classifiers = {}
_cli_interrogator = None
_blip_processor = None
_blip_model = None
_qwen_model = None      # ✅ 新增
_qwen_processor = None  # ✅ 新增

def get_classifier(model_name):
    """获取图像分类器（单例，支持多模型）"""
    global _classifiers
    
    if model_name not in _classifiers:
        print(f"   📦 加载图像分类模型: {model_name}...")
        from transformers import pipeline
        import time
        
        model_paths = {
            "ViT-Base (快速)": "google/vit-base-patch16-224",
            "ViT-Large (准确)": "google/vit-large-patch16-224",
            "CLIP-B-32 (推荐)": "laion/CLIP-ViT-B-32-laion2B-s34B-b79K",
        }
        actual_model = model_paths.get(model_name, "google/vit-base-patch16-224")
        
        # ✅ 使用环境变量禁用进度条，减少干扰
        import os
        os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '0'  # 保留进度条，但等待完成
        
        start_time = time.time()
        _classifiers[model_name] = pipeline(
            "image-classification",
            model=actual_model,
            device=-1,
            use_fast=True
        )
        
        # ✅ 等待模型完全加载（pipeline 返回时已加载完成）
        elapsed = time.time() - start_time
        print(f"   ✅ 模型加载完成: {model_name} (耗时: {elapsed:.1f}秒)")
    return _classifiers[model_name]


def get_cli_interrogator():
    """获取 CLIP Interrogator（单例）"""
    global _cli_interrogator
    if _cli_interrogator is None:
        try:
            from clip_interrogator import Config, Interrogator
            print("   📦 加载 CLIP 模型（缓存）...")
            print("   ⚠️ 首次加载约 3-5GB，请耐心等待...")
            config = Config()
            config.clip_model_name = "ViT-L-14/openai"
            config.device = "cpu"
            _cli_interrogator = Interrogator(config)
            print("   ✅ CLIP 模型加载完成")
        except ImportError:
            print("   ❌ clip-interrogator 未安装")
            return None
    return _cli_interrogator

def get_blip_captioner():
    """获取 BLIP 模型（单例）"""
    global _blip_processor, _blip_model
    if _blip_processor is None:
        print("   📦 加载 BLIP 模型...")
        from transformers import BlipProcessor, BlipForConditionalGeneration
        _blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        _blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        print("   ✅ BLIP 模型加载完成")
    return _blip_processor, _blip_model

def get_qwen_model():
    """获取 Qwen-VL 模型（单例）- 使用 Qwen2-VL"""
    global _qwen_model, _qwen_processor
    if _qwen_model is not None:
        print("   📦 使用已加载的 Qwen2-VL 模型（缓存）")
        return _qwen_model, _qwen_processor
    
    try:
        import torch
        from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
        print("   📦 首次加载 Qwen2-VL 模型...")
        print("   ⚠️ 约 8-10GB，请耐心等待...")
        
        model_name = "Qwen/Qwen2-VL-2B-Instruct"
        
        _qwen_processor = AutoProcessor.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        _qwen_model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_name,
            device_map="cpu",
            torch_dtype=torch.float16
        )
        print("   ✅ Qwen2-VL 模型加载完成")
    except Exception as e:
        print(f"   ❌ Qwen-VL 加载失败: {e}")
        return None, None
    return _qwen_model, _qwen_processor
    

class InterrogateTab(BaseTab):
    """图片反推标签页"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.interrogate_image_path = None
        self._init_vars()
        self.setup_ui()
    
    def _init_vars(self):
        self.path_var = tk.StringVar(value="")
        self.backend_var = tk.StringVar(value="tag")
        self.mode_var = tk.StringVar(value="fast")
        self.thresh_var = tk.DoubleVar(value=0.02)
        self.tag_model_var = tk.StringVar(value="ViT-Large (准确)")  # 默认用最好的
        self.blip_model_var = tk.StringVar(value="BLIP-large (详细)")  # ✅ 新增 BLIP 模型
        self.clip_model_var = tk.StringVar(value="ViT-L-14/openai")    # ✅ 新增 CLIP 模型
        self.cancel_interrogate = False  # ✅ 取消标志
        self.is_interrogating = False  # ✅ 添加运行标志
        

    def setup_ui(self):
        frame = self.frame
        row = 0
        
        ttk.Label(frame, text="上传图片:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.path_label = ttk.Label(frame, textvariable=self.path_var, 
                                    foreground="gray", background="white", relief="sunken")
        self.path_label.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Button(frame, text="浏览", command=self._select_image).grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        param_frame = ttk.Frame(frame)
        param_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # 后端选择
        ttk.Label(param_frame, text="后端:").pack(side=tk.LEFT, padx=5)
        self.backend_combo = ttk.Combobox(
            param_frame, 
            textvariable=self.backend_var, 
            values=["tag", "clip", "blip", "combined","qwen-v2"], 
            width=8
        )
        self.backend_combo.pack(side=tk.LEFT, padx=5)
        self.backend_combo.bind('<<ComboboxSelected>>', self._on_backend_changed)
        
        # ✅ 模型选择（通用，用于 tag 和 blip）
        self.model_label = ttk.Label(param_frame, text="模型:")
        self.model_combo = ttk.Combobox(
            param_frame,
            textvariable=self.tag_model_var,
            width=15
        )
        
        # ✅ BLIP 模型选择（仅 combined 模式显示）
        self.blip_model_label = ttk.Label(param_frame, text="BLIP:")
        self.blip_model_combo = ttk.Combobox(
            param_frame,
            textvariable=self.blip_model_var,
            values=["BLIP-base (快速)", "BLIP-large (详细)"],
            width=15
        )
        
        # ✅ CLIP 模型选择（仅 combined 模式显示）
        self.clip_model_label = ttk.Label(param_frame, text="CLIP:")
        self.clip_model_combo = ttk.Combobox(
            param_frame,
            textvariable=self.clip_model_var,
            values=["ViT-L-14/openai"],
            width=15
        )
        
        # 模式选择（CLIP 专用）
        ttk.Label(param_frame, text="模式:").pack(side=tk.LEFT, padx=5)
        self.mode_combo = ttk.Combobox(
            param_frame, 
            textvariable=self.mode_var, 
            values=["fast", "classic", "best"], 
            width=6
        )
        self.mode_combo.pack(side=tk.LEFT, padx=5)
        
        # 阈值（TAG 专用）
        ttk.Label(param_frame, text="阈值:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(param_frame, from_=0.01, to=0.9, textvariable=self.thresh_var, width=4, increment=0.01).pack(side=tk.LEFT, padx=5)
        
        self.interrogate_btn = ttk.Button(param_frame, text="🔍 开始反推", command=self.start_interrogate)
        self.interrogate_btn.pack(side=tk.LEFT, padx=10)
        
        # ✅ 添加取消按钮
        self.cancel_interrogate_btn = ttk.Button(param_frame, text="⏹️ 取消", command=self.cancel_interrogation, state=tk.DISABLED)
        self.cancel_interrogate_btn.pack(side=tk.LEFT, padx=5)

        row += 1
        
        self._update_ui_state()
        
        ttk.Label(frame, text="反推结果:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.result_text = tk.Text(frame, height=8, width=70)
        self.result_text.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        action_frame = ttk.Frame(frame)
        action_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Button(action_frame, text="📋 复制到文生图", command=self._copy_to_txt2img).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📋 复制到图生图", command=self._copy_to_img2img).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📋 复制到图生图(推荐)", command=self._copy_to_img2img_recommended).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="💾 保存到文件", command=self._save_result).pack(side=tk.LEFT, padx=5)
        

    def cancel_interrogation(self):
        """取消反推 - 只释放 UI，后台继续运行"""
        self.cancel_interrogate = True
        self.update_status("⏹️ 正在取消...（后台继续处理）")
        self.cancel_interrogate_btn.config(state=tk.DISABLED)
        # ✅ 立即恢复 UI，让用户可以继续操作
        self._reset_ui_state()
        print(f"   ℹ️ 取消信号已发送，后台继续运行")
    
    def _on_backend_changed(self, event):
        """后端切换时更新 UI"""
        self._update_ui_state()


    def _update_ui_state(self):
        """更新 UI 状态"""
        backend = self.backend_var.get()
        
        # ✅ 先清除所有动态控件
        for widget in [self.model_label, self.model_combo, 
                       self.blip_model_label, self.blip_model_combo,
                       self.clip_model_label, self.clip_model_combo,
                       self.mode_combo]:
            try:
                widget.pack_forget()
            except:
                pass
        
        if backend == "tag":
            self.model_label.pack(side=tk.LEFT, padx=5)
            self.model_combo.pack(side=tk.LEFT, padx=5)
            self.model_combo['values'] = ["ViT-Base (快速)", "ViT-Large (准确)", "CLIP-B-32 (推荐)"]
            self.model_combo.set(self.tag_model_var.get())
            
        elif backend == "clip":
            self.model_label.pack(side=tk.LEFT, padx=5)
            self.model_combo.pack(side=tk.LEFT, padx=5)
            self.model_combo['values'] = ["ViT-L-14/openai"]
            self.model_combo.set("ViT-L-14/openai")
            self.mode_combo.pack(side=tk.LEFT, padx=5)
            
        elif backend == "combined":
            self.blip_model_label.pack(side=tk.LEFT, padx=5)
            self.blip_model_combo.pack(side=tk.LEFT, padx=5)
            self.clip_model_label.pack(side=tk.LEFT, padx=5)
            self.clip_model_combo.pack(side=tk.LEFT, padx=5)
            self.mode_combo.pack(side=tk.LEFT, padx=5)
            
        elif backend == "qwen-vl":
            # ✅ Qwen-VL：不显示任何额外控件
            pass
            
        elif backend == "blip":
            self.model_label.pack(side=tk.LEFT, padx=5)
            self.model_combo.pack(side=tk.LEFT, padx=5)
            self.model_combo['values'] = ["BLIP-base (快速)", "BLIP-large (详细)"]
            self.model_combo.set(self.tag_model_var.get())
        
        # 阈值：仅 TAG 显示
        if hasattr(self, 'thresh_spinbox'):
            if backend != "tag":
                pass

  
    def _select_image(self):
        """选择图片"""
        file = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif"), ("所有文件", "*.*")]
        )
        if file:
            self.interrogate_image_path = file
            self.path_var.set(os.path.basename(file))

        # ===== 【新增】显示预览 =====
        self._show_preview(file)
            

    def _show_preview(self, filepath):
        """显示图片预览"""
        try:
            from PIL import Image, ImageTk
            
            # 打开并缩放图片
            img = Image.open(filepath)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # 创建或获取预览标签
            if not hasattr(self, 'preview_label'):
                # 在路径标签下面创建预览标签
                preview_frame = ttk.Frame(self.frame)
                preview_frame.grid(row=1, column=0, columnspan=3, pady=5, padx=5)
                self.preview_label = ttk.Label(preview_frame)
                self.preview_label.pack()
                
                # 调整后续行的 row 索引
                # 注意：需要调整下面所有 grid 的 row 值 +1
            
            self.preview_label.config(image=photo)
            self.preview_label.image = photo  # 保持引用
            
        except Exception as e:
            print(f"⚠️ 预览失败: {e}")
        
    def _interrogate_blip_for_img2img(self, image_path):
        """BLIP 专门用于图生图 - 生成客观描述"""
        print(f"🔍 使用 BLIP 图生图模式...")
        
        if self.cancel_interrogate:
            return "已取消"
        
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
        except ImportError:
            return "BLIP 未安装"
        
        image = Image.open(image_path).convert('RGB')
        original_size = image.size

        # ✅ 对齐到 64 的倍数
        w, h = image.size
        new_w = ((w + 31) // 64) * 64
        new_h = ((h + 31) // 64) * 64
        if new_w != w or new_h != h:
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            print(f"   📐 图片尺寸对齐: {w}x{h} -> {new_w}x{new_h}")
        
        if max(image.size) > 512:
            image.thumbnail((512, 512))
            print(f"   📐 图片已压缩: {original_size} -> {image.size}")
        
        print("   📦 加载 BLIP-large 模型...")
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
        print("   ✅ BLIP-large 模型加载完成")
        
        if self.cancel_interrogate:
            return "已取消"
        
        print("   🎨 正在生成描述...")
        inputs = processor(image, return_tensors="pt")
        out = model.generate(
            **inputs, 
            max_length=60,
            num_beams=4,
            repetition_penalty=1.1,
        )
        caption = processor.decode(out[0], skip_special_tokens=True)
        
        # ✅ 清理结果，移除艺术风格标签
        caption = caption.replace('arafed', '').replace('trending on', '').strip()
        
        print(f"   ✅ 描述完成: {caption}")
        return caption
        


    def _interrogate_qwen(self, image_path):
        """使用 Qwen-VL 生成详细描述 - 使用 Qwen2-VL"""
        print(f"🔍 使用 Qwen-VL 详细描述模式...")
        
        if self.cancel_interrogate:
            return "已取消"
        
        import torch
        
        model, processor = get_qwen_model()
        if model is None:
            return "Qwen-VL 模型加载失败"
        
        image = Image.open(image_path).convert('RGB')
        original_size = image.size
        
        # ✅ 保持原图尺寸，不要缩太小
        if max(image.size) > 1024:
            image.thumbnail((1024, 1024))
            print(f"   📐 图片已压缩: {original_size} -> {image.size}")
        else:
            print(f"   📐 图片尺寸: {image.size}")
        
        if self.cancel_interrogate:
            return "已取消"
        
        print("   🎨 正在生成详细描述...")
        
        # ✅ Qwen2-VL 对话格式
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": "请详细描述这张图片中的人物，包括：性别、年龄、发型、发色、脸型、五官特征、服装、表情、背景、光线、氛围。用中文回答。"}
                ]
            }
        ]
        
        # ✅ 使用 processor 处理
        inputs = processor(
            text=processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True),
            images=image,
            return_tensors="pt"
        )
        
        # ✅ 生成
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=300,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
            )
        
        result = processor.decode(outputs[0], skip_special_tokens=True)
        
        # ✅ 清理结果
        if "assistant" in result.lower():
            parts = result.lower().split("assistant")
            result = parts[-1].strip()
            if result.startswith(":"):
                result = result[1:].strip()
        
        print(f"   ✅ 描述完成: {result[:100]}...")
        return result
    
    
    def start_interrogate(self):
        if not self.interrogate_image_path:
            messagebox.showwarning("提示", "请先选择图片")
            return

        # ✅ 强制重置状态（允许取消后立即开始）
        if self.is_interrogating and self.cancel_interrogate:
            # 取消状态，允许强制重新开始
            self.is_interrogating = False
            print(f"   ℹ️ 重置取消状态，允许新反推")
        
        if self.is_interrogating:
            messagebox.showwarning("提示", "反推正在进行中，请等待完成")
            return
        
        self.cancel_interrogate = False
        self.is_interrogating = True
        
        self.interrogate_btn.config(state=tk.DISABLED)
        self.cancel_interrogate_btn.config(state=tk.NORMAL)
        self.update_status("🔍 正在分析图片，请稍候...")
        threading.Thread(target=self._run_interrogate, daemon=True).start()
        
    def _run_interrogate(self):
        try:
            backend = self.backend_var.get()
            model = self.tag_model_var.get()
            blip_model = self.blip_model_var.get()  # ✅ 获取 BLIP 模型
            clip_model = self.clip_model_var.get()  # ✅ 获取 CLIP 模型
            
            # ✅ 打印配置到命令行
            print(f"\n{'='*60}")
            print(f"📋 反推配置")
            print(f"   后端: {backend.upper()}")
            
            if backend == "tag":
                print(f"   模型: {model}")
            elif backend == "clip":
                print(f"   模型: {clip_model}")
                print(f"   模式: {self.mode_var.get()}")
            elif backend == "combined":
                print(f"   BLIP 模型: {blip_model}")
                print(f"   CLIP 模型: {clip_model}")
                print(f"   CLIP 模式: {self.mode_var.get()}")
            elif backend == "qwen-vl":  # ✅ 新增 qwen-vl 分支
                print(f"   模型: Qwen2-VL (8-10GB)")
            elif backend == "blip":
                print(f"   模型: {model}")
            else:
                print(f"   模型: {model}")
            print(f"{'='*60}\n")
            
            if backend == "tag":
                result = self._interrogate_tag(
                    self.interrogate_image_path,
                    self.thresh_var.get(),
                    model
                )
            elif backend == "clip":
                result = self._interrogate_clip(
                    self.interrogate_image_path,
                    self.mode_var.get(),
                    clip_model
                )
            elif backend == "combined":
                result = self._interrogate_combined(
                    self.interrogate_image_path,
                    blip_model,
                    clip_model,
                    self.mode_var.get()
                )

            elif backend == "qwen-v2":  # ✅ 新增
                result = self._interrogate_qwen(
                    self.interrogate_image_path
                )
            
            else:  # blip
                result = self._interrogate_blip(
                    self.interrogate_image_path,
                    model
                )

            # ✅ 打印结果到命令行
            print(f"\n📝 反推结果:")
            print(f"{result}")
            print(f"{'='*60}\n")

            # ✅ 检查是否被取消，如果是则不更新 UI
            if self.cancel_interrogate:
                print(f"   ℹ️ 反推已完成但被取消，不更新 UI")
                return
            
            def update_ui():
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", result)
                self.update_status("✅ 反推完成")
                self._reset_ui_state()
            
            self.app.root.after(0, update_ui)
            
        except ImportError as e:
            self._show_error(f"缺少依赖: {e}\n请运行: pip install transformers torch Pillow")
        except Exception as e:
            self._show_error(f"出错: {e}")
        finally:
            # ✅ 确保标志被重置
            self.is_interrogating = False
            # ✅ 如果被取消，确保 UI 已恢复
            if self.cancel_interrogate:
                self.app.root.after(0, self._reset_ui_state)
            
    def _reset_ui_state(self):
        """重置 UI 状态"""
        self.is_interrogating = False
        self.interrogate_btn.config(state=tk.NORMAL)
        self.cancel_interrogate_btn.config(state=tk.DISABLED)
    

    def _interrogate_tag(self, image_path, threshold=0.02, model_name="ViT-Large (准确)"):
        """使用图像分类模型 - 带缓存，支持模型选择"""
        print(f"🔍 使用 TAG 快速标签模式 (模型: {model_name}, 阈值: {threshold})...")

        # ✅ 检查取消
        if self.cancel_interrogate:
            return "已取消"
        
        image = Image.open(image_path).convert('RGB')
        original_size = image.size
        if max(image.size) > 448:
            image.thumbnail((448, 448))
            print(f"   📐 图片已压缩: {original_size} -> {image.size}")
        
        # ✅ 加载模型（会等待完成）
        classifier = get_classifier(model_name)
        
        # ✅ 方案4：添加短暂等待，确保模型就绪
        import time
        time.sleep(0.3)
        
        print("   🎨 正在识别标签...")
        results = classifier(image)

        # ✅ 检查取消
        if self.cancel_interrogate:
            return "已取消"
        
        tags = []
        for r in results:
            if r['score'] > threshold:
                label = r['label'].replace('_', ' ')
                # ✅ 跳过数字标签
                if not label.isdigit():
                    tags.append(label)
        
        tags = tags[:20]
        
        if not tags:
            tags = ["photo", "high quality"]
            print(f"   ⚠️ 无有效标签，返回默认词")
        
        if len(tags) < 3:
            tags.append("photo")
            tags.append("high quality")
        
        result = ", ".join(tags)
        print(f"   ✅ 识别完成: {result}")
        return result
        
    def _interrogate_clip(self, image_path, mode="fast", model="ViT-L-14/openai"):
        """使用 CLIP Interrogator - 带缓存，支持三种模式"""
        print(f"🔍 使用 CLIP 详细模式 (模型: {model}, 模式: {mode})...")
        
        # ✅ 直接使用全局缓存
        global _cli_interrogator
        if _cli_interrogator is None:
            try:
                from clip_interrogator import Config, Interrogator
                print("   📦 首次加载 CLIP 模型...")
                config = Config()
                config.clip_model_name = "ViT-L-14/openai"
                config.device = "cpu"
                _cli_interrogator = Interrogator(config)
                print("   ✅ CLIP 模型加载完成")
            except ImportError:
                return "CLIP Interrogator 未安装"
        ci = _cli_interrogator
        
        print(f"   📦 使用已加载的 CLIP 模型")
        
        image = Image.open(image_path).convert('RGB')
        original_size = image.size
        if max(image.size) > 512:
            image.thumbnail((512, 512))
            print(f"   📐 图片已压缩: {original_size} -> {image.size}")
        
        print("   🎨 正在分析图片内容...")
        print(f"   📌 模式: {mode}")
        
        if mode == "best":
            result = ci.interrogate(image)
        elif mode == "fast":
            result = ci.interrogate_fast(image)
        else:  # classic
            result = ci.interrogate_classic(image)
        
        import re
        result = result.replace('"', '').replace('"', '')
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result


    def _interrogate_blip(self, image_path, model="BLIP-base (快速)"):
        """使用 BLIP 生成自然语言描述"""
        print(f"🔍 使用 BLIP 自然语言描述模式 (模型: {model})...")
        
        if self.cancel_interrogate:
            return "已取消"
        
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            # ✅ 抑制 transformers 的警告日志
            import logging
            logging.getLogger("transformers").setLevel(logging.ERROR)
        except ImportError:
            return "BLIP 未安装，请运行: pip install transformers"
        
        image = Image.open(image_path).convert('RGB')
        original_size = image.size
        if max(image.size) > 512:
            image.thumbnail((512, 512))
            print(f"   📐 图片已压缩: {original_size} -> {image.size}")
        
        # ✅ 根据选择的模型加载不同版本
        if "large" in model.lower():
            print("   📦 加载 BLIP-large 模型...")
            processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
            model_blip = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
            print("   ✅ BLIP-large 模型加载完成")
        else:
            print("   📦 加载 BLIP-base 模型...")
            processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            model_blip = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            print("   ✅ BLIP-base 模型加载完成")
        
        if self.cancel_interrogate:
            return "已取消"
        
        print("   🎨 正在生成描述...")
        inputs = processor(image, return_tensors="pt")
        
        # ✅ 大模型用更长的描述
        max_len = 80 if "large" in model.lower() else 50
        out = model_blip.generate(
            **inputs, 
            max_length=max_len,
            num_beams=3,
            repetition_penalty=1.1,  # ✅ 减少重复
        )
        caption = processor.decode(out[0], skip_special_tokens=True)
        
        print(f"   ✅ 描述完成: {caption}")
        return caption
            
            
    def _interrogate_combined(self, image_path, blip_model="BLIP-large (详细)", 
                              clip_model="ViT-L-14/openai", clip_mode="fast"):
        """组合反推：BLIP + CLIP，用户可分别选择模型"""
        print(f"🔍 使用组合模式 (BLIP: {blip_model}, CLIP: {clip_model}, 模式: {clip_mode})...")
        
        if self.cancel_interrogate:
            return "已取消"
        
        # ✅ 使用用户选择的 BLIP 模型
        blip_result = self._interrogate_blip(image_path, blip_model)
        
        if self.cancel_interrogate:
            return "已取消"
        
        # ✅ 使用用户选择的 CLIP 模型和模式
        clip_result = self._interrogate_clip(image_path, clip_mode, clip_model)
        
        # ✅ 智能过滤 CLIP 标签
        # 1. 保留描述性标签（特征）
        # 2. 移除名人名称（中文名、英文名）
        # 3. 移除艺术风格标签
        import re
        
        useful_tags = []
        skip_patterns = [
            r'kim\s+\w+', r'jia\s+\w+', r'leslie\s+\w+', r'wenfei\s+\w+', 
            r'pengzhen\s+\w+', r'kwak\s+\w+', r'lei\s+\w+',
            r'arafed', r'trending', r'cg society', r'marble sculpture', 
            r'dau-al-set', r'gongbi', r'kpop', r'idol'
        ]
        skip_words = ['korean idol', 'korean girl', 'female actress', 'korean woman']
        
        for tag in clip_result.split(','):
            tag_clean = tag.strip()
            tag_lower = tag_clean.lower()
            
            # 跳过空标签
            if not tag_clean:
                continue
            
            # 跳过名人名称
            is_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, tag_lower):
                    is_skip = True
                    break
            
            if is_skip:
                continue
            
            # 跳过特定的词
            if any(skip in tag_lower for skip in skip_words):
                continue
            
            # 跳过过长的标签（>25字符）
            if len(tag_clean) > 25:
                continue
            
            # 保留有用的标签
            useful_tags.append(tag_clean)
        
        # ✅ 只取前 3 个最有用的标签
        useful_tags = useful_tags[:3]
        
        # ✅ 组合结果
        if useful_tags:
            combined = f"{blip_result}, {', '.join(useful_tags)}"
        else:
            combined = blip_result
        
        print(f"   ✅ 组合完成: {combined}")
        return combined
    
    def _copy_to_img2img_recommended(self):
        """复制到图生图（推荐模式 - 使用 BLIP 描述）"""
        result = self.result_text.get("1.0", tk.END).strip()
        if result and not result.startswith("❌"):
            # ✅ 只复制描述部分，过滤无用标签
            if "arafed" in result or "trending" in result:
                # 如果是 CLIP 结果，重新用 BLIP 生成
                self.update_status("🔄 用 BLIP 生成更准确的描述...")
                blip_result = self._interrogate_blip_for_img2img(self.interrogate_image_path)
                if hasattr(self.app, 'img2img_tab'):
                    self.app.img2img_tab.set_prompt(blip_result, "")
                    self.update_status("✅ 已复制到图生图（BLIP 描述）")
                return
            
            if hasattr(self.app, 'img2img_tab'):
                self.app.img2img_tab.set_prompt(result, "")
                self.update_status("✅ 已复制到图生图")
            else:
                messagebox.showwarning("提示", "图生图标签页未初始化")
        else:
            messagebox.showwarning("提示", "没有有效的反推结果")
        
    def _show_error(self, message: str):
        def update_ui():
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", f"❌ {message}")
            self.update_status("❌ 反推失败")
            self._reset_ui_state()
        self.app.root.after(0, update_ui)
    
    def _copy_to_txt2img(self):
        """复制到文生图"""
        result = self.result_text.get("1.0", tk.END).strip()
        if result and not result.startswith("❌"):
            if hasattr(self.app, 'txt2img_tab'):
                self.app.txt2img_tab.set_prompt(result, "")
                self.update_status("✅ 已复制到文生图")
            else:
                messagebox.showwarning("提示", "文生图标签页未初始化")
        else:
            messagebox.showwarning("提示", "没有有效的反推结果")
    
    def _copy_to_img2img(self):
        """复制到图生图"""
        result = self.result_text.get("1.0", tk.END).strip()
        if result and not result.startswith("❌"):
            if hasattr(self.app, 'img2img_tab'):
                self.app.img2img_tab.set_prompt(result, "")
                self.update_status("✅ 已复制到图生图")
            else:
                messagebox.showwarning("提示", "图生图标签页未初始化")
        else:
            messagebox.showwarning("提示", "没有有效的反推结果")
    
    def _save_result(self):
        """保存结果到文件"""
        result = self.result_text.get("1.0", tk.END).strip()
        if not result or result.startswith("❌"):
            messagebox.showwarning("提示", "没有有效的反推结果可保存")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="保存反推结果",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=f"interrogate_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(result)
                self.update_status(f"✅ 已保存到: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")