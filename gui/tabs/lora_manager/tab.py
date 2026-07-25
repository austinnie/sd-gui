# gui/tabs/lora_manager/tab.py
"""LoRA 管理标签页主类"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import shutil
import re
from datetime import datetime

from ..base_tab import BaseTab
from .ui import LoraManagerUI
from .test_runner import LoraTestRunner
from .analyzer import LoraAnalyzer
from .utils import load_run_log, save_run_log, format_size, extract_lora_name
from gui.components import LoraInfoViewer


class LoraManagerTab(BaseTab):
    """LoRA 管理标签页"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._init_vars()
        
        self.test_runner = LoraTestRunner(self)
        self.analyzer = LoraAnalyzer(self)
        
        self.ui = LoraManagerUI(self)
        self.ui.build()
        
        self._scan_lora_files()
        self._refresh_single_lora_list()
    
    def _init_vars(self):
        """初始化变量"""
        # ===== 路径配置 =====
        self.image_dir_var = tk.StringVar(value="output/all_images")
        self.output_file_var = tk.StringVar(value="output/high_sex_lora_list.txt")
        self.extract_dir_var = tk.StringVar(value="output/selected_high_loras")
        self.top_k_var = tk.IntVar(value=30)
        
        # 模型目录
        self.models_root_var = tk.StringVar(value=r"E:\SD_OpenVINO\models")
        self.test_lora_dir_var = tk.StringVar(value=r"E:\SD_OpenVINO\models\test_lora")
        self.sd15_lora_dir_var = tk.StringVar(value=r"E:\SD_OpenVINO\models\sd15-lora")
        self.sdxl_lora_dir_var = tk.StringVar(value=r"E:\SD_OpenVINO\models\sdxl-lora")
        
        # ===== 批量测试配置 =====
        self.sd15_model_path_var = tk.StringVar(value=r"../models/sd-v1-5/aiiiiii01_v10.safetensors")
        self.sdxl_model_path_var = tk.StringVar(value=r"../models/sdxl/perfectionAsianILXL_v10.safetensors")
        self.output_previews_dir_var = tk.StringVar(value="./output/lora_previews")
        self.test_steps_sd15_var = tk.IntVar(value=12)
        self.test_steps_sdxl_var = tk.IntVar(value=20)
        self.test_prompt_sd15_var = tk.StringVar(
            value="masterpiece, best quality, 1girl, solo, white background, sharp focus, <lora:NAME:1>"
        )
        self.test_prompt_sdxl_var = tk.StringVar(
            value="masterpiece, best quality, 1girl, solo, white background, studio lighting, highly detailed, sharp focus, <lora:NAME:1>"
        )
        self.test_negative_sd15_var = tk.StringVar(
            value="worst quality, low quality, deformed, blurry, bad anatomy"
        )
        self.test_negative_sdxl_var = tk.StringVar(
            value="worst quality, low quality, deformed, blurry, bad anatomy, extra limbs, missing limbs, text"
        )
        self.test_size_sd15_var = tk.StringVar(value="512x768")
        self.test_size_sdxl_var = tk.StringVar(value="1024x1024")
        self.test_filter_var = tk.StringVar(value="all")
        self.test_re_run_var = tk.BooleanVar(value=False)
        
        # ===== 状态 =====
        self.is_scanning = False
        self.is_testing = False
        self.is_processing = False
        self.cancel_operation = False
        
        # ===== 数据 =====
        self.lora_scores = []
        self.top_loras = []
        self.lora_files = []
        self.test_run_log = {}
        
        # ✅ 新增
        self.test_model_type_var = tk.StringVar(value="both")
    
    # ==================== 日志方法 ====================
    
    def _append_test_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        def update():
            try:
                self.test_log_text.config(state=tk.NORMAL)
                self.test_log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
                self.test_log_text.see(tk.END)
                self.test_log_text.config(state=tk.DISABLED)
            except:
                pass
        self.app.root.after(0, update)
    
    def _append_analyze_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        def update():
            try:
                self.analyze_log_text.config(state=tk.NORMAL)
                self.analyze_log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
                self.analyze_log_text.see(tk.END)
                self.analyze_log_text.config(state=tk.DISABLED)
            except:
                pass
        self.app.root.after(0, update)
    
    # ==================== 扫描方法 ====================
    
    def _scan_lora_files(self):
        """扫描 LoRA 文件"""
        test_dir = self.test_lora_dir_var.get()
        if os.path.exists(test_dir):
            self.lora_files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
    
    def _refresh_single_lora_list(self):
        """刷新单个 LoRA 下拉列表"""
        test_dir = self.test_lora_dir_var.get()
        if os.path.exists(test_dir):
            files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
            files.sort()
            if hasattr(self, 'single_lora_combo'):
                self.single_lora_combo['values'] = files
    
    def _get_filtered_lora_list(self):
        """获取筛选后的 LoRA 列表"""
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            return []
        
        files = []
        for f in os.listdir(test_dir):
            if f.endswith('.safetensors'):
                path = os.path.join(test_dir, f)
                size_mb = os.path.getsize(path) / (1024 * 1024)
                mtime = os.path.getmtime(path)
                files.append({"name": f, "path": path, "size_mb": size_mb, "mtime": mtime})
        
        files.sort(key=lambda x: x["size_mb"])
        
        filter_type = self.test_filter_var.get()
        if filter_type == "small":
            files = [f for f in files if f['size_mb'] < 50]
        elif filter_type == "medium":
            files = [f for f in files if 50 <= f['size_mb'] < 200]
        elif filter_type == "large":
            files = [f for f in files if f['size_mb'] >= 200]
        
        return files
    
    # ==================== 批量测试 ====================
    
    def _start_batch_test(self):
        """开始批量测试"""
        if self.is_testing:
            return
        
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            messagebox.showwarning("提示", f"LoRA 目录不存在: {test_dir}")
            return
        
        lora_files = self._get_filtered_lora_list()
        if not lora_files:
            messagebox.showwarning("提示", "没有找到符合条件的 LoRA 文件")
            return
        
        sd15_model = self.sd15_model_path_var.get()
        sdxl_model = self.sdxl_model_path_var.get()
        if not os.path.exists(sd15_model) and not os.path.exists(sdxl_model):
            messagebox.showwarning("提示", "请配置有效的模型路径")
            return
        
        if not messagebox.askyesno("确认测试",
            f"将测试 {len(lora_files)} 个 LoRA\n"
            f"输出目录: {self.output_previews_dir_var.get()}\n\n"
            f"确定继续吗？"
        ):
            return
        
        self.is_testing = True
        self.cancel_operation = False
        self.test_btn.config(state=tk.DISABLED)
        self.test_cancel_btn.config(state=tk.NORMAL)
        self.test_progress_bar.config(value=0, maximum=100)
        self.test_status_var.set("测试中...")
        
        config = {
            'sd15_model_path': self.sd15_model_path_var.get(),
            'sdxl_model_path': self.sdxl_model_path_var.get(),
            'sd15_steps': self.test_steps_sd15_var.get(),
            'sdxl_steps': self.test_steps_sdxl_var.get(),
            'sd15_prompt': self.test_prompt_sd15_var.get(),
            'sdxl_prompt': self.test_prompt_sdxl_var.get(),
            'sd15_negative': self.test_negative_sd15_var.get(),
            'sdxl_negative': self.test_negative_sdxl_var.get(),
            'sd15_size': self.test_size_sd15_var.get(),
            'sdxl_size': self.test_size_sdxl_var.get(),
            'output_dir': self.output_previews_dir_var.get(),
            'model_type': self.test_model_type_var.get(),  # ✅ 添加
            're_run': self.test_re_run_var.get(),
        }
        
        def progress_cb(value, msg):
            self.app.root.after(0, lambda: self.test_progress_bar.config(value=value * 100))
            self.app.root.after(0, lambda: self.test_status_var.set(msg))
        
        def run_thread():
            result = self.test_runner.run_tests(lora_files, config, progress_cb)
            self.app.root.after(0, lambda: self._on_test_complete(result))
        
        threading.Thread(target=run_thread, daemon=True).start()
    
    def _on_test_complete(self, result):
        """测试完成"""
        self.is_testing = False
        self.test_btn.config(state=tk.NORMAL)
        self.test_cancel_btn.config(state=tk.DISABLED)
        self.test_progress_bar.config(value=0)
        self.test_status_var.set(f"✅ 完成 (共 {result.get('total', 0)} 个)")
    
    # ==================== 分析功能 ====================
    
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
        self.analyze_status_var.set("扫描中...")
        self.analyze_progress_bar.config(value=0, maximum=100)
        
        def progress_cb(value, msg):
            self.app.root.after(0, lambda: self.analyze_progress_bar.config(value=value * 100))
            self.app.root.after(0, lambda: self.analyze_status_var.set(msg))
        
        def scan_thread():
            self.analyzer.cancel_operation = False
            sorted_loras, top_loras = self.analyzer.analyze(
                image_dir, self.top_k_var.get(), progress_cb
            )
            self.app.root.after(0, lambda: self._on_scan_complete(sorted_loras, top_loras))
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def _on_scan_complete(self, sorted_loras, top_loras):
        """扫描完成"""
        self.is_scanning = False
        self.analyze_status_var.set("✅ 完成")
        self.analyze_progress_bar.config(value=100)
        
        if sorted_loras:
            self.lora_scores = sorted_loras
            self.top_loras = top_loras
            self._update_tree()
            self._append_analyze_log(f"✅ 扫描完成！共 {len(sorted_loras)} 个 LoRA")
            
            output_file = self.output_file_var.get()
            os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== 高分 LoRA 排行 ===\n\n")
                for i, (lora, score) in enumerate(sorted_loras[:self.top_k_var.get()], 1):
                    f.write(f"{i:02d}. {lora} (评分: {score:.4f})\n")
            self._append_analyze_log(f"📄 列表已保存: {output_file}")
        else:
            self._append_analyze_log("⚠️ 没有找到可分析的 LoRA")
    
    def _update_tree(self):
        """更新树形列表"""
        self.tree.delete(*self.tree.get_children())
        test_dir = self.test_lora_dir_var.get()
        test_files = set(os.listdir(test_dir)) if os.path.exists(test_dir) else set()
        
        for i, (name, score) in enumerate(self.lora_scores[:100], 1):
            size_mb = 0
            status = "❌ 未找到"
            for f in test_files:
                if name in f and f.endswith('.safetensors'):
                    size_mb = os.path.getsize(os.path.join(test_dir, f)) / (1024 * 1024)
                    status = "✅ 存在"
                    break
            if i <= self.top_k_var.get():
                status = "⭐ " + status
            self.tree.insert("", tk.END, values=(i, name[:60], f"{score:.4f}", f"{size_mb:.1f}", status))
    
    def _show_ranking(self):
        """显示排行"""
        if not self.lora_scores:
            messagebox.showinfo("提示", "请先运行扫描分析")
            return
        self._update_tree()
        self._append_analyze_log(f"📋 显示排行，共 {len(self.lora_scores)} 个 LoRA")
    
    def _extract_high_loras(self):
        """提取高分 LoRA"""
        if not self.top_loras:
            messagebox.showinfo("提示", "请先运行扫描分析")
            return
        
        if not messagebox.askyesno("确认提取",
            f"将复制前 {self.top_k_var.get()} 个 LoRA 的图片到:\n{self.extract_dir_var.get()}\n\n确定继续吗？"
        ):
            return
        
        self.is_processing = True
        self.cancel_operation = False
        self.analyze_status_var.set("提取中...")
        self.analyze_progress_bar.config(value=0, maximum=100)
        
        def progress_cb(value, msg):
            self.app.root.after(0, lambda: self.analyze_progress_bar.config(value=value * 100))
            self.app.root.after(0, lambda: self.analyze_status_var.set(msg))
        
        def extract_thread():
            self.analyzer.cancel_operation = False
            copied = self.analyzer.extract_high_loras(
                self.top_loras, self.image_dir_var.get(),
                self.extract_dir_var.get(), progress_cb
            )
            self.app.root.after(0, lambda: self._on_extract_complete(copied))
        
        threading.Thread(target=extract_thread, daemon=True).start()
    
    def _on_extract_complete(self, copied):
        """提取完成"""
        self.is_processing = False
        self.analyze_status_var.set(f"✅ 完成 (复制 {copied} 张)")
        self.analyze_progress_bar.config(value=100)
        self._append_analyze_log(f"✅ 提取完成！共复制 {copied} 张图片")
    
    def _filter_low_loras(self):
        """过滤低分 LoRA"""
        if not self.lora_scores:
            messagebox.showinfo("提示", "请先运行扫描分析")
            return
        
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            messagebox.showwarning("提示", f"目录不存在: {test_dir}")
            return
        
        keep_names = set(self.top_loras)
        files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
        to_delete = [f for f in files if not any(name in f for name in keep_names)]
        
        if not to_delete:
            messagebox.showinfo("提示", "没有需要删除的文件")
            return
        
        if not messagebox.askyesno("确认删除",
            f"将删除 {len(to_delete)} 个低分 LoRA 文件\n\n确定继续吗？"
        ):
            return
        
        self.is_processing = True
        self.cancel_operation = False
        self.analyze_status_var.set("删除中...")
        self.analyze_progress_bar.config(value=0, maximum=100)
        
        def progress_cb(value, msg):
            self.app.root.after(0, lambda: self.analyze_progress_bar.config(value=value * 100))
            self.app.root.after(0, lambda: self.analyze_status_var.set(msg))
        
        def filter_thread():
            self.analyzer.cancel_operation = False
            deleted = self.analyzer.filter_low_loras(
                self.top_loras, test_dir, progress_cb
            )
            self.app.root.after(0, lambda: self._on_filter_complete(deleted))
        
        threading.Thread(target=filter_thread, daemon=True).start()
    
    def _on_filter_complete(self, deleted):
        """过滤完成"""
        self.is_processing = False
        self.analyze_status_var.set(f"✅ 完成 (删除 {deleted} 个)")
        self.analyze_progress_bar.config(value=100)
        self._append_analyze_log(f"✅ 过滤完成！共删除 {deleted} 个文件")
        self._scan_lora_files()
        self._update_tree()
    
    def _rename_loras(self):
        """重命名 LoRA"""
        if not self.top_loras:
            messagebox.showinfo("提示", "请先运行扫描分析")
            return
        
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            messagebox.showwarning("提示", f"目录不存在: {test_dir}")
            return
        
        if not messagebox.askyesno("确认重命名",
            f"将按排名重命名 test_lora 目录中的文件\n\n共 {len(self.top_loras)} 个文件\n确定继续吗？"
        ):
            return
        
        self.is_processing = True
        self.cancel_operation = False
        self.analyze_status_var.set("重命名中...")
        self.analyze_progress_bar.config(value=0, maximum=100)
        
        def progress_cb(value, msg):
            self.app.root.after(0, lambda: self.analyze_progress_bar.config(value=value * 100))
            self.app.root.after(0, lambda: self.analyze_status_var.set(msg))
        
        def rename_thread():
            self.analyzer.cancel_operation = False
            renamed = self.analyzer.rename_loras(
                self.top_loras, test_dir, progress_cb
            )
            self.app.root.after(0, lambda: self._on_rename_complete(renamed))
        
        threading.Thread(target=rename_thread, daemon=True).start()
    
    def _on_rename_complete(self, renamed):
        """重命名完成"""
        self.is_processing = False
        self.analyze_status_var.set(f"✅ 完成 (重命名 {renamed} 个)")
        self.analyze_progress_bar.config(value=100)
        self._append_analyze_log(f"✅ 重命名完成！成功: {renamed} 个")
        self._scan_lora_files()
        self._update_tree()
    
    def _sync_loras(self):
        """同步 LoRA"""
        test_dir = self.test_lora_dir_var.get()
        if not os.path.exists(test_dir):
            messagebox.showwarning("提示", f"test_lora 目录不存在: {test_dir}")
            return
        
        if not messagebox.askyesno("确认同步",
            "将按文件大小判断架构，分别同步到 sd15-lora 和 sdxl-lora 目录\n\n确定继续吗？"
        ):
            return
        
        self.is_processing = True
        self.cancel_operation = False
        self.analyze_status_var.set("同步中...")
        self.analyze_progress_bar.config(value=0, maximum=100)
        
        def progress_cb(value, msg):
            self.app.root.after(0, lambda: self.analyze_progress_bar.config(value=value * 100))
            self.app.root.after(0, lambda: self.analyze_status_var.set(msg))
        
        def sync_thread():
            self.analyzer.cancel_operation = False
            sd15_copied, sdxl_copied, unknown = self.analyzer.sync_loras(
                test_dir, self.sd15_lora_dir_var.get(),
                self.sdxl_lora_dir_var.get(), progress_cb
            )
            self.app.root.after(0, lambda: self._on_sync_complete(sd15_copied, sdxl_copied, unknown))
        
        threading.Thread(target=sync_thread, daemon=True).start()
    
    def _on_sync_complete(self, sd15_copied, sdxl_copied, unknown):
        """同步完成"""
        self.is_processing = False
        self.analyze_status_var.set("✅ 完成")
        self.analyze_progress_bar.config(value=100)
        self._append_analyze_log(f"✅ 同步完成！")
        self._append_analyze_log(f"   SD 1.5: {sd15_copied} 个")
        self._append_analyze_log(f"   SDXL: {sdxl_copied} 个")
        if unknown:
            self._append_analyze_log(f"   ⚠️ 无法判断: {unknown} 个")
    
    # ==================== 取消操作 ====================
    
    def _cancel_operation(self):
        """取消操作"""
        self.cancel_operation = True
        self.test_runner.cancel_operation = True
        self.analyzer.cancel_operation = True
        self._append_test_log("⏹️ 正在取消...")
        self._append_analyze_log("⏹️ 正在取消...")
        self.test_cancel_btn.config(state=tk.DISABLED)
        self.analyze_cancel_btn.config(state=tk.DISABLED)
    
    # ==================== 辅助方法 ====================
    
    def _open_previews_output(self):
        """打开输出目录"""
        output_dir = self.output_previews_dir_var.get()
        if os.path.exists(output_dir):
            try:
                os.startfile(output_dir)
            except:
                pass
        else:
            messagebox.showinfo("提示", f"输出目录不存在: {output_dir}")
    
    def _copy_selected_name(self):
        """复制选中名称"""
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0], "values")
            if values and len(values) > 1:
                self.app.root.clipboard_clear()
                self.app.root.clipboard_append(values[1])
                self._append_analyze_log(f"📋 已复制: {values[1]}")
    
    def _open_selected_dir(self):
        """打开选中文件目录"""
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0], "values")
            if values and len(values) > 1:
                name = values[1]
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