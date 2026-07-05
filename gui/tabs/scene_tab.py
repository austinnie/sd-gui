#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
亲密文生图标签页 - 场景模式（快速生成两人亲密场景）
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .base_tab import BaseTab
from gui.scene_manager import SceneManager
import threading
import random
import time

from core.nsfw_filter import nsfw_filter
from config.nsfw_config import nsfw_config, ContentLevel


class SceneTab(BaseTab):
    """亲密文生图标签页"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.scene_manager = SceneManager()
        self.category_vars = {}
        self.category_combos = {}
        
        self.is_generating = False
        self.cancel_generation = False
        self.params = app.params_panel
        
        self._init_vars()
        self.setup_ui()
    
    def _init_vars(self):
        """初始化变量"""
        self.template_var = tk.StringVar()
        self.custom_suffix_var = tk.StringVar(
            value="soft lighting, intimate atmosphere, romantic mood, full body visible, both people fully in frame"
        )
        self.cancel_generation = False
    
    def setup_ui(self):
        frame = self.frame
        row = 0
        
        # ===== 标题 =====
        ttk.Label(frame, text="💑 快速生成两人亲密场景", font=("", 12, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, padx=5, pady=10)
        row += 1
        
        # ===== 模板选择 =====
        template_frame = ttk.Frame(frame)
        template_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(template_frame, text="选择模板:").pack(side=tk.LEFT, padx=5)
        self.template_combo = ttk.Combobox(template_frame, textvariable=self.template_var, width=30)
        self.template_combo.pack(side=tk.LEFT, padx=5)
        
        templates = self.scene_manager.get_all_templates()
        if templates:
            self.template_combo['values'] = [""] + templates
            self.template_combo.set("")
        
        ttk.Button(template_frame, text="应用模板", command=self._apply_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(template_frame, text="🔄 重载场景", command=self._reload_scene).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # ===== 场景分类选择 =====
        row = self._build_category_widgets(frame, row + 1)
        
        # ===== 自定义后缀 =====
        suffix_frame = ttk.Frame(frame)
        suffix_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Label(suffix_frame, text="自定义后缀:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(suffix_frame, textvariable=self.custom_suffix_var, width=50).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # ===== NSFW 提示 =====
        nsfw_hint_frame = ttk.Frame(frame)
        nsfw_hint_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2, padx=5)
        self.nsfw_hint_label = ttk.Label(
            nsfw_hint_frame,
            text=self._get_nsfw_hint(),
            foreground="orange" if nsfw_config.level != ContentLevel.SAFE else "green",
            font=("", 8)
        )
        self.nsfw_hint_label.pack(side=tk.LEFT, padx=5)
        row += 1
        
        # ===== 生成按钮 =====
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)

        ttk.Button(btn_frame, text="✨ 生成场景提示词", 
            command=self._generate_scene_prompt).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="📋 复制到文生图", 
            command=self._copy_to_txt2img).pack(side=tk.LEFT, padx=5)

        self.generate_image_btn = ttk.Button(btn_frame, text="🚀 生成图片", 
            command=self._generate_image)
        self.generate_image_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_scene_btn = ttk.Button(btn_frame, text="⏹️ 取消", 
            command=self._cancel_generation)
        self.cancel_scene_btn.pack(side=tk.LEFT, padx=5)
        self.cancel_scene_btn.config(state=tk.DISABLED)

        ttk.Button(btn_frame, text="📁 打开输出文件夹", 
            command=self.app.open_output_folder).pack(side=tk.LEFT, padx=5)

        row += 1
        
        # ===== 结果显示 =====
        ttk.Label(frame, text="生成的提示词:", font=("", 9, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5)
        row += 1
        
        self.prompt_text = tk.Text(frame, height=5, width=85, wrap=tk.WORD)
        self.prompt_text.grid(row=row, column=0, columnspan=3, padx=5, pady=5)
        row += 1
        
        self.neg_text = tk.Text(frame, height=4, width=85, wrap=tk.WORD)
        self.neg_text.grid(row=row, column=0, columnspan=3, padx=5, pady=5)
    
    def _get_nsfw_hint(self) -> str:
        """获取 NSFW 状态提示"""
        level = nsfw_config.level
        if level == ContentLevel.SAFE:
            return "🔒 当前为安全模式，NSFW 内容会被过滤"
        elif level == ContentLevel.SUGGESTIVE:
            return "💋 当前为暗示模式，保留性感内容"
        elif level == ContentLevel.EXPLICIT:
            return "🔞 当前为露骨模式，允许明确成人内容"
        else:
            return "⚠️ 当前为极端模式，内容不受限制"
    
    def _update_nsfw_hint(self):
        """更新 NSFW 提示"""
        self.nsfw_hint_label.config(text=self._get_nsfw_hint())
    
    def _build_category_widgets(self, parent, start_row) -> int:
        """构建场景分类选择器"""
        categories = self.scene_manager.get_categories("两人亲密场景")
        row = start_row
        
        for category_name, items in categories.items():
            if not items:
                continue
            
            frame = ttk.Frame(parent)
            frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2, padx=5)
            
            ttk.Label(frame, text=category_name + ":", width=10).pack(side=tk.LEFT)
            
            var = tk.StringVar()
            self.category_vars[category_name] = var
            
            choices = [""]
            for key, value in items.items():
                if isinstance(value, dict):
                    display = value.get("name", key)
                else:
                    display = value
                choices.append(display)
            
            combo = ttk.Combobox(frame, textvariable=var, values=choices, width=25)
            combo.pack(side=tk.LEFT, padx=5)
            self.category_combos[category_name] = combo
            
            row += 1
        
        return row
    
    def _apply_template(self):
        """应用模板"""
        template_name = self.template_var.get()
        if not template_name:
            return
        
        selections = self.scene_manager.get_template(template_name)
        if not selections:
            return
        
        categories = self.scene_manager.get_categories("两人亲密场景")
        
        key_map = {
            "基本姿势": "basic_pose",
            "亲密程度": "intimacy_level",
            "视角": "view_angle",
            "环境氛围": "environment",
            "服装状态": "clothing",
            "情感表达": "emotion",
            "男士特征": "body_features_man",
            "女士特征": "body_features_woman"
        }
        
        for display_name, var in self.category_vars.items():
            if display_name in key_map:
                key = key_map[display_name]
                if key in selections and selections[key]:
                    value = selections[key]
                    if display_name in categories:
                        items = categories[display_name]
                        for item_key, item_value in items.items():
                            if isinstance(item_value, dict):
                                if item_value.get("name") == value or item_key == value:
                                    var.set(item_value.get("name", item_key))
                                    break
                            else:
                                if item_value == value or item_key == value:
                                    var.set(item_value if isinstance(item_value, str) else item_key)
                                    break
        
        if "custom_suffix" in selections and selections["custom_suffix"]:
            self.custom_suffix_var.set(selections["custom_suffix"])
        
        self._generate_scene_prompt()
    
    def _generate_scene_prompt(self):
        """生成场景提示词"""
        selections = {}
        categories = self.scene_manager.get_categories("两人亲密场景")
        
        key_map = {
            "基本姿势": "basic_pose",
            "亲密程度": "intimacy_level",
            "视角": "view_angle",
            "环境氛围": "environment",
            "服装状态": "clothing",
            "情感表达": "emotion",
            "男士特征": "body_features_man",
            "女士特征": "body_features_woman"
        }
        
        for display_name, var in self.category_vars.items():
            if display_name in key_map:
                selected_display = var.get()
                if selected_display:
                    key = key_map[display_name]
                    if display_name in categories:
                        items = categories[display_name]
                        for item_key, item_value in items.items():
                            if isinstance(item_value, dict):
                                if item_value.get("name") == selected_display:
                                    selections[key] = item_value.get("prompt", item_key)
                                    break
                            else:
                                if item_value == selected_display:
                                    selections[key] = selected_display
                                    break
                    else:
                        selections[key] = selected_display
        
        custom_suffix = self.custom_suffix_var.get()
        if custom_suffix:
            selections["custom_suffix"] = custom_suffix
        
        prompt, negative = self.scene_manager.build_prompt(selections)
        
        # ===== NSFW 过滤 =====
        if nsfw_config.enabled:
            prompt, negative = nsfw_filter.filter_prompt(prompt, negative)
            print(f"   NSFW 过滤后提示词长度: {len(prompt)} 字符")
        
        # ===== 精简提示词 =====
        prompt = self._shorten_for_clip(prompt, max_len=280)
        negative = self._shorten_for_clip(negative, max_len=150)
        
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", prompt)
        self.neg_text.delete("1.0", tk.END)
        self.neg_text.insert("1.0", negative)
        
        self.update_status("✅ 场景提示词已生成")
    
    def _reload_scene(self):
        """重新加载场景"""
        try:
            self.scene_manager.load_config()
            templates = self.scene_manager.get_all_templates()
            if templates:
                self.template_combo['values'] = [""] + templates
            else:
                self.template_combo['values'] = [""]
            self.update_status("✅ 场景配置已重新加载")
        except Exception as e:
            self.update_status(f"❌ 重新加载失败: {e}")
    
    def _copy_to_txt2img(self):
        """复制到文生图"""
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        negative = self.neg_text.get("1.0", tk.END).strip()
        
        if prompt:
            if hasattr(self.app, 'txt2img_tab'):
                self.app.txt2img_tab.set_prompt(prompt, negative)
                self.update_status("✅ 已复制到文生图")
            else:
                messagebox.showwarning("提示", "文生图标签页未初始化")
        else:
            messagebox.showwarning("提示", "请先生成场景提示词")
    
    def get_prompt(self) -> tuple:
        """获取当前提示词"""
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        negative = self.neg_text.get("1.0", tk.END).strip()
        return prompt, negative

    def _generate_image(self):
        """直接生成图片（调用文生图）"""
        if self.is_generating:
            messagebox.showwarning("提示", "正在生成中，请等待完成")
            return

        if hasattr(self.app, 'txt2img_tab') and self.app.txt2img_tab:
            if self.app.txt2img_tab.is_generating:
                messagebox.showwarning("提示", "文生图正在生成中，请等待完成")
                return
            
        self._generate_scene_prompt()
        
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        negative = self.neg_text.get("1.0", tk.END).strip()
        
        if not prompt:
            messagebox.showwarning("提示", "请先生成场景提示词")
            return
        
        if not hasattr(self.app, 'txt2img_tab') or self.app.txt2img_tab is None:
            messagebox.showwarning("提示", "文生图标签页未初始化")
            return
        
        if not self.app.is_pipe_loaded():
            messagebox.showwarning("提示", "请先在主界面加载模型")
            return

        params = self.app.params_panel.get_params()
        
        # ===== 智能尺寸调整 =====
        from gui.tabs.txt2img_tab import get_smart_size
        smart_w, smart_h, size_msg = get_smart_size(params["width"], params["height"], prompt)
        print(f"📐 {size_msg}")
        
        # ===== 智能参数调整 =====
        from gui.tabs.txt2img_tab import get_smart_params
        smart_steps, smart_cfg, _, param_msg = get_smart_params(
            prompt, params["steps"], params["cfg"], None
        )
        if smart_steps != params["steps"] or smart_cfg != params["cfg"]:
            print(f"⚙️ {param_msg}")
        
        txt2img = self.app.txt2img_tab
        txt2img.set_params(
            steps=smart_steps,
            cfg=smart_cfg,
            seed=params["seed"],
            width=smart_w,
            height=smart_h,
            num_images=params["num_images"]
        )
    
        self.is_generating = True
        self.generate_image_btn.config(state=tk.DISABLED)
        self.cancel_scene_btn.config(state=tk.NORMAL)
    
        self.app.txt2img_tab.set_prompt(prompt, negative)
        self.app.txt2img_tab.start_generate()
        
        self.update_status("🚀 正在生成图片...")

        threading.Thread(target=self._monitor_generation, daemon=True).start()
    
    def _cancel_generation(self):
        """取消生成"""
        if hasattr(self.app, 'txt2img_tab') and self.app.txt2img_tab:
            self.app.txt2img_tab.cancel_generation_cmd()
            self.app.txt2img_tab.is_generating = False
            self.app.txt2img_tab.generate_btn.config(state=tk.NORMAL)
            self.app.txt2img_tab.cancel_btn.config(state=tk.DISABLED)
        
        self.is_generating = False
        self.generate_image_btn.config(state=tk.NORMAL)
        self.cancel_scene_btn.config(state=tk.DISABLED)
        self.update_status("⏹️ 已取消生成")
    
    def _shorten_for_clip(self, text, max_len=150):
        """精简文本以适应 CLIP 77 token 限制"""
        if len(text) <= max_len:
            return text
        
        parts = [p.strip() for p in text.split(',') if p.strip()]
        seen = set()
        unique_parts = []
        for p in parts:
            if p not in seen:
                seen.add(p)
                unique_parts.append(p)
        
        unique_parts.sort(key=lambda x: len(x), reverse=True)
        
        result = []
        current_len = 0
        for p in unique_parts:
            add_len = len(p) + 2
            if current_len + add_len <= max_len:
                result.append(p)
                current_len += add_len
        
        return ', '.join(result) if result else text[:max_len]
    
    def _monitor_generation(self):
        """监控文生图生成状态"""
        import time
        while True:
            if hasattr(self.app, 'txt2img_tab'):
                if not self.app.txt2img_tab.is_generating:
                    self.app.root.after(0, self._on_generation_done)
                    break
            time.sleep(0.5)

    def _on_generation_done(self):
        """生成完成回调"""
        self.is_generating = False
        self.generate_image_btn.config(state=tk.NORMAL)
        self.cancel_scene_btn.config(state=tk.DISABLED)
        self.update_status("✅ 图片生成完成")

    def batch_generate(self, prompts):
        """批量生成（场景模式）"""
        if self.is_generating:
            messagebox.showwarning("提示", "正在生成中，请等待完成")
            return
        
        prompts_list = []
        negs_list = []
        category_keys = ["basic_pose", "intimacy_level", "view_angle", "environment", "clothing", "emotion"]
        
        for line in prompts:
            parts = line.split('|')
            if len(parts) >= 6:
                selections = {}
                for i, key in enumerate(category_keys):
                    if i < len(parts):
                        selections[key] = parts[i].strip()
                prompt, negative = self.scene_manager.build_prompt(selections)
                prompts_list.append(prompt)
                negs_list.append(negative)
            else:
                print(f"⚠️ 格式错误，跳过: {line}")
        
        if not prompts_list:
            messagebox.showwarning("提示", "没有有效的场景配置")
            return
        
        self._run_batch_generation(prompts_list, negs_list)

    def _run_batch_generation(self, prompts_list, negs_list):
        """运行批量生成（场景模式）"""
        if not prompts_list:
            return
        
        self.is_generating = True
        self.generate_image_btn.config(state=tk.DISABLED)
        
        for idx, (prompt, negative) in enumerate(zip(prompts_list, negs_list)):
            if self.cancel_generation:
                break
            
            self.update_status(f"🔄 正在生成第 {idx+1}/{len(prompts_list)} 张...")
            
            if hasattr(self.app, 'txt2img_tab'):
                txt2img = self.app.txt2img_tab
                txt2img.set_prompt(prompt, negative)
                
                seed = self.app.params_panel.seed_var.get()
                if seed == -1:
                    seed = random.randint(1, 2**32 - 1)
                seed = seed + idx
                
                # ===== 智能尺寸和参数调整 =====
                from gui.tabs.txt2img_tab import get_smart_size, get_smart_params
                params = self.app.params_panel.get_params()
                smart_w, smart_h, _ = get_smart_size(params["width"], params["height"], prompt)
                smart_steps, smart_cfg, _, _ = get_smart_params(prompt, params["steps"], params["cfg"], None)
                
                txt2img._generate_single_image(
                    prompt, negative,
                    steps=smart_steps,
                    cfg=smart_cfg,
                    seed=seed,
                    height=smart_h,
                    width=smart_w,
                    index=idx+1,
                    total=len(prompts_list)
                )
            
            time.sleep(0.5)
        
        self.is_generating = False
        self.generate_image_btn.config(state=tk.NORMAL)
        self.update_status("✅ 批量生成完成")