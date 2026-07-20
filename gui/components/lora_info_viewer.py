# gui/components/lora_info_viewer.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LoRA 信息查看器组件 - 紧凑布局
Keys 列表在信息框下方
"""

import tkinter as tk
from tkinter import ttk
import os
import threading
from datetime import datetime


class LoraInfoViewer:
    """LoRA 信息查看器 - Keys 在信息下方"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = None
        self._is_loading = False
        self._current_lora_path = None
        self._init_vars()
        self._create_widgets()
    
    def _init_vars(self):
        self.info_var = tk.StringVar(value="选择 LoRA 查看信息")
        self.status_var = tk.StringVar(value="就绪")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.lora_display_var = tk.StringVar(value="")



    def _create_widgets(self):
        """创建控件 - Keys 在信息下方"""
        self.frame = ttk.LabelFrame(self.parent, text="🔍 LoRA 信息查看器", padding=3)
        
        # ===== 第一行：选择 + 按钮（左对齐） =====
        row1 = ttk.Frame(self.frame)
        row1.pack(fill=tk.X, pady=1)
        
        ttk.Label(row1, text="选择:").pack(side=tk.LEFT, padx=2)
        
        # ✅ 固定宽度，不拉伸
        self.lora_combo = ttk.Combobox(
            row1,
            textvariable=self.lora_display_var,
            width=30,
            state="readonly"
        )
        self.lora_combo.pack(side=tk.LEFT, padx=2)  # 不再 fill=tk.X, expand=True
        self.lora_combo.bind('<<ComboboxSelected>>', self._on_lora_selected)
        
        ttk.Button(row1, text="🔍 分析", command=self._analyze_selected, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(row1, text="🔄", command=self._refresh_list, width=3).pack(side=tk.LEFT, padx=1)
        
        # ===== 第二行：兼容性状态 + 进度 =====
        row2 = ttk.Frame(self.frame)
        row2.pack(fill=tk.X, pady=1)
        
        self.compat_status_label = ttk.Label(
            row2,
            text="💡 选择 LoRA 查看兼容性",
            foreground="gray",
            font=("", 8)
        )
        self.compat_status_label.pack(side=tk.LEFT, padx=2)
        
        self.progress_bar = ttk.Progressbar(
            row2, 
            variable=self.progress_var, 
            maximum=100, 
            length=80,
            mode='determinate'
        )
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(
            row2, 
            textvariable=self.status_var, 
            foreground="blue",
            font=("", 8)
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # ===== 第三行：信息显示区域 =====
        info_container = ttk.Frame(self.frame)
        info_container.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # 上方：基本信息
        info_frame = ttk.LabelFrame(info_container, text="📋 信息", padding=2)
        info_frame.pack(fill=tk.X, pady=1)
        
        self.info_text = tk.Text(
            info_frame, 
            height=3,
            wrap=tk.WORD, 
            state=tk.DISABLED,
            font=("", 8),
            relief="flat",
            borderwidth=1
        )
        self.info_text.pack(fill=tk.X, pady=1)
        
        # 下方：Key 列表
        key_frame = ttk.LabelFrame(info_container, text="🔑 Keys", padding=2)
        key_frame.pack(fill=tk.BOTH, expand=True, pady=1)
        
        key_container = ttk.Frame(key_frame)
        key_container.pack(fill=tk.BOTH, expand=True)
        
        self.key_listbox = tk.Listbox(
            key_container, 
            height=4,
            font=("Consolas", 8),
            relief="flat",
            borderwidth=1
        )
        key_scrollbar_y = ttk.Scrollbar(
            key_container, 
            orient=tk.VERTICAL, 
            command=self.key_listbox.yview
        )
        key_scrollbar_x = ttk.Scrollbar(
            key_container, 
            orient=tk.HORIZONTAL, 
            command=self.key_listbox.xview
        )
        self.key_listbox.configure(
            yscrollcommand=key_scrollbar_y.set,
            xscrollcommand=key_scrollbar_x.set
        )
        self.key_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        key_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        key_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # ===== 第四行：操作按钮（左对齐） =====
        row4 = ttk.Frame(self.frame)
        row4.pack(fill=tk.X, pady=1)
        
        ttk.Button(row4, text="📋 复制信息", command=self._copy_info, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(row4, text="📋 复制 Keys", command=self._copy_keys, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(row4, text="📂 打开目录", command=self._open_folder, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(row4, text="🗑️ 清空", command=self._clear_info, width=8).pack(side=tk.LEFT, padx=2)
        
        # 初始化列表
        self._refresh_list()
        
    def _refresh_list(self):
        """从主界面刷新 LoRA 列表，并同步当前选择"""
        if not hasattr(self.app, 'lora_files') or not self.app.lora_files:
            self.lora_combo['values'] = []
            self.lora_combo.set("")
            self.status_var.set("无 LoRA")
            self.compat_status_label.config(text="💡 没有可用的 LoRA", foreground="gray")
            return
        
        current_values = list(self.lora_combo['values'])
        new_values = self.app.lora_files
        
        # 更新下拉列表
        if current_values != new_values:
            self.lora_combo['values'] = new_values
        
        # ✅ 同步主界面的 LoRA 选择
        main_lora = self.app.lora_var.get() if hasattr(self.app, 'lora_var') else ""
        
        # 检查主界面选择的 LoRA 是否在当前列表中
        current_display = self.lora_display_var.get()
        
        if main_lora and main_lora in new_values:
            if current_display != main_lora:
                self.lora_combo.set(main_lora)
                self.lora_display_var.set(main_lora)
                self._analyze_selected()
        elif main_lora and main_lora not in new_values:
            if new_values:
                self.lora_combo.set(new_values[0])
                self.lora_display_var.set(new_values[0])
                self._analyze_selected()
            else:
                self.lora_combo.set("")
                self.status_var.set("无匹配 LoRA")
        elif not main_lora and new_values and not current_display:
            self.lora_combo.set(new_values[0])
            self.lora_display_var.set(new_values[0])
            self._analyze_selected()
        
        count = len(new_values)
        self.status_var.set(f"{count} 个")
    
    def _on_lora_selected(self, event):
        """选择 LoRA 时自动分析"""
        self._analyze_selected()
    
    def _analyze_selected(self):
        """分析当前选中的 LoRA"""
        display_name = self.lora_display_var.get()
        if not display_name:
            self.status_var.set("请选择")
            self.compat_status_label.config(text="💡 请选择一个 LoRA", foreground="gray")
            return
        
        if display_name not in self.app.lora_paths:
            self.status_var.set("路径不存在")
            self.compat_status_label.config(text="❌ 路径不存在", foreground="red")
            return
        
        file_path = self.app.lora_paths[display_name]
        lora_type = self.app.lora_types.get(display_name, 'unknown')
        
        if not os.path.exists(file_path):
            self.status_var.set("文件不存在")
            self.compat_status_label.config(text="❌ 文件不存在", foreground="red")
            return
        
        self._current_lora_path = file_path
        self._update_compat_status(display_name, lora_type)
        self._analyze_lora(file_path)
    
    def _update_compat_status(self, display_name: str, lora_type: str):
        """更新兼容性状态显示"""
        if not self.app.model_manager.is_sd_loaded:
            self.compat_status_label.config(
                text="⚠️ 模型未加载",
                foreground="orange"
            )
            return
        
        current_model_type = self.app.model_manager.get_sd_model_type()
        lora_type_clean = lora_type.lower()
        model_type_clean = current_model_type.lower()
        
        if '双兼容' in lora_type or 'both' in lora_type_clean:
            self.compat_status_label.config(
                text="✅ 双兼容 (SD1.5 + SDXL)",
                foreground="green"
            )
        elif lora_type_clean == 'unknown' or lora_type == '未知':
            self.compat_status_label.config(
                text=f"❓ 类型未知 (模型: {current_model_type.upper()})",
                foreground="gray"
            )
        elif ('sdxl' in lora_type_clean or 'sdxl' in lora_type.lower()) and model_type_clean == 'sdxl':
            self.compat_status_label.config(
                text=f"✅ 兼容 (SDXL)",
                foreground="green"
            )
        elif ('sd15' in lora_type_clean or 'sd1.5' in lora_type.lower()) and model_type_clean == 'sd15':
            self.compat_status_label.config(
                text=f"✅ 兼容 (SD1.5)",
                foreground="green"
            )
        elif 'sdxl' in lora_type_clean or 'sd1.5' in lora_type_clean:
            short_type = "SDXL" if 'sdxl' in lora_type_clean else "SD1.5"
            self.compat_status_label.config(
                text=f"❌ 不兼容 ({short_type} ↔ {current_model_type.upper()})",
                foreground="red"
            )
        else:
            self.compat_status_label.config(
                text=f"❓ 类型未知 (模型: {current_model_type.upper()})",
                foreground="gray"
            )
    
    def _analyze_lora(self, file_path=None):
        """分析 LoRA 文件"""
        if file_path is None:
            file_path = self._current_lora_path
        
        if not file_path or not os.path.exists(file_path):
            self.status_var.set("文件无效")
            return
        
        if self._is_loading:
            return
        
        self._is_loading = True
        self.status_var.set("分析中...")
        self.progress_var.set(0)
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", "⏳ 加载中...")
        self.info_text.config(state=tk.DISABLED)
        self.key_listbox.delete(0, tk.END)
        
        threading.Thread(target=self._analyze_thread, args=(file_path,), daemon=True).start()
    
    def _analyze_thread(self, file_path):
        """后台分析线程"""
        try:
            import safetensors.torch
            
            self.app.root.after(0, lambda: self.progress_var.set(20))
            
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            file_name = os.path.basename(file_path)
            file_dir = os.path.dirname(file_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
            
            self.app.root.after(0, lambda: self.progress_var.set(40))
            
            data = safetensors.torch.load_file(file_path)
            keys = list(data.keys())
            total_keys = len(keys)
            
            self.app.root.after(0, lambda: self.progress_var.set(60))
            
            lora_type = self._detect_lora_type(keys)
            dim_info = self._analyze_dimensions(data, keys)
            
            self.app.root.after(0, lambda: self.progress_var.set(80))
            
            # 构建信息（紧凑，多行显示）
            info_lines = []
            info_lines.append(f"📁 {file_name}")
            info_lines.append(f"📏 {file_size_mb:.1f}MB | 🔑 {total_keys} keys")
            info_lines.append(f"🏷️ {lora_type}")
            
            if dim_info:
                rank = dim_info.get("LoRA Rank", "?")
                info_lines.append(f"📊 Rank: {rank}")
            
            # ✅ 兼容性判断
            if self.app.model_manager.is_sd_loaded:
                current_type = self.app.model_manager.get_sd_model_type()
                
                if '双兼容' in lora_type:
                    info_lines.append("✅ 兼容当前模型 (双兼容)")
                elif "SDXL" in lora_type and current_type == "sdxl":
                    info_lines.append("✅ 兼容当前模型")
                elif "SD1.5" in lora_type and current_type == "sd15":
                    info_lines.append("✅ 兼容当前模型")
                elif "SDXL" in lora_type or "SD1.5" in lora_type:
                    info_lines.append(f"❌ 不兼容 ({current_type.upper()})")
                else:
                    info_lines.append(f"❓ 类型未知")
            
            self.app.root.after(0, lambda: self._update_info(info_lines, keys))
            self.app.root.after(0, lambda: self.progress_var.set(100))
            self.app.root.after(0, lambda: self.status_var.set("✅ 完成"))
            
        except Exception as e:
            self.app.root.after(0, lambda: self._show_error(str(e)))
        
        finally:
            self.app.root.after(0, lambda: setattr(self, '_is_loading', False))
    
    def _detect_lora_type(self, keys: list) -> str:
        """检测 LoRA 类型（与 ModelManager._detect_lora_type 保持一致）"""
        if not keys:
            return '未知'
        
        sdxl_patterns = [
            'base_unet',
            'lora_te1',
            'text_encoder',
            'time_embedding',
            'transformer_blocks',
        ]
        
        sd15_patterns = [
            'lora_unet',
            'lora_te',
            'down_blocks',
            'up_blocks',
            'mid_block',
        ]
        
        keys_str = " ".join(keys).lower()
        
        sdxl_score = sum(1 for p in sdxl_patterns if p in keys_str)
        sd15_score = sum(1 for p in sd15_patterns if p in keys_str)
        
        has_sdxl_dim = any(k.startswith('base_unet') or k.startswith('lora_te1') for k in keys)
        has_sd15_dim = any(k.startswith('lora_unet') or k.startswith('lora_te') for k in keys)
        
        if (has_sdxl_dim and has_sd15_dim) or (sdxl_score >= 2 and sd15_score >= 2):
            return "双兼容 ⭐ (SD1.5/SDXL)"
        
        if has_sdxl_dim or (sdxl_score > sd15_score and sdxl_score >= 2):
            return "SDXL ⭐"
        elif has_sd15_dim or (sd15_score > sdxl_score and sd15_score >= 2):
            return "SD1.5"
        else:
            return "未知"
    
    def _analyze_dimensions(self, data: dict, keys: list) -> dict:
        """分析维度信息"""
        dim_info = {}
        
        rank_values = []
        for k in keys:
            if 'lora_down' in k or 'lora_up' in k:
                tensor = data[k]
                if len(tensor.shape) >= 2:
                    rank_values.append(min(tensor.shape))
        
        if rank_values:
            from collections import Counter
            rank_counter = Counter(rank_values)
            most_common_rank = rank_counter.most_common(1)
            if most_common_rank:
                dim_info["LoRA Rank"] = most_common_rank[0][0]
        
        return dim_info
    
    def _update_info(self, info_lines: list, keys: list):
        """更新信息显示"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", "\n".join(info_lines))
        self.info_text.config(state=tk.DISABLED)
        
        # 更新 Key 列表（显示完整 key，使用横向滚动）
        self.key_listbox.delete(0, tk.END)
        for i, key in enumerate(keys[:20]):
            self.key_listbox.insert(tk.END, f"{i+1:2d}. {key}")
        
        if len(keys) > 20:
            self.key_listbox.insert(tk.END, f"   ... 共 {len(keys)} 个")
    
    def _show_error(self, error_msg: str):
        """显示错误"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", f"❌ {error_msg[:60]}")
        self.info_text.config(state=tk.DISABLED)
        self.status_var.set("❌ 失败")
        self.progress_var.set(0)
    
    def _copy_info(self):
        """复制信息到剪贴板"""
        content = self.info_text.get("1.0", tk.END).strip()
        if content and not content.startswith("⏳") and not content.startswith("❌"):
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(content)
            self.status_var.set("✅ 已复制")
    
    def _copy_keys(self):
        """复制 Key 列表到剪贴板"""
        keys = []
        for i in range(self.key_listbox.size()):
            item = self.key_listbox.get(i)
            keys.append(item)
        
        if keys:
            content = "\n".join(keys)
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(content)
            self.status_var.set("✅ Keys 已复制")
    
    def _open_folder(self):
        """打开文件所在目录"""
        file_path = self._current_lora_path
        if file_path and os.path.exists(file_path):
            folder = os.path.dirname(file_path)
            import sys
            if sys.platform == 'win32':
                os.startfile(folder)
            else:
                import subprocess
                subprocess.run(['open', folder] if sys.platform == 'darwin' else ['xdg-open', folder])
    
    def _clear_info(self):
        """清空信息"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", "选择 LoRA 查看信息")
        self.info_text.config(state=tk.DISABLED)
        self.key_listbox.delete(0, tk.END)
        self.compat_status_label.config(text="💡 选择 LoRA 查看兼容性", foreground="gray")
        self.status_var.set("已清空")
        self.progress_var.set(0)
        self._current_lora_path = None
    
    def get_frame(self):
        return self.frame