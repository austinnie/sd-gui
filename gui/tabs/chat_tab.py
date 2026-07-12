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

        # ✅ 延迟检测 LLM（给程序启动留时间）
        self.app.root.after(3000, self._check_ollama)
    
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
        self._is_loading_model = False
        # 会话生图参数
        self.chat_steps_var = tk.IntVar(value=20)  # 默认 20 步，提高质量
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
            "quality": "high",  # 新增：质量偏好
        }

        # 本地 LLM 配置
        self.llm_enabled = tk.BooleanVar(value=True)
        self.llm_model = tk.StringVar(value="qwen2.5:1.5b")
        self.llm_available = False
        self.llm_installing = False
        self.llm_model_size = "1GB"
        
        # ✅ 新增：缓存增强后的提示词
        self._enhanced_prompt_cache = {}
        
        # ✅ 新增：负面提示词模板
        self._negative_templates = {
            "default": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, extra limbs, bad proportions, bad hands, missing fingers, extra fingers",
            "portrait": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, extra limbs, bad proportions, bad hands, bad face, distorted face",
            "landscape": "worst quality, low quality, ugly, deformed, blurry, watermark, text, bad composition, cluttered",
            "nude": "clothes, fabric, dress, shirt, pants, underwear, bra, panties, bikini, swimsuit, covering, censorship, mosaic",
        }

    def _check_ollama_installed(self) -> bool:
        """检查 Ollama 是否已安装"""
        import subprocess
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def _check_ollama_running(self) -> bool:
        """检查 Ollama 服务是否运行"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False

    def _check_model_available(self, model: str) -> bool:
        """检查模型是否已下载"""
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
        """自动安装 Ollama (Windows) - 后台线程"""
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
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                
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
        """启动 Ollama 服务（后台线程）"""
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
        """下载 LLM 模型（后台线程）"""
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
        """LLM 准备就绪"""
        self.llm_available = True
        self.llm_installing = False
        self.llm_status.config(text="●", foreground="green")
        self._append_message("system", f"✅ LLM 已就绪！模型: {self.llm_model.get()}")
        self._append_message("assistant", "🧠 本地 LLM 已启用，可以智能理解你的需求了！")
        self._update_status("✅ LLM 就绪", 1.0)

    def _check_ollama(self):
        """检测并自动设置 LLM（完整版）- 后台线程"""
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
    
    # ==================== 🚀 核心优化：LLM 提示词增强 ====================
    
    def _call_ollama(self, prompt: str, timeout: int = 30, max_tokens: int = 512) -> str:
        """调用本地 Ollama（增强版）"""
        if not self.llm_available:
            return None
        
        try:
            import requests
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.llm_model.get(),
                    "prompt": prompt,
                    "temperature": 0.8,  # 提高温度增加创意
                    "stream": False,
                    "max_tokens": max_tokens,
                    "top_p": 0.9,
                },
                timeout=timeout
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            return None
        except requests.exceptions.Timeout:
            print("⚠️ Ollama 超时")
            return None
        except Exception as e:
            print(f"⚠️ Ollama 调用失败: {e}")
            return None


    def _build_preserve_parts_from_features(self, image_features: dict, user_text: str = "") -> list:
        """
        从原图特征构建保留词列表
        
        Args:
            image_features: 原图特征字典
            user_text: 用户输入文本，用于判断性别
        
        Returns:
            preserve_parts: 保留词列表
        """
        preserve_parts = ["same person", "same face", "same identity"]
        
        # 1. 根据人脸数量确定人数指示词
        face_count = image_features.get("face_count", 0)
        has_multiple = image_features.get("has_multiple_subjects", False)

        # ✅ 判断风格：从用户输入或原图文件名判断
        # 如果原图是写实风格，用 woman；否则用 girl
        is_realistic = image_features.get("is_realistic", True)  # 默认写实
        
        
        
        # 检查用户输入中是否有提示
        if user_text and any(k in user_text.lower() for k in ['动漫', '二次元', 'anime', '卡通']):
            is_realistic = False
        
        # 检查原图文件名（如果有提示）
        if self.uploaded_image_path:
            filename = os.path.basename(self.uploaded_image_path).lower()
            if 'anime' in filename or 'cartoon' in filename or '动漫' in filename:
                is_realistic = False
            
        if face_count == 1:
            if user_text and any(k in user_text.lower() for k in ['男', '帅哥', '男孩', '男性', '小哥哥', '男神']):
                preserve_parts.append("1boy" if is_realistic else "1boy")
            else:
                # ✅ 根据风格选择
                if is_realistic:
                    preserve_parts.append("1woman")  # 写实用 1woman
                else:
                    preserve_parts.append("1girl")   # 动漫用 1girl
        elif face_count >= 2 or has_multiple:
            if user_text and any(k in user_text.lower() for k in ['男', '帅哥', '男孩', '男性']):
                preserve_parts.append("2boys")
            else:
                preserve_parts.append("2women" if is_realistic else "2girls")
        
        # 2. 姿势
        preserve_parts.append("same pose")
        preserve_parts.append("same body language")
        
        # 3. 全身/半身
        if image_features.get("is_full_body", True):
            preserve_parts.append("full body")
        else:
            preserve_parts.append("half body")
        
        return preserve_parts

    def _merge_llm_prompt_with_features(self, llm_prompt: str, preserve_parts: list) -> str:
        """合并 LLM 生成的提示词和原图特征保留词"""
        prompt_lower = llm_prompt.lower()
        
        # 1. 检查是否已有保留词
        has_preserve = "same person" in prompt_lower and "same face" in prompt_lower
        
        # ✅ 检查用户是否指定了姿势（从 preserve_parts 中检测）
        # 注意：如果 preserve_parts 中没有 "same pose"，说明用户指定了新姿势
        has_user_pose = "same pose" not in preserve_parts
        
        # 2. 提取需要添加的保留词（去重，并跳过 same pose）
        parts_to_add = []
        for part in preserve_parts:
            if part.lower() not in prompt_lower:
                # ✅ 如果用户指定了新姿势，不添加 "same pose"
                if has_user_pose and part == "same pose":
                    continue
                parts_to_add.append(part)
        
        # 3. 合并
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
        """
        使用原图特征增强提示词（主入口函数）
        
        Args:
            prompt: 当前提示词
            intent: 意图字典
            image_features: 原图特征
        
        Returns:
            增强后的提示词
        """
        user_text = intent.get("original_text", "")
        keywords = intent.get("keywords", {})
        user_poses = keywords.get("poses", [])  # ✅ 获取用户指定的姿势
        
        # 1. 从原图特征构建保留词
        preserve_parts = self._build_preserve_parts_from_features(image_features, user_text)
        
        # ✅ 如果用户指定了姿势，移除 preserve_parts 中的 "same pose"
        if user_poses:
            preserve_parts = [p for p in preserve_parts if p != "same pose"]
            print(f"   🧍 用户指定姿势: {user_poses}，已移除 'same pose'")
        
        # 2. 检查 prompt 是否是自然语言
        prompt_lower = prompt.lower()
        sentence_indicators = ['maintain', 'exchange', 'retain', 'keep', 'change', 'feature', 'outfit', 'gown']
        is_natural = any(ind in prompt_lower for ind in sentence_indicators)
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in prompt)
        
        # 3. 检查是否已有保留词
        has_preserve = "same person" in prompt_lower and "same face" in prompt_lower
        
        # 4. 如果已有保留词，只补充缺失的
        if has_preserve:
            parts_to_add = [p for p in preserve_parts if p.lower() not in prompt_lower]
            if parts_to_add:
                return prompt + ", " + ", ".join(parts_to_add)
            return prompt
        
        # 5. 如果是自然语言，重新构建
        if is_natural or has_chinese:
            # 提取服装关键词
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
            
            # 构建标准提示词
            result_parts = []
            # 性别
            gender = next((p for p in preserve_parts if p in ["1girl", "1boy", "2girls", "2boys"]), "1girl")
            result_parts.append(gender)
            # 保留词（除了性别和姿势）
            other_parts = [p for p in preserve_parts if p not in ["1girl", "1boy", "2girls", "2boys"]]
            result_parts.extend(other_parts)
            # ✅ 用户指定的姿势（如果有时）
            if user_poses:
                result_parts.append(" ".join(user_poses) + " pose")
            # 服装
            if clothes:
                result_parts.append("wearing " + ", ".join(clothes))
            # 质量词
            result_parts.append("masterpiece")
            result_parts.append("best quality")
            result_parts.append("photorealistic")
            result_parts.append("8k")
            result_parts.append("highly detailed")
            
            return ", ".join(result_parts)
        
        # 6. 标准 SD 提示词 → 合并保留词
        return self._merge_llm_prompt_with_features(prompt, preserve_parts)
        
    def debug_test_llm(self):
        """调试测试 LLM（在 UI 中调用）"""
        import requests
        
        self._append_message("system", "🔍 开始测试 LLM...")
        
        # 1. 检查服务
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
        
        # 2. 测试推理
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
        """使用 LLM 增强提示词"""
        if not self.llm_available or not self.llm_enabled.get():
            return None
        
        cache_key = f"{text}_{is_img2img}"
        if cache_key in self._enhanced_prompt_cache:
            return self._enhanced_prompt_cache[cache_key]
        
        # ✅ 修复：在 if 外部定义 prompt_template
        if is_img2img:
            prompt_template = """你是一个专业的 Stable Diffusion 提示词专家。用户想修改一张图片，请生成高质量的图生图提示词。

    用户需求：{text}

    【重要规则】
    1. 必须保留原始人物的核心特征：same person, same face, same pose, same identity
    2. 必须保留原始图片的风格、光影和质感
    3. 只修改用户明确要求的部分（如换衣服、换背景等）
    4. 不要添加用户未提及的风格词（如 elegant, modern, professional 等）
    5. 如果用户没有指定具体服装，用"changing outfit"代替具体服装名
    6. 提示词要简洁，不要过度描述
    7. 只输出提示词，不要解释

    【输出格式】
    正面提示词：xxx
    负面提示词：xxx"""
        else:
            prompt_template = """你是一个专业的 Stable Diffusion 提示词专家。请根据用户描述生成高质量的文生图提示词。

    用户描述：{text}

    【重要规则】
    1. 生成详细、具体、有画面感的提示词
    2. 包含：主体描述、场景、光线、风格、构图、色彩、情绪
    3. 添加高质量修饰词
    4. 提示词用英文，用逗号分隔
    5. 只输出提示词，不要解释

    【输出格式】
    正面提示词：xxx
    负面提示词：xxx
    风格：xxx
    质量：xxx"""

        prompt = prompt_template.format(text=text)
        result = self._call_ollama(prompt, timeout=30, max_tokens=256)
        
        if not result:
            return None
        
        parsed = self._parse_llm_response(result)
        
        if parsed and parsed.get('prompt'):
            self._enhanced_prompt_cache[cache_key] = parsed
            return parsed
        
        return None


    def _parse_llm_response(self, response: str) -> dict:
        """解析 LLM 返回的结构化提示词"""
        lines = response.strip().split('\n')
        
        result = {
            "prompt": "",
            "negative": "",
            "style": "",
            "quality": "masterpiece, best quality, photorealistic, 8k, highly detailed",
        }
        
        current_key = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测关键词
            if '正面提示词' in line or '正面' in line:
                current_key = 'prompt'
                content = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                if content:
                    result['prompt'] = content
            elif '负面提示词' in line or '负面' in line:
                current_key = 'negative'
                content = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                if content:
                    result['negative'] = content
            elif '风格' in line:
                current_key = 'style'
                content = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                if content:
                    result['style'] = content
            elif '质量' in line:
                current_key = 'quality'
                content = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                if content:
                    result['quality'] = content
            elif current_key and line:
                # 续行
                if current_key == 'prompt':
                    result['prompt'] += ', ' + line if result['prompt'] else line
                elif current_key == 'negative':
                    result['negative'] += ', ' + line if result['negative'] else line
        
        # ✅ 如果解析失败，使用原始响应作为提示词
        if not result['prompt']:
            # 清理响应
            cleaned = re.sub(r'^.*?：', '', response)
            cleaned = re.sub(r'^.*?:', '', cleaned)
            cleaned = cleaned.strip()
            if cleaned:
                result['prompt'] = cleaned
            else:
                return None
        
        # ===== 🚀 新增：检测自然语言并转换为 SD 格式 =====
        prompt_text = result['prompt']
        
        # 检测是否是自然语言（包含完整句子的特征）
        sentence_indicators = [
            'maintain', 'exchange', 'retain', 'keep', 'change', 
            'feature', 'outfit', 'formal', 'gown', 'the woman',
            'the man', 'the person', 'the image', 'the picture'
        ]
        is_natural_language = any(ind in prompt_text.lower() for ind in sentence_indicators)
        
        # 检测是否包含中文（也是自然语言的特征）
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in prompt_text)
        
        if is_natural_language or has_chinese:
            print(f"   ⚠️ 检测到自然语言格式，正在转换为 SD 提示词...")
            print(f"   📝 原始: {prompt_text[:100]}...")
            
            # 提取性别
            gender = "1girl"
            if "woman" in prompt_text.lower() or "female" in prompt_text.lower() or "her" in prompt_text.lower():
                gender = "1girl"
            elif "man" in prompt_text.lower() or "male" in prompt_text.lower() or "him" in prompt_text.lower():
                gender = "1boy"
            
            # ✅ 修复：定义 prompt_parts 列表
            prompt_parts = []
            
            # 1. 性别
            prompt_parts.append(gender)
            
            # 2. 保留人物特征（图生图）
            prompt_parts.append("same person")
            prompt_parts.append("same face")
            prompt_parts.append("same pose")
            
            # 3. 提取服装关键词
            clothes_keywords = []
            clothes_map = {
                '旗袍': 'qipao',
                'qipao': 'qipao',
                '汉服': 'hanfu',
                '礼服': 'evening gown',
                'dress': 'dress',
                'gown': 'evening gown',
                '裙子': 'dress',
                '西装': 'suit',
                '制服': 'uniform',
                '泳衣': 'swimsuit',
                '比基尼': 'bikini',
            }
            for cn, en in clothes_map.items():
                if cn in prompt_text.lower():
                    if en not in clothes_keywords:
                        clothes_keywords.append(en)
            
            if clothes_keywords:
                prompt_parts.append("wearing " + ", ".join(clothes_keywords))
            else:
                # 如果没有任何服装关键词，添加默认的 qipao
                prompt_parts.append("wearing qipao")
            
            # 4. 提取场景关键词
            scene_keywords = []
            scenes_map = {
                '沙滩': 'beach',
                '海滩': 'beach',
                '海边': 'ocean',
                '花园': 'garden',
                '森林': 'forest',
                '城市': 'city',
                '卧室': 'bedroom',
                '浴室': 'bathroom',
                '舞台': 'stage',
                '宫殿': 'palace',
            }
            for cn, en in scenes_map.items():
                if cn in prompt_text.lower():
                    if en not in scene_keywords:
                        scene_keywords.append(en)
            if scene_keywords:
                prompt_parts.extend(scene_keywords)
            
            # 5. 提取风格关键词
            style_keywords = []
            styles_map = {
                '现代': 'modern style',
                '传统': 'traditional style',
                '复古': 'vintage style',
                '优雅': 'elegant style',
                '性感': 'sexy style',
                '可爱': 'cute style',
                '梦幻': 'dreamy style',
                '暗黑': 'dark style',
                '古风': 'traditional chinese style',
                '东方': 'eastern style',
                '中国风': 'chinese style',
            }
            for cn, en in styles_map.items():
                if cn in prompt_text.lower():
                    if en not in style_keywords:
                        style_keywords.append(en)
            if style_keywords:
                prompt_parts.extend(style_keywords)
            
            # 6. 质量词
            prompt_parts.append("masterpiece")
            prompt_parts.append("best quality")
            prompt_parts.append("photorealistic")
            prompt_parts.append("8k")
            prompt_parts.append("highly detailed")
            
            # 组合成最终提示词
            new_prompt = ", ".join(prompt_parts)
            result['prompt'] = new_prompt
            
            print(f"   ✅ 转换后提示词: {new_prompt}")
        
        # ✅ 确保有质量词（如果还没有）
        if 'masterpiece' not in result['prompt'].lower() and 'best quality' not in result['prompt'].lower():
            result['prompt'] = f"masterpiece, best quality, photorealistic, 8k, highly detailed, {result['prompt']}"
        
        # ✅ 确保有默认负面提示词
        if not result['negative']:
            result['negative'] = self._negative_templates["default"]
        
        return result
    
    def _enhance_prompt_with_context(self, base_prompt: str, keywords: dict) -> str:
        """使用上下文和关键词增强提示词"""
        
        # 1. 质量词
        quality_parts = ["masterpiece", "best quality", "photorealistic", "8k", "highly detailed", "ultra detailed"]
        prompt_parts = quality_parts.copy()
        
        # 2. 性别（确保有）
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
        
        # 3. 添加性别（去重）
        existing_genders = [p for p in prompt_parts if p in ["1girl", "1boy", "2girls", "2boys", "1girl, 1boy"]]
        if not existing_genders:
            prompt_parts = genders + prompt_parts
        elif existing_genders and genders and existing_genders[0] != genders[0]:
            for g in existing_genders:
                prompt_parts.remove(g)
            prompt_parts = genders + prompt_parts
        
        # 4. ✅ 修复：加入 base_prompt 中的核心描述
        # 将 prompt_parts 转为字符串检查
        current_prompt = ", ".join(prompt_parts)
        if base_prompt and base_prompt not in current_prompt:
            prompt_parts.append(base_prompt)
        
        # 5. 风格
        if keywords.get("styles"):
            for style in keywords["styles"]:
                if style not in prompt_parts:
                    prompt_parts.append(style)
        
        # 6. 主体描述（场景、光线、姿势等）
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
        
        # 7. 组合
        full_prompt = ", ".join(prompt_parts)
        if subject_parts:
            full_prompt += ", " + ", ".join(subject_parts)
        
        # 8. 用户偏好
        if self.user_preferences.get("style"):
            style = self.user_preferences["style"]
            if style not in full_prompt:
                full_prompt += f", {style} style"
        
        return full_prompt
    
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
        
        ttk.Button(toolbar, text="🔧 测试 LLM", command=self.debug_test_llm, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ 清除对话", command=self._clear_chat, width=12).pack(side=tk.LEFT, padx=2)
        
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

    def _manual_install_llm(self):
        """手动安装 LLM"""
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
        """LLM 开关切换"""
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
        """更新上下文"""
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
        """获取上下文摘要"""
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
        """检查是否有上下文"""
        return len(self.conversation_history) > 0 or self.last_prompt is not None
        
    def _on_send_shift_check(self, event):
        """检查是否按了 Shift+Enter"""
        if event.state & 0x1:
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
        
        self.input_text.delete("1.0", tk.END)
        self._append_message("user", user_input)
        
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
            
            self.image_status.config(text=f"📎 {os.path.basename(file)}")
            
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
        self._enhanced_prompt_cache = {}  # 清除缓存
        self._append_message("assistant", "🗑️ 对话已清空，有什么可以帮你的？")
    
    def _append_message(self, role: str, content: str):
        """添加消息到对话"""
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
        """添加图片生成结果"""
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
        """分析用户意图"""
        print("\n" + "=" * 60)
        print("🔍 [意图分析调试]")
        print(f"   用户输入: {text}")

        text_lower = text.lower()
        has_image = self.uploaded_image is not None
        
        keywords = self._extract_keywords(text)
        print(f"   提取的关键词: {keywords}")
        
        # 检测延续性指令
        continuation_keywords = ['再来', '继续', '换一个', '换一张', '再生成', '再来一张', 'another', 'continue']
        is_continuation = any(k in text_lower for k in continuation_keywords)
        
        # ===== 🚀 修复：判断是否为图生图 =====
        # 在 _analyze_intent 中，edit_keywords 添加：
        edit_keywords = ['修改', '改', '换', '变成', '改成', '做成', '转换为', '转化', '制作成', 
                         'edit', 'change', 'modify', '替换', '去除', '去掉', 'turn into', 'make into',
                         '穿上', '换上', '穿着', '穿', '换衣服', '换装',
                         '服装', '衣服', '衣服改成', '换成服装', '裙子', '上衣', '外套', '裤子',  # ✅ 新增
                         '蕾丝', 'lace', '旗袍', '汉服', '礼服', '制服']  # ✅ 新增

        # ✅ 新增：服装关键词（有图片时触发图生图）
        clothing_keywords = ['服装', '衣服', '蕾丝', 'lace', '旗袍', '汉服', '礼服', '制服', 
                             '裙子', '上衣', '外套', '裤子', '泳衣', '比基尼', '穿着', '穿上']
                             
        # ✅ 新增：姿势/动作关键词（如果有图片，这些词也应触发图生图）
        pose_keywords = ['站立', '坐', '躺', '蹲', '跪', '弯腰', '回头', '侧身', '趴', '睡', 
                         '奔跑', '走路', '跳舞', '拥抱', '接吻', '仰头', '低头', '托腮', '叉腰', '比心',
                         'standing', 'sitting', 'lying', 'running', 'walking', 'dancing', 'pose',
                         '服装', '衣服', '穿着', '蕾丝', 'lace']  # ✅ 新增
        
        # 判断是否有修改意图
        has_edit_intent = any(k in text_lower for k in edit_keywords)
        has_clothing_intent = has_image and any(k in text_lower for k in clothing_keywords)  # ✅ 新增
        has_pose_intent = has_image and any(k in text_lower for k in pose_keywords)
        
        is_img2img = has_image and (has_edit_intent or has_clothing_intent or has_pose_intent)  # ✅ 包含服装意图
        
        # ===== 调用 LLM =====
        use_llm = self.llm_enabled.get() and self.llm_available
        
        llm_result = None
        if use_llm:
            print("   🧠 正在调用 LLM 增强...")
            self._append_message("system", "🧠 正在使用 LLM 增强提示词...")
            
            llm_result = self._llm_enhance_prompt(text, is_img2img)
            if llm_result:
                print(f"   ✅ LLM 增强成功")
                print(f"   📝 增强后提示词: {llm_result.get('prompt', '')[:100]}...")
                if llm_result.get('negative'):
                    print(f"   📝 负面提示词: {llm_result.get('negative', '')[:50]}...")
                self._append_message("system", f"🧠 LLM 增强完成")
                if llm_result.get('style'):
                    self._append_message("system", f"🎨 风格: {llm_result['style']}")
            else:
                print("   ⚠️ LLM 增强失败，使用备用方案")
        
        # ===== 构建最终提示词 =====
        if llm_result and llm_result.get('prompt'):
            smart_prompt = llm_result['prompt']
            negative_prompt = llm_result.get('negative', self._negative_templates["default"])
            self._last_negative = negative_prompt
            print(f"   ✅ 使用 LLM 生成的提示词")
        elif is_continuation and self.last_prompt:
            smart_prompt = self.last_prompt
            self._append_message("system", f"🔄 复用上次提示词")
            print(f"   🔄 复用上次提示词")
        else:
            smart_prompt = self._enhance_prompt_with_context(text, keywords)
            self._last_negative = self._negative_templates["default"]
            print(f"   📝 使用关键词构建提示词")
        
        # ===== 判断意图类型 =====
        gen_keywords = ['生成', '画', '创建', 'create', 'generate', '画一张', '生成一张']
        
        is_gen = any(k in text_lower for k in gen_keywords)
        is_edit = any(k in text_lower for k in edit_keywords)
        
        # ===== 图生图处理（包含姿势意图） =====
        if has_image and (is_edit or (not is_gen and has_pose_intent)):
            actions = keywords.get("actions", [])
            
            if not llm_result or not llm_result.get('prompt'):
                gender = keywords.get("genders", ["1girl"])[0]
                
                if "remove_clothes" in actions:
                    smart_prompt = f"same person, same face, same pose, {gender}, nude, naked, bare skin, no clothes, without clothes, artistic nude, (masterpiece:1.2), (best quality:1.2)"
                    self._last_negative = self._negative_templates["nude"]
                    self._append_message("system", f"👗 检测到去衣指令")
                elif "change_clothes" in actions and keywords.get("clothes"):
                    clothes_str = ", ".join(keywords["clothes"])
                    smart_prompt = f"same person, same face, same pose, {gender}, wearing {clothes_str}, (masterpiece:1.2), (best quality:1.2)"
                    self._append_message("system", f"👗 检测到换衣指令: {clothes_str}")
                elif "change_background" in actions and keywords.get("scenes"):
                    scene_str = ", ".join(keywords["scenes"])
                    smart_prompt = f"same person, same face, same pose, {gender}, {scene_str} background, (masterpiece:1.2), (best quality:1.2)"
                    self._append_message("system", f"🏠 检测到换背景指令: {scene_str}")
                elif keywords.get("poses"):
                    pose_str = ", ".join(keywords["poses"])
                    smart_prompt = f"same person, same face, {gender}, {pose_str} pose, (masterpiece:1.2), (best quality:1.2)"
                    self._append_message("system", f"🧍 检测到姿势指令: {pose_str}")
                else:
                    smart_prompt = f"same person, same face, same pose, {gender}, {smart_prompt}"
            
            result = {
                "type": "image_to_image",
                "prompt": smart_prompt,
                "keywords": keywords,
                "original_text": text,
                "is_continuation": is_continuation,
                "llm_enhanced": llm_result is not None
            }
            print(f"   分析结果: {result['type']}")
            print(f"   提示词: {result['prompt'][:150]}...")
            print(f"   LLM增强: {result['llm_enhanced']}")
            print("=" * 60 + "\n")
            return result
            
        elif is_gen or (not is_edit and len(text) > 10):
            result = {
                "type": "text_to_image",
                "prompt": smart_prompt,
                "keywords": keywords,
                "original_text": text,
                "is_continuation": is_continuation,
                "llm_enhanced": llm_result is not None
            }
            print(f"   分析结果: {result['type']}")
            print(f"   提示词: {result['prompt'][:150]}...")
            print(f"   LLM增强: {result['llm_enhanced']}")
            print("=" * 60 + "\n")
            return result
            
        else:
            # 对话
            if self.llm_enabled.get() and self.llm_available:
                reply = self._call_ollama(f"用户说：{text}\n请简短友好地回复（一句话）：", timeout=15, max_tokens=128)
                if reply:
                    result = {
                        "type": "chat",
                        "original_text": text,
                        "llm_reply": reply
                    }
                    print(f"   分析结果: {result['type']}")
                    print(f"   LLM回复: {reply}")
                    print("=" * 60 + "\n")
                    return result
            
            result = {
                "type": "chat",
                "original_text": text
            }
            print(f"   分析结果: {result['type']}")
            print("=" * 60 + "\n")
            return result
        
    def _extract_keywords(self, text: str) -> dict:
        """提取关键词（增强版）"""
        text_lower = text.lower()
        
        # 性别
        genders = []
        if any(k in text_lower for k in ['女', '美女', '女孩', '女性', '姑娘', '小姐姐', '女神']):
            genders.append("1girl")
        elif any(k in text_lower for k in ['男', '帅哥', '男孩', '男性', '小哥哥', '男神']):
            genders.append("1boy")
        elif any(k in text_lower for k in ['情侣', '双人', '两人', '夫妻', 'couple', '恋人']):
            genders.append("1girl, 1boy")
        
        # 服装（扩充）
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
        
        # 颜色（扩充）
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
        
        # 场景（扩充）
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
        
        # 风格（扩充）
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
        
        # 姿势（扩充）
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
        
        # 表情（扩充）
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
        
        # 身体特征
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
        
        # 光线（扩充）
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

        # 材质
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
        
        # 操作指令
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
        """根据提示词估算参数（优化版）"""
        prompt_lower = prompt.lower()
        
        # 检测场景
        is_portrait = any(k in prompt_lower for k in ['portrait', 'headshot', 'close up', 'face', '头像', '特写', '自拍'])
        is_full_body = any(k in prompt_lower for k in ['full body', 'standing', '全身', '站立', 'full-length'])
        is_half_body = any(k in prompt_lower for k in ['half body', '半身', 'from waist up', 'upper body'])
        is_landscape = any(k in prompt_lower for k in ['landscape', 'scenery', '风景', '山水', 'cityscape'])
        is_couple = any(k in prompt_lower for k in ['couple', 'two people', '双人', '情侣', '两人'])
        is_group = any(k in prompt_lower for k in ['group', 'three people', '多人', '三人', '人群'])
        is_square = any(k in prompt_lower for k in ['square', '1:1', '方图'])
        
        # ===== 图生图：使用原图尺寸 =====
        if is_image and self.uploaded_image_path:
            try:
                from PIL import Image
                img = Image.open(self.uploaded_image_path)
                w, h = img.size
                
                # 限制最大尺寸
                max_size = 1024
                if max(w, h) > max_size:
                    scale = max_size / max(w, h)
                    w = int(w * scale)
                    h = int(h * scale)
                
                width = ((w + 31) // 64) * 64
                height = ((h + 31) // 64) * 64
                
                # 限制最小尺寸
                if width < 256:
                    width = 256
                if height < 256:
                    height = 256
                if width > 1024:
                    width = 1024
                if height > 1024:
                    height = 1024
                
                steps = self.chat_steps_var.get()
                cfg = self.chat_cfg_var.get()
                
                return {
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg": cfg,
                    "strength": 0.4,  # 默认强度
                    "num_images": 1
                }
            except:
                pass
        
        # ===== 文生图尺寸判断（优化） =====
        if is_portrait:
            width, height = 512, 640
            size_msg = "头像/特写（竖图）"
        elif is_full_body:
            width, height = 512, 768
            size_msg = "全身照（竖图）"
        elif is_half_body:
            width, height = 640, 768
            size_msg = "半身照（竖图）"
        elif is_landscape:
            width, height = 896, 512
            size_msg = "风景/横图"
        elif is_couple:
            width, height = 640, 896
            size_msg = "双人照（竖图）"
        elif is_group:
            width, height = 768, 640
            size_msg = "多人照"
        elif is_square:
            width, height = 640, 640
            size_msg = "方图"
        else:
            width, height = 512, 768
            size_msg = "默认竖图"
        
        steps = self.chat_steps_var.get()
        cfg = self.chat_cfg_var.get()
        
        return {
            "width": width,
            "height": height,
            "steps": steps,
            "cfg": cfg,
            "strength": 0.4 if is_image else None,
            "num_images": 1
        }
    
    # ==================== 文生图处理 ====================
    
    def _handle_text_to_image(self, intent: dict):
        """处理文生图（优化版）"""
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
        original_text = intent.get("original_text", "")
        
        print("\n" + "=" * 60)
        print("📊 [文生图调试]")
        print(f"   用户输入: {original_text}")
        print(f"   提示词: {prompt}")
        if intent.get("llm_enhanced"):
            print(f"   🧠 已启用 LLM 增强")
        print("=" * 60 + "\n")
        
        params = self._estimate_params(prompt)
        
        self._append_message("system", f"⚙️ 参数: 步数={params['steps']}, CFG={params['cfg']}, 尺寸={params['width']}x{params['height']}")
        
        # 显示提示词摘要
        if intent.get("llm_enhanced"):
            self._append_message("system", f"🧠 已使用 LLM 增强提示词")
        
        self._append_message("assistant", f"🎨 正在生成图片...\n\n📝 提示词:\n{prompt[:200]}{'...' if len(prompt) > 200 else ''}")
        
        self._update_status(f"🎨 生成中... (尺寸: {params['width']}x{params['height']})", 0.1)
        
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
            
            # 使用负面提示词
            negative_prompt = getattr(self, '_last_negative', self._negative_templates["default"])
            
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
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
            
            pipeline_pool.release_pipeline(model_path, lora_path, task_id)
            
            self._append_image_result(filepath)
            self._append_message("assistant", f"✅ 图片已生成！\n📁 {os.path.basename(filepath)}\n\n💡 提示: 继续发送描述可以生成更多图片")

            self._update_context(intent, {"image_path": filepath, "prompt": prompt})
            self._update_status("✅ 生成完成", 1.0)
            self.app.add_to_preview(filepath, result.images[0])
            self._pending_intent = None
            
        except Exception as e:
            self._append_message("assistant", f"❌ 生成失败: {str(e)}")
            self._update_status("❌ 生成失败", 0)
            import traceback
            traceback.print_exc()
            self._pending_intent = None
    
    # ==================== 图生图处理 ====================
        
    def _handle_image_to_image(self, intent: dict):
        """处理图生图（优化版）"""
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
        # 如果 LLM 生成了太多风格词，精简它
        if intent.get("llm_enhanced"):
            # 移除可能导致风格变化的词
            style_removals = ['elegant', 'modern', 'professional', 'fashionable', 'professional style']
            for word in style_removals:
                prompt = prompt.replace(word, '')
            # 清理多余逗号
            prompt = re.sub(r',\s*,', ',', prompt)
            prompt = prompt.strip(', ')
            intent["prompt"] = prompt
            print(f"   ✂️ 精简风格词后: {prompt[:100]}...")
        
        keywords = intent.get("keywords", {})

        # ===== 🚀 新增：分析原图特征并增强提示词 =====
        image_features = self._analyze_image_features(self.uploaded_image_path)
        enhanced_prompt = self._enhance_prompt_with_features(prompt, intent, image_features)
        if enhanced_prompt != prompt:
            prompt = enhanced_prompt
            intent["prompt"] = prompt
            print(f"   ✅ 已结合原图特征增强提示词: {prompt[:150]}...")
        
        # ===== 如果 LLM 增强失败，使用备用方案 =====
        if not intent.get("llm_enhanced"):
            # 使用关键词构建更丰富的提示词
            enhanced_prompt = self._enhance_prompt_with_context(prompt, keywords)
            if enhanced_prompt:
                prompt = enhanced_prompt
                print(f"   📝 使用备用增强提示词: {prompt[:150]}...")
            
        # 检测材质转换
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
        
        # ===== 🚀 修复：避免提示词重复 =====
        # 检查 prompt 是否已经包含保留词
        prompt_lower = prompt.lower()
        has_preserve = "same person" in prompt_lower and "same face" in prompt_lower
        
        if has_preserve:
            # 如果 prompt 已经包含保留词，直接使用
            full_prompt = prompt
        else:
            # 构建保留特征的提示词（不重复添加）
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
            
            # 只添加一次保留词
            preserve_str = ", ".join(preserve_parts)
            
            # 如果 prompt 已经包含某些保留词，去重
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
        
        strength = 0.2  # 从 0.3 改为 0.2
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

    def _analyze_image_features(self, image_path: str) -> dict:
        """分析图片特征（增强版）"""
        try:
            import cv2
            import numpy as np
            
            img = cv2.imread(image_path)
            if img is None:
                return {}
            
            h, w = img.shape[:2]            
          
            
            # ===== ✅ 新增：判断是写实还是动漫风格 =====
            # 方法：检测边缘平滑度（动漫风格边缘更平滑）
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (h * w)
            
            # 写实风格：边缘密度较高（细节多）
            # 动漫风格：边缘密度较低（色块平滑）
            is_realistic = edge_density > 0.03  # 阈值可调整

            # ===== ✅ 新增：定义 face_cascade =====
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


        
            # 去重
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
                "is_realistic": is_realistic,  # ✅ 新增
            }
        except Exception as e:
            print(f"⚠️ 分析图片失败: {e}")
            return {}
    
    # ==================== 对话处理 ====================
    
    def _handle_chat(self, intent: dict):
        """处理对话（增强版）"""
        text = intent["original_text"]
        text_lower = text.lower()

        if intent.get("llm_reply"):
            self._append_message("assistant", intent["llm_reply"])
            return
        
        # 图片描述
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
        
        # 上下文查询
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
        
        # 简单规则对话
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
            # 使用 LLM 对话
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
        """确保模型已加载"""
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
        """模型加载完成回调"""
        self._is_loading_model = False
        
        if success:
            self._append_message("system", f"✅ 模型加载完成: {model_name[:40]}...")
            self._update_status("✅ 模型就绪", 1.0)
            self.progress_bar.config(value=0)
            
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
            
    def _clear_upload(self):
        """清除上传的图片"""
        self.uploaded_image = None
        self.uploaded_image_path = None
        self.image_status.config(text="")
        self.preview_label.config(image="")
        self.preview_label.image = None
    
    def get_frame(self):
        return self.frame