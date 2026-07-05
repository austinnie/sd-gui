#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量生成面板 - 支持最多10组参数的批量文生图
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import time
import random


class BatchPanel:
    """批量生成面板"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = None
        self.start_callback = None
        
        # 批量状态
        self.batch_running = False
        self.batch_prompts = []
        self.batch_negs = []
        self.batch_current = 0
        self.batch_total = 0
        
        # 最多支持10组
        self.MAX_BATCH = 10
        
        # 进度变量
        self.batch_progress_var = tk.StringVar(value="就绪")
        self.batch_progress_bar = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建控件"""
        self.frame = ttk.LabelFrame(self.parent, text="📦 批量生成 (最多10组)", padding=5)
        
        row = 0
        
        # ===== 工具栏 =====
        toolbar = ttk.Frame(self.frame)
        toolbar.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=3, padx=3)
        
        ttk.Button(toolbar, text="📂 加载提示词", command=self._load_prompts).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 加载负面词", command=self._load_negatives).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 保存配置", command=self._save_prompts).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ 清空", command=self._clear_all).pack(side=tk.LEFT, padx=2)
        
        # 组数显示（右侧）
        self.count_label = ttk.Label(toolbar, text="组数: 0/10", foreground="blue")
        self.count_label.pack(side=tk.RIGHT, padx=10)
        
        row += 1
        
        # ===== 双列输入区域 =====
        input_frame = ttk.Frame(self.frame)
        input_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        # 正面提示词列
        pos_frame = ttk.LabelFrame(input_frame, text="正面提示词 (每行一组)", padding=3)
        pos_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        
        self.prompt_text = tk.Text(pos_frame, height=6, width=40, wrap=tk.WORD)
        self.prompt_text.pack(fill=tk.BOTH, expand=True)
        self.prompt_text.insert("1.0", self._get_default_prompts())
        self.prompt_text.bind("<KeyRelease>", self._update_count)
        
        # 负面提示词列
        neg_frame = ttk.LabelFrame(input_frame, text="负面提示词 (每行对应)", padding=3)
        neg_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2)
        
        self.neg_text = tk.Text(neg_frame, height=6, width=40, wrap=tk.WORD)
        self.neg_text.pack(fill=tk.BOTH, expand=True)
        self.neg_text.insert("1.0", self._get_default_negatives())
        self.neg_text.bind("<KeyRelease>", self._update_count)
        
        row += 1
        
        # ===== 进度和控制栏 =====
        control_frame = ttk.Frame(self.frame)
        control_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=3)
        
        # 状态标签
        self.status_label = ttk.Label(control_frame, textvariable=self.batch_progress_var, foreground="blue")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.batch_progress_bar = ttk.Progressbar(control_frame, length=250, mode='determinate')
        self.batch_progress_bar.pack(side=tk.LEFT, padx=10)
        
        # 控制按钮（右侧）
        btn_container = ttk.Frame(control_frame)
        btn_container.pack(side=tk.RIGHT, padx=5)
        
        self.batch_start_btn = ttk.Button(btn_container, text="▶ 开始批量", command=self._start_batch)
        self.batch_start_btn.pack(side=tk.LEFT, padx=3)
        
        self.batch_stop_btn = ttk.Button(btn_container, text="⏹️ 停止", command=self._stop_batch, state=tk.DISABLED)
        self.batch_stop_btn.pack(side=tk.LEFT, padx=3)
        
        # 结果显示
        self.result_label = ttk.Label(btn_container, text="", foreground="green")
        self.result_label.pack(side=tk.LEFT, padx=10)
        
        self._update_count()
        
        return self.frame
    
    def _get_default_prompts(self) -> str:
        """获取默认提示词"""
        return """masterpiece, best quality, realistic, 8k, a beautiful asian woman, full body shot
masterpiece, best quality, realistic, 8k, a beautiful asian woman, full body shot
masterpiece, best quality, realistic, 8k, a beautiful asian woman, full body shot"""
    
    def _get_default_negatives(self) -> str:
        """获取默认负面词"""
        return "worst quality, low quality, ugly, deformed, blurry"
    
    def _update_count(self, event=None):
        """更新组数显示"""
        prompts = self._get_prompts_list()
        count = len(prompts)
        color = "red" if count > self.MAX_BATCH else "blue"
        self.count_label.config(text=f"组数: {count}/{self.MAX_BATCH}", foreground=color)
        
        if count > self.MAX_BATCH:
            self.batch_progress_var.set(f"⚠️ 超过限制！最多 {self.MAX_BATCH} 组")
            self.batch_start_btn.config(state=tk.DISABLED)
        else:
            if not self.batch_running:
                self.batch_start_btn.config(state=tk.NORMAL if count > 0 else tk.DISABLED)
            if count == 0:
                self.batch_progress_var.set("请至少输入1组提示词")
            elif count > 0:
                self.batch_progress_var.set(f"就绪 - 共 {count} 组")
    
    def _get_prompts_list(self) -> list:
        """获取提示词列表"""
        text = self.prompt_text.get("1.0", tk.END).strip()
        prompts = [p.strip() for p in text.split('\n') if p.strip()]
        return prompts[:self.MAX_BATCH]
    
    def _get_negatives_list(self) -> list:
        """获取负面词列表"""
        text = self.neg_text.get("1.0", tk.END).strip()
        negatives = [n.strip() for n in text.split('\n') if n.strip()]
        return negatives
    
    def _load_prompts(self):
        """加载提示词文件"""
        filepath = filedialog.askopenfilename(
            title="选择正面提示词文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.prompt_text.delete("1.0", tk.END)
                self.prompt_text.insert("1.0", content)
                self._update_count()
                self.batch_progress_var.set(f"✅ 已加载: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {e}")
    
    def _load_negatives(self):
        """加载负面词文件"""
        filepath = filedialog.askopenfilename(
            title="选择负面提示词文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.neg_text.delete("1.0", tk.END)
                self.neg_text.insert("1.0", content)
                self.batch_progress_var.set(f"✅ 已加载: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {e}")
    
    def _save_prompts(self):
        """保存提示词到文件"""
        filepath = filedialog.asksaveasfilename(
            title="保存提示词",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filepath:
            try:
                content = self.prompt_text.get("1.0", tk.END).strip()
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.batch_progress_var.set(f"✅ 已保存到 {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")
    
    def _clear_all(self):
        """清空所有"""
        self.prompt_text.delete("1.0", tk.END)
        self.neg_text.delete("1.0", tk.END)
        self.batch_progress_var.set("已清空")
        self.result_label.config(text="")
        self._update_count()
    
    def set_start_callback(self, callback):
        """设置批量开始回调"""
        self.start_callback = callback
    
    def get_prompts(self):
        """获取正面提示词列表"""
        return self._get_prompts_list()
    
    def get_negatives(self):
        """获取负面词列表"""
        return self._get_negatives_list()
    
    def _start_batch(self):
        """开始批量生成 - 调用回调"""
        if self.batch_running:
            return
        
        prompts = self._get_prompts_list()
        if not prompts:
            messagebox.showwarning("提示", "请至少输入一组提示词")
            return
        
        if len(prompts) > self.MAX_BATCH:
            messagebox.showwarning("提示", f"最多支持 {self.MAX_BATCH} 组")
            return
        
        # 更新 UI 状态
        self.batch_running = True
        self.batch_start_btn.config(state=tk.DISABLED)
        self.batch_stop_btn.config(state=tk.NORMAL)
        self.batch_progress_bar['maximum'] = len(prompts)
        self.batch_progress_bar['value'] = 0
        self.result_label.config(text="")
        self.batch_progress_var.set(f"🚀 开始批量生成，共 {len(prompts)} 组...")
        
        # ✅ 调用回调，由 app 决定使用哪个 Tab
        if self.start_callback:
            self.start_callback(prompts)
    
    def _stop_batch(self):
        """停止批量生成"""
        self.batch_running = False
        
        # 取消文生图的生成
        if hasattr(self.app, 'txt2img_tab') and self.app.txt2img_tab:
            self.app.txt2img_tab.cancel_generation = True
        
        self.batch_stop_btn.config(state=tk.DISABLED)
        self.batch_progress_var.set("⏹️ 正在停止...")
    
    def get_frame(self):
        """获取框架"""
        return self.frame