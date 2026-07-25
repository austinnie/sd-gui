# gui/app.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stable Diffusion 桌面GUI版 - 精简版
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from utils.logger import get_logger

logger = get_logger(__name__)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.app_config import app_config
from gui.model_manager import ModelManager, ModelType
from gui.model_loader import scan_checkpoints, scan_loras, scan_vaes, get_optimization_info
from gui.ui_builder import UIBuilder
from gui.lora_handler import LoraHandler
from gui.vae_handler import VaeHandler
from gui.reloader import Reloader
from gui.components.memory_monitor import MemoryMonitor, force_memory_cleanup
from gui.components.progress_bar import ProgressBar
from gui.components.image_preview import ImagePreview
from gui.components.params_panel import ParamsPanel
from gui.components.batch_panel import BatchPanel


class SDApp:
    """主应用程序 - 精简版"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Stable Diffusion 桌面版 - v8")
        
        ui_config = app_config.ui
        self.root.geometry(f"{ui_config.window_width}x{ui_config.window_height}")
        
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # ===== 初始化组件 =====
        self.memory_monitor = MemoryMonitor(self.root, ui_config.memory_update_interval)
        self.progress_bar = ProgressBar(self.root)
        self.image_preview = ImagePreview(self.root)
        self.params_panel = ParamsPanel()
        
        # ===== 初始化管理器 =====
        self.model_manager = ModelManager(self)
        self.lora_handler = LoraHandler(self)
        self.vae_handler = VaeHandler(self)
        self.reloader = Reloader(self)
        self.ui_builder = UIBuilder(self)
        
        # ===== 状态变量 =====
        self.status_var = tk.StringVar(value="就绪")
        
        # ===== 模型数据 =====
        self.checkpoints = []
        self.checkpoint_paths = {}
        self.lora_files = []
        self.lora_paths = {}
        self.lora_types = {}
        self.vae_files = []
        self.vae_paths = {}
        
        # ===== 构建 UI =====
        self._setup_ui()
        
        # ===== 启动监控 =====
        if ui_config.show_memory_monitor:
            self.memory_monitor.start_monitoring()
        
        # ===== 自动加载 =====
        if app_config.model.auto_load_first:
            self.root.after(100, self._auto_load_model)
    
    def _setup_ui(self):
        """设置 UI"""
        self.scrollable_frame = self.ui_builder.build_scrollable_frame()
        main_frame = self.scrollable_frame
        
        # 构建各组件
        self.ui_builder.build_status_bar(main_frame)
        self.ui_builder.build_model_selector(main_frame)
        self.ui_builder.build_lora_selector(main_frame)
        self.ui_builder.build_vae_selector(main_frame)
        
        # 优化信息
        opt_info = get_optimization_info()
        ttk.Label(main_frame, text=opt_info, foreground="purple", font=("", 8)).pack(anchor=tk.W, padx=5)
        
        # 参数面板
        self.ui_builder.build_params_panel(main_frame)
        
        # NSFW 面板
        self.ui_builder.build_nsfw_panel(main_frame)
        
        # 标签页
        self.notebook = self.ui_builder.build_tabs(main_frame)
        
        # 进度条和预览
        self.ui_builder.build_progress_and_preview(main_frame)
        
        # 扫描模型
        self.checkpoints, self.checkpoint_paths = scan_checkpoints()
        self.model_combo['values'] = self.checkpoints
        if self.checkpoints:
            self.model_var.set(self.checkpoints[0])
        
        # 扫描 LoRA
        self.lora_files, self.lora_paths, self.lora_types = scan_loras()
        self.lora_combo['values'] = self.lora_files
        if self.lora_files:
            self.lora_var.set("")
            self.lora_handler._update_lora_status()
        
        # 扫描 VAE
        self.vae_files, self.vae_paths = scan_vaes()
        self.vae_combo['values'] = self.vae_files
        if self.vae_files:
            self.vae_var.set("")
        
        self._update_model_ui()
    
    # ==================== 模型管理 ====================
    
    def _auto_load_model(self):
        """自动加载模型"""
        if self.checkpoints:
            first_model = self.checkpoints[0]
            self.model_var.set(first_model)
            self.update_status(f"🔄 自动加载: {first_model[:40]}...")
            self._load_sd_model()
        else:
            self.update_status("⚠️ 未找到模型文件，请检查模型目录")
    
    def _load_sd_model(self):
        """加载 SD 模型"""
        if self.model_manager.is_loading:
            return
        
        model_name = self.model_var.get()
        if not model_name or model_name not in self.model_combo['values']:
            self.update_status("❌ 请选择有效的模型")
            return
        
        model_path = self._get_model_path(model_name)
        if not model_path:
            self.update_status("❌ 找不到模型文件")
            return
        
        lora_display = self.lora_var.get()
        lora_path = None
        lora_weight = 1.0
        if lora_display and lora_display in self.lora_paths:
            lora_path = self.lora_paths[lora_display]
            lora_weight = self.lora_weight_var.get()
            logger.info(f"🔗 将加载 LoRA: {lora_display} (权重: {lora_weight})")
        
        self.update_status(f"📦 加载 SD 模型...")
        self.load_btn.config(state=tk.DISABLED)
        
        def load_thread():
            def progress_cb(value, msg):
                self.root.after(0, lambda: self.update_progress(value, msg))
            
            success = self.model_manager.load_sd(model_path, model_name, progress_cb, lora_path, lora_weight)
            self.root.after(0, lambda: self._on_load_sd_complete(success))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def _on_load_sd_complete(self, success: bool):
        """SD 模型加载完成"""
        self.load_btn.config(state=tk.NORMAL)
        self._update_model_ui()
        
        if success:
            model_type = self.model_manager.get_sd_model_type()
            self.update_status(f"✅ SD 模型加载完成 ({model_type.upper()})")
            self.update_progress(1.0, "✅ SD 模型就绪")
            self.lora_handler._update_lora_list()
            
            lora_status = self.model_manager.get_lora_status()
            if lora_status["loaded"]:
                lora_name = os.path.basename(lora_status["path"])
                self.update_status(f"✅ SD 模型加载完成 | 🔗 LoRA: {lora_name}")
            
            self.lora_handler._update_lora_status()
        else:
            self.update_status("❌ SD 模型加载失败")
            messagebox.showerror("错误", "SD 模型加载失败，请查看控制台输出")
    
    # ==================== LoRA 管理 ====================
    
    def _load_lora_from_ui(self):
        """加载 LoRA"""
        self.lora_handler.load_lora()
    
    def _unload_lora(self):
        """卸载 LoRA"""
        self.lora_handler.unload_lora()
    
    def _clear_lora(self):
        """清除 LoRA"""
        self.lora_handler.clear_lora()
    
    def _update_lora_list(self):
        """更新 LoRA 列表"""
        self.lora_handler._update_lora_list()
    
    def _refresh_lora_viewer(self):
        """刷新 LoRA 信息查看器"""
        self.lora_handler._refresh_lora_viewer()
    
    # ==================== VAE 管理 ====================
    
    def _load_vae(self):
        """加载 VAE"""
        self.vae_handler.load_vae()
    
    def _unload_vae(self):
        """卸载 VAE"""
        self.vae_handler.unload_vae()
    
    def _clear_vae(self):
        """清除 VAE"""
        self.vae_handler.clear_vae()
    
    # ==================== 模型切换 ====================
    
    def _switch_to_janus(self):
        """切换到 Janus"""
        if self.model_manager.is_loading:
            return
        
        model_key = "1B"
        if self.janus_tab and hasattr(self.janus_tab, '_get_model_key'):
            model_key = self.janus_tab._get_model_key()
        
        self.update_status("🔄 正在切换到 Janus-Pro...")
        
        def load_thread():
            def progress_cb(value, msg):
                self.root.after(0, lambda: self.update_progress(value, msg))
            
            success = self.model_manager.load_janus(model_key, progress_cb)
            self.root.after(0, lambda: self._on_switch_complete(success, "Janus"))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def _switch_to_sd(self):
        """切换到 SD"""
        if self.model_manager.is_loading:
            return
        
        model_name = self.model_var.get()
        if not model_name or model_name not in self.model_combo['values']:
            messagebox.showwarning("提示", "请选择有效的 SD 模型")
            return
        
        model_path = self._get_model_path(model_name)
        if not model_path:
            messagebox.showwarning("提示", "找不到模型文件")
            return
        
        self.update_status("🔄 正在切换到 SD...")
        
        def load_thread():
            def progress_cb(value, msg):
                self.root.after(0, lambda: self.update_progress(value, msg))
            
            success = self.model_manager.load_sd(model_path, model_name, progress_cb)
            self.root.after(0, lambda: self._on_switch_complete(success, "SD"))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def _on_switch_complete(self, success: bool, model_type: str):
        """切换完成"""
        if success:
            self.update_status(f"✅ 已切换到 {model_type}")
        else:
            self.update_status(f"❌ 切换到 {model_type} 失败")
            messagebox.showerror("错误", f"{model_type} 模型加载失败")
        
        self._update_model_ui()
        self.update_progress(1.0, f"✅ {model_type} 模型就绪")
        force_memory_cleanup()
    
    def _unload_current_model(self):
        """卸载当前模型"""
        if self.model_manager.is_loading:
            return
        
        if messagebox.askyesno("确认", "确定要卸载当前模型吗？"):
            self.model_manager.unload_all()
            self._update_model_ui()
            self.update_status("✅ 模型已卸载")
            force_memory_cleanup()
    
    def _update_model_ui(self):
        """更新模型 UI 状态"""
        status = self.model_manager.get_status_text()
        self.model_status_label.config(text=status)
        
        is_sd = self.model_manager.is_sd_loaded
        is_janus = self.model_manager.is_janus_loaded
        is_loading = self.model_manager.is_loading
        
        if is_loading:
            self.switch_to_janus_btn.config(state=tk.DISABLED)
            self.switch_to_sd_btn.config(state=tk.DISABLED)
            self.load_btn.config(state=tk.DISABLED)
        else:
            self.switch_to_janus_btn.config(state=tk.NORMAL if is_sd and not is_janus else tk.DISABLED)
            self.switch_to_sd_btn.config(state=tk.NORMAL if is_janus else tk.DISABLED)
            self.load_btn.config(state=tk.NORMAL if not is_sd else tk.DISABLED)
        
        if self.janus_tab:
            self.janus_tab.update_model_status()
    
    # ==================== 热重载 ====================
    
    def _reload_modules(self):
        """热重载模块"""
        self.reloader.reload_all()
    
    # ==================== 工具方法 ====================
    
    def _get_model_path(self, display_name: str) -> str:
        """获取模型路径"""
        return self.checkpoint_paths.get(display_name)
    
    def _get_memory_usage(self):
        """获取内存使用"""
        import psutil
        return psutil.Process().memory_info().rss / 1024 / 1024 / 1024
    
    def update_status(self, message: str):
        """更新状态"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        def update():
            self.status_var.set(message)
            logger.info(f"[{timestamp}] [状态] {message}")
        self.root.after(0, update)
    
    def update_progress(self, value: float, message: str = ""):
        """更新进度"""
        self.progress_bar.update(value, message)
    
    def add_to_preview(self, filepath: str, image):
        """添加到预览"""
        self.image_preview.add_image(filepath, image)
    
    def open_output_folder(self):
        """打开输出文件夹"""
        from config.app_config import app_config
        output_dir = app_config.paths.get_resolved_output_dir()
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                self.update_status(f"❌ 无法创建输出目录: {e}")
                return
        
        try:
            if sys.platform == 'win32':
                os.startfile(output_dir)
            else:
                os.system(f'open "{output_dir}"')
        except Exception as e:
            self.update_status(f"❌ 无法打开文件夹: {e}")
    
    def run(self):
        """运行应用"""
        self.root.mainloop()


def main():
    """主入口"""
    from utils.performance import start_timer, log_startup
    start_timer()
    
    print("=" * 60)
    logger.info(f"Stable Diffusion 桌面GUI版 - v8")
    logger.info(f"输出目录: {app_config.paths.output_dir}")
    print("=" * 60)
    
    try:
        import torch
        logger.info(f"PyTorch: {torch.__version__}")
        logger.info(f"CUDA可用: {torch.cuda.is_available()}")
    except:
        logger.info(f"⚠️ PyTorch 未安装或导入失败")
    
    logger.info(f"\n🌍 通用生成器已集成")
    logger.info(f"💡 模型互斥加载: SD ↔ Janus 自动切换")
    print("=" * 60)
    
    app = SDApp()
    log_startup("GUI 初始化完成")
    app.run()


if __name__ == "__main__":
    main()