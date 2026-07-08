#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LoRA 管理标签页 - 集成分析、筛选、重命名、同步功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import shutil
import re
from datetime import datetime
from collections import defaultdict

from .base_tab import BaseTab
from gui.components.memory_monitor import force_memory_cleanup


class LoraManagerTab(BaseTab):
    """LoRA 管理标签页"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._init_vars()
        self.setup_ui()
        self._scan_lora_files()
    
    def _init_vars(self):
        """初始化变量"""
        self.image_dir_var = tk.StringVar(value="output/all_images")
        self.output_file_var = tk.StringVar(value="output/high_sex_lora_list.txt")
        self.extract_dir_var = tk.StringVar(value="output/selected_high_loras")
        self.top_k_var = tk.IntVar(value=30)
        
        # 模型目录
        self.models_root_var = tk.StringVar(value=r"E:\SD_OpenVINO\models")
        self.test_lora_dir_var = tk.StringVar(value=r"E:\SD_OpenVINO\models\test_lora")
        self.sd15_lora_dir_var = tk.StringVar(value=r"E:\SD_OpenVINO\models\sd15-lora")
        self.sdxl_lora_dir_var = tk.StringVar(value=r"E:\SD_OpenVINO\models\sdxl-lora")
        
        # 状态
        self.is_scanning = False
        self.is_processing = False
        self.cancel_operation = False
        
        # 数据
        self.lora_scores = []
        self.top_loras = []
        self.lora_files = []
    
    def setup_ui(self):
        """设置 UI"""
        frame = self.frame
        row = 0
        
        # ===== 标题 =====
        title = ttk.Label(frame, text="🔧 LoRA 管理工具", font=("", 14, "bold"))
        title.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=10, padx=5)
        row += 1
        
        # ===== 路径配置 =====
        path_frame = ttk.LabelFrame(frame, text="📁 路径配置", padding=5)
        path_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # 图片目录
        ttk.Label(path_frame, text="图片目录:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(path_frame, textvariable=self.image_dir_var, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(path_frame, text="浏览", command=lambda: self._browse_dir(self.image_dir_var)).grid(row=0, column=2, padx=5)
        
        # 输出文件
        ttk.Label(path_frame, text="输出列表:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(path_frame, textvariable=self.output_file_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Top K
        ttk.Label(path_frame, text="Top K:").grid(row=1, column=2, sticky=tk.E, padx=5)
        ttk.Spinbox(path_frame, from_=10, to=100, textvariable=self.top_k_var, width=8).grid(row=1, column=3, padx=5)
        
        # 提取目录
        ttk.Label(path_frame, text="提取目录:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(path_frame, textvariable=self.extract_dir_var, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        
        row += 1
        
        # ===== 模型目录配置 =====
        model_frame = ttk.LabelFrame(frame, text="📂 模型目录配置", padding=5)
        model_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(model_frame, text="Models 根目录:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.models_root_var, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(model_frame, text="浏览", command=lambda: self._browse_dir(self.models_root_var)).grid(row=0, column=2, padx=5)
        
        ttk.Label(model_frame, text="test_lora 目录:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.test_lora_dir_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Label(model_frame, text="sd15-lora 目录:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.sd15_lora_dir_var, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Label(model_frame, text="sdxl-lora 目录:").grid(row=3, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.sdxl_lora_dir_var, width=50).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        
        row += 1
        
        # ===== 操作按钮 =====
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=10)
        row += 1
        
        ttk.Button(btn_frame, text="🔍 扫描分析", command=self._start_scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📋 显示排行", command=self._show_ranking).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📂 提取高分", command=self._extract_high_loras).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 过滤删除", command=self._filter_low_loras).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📝 重命名", command=self._rename_loras).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 同步目录", command=self._sync_loras).pack(side=tk.LEFT, padx=5)
        
        # 取消按钮
        self.cancel_btn = ttk.Button(btn_frame, text="⏹️ 取消", command=self._cancel_operation, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # ===== 状态栏 =====
        status_frame = ttk.Frame(frame)
        status_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(status_frame, length=300, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        
        row += 1
        
        # ===== LoRA 列表 =====
        list_frame = ttk.LabelFrame(frame, text="📋 LoRA 列表", padding=5)
        list_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        
        # 列表 + 滚动条
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(
            list_container,
            columns=("rank", "name", "score", "size_mb", "status"),
            show="headings",
            height=12
        )
        
        self.tree.heading("rank", text="排名")
        self.tree.heading("name", text="LoRA 名称")
        self.tree.heading("score", text="评分")
        self.tree.heading("size_mb", text="大小 (MB)")
        self.tree.heading("status", text="状态")
        
        self.tree.column("rank", width=50, anchor=tk.CENTER)
        self.tree.column("name", width=300, anchor=tk.W)
        self.tree.column("score", width=80, anchor=tk.CENTER)
        self.tree.column("size_mb", width=80, anchor=tk.CENTER)
        self.tree.column("status", width=80, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右键菜单
        self._create_context_menu()
        
        row += 1
        
        # ===== 日志区域 =====
        log_frame = ttk.LabelFrame(frame, text="📝 操作日志", padding=5)
        log_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.log_text = tk.Text(log_frame, height=6, width=70, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 设置行权重
        frame.rowconfigure(row, weight=1)
        frame.columnconfigure(1, weight=1)
    
    def _create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="📋 复制名称", command=self._copy_selected_name)
        self.context_menu.add_command(label="📂 打开所在目录", command=self._open_selected_dir)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _copy_selected_name(self):
        """复制选中的名称"""
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0], "values")
            if values and len(values) > 1:
                self.app.root.clipboard_clear()
                self.app.root.clipboard_append(values[1])
                self._append_log(f"📋 已复制: {values[1]}")
    
    def _open_selected_dir(self):
        """打开选中文件的所在目录"""
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0], "values")
            if values and len(values) > 1:
                name = values[1]
                # 在 test_lora 目录中查找
                test_dir = self.test_lora_dir_var.get()
                if os.path.exists(test_dir):
                    for f in os.listdir(test_dir):
                        if name in f and f.endswith('.safetensors'):
                            path = os.path.join(test_dir, f)
                            if os.path.exists(path):
                                try:
                                    os.startfile(os.path.dirname(path))
                                except:
                                    pass
                                return
    
    def _browse_dir(self, var):
        """浏览目录"""
        dir_path = filedialog.askdirectory(title="选择目录")
        if dir_path:
            var.set(dir_path)
    
    def _scan_lora_files(self):
        """扫描 test_lora 目录中的文件"""
        test_dir = self.test_lora_dir_var.get()
        if os.path.exists(test_dir):
            self.lora_files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
    
    # ==================== 核心功能 ====================
    
    def _start_scan(self):
        """开始扫描分析"""
        if self.is_scanning:
            return
        
        image_dir = self.image_dir_var.get()
        if not os.path.exists(image_dir):
            messagebox.showwarning("提示", f"图片目录不存在: {image_dir}")
            return
        
        self.is_scanning = True
        self.cancel_operation = False
        self._set_buttons_state(tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_bar.config(value=0, maximum=100)
        
        self._append_log("🔍 开始扫描分析...")
        self.status_var.set("扫描中...")
        
        threading.Thread(target=self._run_scan, daemon=True).start()
    
    def _run_scan(self):
        """后台运行扫描"""
        try:
            import torch
            from PIL import Image
            import open_clip
            
            image_dir = self.image_dir_var.get()
            top_k = self.top_k_var.get()
            
            self._append_log("📦 正在加载 CLIP 模型...")
            
            model, _, preprocess = open_clip.create_model_and_transforms(
                'ViT-B-32', pretrained='laion2b_s34b_b79k'
            )
            tokenizer = open_clip.get_tokenizer('ViT-B-32')
            
            positive_texts = [
                "a sexy woman", "a beautiful woman", "large breasts", 
                "seductive pose", "hot female"
            ]
            negative_texts = [
                "a man", "a boy", "a child", "ugly", "clothed in heavy coat"
            ]
            
            with torch.no_grad():
                pos_tokens = tokenizer(positive_texts)
                pos_embeddings = model.encode_text(pos_tokens)
                pos_embeddings /= pos_embeddings.norm(dim=-1, keepdim=True)
                positive_score = pos_embeddings.mean(dim=0)
                
                neg_tokens = tokenizer(negative_texts)
                neg_embeddings = model.encode_text(neg_tokens)
                neg_embeddings /= neg_embeddings.norm(dim=-1, keepdim=True)
                negative_score = neg_embeddings.mean(dim=0)
            
            self._append_log(f"📁 扫描目录: {image_dir}")
            
            files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            total = len(files)
            
            lora_scores = defaultdict(list)
            
            for idx, filename in enumerate(files):
                if self.cancel_operation:
                    self._append_log("⏹️ 已取消扫描")
                    break
                
                # 更新进度
                progress = (idx + 1) / total * 100
                self.app.root.after(0, lambda p=progress: self.progress_bar.config(value=p))
                
                if idx % 10 == 0:
                    self.app.root.after(0, lambda i=idx, t=total: 
                        self.status_var.set(f"扫描中... {i+1}/{t}"))
                
                try:
                    image_path = os.path.join(image_dir, filename)
                    image = preprocess(Image.open(image_path).convert('RGB')).unsqueeze(0)
                    
                    with torch.no_grad():
                        image_features = model.encode_image(image)
                        image_features /= image_features.norm(dim=-1, keepdim=True)
                        score = (image_features @ positive_score).item() - (image_features @ negative_score).item()
                        
                        lora_name = filename.split('_')[0] if '_' in filename else filename
                        lora_scores[lora_name].append(score)
                except Exception as e:
                    continue
            
            if self.cancel_operation:
                return
            
            # 计算平均分
            avg_scores = {k: sum(v)/len(v) for k, v in lora_scores.items()}
            sorted_loras = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
            
            self.lora_scores = sorted_loras
            self.top_loras = [name for name, _ in sorted_loras[:top_k]]
            
            # 保存列表
            output_file = self.output_file_var.get()
            os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== 高分 LoRA 排行 ===\n\n")
                for i, (lora, score) in enumerate(sorted_loras[:top_k], 1):
                    f.write(f"{i:02d}. {lora} (评分: {score:.4f})\n")
            
            self._append_log(f"✅ 扫描完成！共 {len(sorted_loras)} 个 LoRA")
            self._append_log(f"📄 列表已保存: {output_file}")
            
            # 更新列表
            self.app.root.after(0, self._update_tree)
            
        except Exception as e:
            self._append_log(f"❌ 扫描失败: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.is_scanning = False
            self.app.root.after(0, self._reset_ui)
    
    def _update_tree(self):
        """更新树形列表"""
        self.tree.delete(*self.tree.get_children())
        
        test_dir = self.test_lora_dir_var.get()
        test_files = set(os.listdir(test_dir)) if os.path.exists(test_dir) else set()
        
        for i, (name, score) in enumerate(self.lora_scores[:100], 1):
            # 检查文件是否存在
            size_mb = 0
            status = "❌ 未找到"
            
            for f in test_files:
                if name in f and f.endswith('.safetensors'):
                    size_mb = os.path.getsize(os.path.join(test_dir, f)) / (1024 * 1024)
                    status = "✅ 存在"
                    break
            
            # 是否在 Top K 中
            if i <= self.top_k_var.get():
                status = "⭐ " + status
            
            self.tree.insert("", tk.END, values=(i, name[:60], f"{score:.4f}", f"{size_mb:.1f}", status))
    
    def _show_ranking(self):
        """显示排行"""
        if not self.lora_scores:
            messagebox.showinfo("提示", "请先运行扫描分析")
            return
        
        self._update_tree()
        self._append_log(f"📋 显示排行，共 {len(self.lora_scores)} 个 LoRA")
    
    def _extract_high_loras(self):
        """提取高分 LoRA 图片"""
        if not self.top_loras:
            messagebox.showinfo("提示", "请先运行扫描分析")
            return
        
        if not messagebox.askyesno("确认提取",
            f"将复制前 {self.top_k_var.get()} 个 LoRA 的图片到:\n{self.extract_dir_var.get()}\n\n确定继续吗？"
        ):
            return
        
        self._start_operation("📂 提取高分 LoRA...")
        threading.Thread(target=self._run_extract, daemon=True).start()
    
    def _run_extract(self):
        """后台运行提取"""
        try:
            image_dir = self.image_dir_var.get()
            extract_dir = self.extract_dir_var.get()
            top_k = self.top_k_var.get()
            
            os.makedirs(extract_dir, exist_ok=True)
            
            files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            copied = 0
            
            for idx, filename in enumerate(files):
                if self.cancel_operation:
                    break
                
                candidate_name = filename.split('_')[0]
                if candidate_name in self.top_loras:
                    src = os.path.join(image_dir, filename)
                    dst = os.path.join(extract_dir, filename)
                    shutil.copy2(src, dst)
                    copied += 1
                
                if idx % 10 == 0:
                    self.app.root.after(0, lambda i=idx, t=len(files): 
                        self.progress_bar.config(value=(i+1)/len(files)*100))
            
            self._append_log(f"✅ 提取完成！共复制 {copied} 张图片到 {extract_dir}")
            
        except Exception as e:
            self._append_log(f"❌ 提取失败: {e}")
        finally:
            self._reset_ui()
    
    def _filter_low_loras(self):
        """过滤低分 LoRA"""
        if not self.lora_scores:
            messagebox.showinfo("提示", "请先运行扫描分析")
            return
        
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            messagebox.showwarning("提示", f"目录不存在: {test_dir}")
            return
        
        # 获取要保留的名称
        keep_names = set(self.top_loras)
        
        # 扫描文件
        files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
        to_delete = []
        
        for filename in files:
            kept = False
            for name in keep_names:
                if name in filename:
                    kept = True
                    break
            if not kept:
                to_delete.append(filename)
        
        if not to_delete:
            messagebox.showinfo("提示", "没有需要删除的文件")
            return
        
        # 确认
        if not messagebox.askyesno("确认删除",
            f"将删除 {len(to_delete)} 个低分 LoRA 文件\n\n"
            f"保留: {len(keep_names)} 个\n"
            f"删除: {len(to_delete)} 个\n\n"
            f"确定继续吗？"
        ):
            return
        
        self._start_operation("🗑️ 过滤低分 LoRA...")
        threading.Thread(target=self._run_filter, args=(to_delete,), daemon=True).start()
    
    def _run_filter(self, to_delete):
        """后台运行过滤"""
        try:
            test_dir = self.test_lora_dir_var.get()
            deleted = 0
            
            for idx, filename in enumerate(to_delete):
                if self.cancel_operation:
                    break
                
                filepath = os.path.join(test_dir, filename)
                try:
                    os.remove(filepath)
                    deleted += 1
                    if idx % 5 == 0:
                        self._append_log(f"   🗑️ 已删除: {filename}")
                except Exception as e:
                    self._append_log(f"   ❌ 删除失败 {filename}: {e}")
                
                self.app.root.after(0, lambda i=idx, t=len(to_delete): 
                    self.progress_bar.config(value=(i+1)/t*100))
            
            self._append_log(f"✅ 过滤完成！共删除 {deleted} 个文件")
            
        except Exception as e:
            self._append_log(f"❌ 过滤失败: {e}")
        finally:
            self._reset_ui()
            self._scan_lora_files()
            self._update_tree()
    
    def _rename_loras(self):
        """重命名 LoRA 文件"""
        if not self.top_loras:
            messagebox.showinfo("提示", "请先运行扫描分析")
            return
        
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            messagebox.showwarning("提示", f"目录不存在: {test_dir}")
            return
        
        if not messagebox.askyesno("确认重命名",
            f"将按排名重命名 test_lora 目录中的文件\n\n"
            f"共 {len(self.top_loras)} 个文件\n"
            f"格式: 01_xxx.safetensors\n\n"
            f"确定继续吗？"
        ):
            return
        
        self._start_operation("📝 重命名 LoRA...")
        threading.Thread(target=self._run_rename, daemon=True).start()
    
    def _run_rename(self):
        """后台运行重命名"""
        try:
            test_dir = self.test_lora_dir_var.get()
            files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
            
            renamed = 0
            skipped = 0
            
            for idx, target_name in enumerate(self.top_loras, 1):
                if self.cancel_operation:
                    break
                
                # 清理名称
                clean_name = re.sub(r'[\\/*?:"<>|]', '_', target_name)
                new_filename = f"{idx:02d}_{clean_name}.safetensors"
                new_path = os.path.join(test_dir, new_filename)
                
                if os.path.exists(new_path):
                    skipped += 1
                    continue
                
                found = False
                for old_filename in files:
                    if old_filename.startswith(f"{idx:02d}_"):
                        found = True
                        break
                    if target_name in old_filename:
                        old_path = os.path.join(test_dir, old_filename)
                        try:
                            os.rename(old_path, new_path)
                            renamed += 1
                            found = True
                            files.remove(old_filename)
                            self._append_log(f"   ✅ [{idx:02d}] {old_filename} -> {new_filename}")
                            break
                        except Exception as e:
                            self._append_log(f"   ❌ 重命名失败: {e}")
                
                if not found:
                    self._append_log(f"   ⚠️ [{idx:02d}] 未找到匹配: {target_name}")
                    skipped += 1
                
                self.app.root.after(0, lambda i=idx, t=len(self.top_loras): 
                    self.progress_bar.config(value=(i+1)/t*100))
            
            self._append_log(f"✅ 重命名完成！成功: {renamed}, 跳过: {skipped}")
            
        except Exception as e:
            self._append_log(f"❌ 重命名失败: {e}")
        finally:
            self._reset_ui()
            self._scan_lora_files()
            self._update_tree()
    
    def _sync_loras(self):
        """同步 LoRA 到不同目录"""
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            messagebox.showwarning("提示", f"test_lora 目录不存在: {test_dir}")
            return
        
        if not messagebox.askyesno("确认同步",
            "将按文件大小判断架构，分别同步到 sd15-lora 和 sdxl-lora 目录\n\n"
            "确定继续吗？"
        ):
            return
        
        self._start_operation("🔄 同步 LoRA...")
        threading.Thread(target=self._run_sync, daemon=True).start()
    
    def _run_sync(self):
        """后台运行同步"""
        try:
            test_dir = self.test_lora_dir_var.get()
            sd15_dir = self.sd15_lora_dir_var.get()
            sdxl_dir = self.sdxl_lora_dir_var.get()
            
            os.makedirs(sd15_dir, exist_ok=True)
            os.makedirs(sdxl_dir, exist_ok=True)
            
            files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
            
            sd15_copied = 0
            sdxl_copied = 0
            unknown = 0
            
            for idx, filename in enumerate(files):
                if self.cancel_operation:
                    break
                
                filepath = os.path.join(test_dir, filename)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                
                # 判断架构
                if size_mb < 200:
                    dst_dir = sd15_dir
                    sd15_copied += 1
                elif size_mb >= 200:
                    dst_dir = sdxl_dir
                    sdxl_copied += 1
                else:
                    unknown += 1
                    continue
                
                dst_path = os.path.join(dst_dir, filename)
                if not os.path.exists(dst_path):
                    shutil.copy2(filepath, dst_path)
                
                if idx % 10 == 0:
                    self.app.root.after(0, lambda i=idx, t=len(files): 
                        self.progress_bar.config(value=(i+1)/t*100))
            
            self._append_log(f"✅ 同步完成！")
            self._append_log(f"   SD 1.5: {sd15_copied} 个 → {sd15_dir}")
            self._append_log(f"   SDXL: {sdxl_copied} 个 → {sdxl_dir}")
            if unknown:
                self._append_log(f"   ⚠️ 无法判断: {unknown} 个")
            
        except Exception as e:
            self._append_log(f"❌ 同步失败: {e}")
        finally:
            self._reset_ui()
    
    # ==================== 辅助方法 ====================
    
    def _start_operation(self, status):
        """开始操作"""
        self.is_processing = True
        self.cancel_operation = False
        self._set_buttons_state(tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_bar.config(value=0, maximum=100)
        self.status_var.set(status)
        self._append_log(status)
    
    def _reset_ui(self):
        """重置 UI"""
        self.is_scanning = False
        self.is_processing = False
        self._set_buttons_state(tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.progress_bar.config(value=0)
        self.status_var.set("就绪")
    
    def _set_buttons_state(self, state):
        """设置按钮状态"""
        for child in self.frame.winfo_children():
            if isinstance(child, ttk.Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, ttk.Button) and btn != self.cancel_btn:
                        try:
                            btn.config(state=state)
                        except:
                            pass
    
    def _cancel_operation(self):
        """取消操作"""
        self.cancel_operation = True
        self._append_log("⏹️ 正在取消...")
        self.cancel_btn.config(state=tk.DISABLED)
    
    def _append_log(self, msg):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        def update():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.app.root.after(0, update)