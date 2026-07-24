#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""智能会话标签页 - 精简版"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import re
import random
from datetime import datetime
from PIL import Image, ImageTk
import torch

from .base_tab import BaseTab
from gui.chat.intent_analyzer import IntentAnalyzer
from gui.chat.llm_client import LLMClient
from gui.chat.prompt_builder import PromptBuilder
from gui.chat.context_manager import ContextManager
from gui.chat.lora_manager import LoraManager
from gui.chat.controlnet_manager import ControlNetManager
from gui.chat.ollama_manager import OllamaManager
from gui.chat.handlers import TextToImageHandler, ImageToImageHandler, CoupleHandler, ChatHandler
from gui.chat.ui import ChatUI
from gui.chat.utils import PromptCleaner, ParamEstimator, ImageAnalyzer, SafetyChecker

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


class ChatTab(BaseTab):
    """智能会话标签页 - 精简版"""

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # ===== 初始化模块 =====
        self.intent_analyzer = IntentAnalyzer()
        self.llm_client = LLMClient()
        self.prompt_builder = PromptBuilder()
        self.context_manager = ContextManager()
        
        # ===== 初始化管理器 =====
        self.lora_manager = LoraManager(self)
        self.controlnet_manager = ControlNetManager(self)
        self.ollama_manager = OllamaManager(self)

        # ===== 初始化变量 =====
        self._init_vars()

        # ===== 设置 UI =====
        self.ui = ChatUI(self)
        self.ui.build()

        # ===== 检查 LLM =====
        self.app.root.after(3000, self.ollama_manager.check_status)

        # ===== 绑定处理器 =====
        self.handlers = {
            "text_to_image": TextToImageHandler(self),
            "image_to_image": ImageToImageHandler(self),
            "couple_generation": CoupleHandler(self),
            "chat": ChatHandler(self),
        }

    def _init_vars(self):
        """初始化所有变量"""
        # ===== 状态变量 =====
        self.is_generating = False
        self.cancel_generation = False
        self._is_loading_model = False
        self._pending_intent = None

        # ===== 图片相关 =====
        self.uploaded_images = []
        self.uploaded_image_paths = []
        self.uploaded_image = None
        self.uploaded_image_path = None

        # ===== 参数变量 =====
        self.chat_steps_var = tk.IntVar(value=20)
        self.chat_cfg_var = tk.DoubleVar(value=7.5)
        self.safe_mode_var = tk.BooleanVar(value=True)
        self.llm_enabled_var = tk.BooleanVar(value=True)
        self.quality_mode_var = tk.StringVar(value="快速")

        # ===== LoRA 相关 =====
        self.lora_var = tk.StringVar(value="")
        self.lora_enabled_var = tk.BooleanVar(value=True)

        # ===== ControlNet 相关 =====
        self.use_controlnet_var = tk.BooleanVar(value=False)
        self.controlnet_type_var = tk.StringVar(value="openpose (OpenPose (姿态))")
        self.controlnet_pipe = None

        # ===== 缓存 =====
        self._enhanced_prompt_cache = {}
        self._last_negative = None
        self._image_refs = []
        self._negative_templates = self.prompt_builder.NEGATIVE_TEMPLATES

        # ===== LLM 状态 =====
        self.llm_available = False
        self.llm_installing = False
        self.llm_model = tk.StringVar(value="qwen2.5:1.5b")
        self.llm_model_size = "1GB"

        # ===== 其他 =====
        self.messages = []
        self.chat_context = {}

    # ==================== 消息处理 ====================

    def _process_message(self, user_input: str):
        """处理用户消息"""
        self.is_generating = True
        self.cancel_generation = False

        try:
            # 1. 分析意图
            intent = self.intent_analyzer.analyze(
                user_input,
                has_image=bool(self.uploaded_images),
                has_multiple_images=len(self.uploaded_images) >= 2
            )

            self._append_message("system", f"🔍 分析意图: {intent.type}")

            # 2. LLM 增强
            if self.llm_enabled_var.get() and self.llm_client.is_available():
                intent = self._enhance_with_llm(intent)

            # 3. 路由到对应处理器
            handler = self.handlers.get(intent.type)
            if handler:
                handler.handle(intent)
            else:
                self._append_message("assistant", f"❌ 未支持的意图类型: {intent.type}")

            # 4. 更新上下文
            self.context_manager.update(vars(intent))

        except Exception as e:
            self._append_message("assistant", f"❌ 处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_generating = False

    # ==================== LLM 增强 ====================

    def _build_llm_prompt(self, intent) -> str:
        """构建 LLM 提示词"""
        text = intent.original_text
        is_img2img = intent.type == "image_to_image"
        
        context = self.context_manager.get_summary() if self.context_manager.has_context() else ""
        context_info = f"\n【对话上下文】\n{context}\n" if context else ""
        
        if is_img2img:
            return f"""你是一个专业的 Stable Diffusion 提示词专家。用户想要修改图片：{text}

{context_info}
【图生图特殊规则】
- 必须包含 "same person, same face, same pose" 保持人物一致性
- 只修改用户明确要求的部分
- 不要添加用户未提及的风格词
- 使用英文，用逗号分隔

【输出格式 - 严格遵守】
正面提示词：[用英文写出一段完整的提示词，用逗号分隔]
负面提示词：[用英文写出一段完整的负面提示词，用逗号分隔]

请直接输出，不要添加额外解释。"""
        else:
            return f"""你是一个专业的 Stable Diffusion 提示词专家。根据用户描述生成详细的英文提示词：{text}

{context_info}
【重要规则】
1. 提示词使用英文，用逗号分隔
2. 包含：主体描述（1girl/1boy）、服装、场景、光线、风格、构图
3. 添加高质量修饰词：masterpiece, best quality, photorealistic, 8k, highly detailed
4. 生成 80-150 个词的详细描述
5. 使用具体、生动的描述词

【输出格式 - 严格遵守】
正面提示词：[用英文写出一段详细的提示词，用逗号分隔，至少80个词]
负面提示词：[用英文写出一段负面提示词，用逗号分隔]

请直接输出，不要添加额外解释。"""

    def _enhance_with_llm(self, intent):
        """使用 LLM 增强提示词"""
        self._append_message("system", "🧠 正在智能分析需求...")
        
        prompt = self._build_llm_prompt(intent)
        response = self.llm_client.generate(prompt, timeout=60, max_tokens=300, stream=True)
        
        if response:
            parsed = self._parse_llm_response_stream(response)
            if parsed and parsed.get("prompt"):
                intent.prompt = parsed["prompt"]
                intent.llm_enhanced = True
                intent.negative = parsed.get("negative", "")
                self._append_message("system", "🧠 LLM 增强完成")
        
        return intent

    def _parse_llm_response_stream(self, response: str) -> dict:
        """解析流式 LLM 响应"""
        result = {"prompt": "", "negative": ""}
        
        if not response:
            return result
        
        lines = response.strip().split('\n')
        current_section = None
        prompt_parts = []
        negative_parts = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if '正面提示词' in line or '正面' in line:
                current_section = 'prompt'
                if '：' in line or ':' in line:
                    sep = '：' if '：' in line else ':'
                    content = line.split(sep, 1)[-1].strip()
                    if content:
                        prompt_parts.append(content)
                continue
            elif '负面提示词' in line or '负面' in line:
                current_section = 'negative'
                if '：' in line or ':' in line:
                    sep = '：' if '：' in line else ':'
                    content = line.split(sep, 1)[-1].strip()
                    if content:
                        negative_parts.append(content)
                continue
            
            if current_section == 'prompt' and line:
                prompt_parts.append(line)
            elif current_section == 'negative' and line:
                negative_parts.append(line)
        
        if prompt_parts:
            result['prompt'] = ', '.join(prompt_parts)
        elif not result['prompt']:
            match = re.search(r'正面提示词[：:]\s*(.+?)(?=负面提示词|$)', response, re.DOTALL)
            if match:
                result['prompt'] = match.group(1).strip()
            else:
                clean = response.strip()
                clean = re.sub(r'(正面|正面提示词)[：:]\s*', '', clean)
                clean = re.sub(r'(负面|负面提示词)[：:]\s*', '', clean)
                if clean:
                    result['prompt'] = clean
        
        if negative_parts:
            result['negative'] = ', '.join(negative_parts)
        else:
            match = re.search(r'负面提示词[：:]\s*(.+?)$', response, re.DOTALL)
            if match:
                result['negative'] = match.group(1).strip()
        
        if not result['negative']:
            result['negative'] = self._negative_templates.get("default", "")
        
        if result['prompt']:
            result['prompt'] = PromptCleaner.clean_for_sd(result['prompt'])
        
        return result

    def _clean_prompt_for_sd(self, prompt: str) -> str:
        """清理提示词"""
        return PromptCleaner.clean_for_sd(prompt)

    # ==================== 消息显示 ====================

    def _append_message(self, role: str, content: str):
        """添加消息到对话"""
        self.chat_text.config(state=tk.NORMAL)

        timestamp = datetime.now().strftime("%H:%M")

        config = {
            "user": {"prefix": f"👤 你 ({timestamp})\n", "tag": "user_msg", "bg": "#e3f2fd"},
            "assistant": {"prefix": f"🤖 助手 ({timestamp})\n", "tag": "assistant_msg", "bg": "#f5f5f5"},
            "system": {"prefix": f"📌 系统 ({timestamp})\n", "tag": "system_msg", "bg": "#fff3e0"},
            "image": {"prefix": f"🖼️ 生成 ({timestamp})\n", "tag": "image_msg", "bg": "#e8f5e9"},
        }

        cfg = config.get(role, {"prefix": f"📝 ({timestamp})\n", "tag": "normal_msg", "bg": "#ffffff"})

        self.chat_text.insert(tk.END, f"\n{cfg['prefix']}", f"{cfg['tag']}_prefix")
        self.chat_text.insert(tk.END, f"{content}\n", cfg['tag'])

        self.chat_text.tag_config(f"{cfg['tag']}_prefix", foreground="gray", font=("", 8))
        self.chat_text.tag_config(
            cfg['tag'],
            background=cfg['bg'],
            font=("微软雅黑", 10),
            spacing1=2,
            spacing2=2,
            lmargin1=10,
            lmargin2=10,
            rmargin=10
        )

        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)

        self.messages.append({"role": role, "content": content, "timestamp": timestamp})

    def _append_image_result(self, filepath: str):
        """添加图片结果"""
        self.chat_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M")

        try:
            img = Image.open(filepath)
            img.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(img)

            self.chat_text.insert(tk.END, f"\n🖼️ 生成 ({timestamp})\n", "image_prefix")
            self.chat_text.image_create(tk.END, image=photo)
            self.chat_text.insert(tk.END, f"\n📁 {os.path.basename(filepath)}\n", "image_info")

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

    # ==================== UI 事件 ====================

    def _on_send(self, event=None):
        """发送消息"""
        if self.is_generating:
            return
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return
        self.input_text.delete("1.0", tk.END)
        self._append_message("user", user_input)
        threading.Thread(target=self._process_message, args=(user_input,), daemon=True).start()

    def _on_send_shift_check(self, event):
        """Shift+Enter 换行，普通 Enter 发送"""
        if event.state & 0x1:
            return
        self._on_send()
        return "break"

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
        self._enhanced_prompt_cache = {}
        self.context_manager.clear()
        self._append_message("assistant", "🗑️ 对话已清空，有什么可以帮你的？")

    def _clear_upload(self):
        """清除上传的图片"""
        self.uploaded_images = []
        self.uploaded_image_paths = []
        self.uploaded_image = None
        self.uploaded_image_path = None
        self.image_status.config(text="")
        self.preview_label.config(image="")
        self.preview_label.image = None
        self._append_message("system", "🗑️ 已清除所有图片")

    def _upload_image(self):
        """上传图片"""
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

    def _toggle_safe_mode(self):
        """切换安全模式"""
        current = self.safe_mode_var.get()
        self.safe_mode_var.set(not current)

        if self.safe_mode_var.get():
            self.safe_mode_btn.config(relief="sunken", bg="#e8f5e9", text="🛡️ 安全模式")
            self.safe_mode_label.config(text="🟢 已启用", foreground="green")
            self._append_message("system", "🛡️ 安全模式已启用 - 将过滤不当内容")
        else:
            self.safe_mode_btn.config(relief="raised", bg="#ffebee", text="⚠️ 自由模式")
            self.safe_mode_label.config(text="🔴 已禁用", foreground="red")
            self._append_message("system", "⚠️ 安全模式已禁用 - 内容不受限制")

    def _set_quality_mode(self, mode: str):
        """设置质量模式"""
        self.quality_mode_var.set(mode)

        mode_config = {
            "快速": {"steps": 8, "hint": "⚡ 快速模式 (8步, 小尺寸)", "color": "green"},
            "平衡": {"steps": 12, "hint": "⚖️ 平衡模式 (12步, 中等尺寸)", "color": "blue"},
            "高质量": {"steps": 20, "hint": "🌟 高质量模式 (20步, 大尺寸)", "color": "orange"},
            "超高质量": {"steps": 30, "hint": "✨ 超高质量模式 (30步, 超大尺寸)", "color": "red"},
        }

        config = mode_config.get(mode, mode_config["快速"])
        self.chat_steps_var.set(config["steps"])
        self.mode_hint.config(text=config["hint"], foreground=config["color"])

        for btn_name in ["快速", "平衡", "高质量", "超高质量"]:
            btn = getattr(self, f"_{btn_name}_btn", None)
            if btn:
                btn.config(
                    relief="sunken" if btn_name == mode else "raised",
                    bg="#e8f5e9" if btn_name == "快速" else "#e3f2fd" if btn_name == "平衡" else "#fff3e0" if btn_name == "高质量" else "#fce4ec" if btn_name == "超高质量" else "#f5f5f5"
                )

        self._append_message("system", f"📊 切换到 {mode} 模式")

    # ==================== LLM UI 事件 ====================

    def _on_llm_toggle(self):
        """LLM 开关切换"""
        if self.llm_enabled_var.get():
            if self.ollama_manager.available:
                self.llm_status.config(text="●", foreground="green")
                self._append_message("system", "🧠 LLM 增强已启用")
            else:
                self._append_message("system", "⏳ LLM 未就绪，请等待或点击「安装 LLM」")
                self.llm_enabled_var.set(False)
        else:
            self.llm_status.config(text="●", foreground="gray")
            self._append_message("system", "🧠 LLM 增强已禁用")

    def _manual_install_llm(self):
        """手动安装 LLM"""
        if self.ollama_manager.installing:
            self._append_message("system", "⏳ 正在安装中...")
            return

        if self.ollama_manager.available:
            self._append_message("system", "✅ LLM 已就绪")
            return

        if messagebox.askyesno("安装 LLM",
            "将自动安装 Ollama 并下载模型。\n\n"
            f"1. 下载 Ollama (约 100MB)\n"
            f"2. 下载模型 {self.llm_model.get()} (约 {self.llm_model_size})\n"
            f"3. 自动启动服务\n\n"
            "整个过程可能需要 10-30 分钟，确定继续吗？"
        ):
            self.ollama_manager.install()

    def _debug_test_llm(self):
        """调试测试 LLM"""
        self.ollama_manager.debug_test()

    # ==================== 模型加载 ====================

    def _ensure_model_loaded(self) -> bool:
        """确保模型已加载"""
        if self.app.model_manager.is_sd_loaded:
            return True

        self._append_message("system", "📦 检测到模型未加载，正在自动加载...")
        self._update_status("📦 正在加载模型...")

        checkpoints = getattr(self.app, 'checkpoints', [])
        if not checkpoints:
            self._append_message("assistant", "❌ 没有找到可用的 SD 模型文件")
            self._update_status("❌ 未找到模型", 0)
            return False

        model_name = checkpoints[0]
        model_path = self.app._get_model_path(model_name)

        if not model_path:
            self._append_message("assistant", f"❌ 找不到模型文件: {model_name}")
            self._update_status("❌ 模型文件不存在", 0)
            return False

        self._is_loading_model = True

        def load_thread():
            def progress_cb(value, msg):
                self.app.root.after(0, lambda: self._update_status(f"🔄 {msg}", value))

            success = self.app.model_manager.load_sd(model_path, model_name, progress_cb)
            self.app.root.after(0, lambda: self._on_model_loaded(success, model_name))

        threading.Thread(target=load_thread, daemon=True).start()
        return True

    def _on_model_loaded(self, success: bool, model_name: str):
        """模型加载完成"""
        self._is_loading_model = False

        if success:
            self._append_message("system", f"✅ 模型加载完成: {model_name[:40]}...")
            self._update_status("✅ 模型就绪", 1.0)
            self.progress_bar.config(value=0)

            # 自动加载 LoRA
            if self.lora_enabled_var.get():
                self.lora_manager.auto_load_default()

            if self._pending_intent is not None:
                intent = self._pending_intent
                self._pending_intent = None
                self._append_message("system", "🔄 继续执行之前的请求...")
                self._process_message(intent.original_text)
            else:
                self._append_message("assistant", "✅ 模型已就绪，可以开始生图了！")
        else:
            self._append_message("assistant", "❌ 模型加载失败\n\n请在主界面手动加载模型后重试。")
            self._update_status("❌ 加载失败", 0)
            self._pending_intent = None

    # ==================== 兼容性方法 ====================

    def get_frame(self):
        """返回框架"""
        return self.frame