#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用生成器标签页
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .base_tab import BaseTab
import random
import time
from generators.single_generator import SingleGenerator
from generators.couple_generator import CoupleGenerator


class UniversalTab(BaseTab):
    """通用生成器标签页"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._init_vars()
        self.setup_ui()
    
    def _init_vars(self):
        """初始化变量"""
        # 单人生成
        self.uni_gender = tk.StringVar(value="female")
        self.uni_ethnicity = tk.StringVar(value="chinese")
        self.uni_age = tk.StringVar(value="adult")
        self.uni_clothing = tk.StringVar(value="casual")
        
        # 双人生成
        self.uni_p1_gender = tk.StringVar(value="male")
        self.uni_p1_ethnicity = tk.StringVar(value="chinese")
        self.uni_p2_gender = tk.StringVar(value="female")
        self.uni_p2_ethnicity = tk.StringVar(value="russian")
        self.uni_intimacy = tk.StringVar(value="romantic")
        
        # 生成参数
        self.params = self.app.params_panel
        
        # 结果
        self.uni_last_prompt = ""
        self.uni_last_negative = ""

        # ✅ 添加生成状态和取消标志
        self.is_generating = False
        self.cancel_generation = False
    
    def setup_ui(self):
        frame = self.frame
        
        row = 0
        # 说明
        ttk.Label(frame, text="支持多种人物组合：不同年龄、性别、种族、服装", 
                  foreground="blue", font=("", 9)).grid(
            row=row, column=0, columnspan=6, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # ===== 单人生成 =====
        ttk.Label(frame, text="📸 单人生成", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=6, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 性别
        ttk.Label(frame, text="性别:").grid(row=row, column=0, sticky=tk.W, padx=5)
        combo = ttk.Combobox(frame, textvariable=self.uni_gender, values=["female", "male"], width=8)
        combo.grid(row=row, column=1, padx=5)
        
        ttk.Label(frame, text="种族:").grid(row=row, column=2, sticky=tk.W, padx=5)
        combo = ttk.Combobox(frame, textvariable=self.uni_ethnicity, 
            values=["chinese", "japanese", "korean", "russian", "american", "british", 
                    "french", "indian", "african", "latin", "arab"], width=10)
        combo.grid(row=row, column=3, padx=5)
        row += 1
        
        # 年龄和服装
        ttk.Label(frame, text="年龄:").grid(row=row, column=0, sticky=tk.W, padx=5)
        combo = ttk.Combobox(frame, textvariable=self.uni_age,
            values=["young_adult", "adult", "middle_aged", "elderly", "teen"], width=10)
        combo.grid(row=row, column=1, padx=5)
        
        ttk.Label(frame, text="服装:").grid(row=row, column=2, sticky=tk.W, padx=5)
        combo = ttk.Combobox(frame, textvariable=self.uni_clothing,
            values=["casual", "formal", "traditional_chinese", "traditional_japanese", 
                    "sportswear", "business", "swimsuit"], width=14)
        combo.grid(row=row, column=3, padx=5)
        row += 1
        
        # ===== 双人生成 =====
        ttk.Separator(frame, orient='horizontal').grid(row=row, column=0, columnspan=6, sticky=tk.EW, pady=10)
        row += 1
        
        ttk.Label(frame, text="💑 双人生成", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=6, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 人物1
        ttk.Label(frame, text="人物1:").grid(row=row, column=0, sticky=tk.W, padx=5)
        combo = ttk.Combobox(frame, textvariable=self.uni_p1_gender, values=["male", "female"], width=6)
        combo.grid(row=row, column=1, padx=5)
        
        combo = ttk.Combobox(frame, textvariable=self.uni_p1_ethnicity,
            values=["chinese", "japanese", "korean", "russian", "american"], width=10)
        combo.grid(row=row, column=2, padx=5)
        row += 1
        
        # 人物2
        ttk.Label(frame, text="人物2:").grid(row=row, column=0, sticky=tk.W, padx=5)
        combo = ttk.Combobox(frame, textvariable=self.uni_p2_gender, values=["male", "female"], width=6)
        combo.grid(row=row, column=1, padx=5)
        
        combo = ttk.Combobox(frame, textvariable=self.uni_p2_ethnicity,
            values=["chinese", "japanese", "korean", "russian", "american"], width=10)
        combo.grid(row=row, column=2, padx=5)
        
        ttk.Label(frame, text="亲密程度:").grid(row=row, column=3, sticky=tk.W, padx=5)
        combo = ttk.Combobox(frame, textvariable=self.uni_intimacy, 
            values=["romantic", "kissing", "hugging", "passionate"], width=10)
        combo.grid(row=row, column=4, padx=5)
        row += 1
        
        # 生成按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=6, pady=10)
        
        ttk.Button(btn_frame, text="✨ 生成单人提示词", 
            command=self._generate_single).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💑 生成双人提示词", 
            command=self._generate_couple).pack(side=tk.LEFT, padx=5)
        
        # ✅ 取消按钮
        self.cancel_btn = ttk.Button(
            btn_frame, 
            text="⏹️ 取消", 
            command=self._cancel_generation,
            state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # ===== 结果显示 =====
        ttk.Separator(frame, orient='horizontal').grid(row=row, column=0, columnspan=6, sticky=tk.EW, pady=10)
        row += 1
        
        ttk.Label(frame, text="生成的提示词:", font=("", 9, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5)
        row += 1
        
        self.result_text = tk.Text(frame, height=8, width=85, wrap=tk.WORD)
        self.result_text.grid(row=row, column=0, columnspan=6, padx=5, pady=5)
        row += 1
        
        # 操作按钮
        action_frame = ttk.Frame(frame)
        action_frame.grid(row=row, column=0, columnspan=6, pady=5)
        
        ttk.Button(action_frame, text="📋 复制到文生图", 
            command=self._copy_to_txt2img).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🚀 立即生成", 
            command=self._generate_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🗑️ 清空", 
            command=self._clear_result).pack(side=tk.LEFT, padx=5)
    
    def _generate_single(self):
        """生成单人提示词"""
        try:
            generator = SingleGenerator()
            prompt, negative = generator.generate(
                age=self.uni_age.get(),
                gender=self.uni_gender.get(),
                ethnicity=self.uni_ethnicity.get(),
                clothing=self.uni_clothing.get(),
                quality="photorealistic"
            )
            
            self._display_result(prompt, negative)
            self.update_status(f"✅ 已生成 {self.uni_gender.get()}_{self.uni_ethnicity.get()} 提示词")
        except Exception as e:
            self.update_status(f"❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_couple(self):
        """生成双人提示词"""
        try:
            generator = CoupleGenerator()
            prompt, negative = generator.generate(
                person1={
                    "gender": self.uni_p1_gender.get(),
                    "ethnicity": self.uni_p1_ethnicity.get(),
                    "age": "adult",
                    "clothing": "formal" if self.uni_p1_gender.get() == "male" else "elegant"
                },
                person2={
                    "gender": self.uni_p2_gender.get(),
                    "ethnicity": self.uni_p2_ethnicity.get(),
                    "age": "adult",
                    "clothing": "elegant" if self.uni_p2_gender.get() == "female" else "formal"
                },
                intimacy=self.uni_intimacy.get(),
                scene="restaurant"
            )
            
            self._display_result(prompt, negative)
            self.update_status(f"✅ 已生成 {self.uni_p1_gender.get()}_{self.uni_p1_ethnicity.get()} + {self.uni_p2_gender.get()}_{self.uni_p2_ethnicity.get()} 提示词")
        except Exception as e:
            self.update_status(f"❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _display_result(self, prompt: str, negative: str):
        """显示结果"""
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", f"【正面提示词】\n{prompt}\n\n【负面提示词】\n{negative}")
        self.uni_last_prompt = prompt
        self.uni_last_negative = negative
    
    def _copy_to_txt2img(self):
        """复制到文生图"""
        if self.uni_last_prompt:
            if self.app and hasattr(self.app, 'txt2img_tab'):
                tab = self.app.txt2img_tab
                tab.set_prompt(self.uni_last_prompt, self.uni_last_negative)
                self.update_status("✅ 已复制到文生图")
            else:
                messagebox.showwarning("提示", "文生图标签页未初始化")
        else:
            messagebox.showwarning("提示", "请先生成提示词")
    
    # ============================================================
    # ✅ 核心方法：生成图片和取消
    # ============================================================
    
    def _generate_image(self):
        """立即生成图片"""
        if not self.uni_last_prompt:
            messagebox.showwarning("提示", "请先生成提示词")
            return
        
        if self.is_generating:
            messagebox.showwarning("提示", "正在生成中，请等待完成")
            return
        
        self.cancel_generation = False
        self.is_generating = True
        
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.config(state=tk.NORMAL)
        
        if self.app and hasattr(self.app, 'txt2img_tab'):
            tab = self.app.txt2img_tab
            tab.set_prompt(self.uni_last_prompt, self.uni_last_negative)
            
            # 使用共享参数面板
            params = self.params.get_params()
            tab.set_params(
                steps=params["steps"],
                cfg=params["cfg"],
                seed=params["seed"],
                width=params["width"],
                height=params["height"],
                num_images=params["num_images"]
            )

            # 获取 ControlNet 状态
            use_controlnet = False
            if hasattr(self.app, 'img2img_tab') and hasattr(self.app.img2img_tab, 'use_controlnet_var'):
                use_controlnet = self.app.img2img_tab.use_controlnet_var.get()
            
            tab.use_controlnet = use_controlnet
                
            tab.generate()
            
            # ✅ 启动监控线程，检测生成完成
            import threading
            def monitor():
                import time
                while self.is_generating:
                    if not tab.is_generating:
                        self.app.root.after(0, self._on_generation_done)
                        break
                    if self.cancel_generation:
                        tab.cancel_generation = True
                        tab.is_generating = False
                        self.app.root.after(0, self._on_cancel_complete)
                        break
                    time.sleep(0.5)
            
            threading.Thread(target=monitor, daemon=True).start()
        else:
            messagebox.showwarning("提示", "文生图标签页未初始化")
            self.is_generating = False
            if hasattr(self, 'cancel_btn'):
                self.cancel_btn.config(state=tk.DISABLED)
    
    def _on_generation_done(self):
        """生成完成"""
        self.is_generating = False
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.config(state=tk.DISABLED)
        self.update_status("✅ 生成完成")
    
    def _on_cancel_complete(self):
        """取消完成"""
        self.is_generating = False
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.config(state=tk.DISABLED)
        self.update_status("⏹️ 已取消")
    
    def _cancel_generation(self):
        """取消生成"""
        self.cancel_generation = True
        self.is_generating = False
        self.update_status("⏹️ 正在取消...")
        
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.config(state=tk.DISABLED)
        
        # 也通知文生图取消
        if hasattr(self.app, 'txt2img_tab'):
            txt2img = self.app.txt2img_tab
            if txt2img and txt2img.is_generating:
                txt2img.cancel_generation = True
                txt2img.is_generating = False
    
    def _clear_result(self):
        """清空结果"""
        self.result_text.delete("1.0", tk.END)
        self.uni_last_prompt = ""
        self.uni_last_negative = ""
        self.update_status("已清空")
    
    def get_prompt(self) -> tuple:
        """获取当前提示词"""
        return self.uni_last_prompt, self.uni_last_negative

    def batch_generate(self, prompts):
        """批量生成（通用生成器）"""
        if self.is_generating:
            messagebox.showwarning("提示", "正在生成中，请等待完成")
            return
        
        if not self.uni_last_prompt:
            messagebox.showwarning("提示", "请先生成一个提示词")
            return
        
        # ✅ 直接使用当前提示词，重复生成多张
        prompts_list = [self.uni_last_prompt] * len(prompts)
        
        self._run_batch_generation(prompts_list)
    
    def _run_batch_generation(self, prompts_list):
        """运行批量生成"""
        if not prompts_list:
            return
        
        self.is_generating = True
        self.cancel_generation = False
        
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.config(state=tk.NORMAL)
        
        params = self.params.get_params()

        # 获取 ControlNet 状态
        use_controlnet = False
        if hasattr(self.app, 'img2img_tab') and hasattr(self.app.img2img_tab, 'use_controlnet_var'):
            use_controlnet = self.app.img2img_tab.use_controlnet_var.get()
            
        for idx, prompt in enumerate(prompts_list):
            if self.cancel_generation:
                break
            
            self.update_status(f"🔄 正在生成第 {idx+1}/{len(prompts_list)} 张...")
            
            if hasattr(self.app, 'txt2img_tab'):
                txt2img = self.app.txt2img_tab
                txt2img.set_prompt(prompt, self.uni_last_negative)
                
                seed = params["seed"]
                if seed == -1:
                    seed = random.randint(1, 2**32 - 1)
                seed = seed + idx
                
                # 传递 ControlNet 状态
                txt2img.use_controlnet = use_controlnet
            
                txt2img._generate_single_image(
                    prompt, self.uni_last_negative,
                    steps=params["steps"],
                    cfg=params["cfg"],
                    seed=seed,
                    height=params["height"],
                    width=params["width"],
                    index=idx+1,
                    total=len(prompts_list)
                )
            
            time.sleep(0.5)
        
        self.is_generating = False
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.config(state=tk.DISABLED)
        
        if self.cancel_generation:
            self.update_status("⏹️ 批量生成已取消")
        else:
            self.update_status("✅ 批量生成完成")