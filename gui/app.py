#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stable Diffusion 桌面GUI版 - 重构版
集成通用人物生成器
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from enum import Enum

# ✅ 在文件顶部导入 diffusers 相关内容
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    DPMSolverMultistepScheduler,
    EulerDiscreteScheduler  # ✅ 添加这行
)
# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.app_config import app_config
from gui.components.memory_monitor import MemoryMonitor, force_memory_cleanup
from gui.components.progress_bar import ProgressBar
from gui.components.image_preview import ImagePreview
from gui.tabs.txt2img_tab import Txt2ImgTab
from gui.tabs.img2img_tab import Img2ImgTab
from gui.tabs.interrogate_tab import InterrogateTab
from gui.tabs.universal_tab import UniversalTab
from gui.scene_manager import SceneManager
from gui.components.params_panel import ParamsPanel
from gui.components.batch_panel import BatchPanel
from gui.tabs.janus_tab import JanusTab
from gui.tabs.grid_test_tab import GridTestTab
from gui.components.nsfw_panel import NSFWPanel

from gui.tabs.pipeline_tab import PipelineTab

class ModelType(Enum):
    """模型类型枚举"""
    SD = "sd"
    JANUS = "janus"
    NONE = "none"


class ModelManager:
    """模型管理器 - 管理 SD 和 Janus 模型的互斥加载"""
    
    def __init__(self, app):
        self.app = app
        self._current_type = ModelType.NONE
        self._sd_pipe = None
        self._sd_model_name = None
        self._janus_loaded = False
        self._loading = False
        self._lock = threading.Lock()

        # ===== [新增] 强制设置设备为 CPU =====
        import torch
        torch.device("cpu")  # 设置默认设备为 CPU
        # ===== [新增] 结束 =====
        
    
    @property
    def current_type(self) -> ModelType:
        return self._current_type
    
    @property
    def is_sd_loaded(self) -> bool:
        return self._current_type == ModelType.SD and self._sd_pipe is not None
    
    @property
    def is_janus_loaded(self) -> bool:
        return self._current_type == ModelType.JANUS and self._janus_loaded
    
    @property
    def is_loading(self) -> bool:
        return self._loading
    
    def get_sd_pipe(self):
        """获取 SD pipeline"""
        if self._current_type != ModelType.SD:
            return None
        return self._sd_pipe
    
    def get_sd_model_name(self):
        return self._sd_model_name
    
    def load_sd(self, model_path: str, model_name: str, progress_callback=None) -> bool:
        with self._lock:
            if self._loading:
                return False
            self._loading = True

        try:
            # 1. 先卸载 Janus
            if self._current_type == ModelType.JANUS:
                self._unload_janus_internal()

            # 2. 如果已经加载了相同的 SD 模型，直接返回
            if self._current_type == ModelType.SD and self._sd_model_name == model_name:
                return True

            # 3. 加载 SD 模型
            if progress_callback:
                progress_callback(0.1, f"📦 加载 SD 模型...")

            from diffusers import (
                StableDiffusionPipeline,
                StableDiffusionXLPipeline,
                DPMSolverMultistepScheduler,
                EulerDiscreteScheduler  # ✅ 添加这行
            )
            import torch

            # ===== 【终极修复】在加载前禁用 CUDA =====
            # 备份原来的函数
            original_is_available = torch.cuda.is_available
            
            # 定义一个假的 is_available，永远返回 False
            def mock_is_available():
                return False
            
            # 替换掉原本的检测函数
            torch.cuda.is_available = mock_is_available
            # ========================================

            is_sdxl = 'xl' in model_name.lower() or 'sdxl' in model_name.lower()
            use_half = app_config.memory.use_half_precision
            dtype = torch.float16 if use_half else torch.float32

            common_kwargs = {
                "torch_dtype": dtype,
                "safety_checker": None,
                "requires_safety_checker": False,
                "use_safetensors": True,
                "low_cpu_mem_usage": False,
            }

            if progress_callback:
                progress_callback(0.3, f"🔄 加载权重...")

            # 此时加载模型，内部组件绝不会认为有 CUDA
            if is_sdxl:
                pipe = StableDiffusionXLPipeline.from_single_file(model_path, **common_kwargs)
            else:
                pipe = StableDiffusionPipeline.from_single_file(model_path, **common_kwargs)

            # ===== 恢复原样 =====
            # 加载完成后，恢复原来的检测函数，避免影响后续操作
            torch.cuda.is_available = original_is_available
            # ====================

            if progress_callback:
                progress_callback(0.6, f"⚙️ 配置优化...")

            # ✅ 获取用户选择的调度器
            scheduler_name = self.app.params_panel.get_scheduler_type()
    
            # 配置调度器
            from utils.scheduler_factory import get_scheduler
            is_lightning = "lightning" in model_name.lower()

            if is_lightning:
                # Lightning 模型强制使用 Euler 的 trailing 模式
                from diffusers import EulerDiscreteScheduler
                pipe.scheduler = EulerDiscreteScheduler.from_config(
                    pipe.scheduler.config,
                    timestep_spacing="trailing"
                )
                print(f"⚡ 检测到 Lightning 模型，已配置 EulerDiscreteScheduler (trailing)")
            else:
                # 使用用户选择的调度器
                try:
                    pipe.scheduler = get_scheduler(scheduler_name, pipe.scheduler.config)
                    desc = get_scheduler_description(scheduler_name)
                    print(f"✅ 使用调度器: {scheduler_name.upper()} ({desc})")
                except Exception as e:
                    print(f"⚠️ 调度器切换失败，使用默认: {e}")
                    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)

            # 内存优化 (注意：跳过 CUDA 相关的 offload)
            if app_config.memory.vae_slicing:
                try:
                    pipe.vae.enable_slicing()
                except:
                    pass

            if app_config.memory.vae_tiling:
                try:
                    pipe.vae.enable_tiling()
                except:
                    pass

            if app_config.memory.attention_slicing:
                try:
                    pipe.enable_attention_slicing()
                except:
                    pass

            # 注意：因为您没有 CUDA，所以 enable_model_cpu_offload 和 enable_sequential_cpu_offload 会报错
            # 我们在这里把它们注释掉，或者只在有 CUDA 时启用。
            # 您的日志显示 "⚠️ CPU Offload 启用失败"，说明这部分代码在执行并报错。
            # 把它改成这样：
            if app_config.memory.enable_cpu_offload:
                try:
                    # 因为我们在 CPU 上，实际上不需要 offload，但为了不让它报错，我们加个判断
                    if torch.cuda.is_available():
                        if app_config.memory.enable_sequential_offload:
                            pipe.enable_sequential_cpu_offload()
                        else:
                            pipe.enable_model_cpu_offload()
                    else:
                        # 如果是纯 CPU 环境，直接忽略 offload
                        pass
                except Exception as e:
                    print(f"⚠️ CPU Offload 启用失败 (可能因为无 CUDA): {e}")

            # 保存
            self._sd_pipe = pipe
            self._sd_model_name = model_name
            self._current_type = ModelType.SD

            if progress_callback:
                progress_callback(1.0, f"✅ SD 模型加载完成")

            force_memory_cleanup()
            return True

        except Exception as e:
            print(f"❌ SD 模型加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            with self._lock:
                self._loading = False
    
    def load_janus(self, model_key: str = "1B", progress_callback=None) -> bool:
        """加载 Janus 模型，自动卸载 SD"""
        with self._lock:
            if self._loading:
                return False
            self._loading = True
        
        try:
            # 1. 先卸载 SD
            if self._current_type == ModelType.SD:
                self._unload_sd_internal()
            
            # 2. 如果 Janus 已加载，直接返回
            if self._current_type == ModelType.JANUS and self._janus_loaded:
                return True
            
            # 3. 加载 Janus
            if progress_callback:
                progress_callback(0.1, f"📦 加载 Janus-Pro-{model_key}...")
            
            from core.janus_loader import janus_loader
            
            success = janus_loader.load(model_name=model_key)
            
            if success:
                self._janus_loaded = True
                self._current_type = ModelType.JANUS
                
                if progress_callback:
                    progress_callback(1.0, f"✅ Janus-Pro-{model_key} 加载完成")
                
                force_memory_cleanup()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Janus 模型加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            with self._lock:
                self._loading = False
    
    def _unload_sd_internal(self):
        """内部卸载 SD"""
        if self._sd_pipe is not None:
            try:
                del self._sd_pipe
            except:
                pass
            self._sd_pipe = None
        self._sd_model_name = None
        if self._current_type == ModelType.SD:
            self._current_type = ModelType.NONE
        force_memory_cleanup()
        print("✅ SD 模型已卸载")
    
    def _unload_janus_internal(self):
        """内部卸载 Janus"""
        if self._janus_loaded:
            from core.janus_loader import janus_loader
            janus_loader.unload()
            self._janus_loaded = False
        if self._current_type == ModelType.JANUS:
            self._current_type = ModelType.NONE
        force_memory_cleanup()
        print("✅ Janus 模型已卸载")
    
    def unload_sd(self):
        """卸载 SD（外部调用）"""
        with self._lock:
            self._unload_sd_internal()
    
    def unload_janus(self):
        """卸载 Janus（外部调用）"""
        with self._lock:
            self._unload_janus_internal()
    
    def unload_all(self):
        """卸载所有模型"""
        with self._lock:
            self._unload_sd_internal()
            self._unload_janus_internal()
    
    def get_status_text(self) -> str:
        """获取状态文本"""
        if self._current_type == ModelType.SD:
            name = self._sd_model_name[:40] if self._sd_model_name else "已加载"
            return f"🟢 SD: {name}"
        elif self._current_type == ModelType.JANUS:
            return "🟢 Janus-Pro"
        else:
            return "🔴 未加载模型"


class SDApp:
    """主应用程序"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Stable Diffusion 桌面版 - v8 (集成通用生成器)")
        
        ui_config = app_config.ui
        self.root.geometry(f"{ui_config.window_width}x{ui_config.window_height}")
        
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass

        # ===== 模型管理器 =====
        self.model_manager = ModelManager(self)
        
        # 兼容旧代码的属性
        self._pipeline = None
        self._current_model = None
        self._pipe_loaded = False
        
        # 初始化组件
        self._init_components()
        self._setup_ui()
        
        if ui_config.show_memory_monitor:
            self.memory_monitor.start_monitoring()
        
        if app_config.model.auto_load_first:
            self.root.after(100, self._auto_load_model)
    
    # ===== 兼容旧代码的属性 =====
    @property
    def pipeline(self):
        if self.model_manager.current_type == ModelType.SD:
            return self.model_manager.get_sd_pipe()
        return None
    
    @pipeline.setter
    def pipeline(self, value):
        self._pipeline = value
    
    @property
    def pipe_loaded(self):
        return self.model_manager.is_sd_loaded
    
    @pipe_loaded.setter
    def pipe_loaded(self, value):
        self._pipe_loaded = value
    
    @property
    def current_model(self):
        return self.model_manager.get_sd_model_name()
    
    @current_model.setter
    def current_model(self, value):
        self._current_model = value
    
    def is_pipe_loaded(self) -> bool:
        return self.model_manager.is_sd_loaded
    
    def is_janus_loaded(self) -> bool:
        return self.model_manager.is_janus_loaded
    
    def get_pipeline(self):
        return self.pipeline
    
    def set_pipeline(self, pipe):
        self.pipeline = pipe
    
    def _init_components(self):
        self.memory_monitor = MemoryMonitor(self.root, app_config.ui.memory_update_interval)
        self.progress_bar = ProgressBar(self.root)
        self.image_preview = ImagePreview(self.root)
        
        self.status_var = tk.StringVar(value="就绪")
        
        self.txt2img_tab = None
        self.img2img_tab = None
        self.interrogate_tab = None
        self.universal_tab = None
        self.scene_tab = None
        self.janus_tab = None
        self.grid_test_tab = None
    
    def _setup_ui(self):
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        self.scrollable_frame = ttk.Frame(main_canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = self.scrollable_frame
        
        # ===== 模型状态栏 =====
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.model_status_label = ttk.Label(
            status_frame, 
            text=self.model_manager.get_status_text(),
            foreground="blue",
            font=("", 10)
        )
        self.model_status_label.pack(side=tk.LEFT, padx=5)
        
        self.switch_to_janus_btn = ttk.Button(
            status_frame,
            text="🔄 切换 Janus",
            command=self._switch_to_janus
        )
        self.switch_to_janus_btn.pack(side=tk.LEFT, padx=5)
        
        self.switch_to_sd_btn = ttk.Button(
            status_frame,
            text="🔄 切换 SD",
            command=self._switch_to_sd,
            state=tk.DISABLED
        )
        self.switch_to_sd_btn.pack(side=tk.LEFT, padx=5)
        
        self.unload_model_btn = ttk.Button(
            status_frame,
            text="🗑️ 卸载模型",
            command=self._unload_current_model
        )
        self.unload_model_btn.pack(side=tk.LEFT, padx=5)
        
        self.memory_monitor.create_widget(status_frame).pack(side=tk.RIGHT, padx=5)
        
        # ===== 模型选择 =====
        model_frame = ttk.Frame(main_frame)
        model_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(model_frame, text="📦 SD 模型:").pack(side=tk.LEFT, padx=5)
        
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, width=55)
        self.model_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.load_btn = ttk.Button(model_frame, text="加载 SD", command=self._load_sd_model)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        self.reload_btn = ttk.Button(model_frame, text="🔄 重载模块", command=self._reload_modules)
        self.reload_btn.pack(side=tk.LEFT, padx=5)
        
        # ===== 状态信息 =====
        opt_info = self._get_optimization_info()
        ttk.Label(main_frame, text=opt_info, foreground="purple", font=("", 8)).pack(anchor=tk.W, padx=5)
        
        # ===== 共享参数面板 =====
        self.params_panel = ParamsPanel()
        self.params_panel.create_widgets(main_frame)
        self.params_panel.get_frame().pack(fill=tk.X, padx=10, pady=5)

        # ════════════════════════════════════════════════════════════
        # ║  【在这里添加 NSFW 控制面板】                           ║
        # ║  位置：参数面板之后，标签页之前                        ║
        # ════════════════════════════════════════════════════════════
        
        # ===== NSFW 控制面板 =====
        from gui.components.nsfw_panel import NSFWPanel
        self.nsfw_panel = NSFWPanel(main_frame, self)
        self.nsfw_panel.get_frame().pack(fill=tk.X, padx=10, pady=5)
    
        # ===== 标签页 =====
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.notebook = notebook
        
        self._create_tabs()
        
        # ===== 批量面板 =====
        #self.batch_panel = BatchPanel(main_frame, self)
        #self.batch_panel.get_frame().pack(fill=tk.X, padx=10, pady=5)
        #self.batch_panel.set_start_callback(self._on_batch_start)
        
        # ===== 进度条和预览 =====
        self.progress_bar.create_widgets(main_frame)
        self.image_preview.create_widgets(main_frame)
        
        # 扫描模型
        self.checkpoints, self.checkpoint_paths = self._scan_checkpoints()
        self.model_combo['values'] = self.checkpoints
        if self.checkpoints:
            self.model_var.set(self.checkpoints[0])
        
        self._update_model_ui()
    
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
            if is_sd and not is_janus:
                self.switch_to_janus_btn.config(state=tk.NORMAL)
            else:
                self.switch_to_janus_btn.config(state=tk.DISABLED)
            
            if is_janus:
                self.switch_to_sd_btn.config(state=tk.NORMAL)
            else:
                self.switch_to_sd_btn.config(state=tk.DISABLED)
            
            self.load_btn.config(state=tk.NORMAL if not is_sd else tk.DISABLED)
        
        if self.janus_tab:
            self.janus_tab.update_model_status()
    
    def _switch_to_janus(self):
        """切换到 Janus 模型"""
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
        """切换到 SD 模型"""
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
        if success:
            self.update_status(f"✅ 已切换到 {model_type}")
        else:
            self.update_status(f"❌ 切换到 {model_type} 失败")
            messagebox.showerror("错误", f"{model_type} 模型加载失败")
        
        self._update_model_ui()
        self.update_progress(1.0, f"✅ {model_type} 模型就绪")
        force_memory_cleanup()
    
    def _unload_current_model(self):
        if self.model_manager.is_loading:
            return
        
        if messagebox.askyesno("确认", "确定要卸载当前模型吗？"):
            self.model_manager.unload_all()
            self._update_model_ui()
            self.update_status("✅ 模型已卸载")
            force_memory_cleanup()
    
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
        
        self.update_status(f"📦 加载 SD 模型...")
        self.load_btn.config(state=tk.DISABLED)
        
        def load_thread():
            def progress_cb(value, msg):
                self.root.after(0, lambda: self.update_progress(value, msg))
            
            success = self.model_manager.load_sd(model_path, model_name, progress_cb)
            self.root.after(0, lambda: self._on_load_sd_complete(success))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def _on_load_sd_complete(self, success: bool):
        self.load_btn.config(state=tk.NORMAL)
        self._update_model_ui()
        
        if success:
            mem_gb = self._get_memory_usage()
            self.update_status(f"✅ SD 模型加载完成 (内存: {mem_gb:.1f} GB)")
            self.update_progress(1.0, "✅ SD 模型就绪")
        else:
            self.update_status("❌ SD 模型加载失败")
            messagebox.showerror("错误", "SD 模型加载失败，请查看控制台输出")
    
    def _auto_load_model(self):
        if self.checkpoints:
            first_model = self.checkpoints[0]
            self.model_var.set(first_model)
            self.update_status(f"🔄 自动加载: {first_model[:40]}...")
            self._load_sd_model()
        else:
            self.update_status("⚠️ 未找到模型文件，请检查模型目录")
    
    def _get_optimization_info(self) -> str:
        mem = app_config.memory
        info = "⚡ 内存优化: "
        if mem.use_half_precision:
            info += "半精度 "
        if mem.enable_cpu_offload:
            info += "CPU Offload "
        if mem.vae_slicing:
            info += "VAE切片 "
        if mem.attention_slicing:
            info += "注意力切片 "
        return info.strip() or "⚡ 无特殊优化"
    
    def _scan_checkpoints(self):
        checkpoints = []
        checkpoint_paths = {}
        
        for search_dir in app_config.paths.model_base_paths:
            if not os.path.exists(search_dir):
                continue
            for item in os.listdir(search_dir):
                if item.endswith('.safetensors') or item.endswith('.ckpt'):
                    file_path = os.path.join(search_dir, item)
                    size_mb = os.path.getsize(file_path) // (1024 * 1024)
                    if size_mb >= 2000:
                        display_name = f"{item} ({size_mb}MB)"
                        checkpoints.append(display_name)
                        checkpoint_paths[display_name] = file_path
        
        return checkpoints, checkpoint_paths
    
    def _get_model_path(self, display_name: str) -> str:
        return self.checkpoint_paths.get(display_name)
    
    def _get_memory_usage(self):
        import psutil
        return psutil.Process().memory_info().rss / 1024 / 1024 / 1024
    
    def update_status(self, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        def update():
            self.status_var.set(message)
            print(f"[{timestamp}] [状态] {message}")
        self.root.after(0, update)
    
    def update_progress(self, value: float, message: str = ""):
        self.progress_bar.update(value, message)
    
    def add_to_preview(self, filepath: str, image):
        self.image_preview.add_image(filepath, image)
    
    def open_output_folder(self):
        """打开输出文件夹（自动创建并解析绝对路径）"""
        from config.app_config import app_config
        
        # ✅ 1. 获取解析后的绝对路径（你在 app_config.py 里已经实现了 resolve_path）
        output_dir = app_config.paths.get_resolved_output_dir()
        
        # ✅ 2. 如果文件夹不存在，自动创建它（防止报错）
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                print(f"📁 已自动创建输出目录: {output_dir}")
            except Exception as e:
                self.update_status(f"❌ 无法创建输出目录: {e}")
                return
        
        # ✅ 3. 使用绝对路径打开
        try:
            if sys.platform == 'win32':
                os.startfile(output_dir)
            else:
                os.system(f'open "{output_dir}"')
        except Exception as e:
            self.update_status(f"❌ 无法打开文件夹: {e}")
    
    def _on_batch_start(self):
        current_tab = self.notebook.select()
        tab_index = self.notebook.index(current_tab)
        tab_text = self.notebook.tab(tab_index, "text")
        
        prompts = self.batch_panel.get_prompts()
        if not prompts:
            messagebox.showwarning("提示", "请至少输入一组提示词")
            return
        
        if tab_text == "📝 文生图":
            self.txt2img_tab.batch_generate(prompts)
        elif tab_text == "💑 亲密文生图":
            self.scene_tab.batch_generate(prompts)
        elif tab_text == "🌍 通用生成器":
            self.universal_tab.batch_generate(prompts)
        elif tab_text == "🖼️ 图生图":
            self.img2img_tab.batch_generate(prompts)
        else:
            messagebox.showinfo("提示", "当前 Tab 不支持批量生成")
    
    def _create_tabs(self):
        from gui.tabs.txt2img_tab import Txt2ImgTab
        from gui.tabs.img2img_tab import Img2ImgTab
        from gui.tabs.interrogate_tab import InterrogateTab
        from gui.tabs.universal_tab import UniversalTab
        from gui.tabs.scene_tab import SceneTab
        from gui.tabs.janus_tab import JanusTab
        from gui.tabs.grid_test_tab import GridTestTab
        
        self.txt2img_tab = Txt2ImgTab(self.notebook, self)
        self.notebook.add(self.txt2img_tab.get_frame(), text="📝 文生图")
        
        self.scene_tab = SceneTab(self.notebook, self)
        self.notebook.add(self.scene_tab.get_frame(), text="💑 亲密文生图")
        
        self.universal_tab = UniversalTab(self.notebook, self)
        self.notebook.add(self.universal_tab.get_frame(), text="🌍 通用生成器")
        
        self.img2img_tab = Img2ImgTab(self.notebook, self)
        self.notebook.add(self.img2img_tab.get_frame(), text="🖼️ 图生图")
        
        self.interrogate_tab = InterrogateTab(self.notebook, self)
        self.notebook.add(self.interrogate_tab.get_frame(), text="🔍 图片反推")
        
        self.janus_tab = JanusTab(self.notebook, self, self.model_manager)
        self.notebook.add(self.janus_tab.get_frame(), text="🤖 Janus-Pro")
        
        self.grid_test_tab = GridTestTab(self.notebook, self)
        self.notebook.add(self.grid_test_tab.frame, text="🧪 网格测试")

        # ✅ 流水线标签页
        self.pipeline_tab = PipelineTab(self.notebook, self)
        self.notebook.add(self.pipeline_tab.get_frame(), text="🔧 流水线")        
        
    def _reload_modules(self):
        """热重载模块"""
        from config.app_config import AppConfig
        AppConfig.reload()
        
        # 更新参数面板的步骤和CFG值
        self.params_panel.set_params(
            steps=AppConfig.get_instance().generation.steps["default"],
            cfg=AppConfig.get_instance().generation.cfg["default"]
        )
        
        # 更新文生图的默认提示词
        if hasattr(self, 'txt2img_tab') and self.txt2img_tab:
            new_pos = AppConfig.get_instance().generation.positive_prompt
            new_neg = AppConfig.get_instance().generation.negative_prompt
            self.txt2img_tab.set_prompt(new_pos, new_neg)
        
        import importlib
        import sys
        
        # 检查是否有正在进行的生成任务
        if hasattr(self, 'txt2img_tab') and self.txt2img_tab:
            if hasattr(self.txt2img_tab, 'is_generating') and self.txt2img_tab.is_generating:
                messagebox.showwarning("提示", "文生图正在进行中，请等待完成后再重载")
                return
        
        if hasattr(self, 'img2img_tab') and self.img2img_tab:
            if hasattr(self.img2img_tab, 'is_generating') and self.img2img_tab.is_generating:
                messagebox.showwarning("提示", "图生图正在进行中，请等待完成后再重载")
                return
        
        if hasattr(self, 'grid_test_tab') and self.grid_test_tab:
            if hasattr(self.grid_test_tab, 'is_running') and self.grid_test_tab.is_running:
                messagebox.showwarning("提示", "网格测试正在进行中，请等待完成后再重载")
                return
        
        self.update_status("🔄 正在重载模块...")
        print("\n" + "=" * 60)
        print("🔄 开始热重载模块")
        print("=" * 60)
        
        modules_to_reload = [
            # ===== GUI 组件 =====
            "gui.components.memory_monitor",
            "gui.components.progress_bar",
            "gui.components.image_preview",
            "gui.components.params_panel",
            "gui.components.batch_panel",
            "gui.components.nsfw_panel", 
            
            # ===== GUI 标签页 =====
            "gui.tabs.base_tab",
            "gui.tabs.txt2img_tab",
            "gui.tabs.img2img_tab",
            "gui.tabs.interrogate_tab",
            "gui.tabs.universal_tab",
            "gui.tabs.scene_tab",
            "gui.tabs.janus_tab",
            "gui.tabs.grid_test_tab",
            "gui.tabs.pipeline_tab",  

            # ===== GUI 管理 =====
            "gui.scene_manager", 
            
            # ===== Core 模块 =====
            "core.janus_loader",
            "core.janus_generator",
            "core.janus_analyzer",
            "core.janus_chat",
            "core.grid_runner",  
            "core.nsfw_filter",            
            "core.pipeline",
            "core.pipeline.step",
            "core.pipeline.pipeline",
            "core.pipeline.steps",
            "core.pipeline.steps.marble_step",            

            # ===== Config 模块 =====
            "config.nsfw_config",
            "config.app_config",
            "config.janus_config",
        
            # ===== Utils 模块（全部添加） =====
            "utils",
            "utils.watermark_remover",
            "utils.imagemeta_cleaner",
            "utils.exif_injector",
            "utils.photo_realistic",
            "utils.image_post_processor",
            "utils.scheduler_factory",  # ✅ 新增   

            "utils.strength_tester",      # ✅ 新增
            "utils.scheduler_fix",        # ✅ 新增 

         
        ]
        
        reloaded = []
        failed = []
        
        for mod_name in modules_to_reload:
            try:
                if mod_name in sys.modules:
                    importlib.reload(sys.modules[mod_name])
                    print(f"   ✅ 重载: {mod_name}")
                    reloaded.append(mod_name)
                else:
                    print(f"   ⚠️ 跳过（未加载）: {mod_name}")
            except Exception as e:
                print(f"   ❌ 重载失败 {mod_name}: {e}")
                failed.append(mod_name)
        
        if failed:
            self.update_status(f"⚠️ 部分模块重载失败: {', '.join(failed)}")
            return
        
        # ===== 重建参数面板 =====
        try:
            parent_frame = self.params_panel.frame.master
            self.params_panel.rebuild(parent_frame)
            print("   ✅ 参数面板重建完成")
        except Exception as e:
            print(f"   ❌ 参数面板重建失败: {e}")
            self.update_status(f"❌ 参数面板重建失败: {e}")
            return
        
        # ===== 重建标签页 =====
        try:
            self._recreate_tabs()
            print("   ✅ 标签页重建完成")
        except Exception as e:
            print(f"   ❌ 标签页重建失败: {e}")
            self.update_status(f"❌ 标签页重建失败: {e}")
            return

        # ===== 【新增】重建 NSFW 面板 =====
        try:
            self._recreate_nsfw_panel()
            print("   ✅ NSFW 面板重建完成")
        except Exception as e:
            print(f"   ⚠️ NSFW 面板重建失败: {e}")
        
        # ===== 【关键修改】重新布局参数面板 =====
        try:
            # 获取参数面板的框架
            param_frame = self.params_panel.get_frame()
            if self.notebook and param_frame:
                # 1. 先强制从布局中移除（防止残留布局冲突）
                param_frame.pack_forget()
                
                # 2. 重新 pack 到 notebook 之前（顶部位置）
                # 注意：side=tk.TOP, fill=tk.X 确保它占据整个宽度并位于顶部
                param_frame.pack(
                    side=tk.TOP, 
                    fill=tk.X, 
                    padx=10, 
                    pady=5,
                    before=self.notebook
                )
                print("   ✅ 参数面板重定位完成")
        except Exception as e:
            print(f"   ⚠️ 参数面板重定位失败: {e}")
            # 如果 before 失败，尝试另一种方式
            try:
                param_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
                print("   ✅ 参数面板重定位完成 (备用方式)")
            except:
                pass

        # ===== 【新增】重新定位 NSFW 面板 =====
        try:
            if hasattr(self, 'nsfw_panel') and self.nsfw_panel:
                nsfw_frame = self.nsfw_panel.get_frame()
                if nsfw_frame and self.notebook:
                    # 确保 NSFW 面板在参数面板和标签页之间
                    nsfw_frame.pack_forget()
                    # 找到参数面板的位置
                    param_frame = self.params_panel.get_frame()
                    # 在参数面板之后、标签页之前插入
                    nsfw_frame.pack(
                        side=tk.TOP,
                        fill=tk.X,
                        padx=10,
                        pady=5,
                        before=self.notebook
                    )
                    print("   ✅ NSFW 面板重定位完成")
        except Exception as e:
            print(f"   ⚠️ NSFW 面板重定位失败: {e}")
        
        print("=" * 60)
        print(f"✅ 热重载完成！已重载 {len(reloaded)} 个模块")
        print("=" * 60)
        
        
        self.update_status(f"✅ 热重载完成！已重载 {len(reloaded)} 个模块")


    # gui/app.py - 新增方法

    def _recreate_nsfw_panel(self):
        """
        重建 NSFW 控制面板（用于热重载）
        """
        # 1. 销毁旧的 NSFW 面板
        if hasattr(self, 'nsfw_panel') and self.nsfw_panel:
            try:
                old_frame = self.nsfw_panel.get_frame()
                if old_frame and old_frame.winfo_exists():
                    old_frame.destroy()
                print("   🗑️ 旧 NSFW 面板已销毁")
            except Exception as e:
                print(f"   ⚠️ 销毁旧 NSFW 面板失败: {e}")
        
        # 2. 重新导入 NSFW 模块（确保使用最新代码）
        import importlib
        import sys
        
        try:
            # 重新加载 nsyw 相关模块
            for mod_name in ["gui.components.nsfw_panel", "core.nsfw_filter", "config.nsfw_config"]:
                if mod_name in sys.modules:
                    importlib.reload(sys.modules[mod_name])
        except Exception as e:
            print(f"   ⚠️ NSFW 模块重载失败: {e}")
        
        # 3. 重新创建 NSFW 面板
        from gui.components.nsfw_panel import NSFWPanel
        
        # 获取父容器（main_frame）
        main_frame = self.scrollable_frame
        
        # 创建新面板
        self.nsfw_panel = NSFWPanel(main_frame, self)
        nsfw_frame = self.nsfw_panel.get_frame()
        
        # 4. 放置到正确位置（参数面板之后，标签页之前）
        # 注意：因为参数面板和标签页都在 main_frame 中
        # 我们可以先 pack 到 main_frame，然后通过 before 参数调整顺序
        nsfw_frame.pack(
            side=tk.TOP,
            fill=tk.X,
            padx=10,
            pady=5
        )
        
        # 5. 调整顺序：确保 NSFW 面板在标签页之前
        if hasattr(self, 'notebook') and self.notebook:
            # 将 NSFW 面板移动到标签页之前
            nsfw_frame.pack_forget()
            nsfw_frame.pack(
                side=tk.TOP,
                fill=tk.X,
                padx=10,
                pady=5,
                before=self.notebook
            )
        
        print("   ✅ NSFW 面板已重建")
    
    def _recreate_tabs(self):
        from gui.tabs.txt2img_tab import Txt2ImgTab
        from gui.tabs.img2img_tab import Img2ImgTab
        from gui.tabs.interrogate_tab import InterrogateTab
        from gui.tabs.universal_tab import UniversalTab
        from gui.tabs.scene_tab import SceneTab
        from gui.tabs.janus_tab import JanusTab
        from gui.tabs.grid_test_tab import GridTestTab
        from gui.tabs.pipeline_tab import PipelineTab  # ✅ 添加这行
        
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        
        self.txt2img_tab = Txt2ImgTab(self.notebook, self)
        self.notebook.add(self.txt2img_tab.get_frame(), text="📝 文生图")
        
        self.scene_tab = SceneTab(self.notebook, self)
        self.notebook.add(self.scene_tab.get_frame(), text="💑 亲密文生图")
        
        self.img2img_tab = Img2ImgTab(self.notebook, self)
        self.notebook.add(self.img2img_tab.get_frame(), text="🖼️ 图生图")
        
        self.interrogate_tab = InterrogateTab(self.notebook, self)
        self.notebook.add(self.interrogate_tab.get_frame(), text="🔍 图片反推")
        
        self.universal_tab = UniversalTab(self.notebook, self)
        self.notebook.add(self.universal_tab.get_frame(), text="🌍 通用生成器")
        
        self.janus_tab = JanusTab(self.notebook, self, self.model_manager)
        self.notebook.add(self.janus_tab.get_frame(), text="🤖 Janus-Pro")
        
        self.grid_test_tab = GridTestTab(self.notebook, self)
        self.notebook.add(self.grid_test_tab.frame, text="🧪 网格测试")
        
        # ✅ 添加流水线标签页
        self.pipeline_tab = PipelineTab(self.notebook, self)
        self.notebook.add(self.pipeline_tab.get_frame(), text="🔧 流水线")        

        
    
    def run(self):
        self.root.mainloop()


def main():
    print("=" * 60)
    print("Stable Diffusion 桌面GUI版 - v8")
    print(f"输出目录: {app_config.paths.output_dir}")
    print("=" * 60)

    # ===== [新增] 全局禁用 CUDA =====
    import torch
    torch.cuda.is_available = lambda: False  # 强制让 PyTorch 认为 CUDA 不可用
    # ===== [新增] 结束 =====
    
    try:
        import torch
        print(f"PyTorch: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
    except:
        print("⚠️ PyTorch 未安装或导入失败")
    
    print("\n🌍 通用生成器已集成")
    print("💡 模型互斥加载: SD ↔ Janus 自动切换")
    print("=" * 60)
    
    app = SDApp()
    app.run()


if __name__ == "__main__":
    main()