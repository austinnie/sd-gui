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
from utils.scheduler_factory import get_scheduler, get_scheduler_description 
from gui.tabs.lora_manager_tab import LoraManagerTab
from gui.tabs.chat_tab import ChatTab  # 顶部导入

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
        self._sd_model_type = None  # ✅ 新增: "sd15" 或 "sdxl"
        self._janus_loaded = False
        self._loading = False
        self._lock = threading.Lock()
        # 记录 LoRA 加载状态
        self._loaded_lora_path = None
        self._loaded_lora_type = None
        self._loaded_lora_compatible = True        

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
    
    def get_sd_model_type(self) -> str:
        """获取当前 SD 模型类型: 'sd15' 或 'sdxl'"""
        return self._sd_model_type or "unknown"

    def get_lora_status(self) -> dict:
        """获取 LoRA 加载状态"""
        return {
            "loaded": self._loaded_lora_path is not None,
            "path": self._loaded_lora_path,
            "type": self._loaded_lora_type,
            "compatible": self._loaded_lora_compatible
        }
    
    def load_sd(self, model_path: str, model_name: str, progress_callback=None,
                lora_path: str = None, lora_weight: float = 1.0) -> bool:
        """
        加载 SD 模型（完整区分 SD1.5 和 SDXL）
        """
        with self._lock:
            if self._loading:
                return False
            self._loading = True

        try:
            # 1. 卸载 Janus（如果已加载）
            if self._current_type == ModelType.JANUS:
                self._unload_janus_internal()

            # 2. 如果已加载相同的 SD 模型，直接返回
            if self._current_type == ModelType.SD and self._sd_model_name == model_name:
                return True

            # 3. 判断模型类型
            if progress_callback:
                progress_callback(0.1, f"📦 加载模型...")

            from diffusers import (
                StableDiffusionPipeline,
                StableDiffusionXLPipeline,
                EulerDiscreteScheduler,
            )
            import torch

            # ===== 判断 SD1.5 / SDXL =====
            model_name_lower = model_name.lower()
            is_sdxl = any(k in model_name_lower for k in ['xl', 'sdxl', 'sd_xl', 'pony'])
            
            # 如果文件名没有明确标识，通过文件大小判断（SDXL 通常 > 4GB）
            if not is_sdxl and os.path.exists(model_path):
                file_size_gb = os.path.getsize(model_path) / (1024 ** 3)
                if file_size_gb > 4.0:
                    is_sdxl = True
            
            # 4. 加载模型
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
                progress_callback(0.3, f"🔄 加载权重 ({'SDXL' if is_sdxl else 'SD1.5'})...")

            # ===== 加载主模型 =====
            if is_sdxl:
                pipe = StableDiffusionXLPipeline.from_single_file(model_path, **common_kwargs)
                print(f"✅ SDXL 模型加载完成")
            else:
                pipe = StableDiffusionPipeline.from_single_file(model_path, **common_kwargs)
                print(f"✅ SD1.5 模型加载完成")

            # 5. 内存优化
            if progress_callback:
                progress_callback(0.6, f"⚙️ 配置优化...")

            # VAE 切片
            if app_config.memory.vae_slicing:
                try:
                    pipe.vae.enable_slicing()
                except:
                    pass

            # VAE Tiling
            if app_config.memory.vae_tiling:
                try:
                    pipe.vae.enable_tiling()
                except:
                    pass

            # Attention Slicing
            if app_config.memory.attention_slicing:
                try:
                    pipe.enable_attention_slicing()
                except:
                    pass

            # 6. 配置调度器
            scheduler_name = self.app.params_panel.get_scheduler_type() if self.app else "dpm"
            is_lightning = "lightning" in model_name_lower

            from utils.scheduler_factory import get_scheduler

            if is_lightning:
                from diffusers import EulerDiscreteScheduler
                pipe.scheduler = EulerDiscreteScheduler.from_config(
                    pipe.scheduler.config,
                    timestep_spacing="trailing"
                )
                print(f"⚡ Lightning 模型，已配置 EulerDiscreteScheduler (trailing)")
            else:
                try:
                    pipe.scheduler = get_scheduler(scheduler_name, pipe.scheduler.config)
                    from utils.scheduler_factory import get_scheduler_description
                    desc = get_scheduler_description(scheduler_name)
                    print(f"✅ 使用调度器: {scheduler_name.upper()} ({desc})")
                except Exception as e:
                    print(f"⚠️ 调度器切换失败，使用默认: {e}")
                    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)

            # 7. 加载 LoRA（区分 SD1.5 / SDXL）
            if lora_path and os.path.exists(lora_path):
                if progress_callback:
                    progress_callback(0.7, f"🔗 加载 LoRA...")

                success, is_compatible, detected_type = self._load_lora(
                    pipe, lora_path, lora_weight, is_sdxl
                )
    
                # 保存 LoRA 加载状态
                self._loaded_lora_path = lora_path if success else None
                self._loaded_lora_type = detected_type
                self._loaded_lora_compatible = is_compatible
                
                if success:
                    print(f"✅ LoRA 加载成功 ({detected_type.upper()})")
                else:
                    if not is_compatible:
                        expected_dir = "sdxl-lora" if is_sdxl else "sd15-lora"
                        print(f"⚠️ LoRA 与模型不兼容 ({detected_type.upper()})，请移动到 {expected_dir} 目录")
                    else:
                        print(f"⚠️ LoRA 加载失败，继续使用主模型")
                        

            # 8. CPU Offload（仅在有 CUDA 时启用）
            if app_config.memory.enable_cpu_offload:
                try:
                    if torch.cuda.is_available():
                        if app_config.memory.enable_sequential_offload:
                            pipe.enable_sequential_cpu_offload()
                        else:
                            pipe.enable_model_cpu_offload()
                except Exception as e:
                    print(f"⚠️ CPU Offload 启用失败: {e}")

            # 9. 保存
            self._sd_pipe = pipe
            self._sd_model_name = model_name
            self._sd_model_type = "sdxl" if is_sdxl else "sd15"  # ✅ 记录模型类型
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



    def _load_lora(self, pipe, lora_path: str, lora_weight: float, is_sdxl: bool) -> tuple:
        """
        加载 LoRA（完整区分 SD1.5 / SDXL）
        
        参数:
            pipe: diffusers pipeline
            lora_path: LoRA 文件路径
            lora_weight: LoRA 权重 (0.0 - 2.0)
            is_sdxl: 是否为 SDXL 模型
        
        返回:
            (success: bool, is_compatible: bool, detected_type: str)
            - success: 是否加载成功
            - is_compatible: LoRA 是否与模型兼容
            - detected_type: 检测到的 LoRA 类型 ('sd15', 'sdxl', 'unknown')
        """
        import safetensors.torch
        
        try:
            lora_name = os.path.basename(lora_path)
            print(f"   🔗 加载 LoRA: {lora_name} (权重: {lora_weight})")
            print(f"   📦 模型类型: {'SDXL' if is_sdxl else 'SD1.5'}")

            # ============================================================
            # 步骤 1: 检测 LoRA 类型（通过读取文件内容）
            # ============================================================
            detected_type = 'unknown'
            try:
                lora_state_dict = safetensors.torch.load_file(lora_path)
                first_keys = list(lora_state_dict.keys())[:5]
                print(f"   🔍 LoRA 层前缀: {[k.split('.')[0] for k in first_keys]}")
                
                # 判断 LoRA 类型
                # SDXL LoRA 通常包含: base_unet, lora_te1, text_encoder
                # SD1.5 LoRA 通常包含: lora_unet, lora_te
                is_lora_sdxl = any(
                    k.startswith('base_unet') or 
                    k.startswith('lora_te1') or 
                    k.startswith('text_encoder') or
                    ('unet' in k and 'time_embedding' in k)
                    for k in lora_state_dict.keys()
                )
                
                # 进一步判断：检查是否有 SDXL 特有的 key
                has_sdxl_keys = any(
                    'mid_block' in k and ('time_embedding' in k or 'resnets' in k)
                    for k in lora_state_dict.keys()
                )
                
                if is_lora_sdxl or has_sdxl_keys:
                    detected_type = 'sdxl'
                else:
                    # SD1.5 的 key 通常是 lora_unet_xxx 或 lora_te_xxx
                    detected_type = 'sd15'
                
                print(f"   🏷️ 检测到 LoRA 类型: {detected_type.upper()}")
                
            except Exception as e:
                print(f"   ⚠️ 无法检测 LoRA 类型: {e}")
                detected_type = 'unknown'

            # ============================================================
            # 步骤 2: 兼容性检查
            # ============================================================
            is_compatible = True
            
            if detected_type == 'sdxl' and not is_sdxl:
                print(f"   ❌ 不兼容: LoRA 是 SDXL 格式，但当前模型是 SD1.5")
                print(f"   💡 请将 {lora_name} 移动到 sdxl-lora 目录")
                return False, False, detected_type
            
            elif detected_type == 'sd15' and is_sdxl:
                print(f"   ❌ 不兼容: LoRA 是 SD1.5 格式，但当前模型是 SDXL")
                print(f"   💡 请将 {lora_name} 移动到 sd15-lora 目录")
                return False, False, detected_type
            
            elif detected_type == 'unknown':
                print(f"   ⚠️ 无法确定 LoRA 类型，尝试加载...")

            # ============================================================
            # 步骤 3: 尝试加载 LoRA（多种方法）
            # ============================================================
            
            # 方法 1: 使用 load_lora_weights + adapter_name (推荐)
            try:
                pipe.load_lora_weights(lora_path, adapter_name="lora_adapter")
                pipe.set_adapters(["lora_adapter"], adapter_weights=[lora_weight])
                print(f"   ✅ LoRA 加载成功 (方法1: load_lora_weights + adapter_name)")
                return True, is_compatible, detected_type
            except Exception as e:
                print(f"   ⚠️ 方法1 失败: {e}")

            # 方法 2: 使用 load_lora_weights (不加 adapter_name)
            try:
                pipe.load_lora_weights(lora_path)
                if lora_weight != 1.0 and hasattr(pipe, 'lora_weights'):
                    for key in pipe.lora_weights.keys():
                        pipe.lora_weights[key] = lora_weight
                print(f"   ✅ LoRA 加载成功 (方法2: load_lora_weights 无 adapter_name)")
                return True, is_compatible, detected_type
            except Exception as e:
                print(f"   ⚠️ 方法2 失败: {e}")

            # 方法 3: SDXL 专用 - 使用 fuse_lora
            if is_sdxl:
                try:
                    pipe.load_lora_weights(lora_path)
                    pipe.fuse_lora(lora_weight)
                    print(f"   ✅ LoRA 加载成功 (方法3: fuse_lora, 权重 {lora_weight})")
                    return True, is_compatible, detected_type
                except Exception as e:
                    print(f"   ⚠️ 方法3 (fuse_lora) 失败: {e}")

                try:
                    from diffusers.loaders import LoraLoaderMixin
                    pipe = LoraLoaderMixin.load_lora_weights(pipe, lora_path)
                    print(f"   ✅ LoRA 加载成功 (方法3备用: LoraLoaderMixin)")
                    return True, is_compatible, detected_type
                except Exception as e:
                    print(f"   ⚠️ 方法3备用 失败: {e}")

            # 方法 4: 使用 peft (需要 pip install peft)
            try:
                from peft import PeftModel
                pipe.unet.load_adapter(lora_path, adapter_name="lora")
                pipe.unet.set_adapter("lora")
                if lora_weight != 1.0:
                    pipe.unet.set_adapters(["lora"], adapter_weights=[lora_weight])
                print(f"   ✅ LoRA 加载成功 (方法4: peft)")
                return True, is_compatible, detected_type
            except ImportError:
                print(f"   ⚠️ peft 未安装，跳过方法4")
            except Exception as e:
                print(f"   ⚠️ 方法4 (peft) 失败: {e}")

            # 方法 5: 手动加载 .safetensors 权重 (最后手段)
            try:
                if 'lora_state_dict' not in locals():
                    lora_state_dict = safetensors.torch.load_file(lora_path)
                
                pipe.load_lora_weights(lora_state_dict)
                if lora_weight != 1.0 and hasattr(pipe, 'lora_weights'):
                    for key in pipe.lora_weights.keys():
                        pipe.lora_weights[key] = lora_weight
                print(f"   ✅ LoRA 加载成功 (方法5: 手动加载)")
                return True, is_compatible, detected_type
                
            except Exception as e:
                print(f"   ⚠️ 方法5 (手动加载) 失败: {e}")

            # ===== 所有方法都失败 =====
            print(f"   ❌ 所有 LoRA 加载方法均失败")
            return False, is_compatible, detected_type

        except Exception as e:
            print(f"   ❌ LoRA 加载异常: {e}")
            import traceback
            traceback.print_exc()
            return False, False, 'unknown'
        

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

    def get_sd_model_type(self) -> str:
        """获取当前 SD 模型类型: 'sd15' 或 'sdxl'"""
        return self.model_manager.get_sd_model_type()
    
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


    def show_pipeline_status(self):
        """显示 Pipeline 池状态（调试用）"""
        from utils.pipeline_pool import pipeline_pool
        status = pipeline_pool.get_status()
        
        print("\n" + "=" * 60)
        print("📊 Pipeline 池状态 (调试信息)")
        print(f"   总创建: {status['total_created']}")
        print(f"   活跃数: {status['active_count']}")
        print(f"   最大数: {status['max_instances']}")
        print("-" * 60)
        for pipe_info in status.get("pipes", []):
            lora_status = f"🔗 {pipe_info['lora']}" if pipe_info.get('lora_loaded') else "无 LoRA"
            print(f"   - {pipe_info['model']}")
            print(f"     引用: {pipe_info['ref_count']}, {lora_status}")
            if pipe_info.get('created'):
                print(f"     创建: {pipe_info['created']}")
            if pipe_info.get('last_used'):
                print(f"     最后使用: {pipe_info['last_used']}")
        print("=" * 60)

    
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
        self._current_lora_path = None  # 记录当前加载的 LoRA 路径
        self._sd_model_type = None      # ✅ 新增：记录模型类型
    
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
        model_frame.pack(fill=tk.X, pady=2, padx=5)
        
        ttk.Label(model_frame, text="📦 SD 模型:").pack(side=tk.LEFT, padx=5)
        
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, width=45)  # ✅ 固定宽度
        self.model_combo.pack(side=tk.LEFT, padx=5)
        
        self.load_btn = ttk.Button(model_frame, text="加载 SD", command=self._load_sd_model)
        self.load_btn.pack(side=tk.LEFT, padx=2)
        
        self.reload_btn = ttk.Button(model_frame, text="🔄 重载模块", command=self._reload_modules)
        self.reload_btn.pack(side=tk.LEFT, padx=2)

        # ===== LoRA 选择 =====
        lora_frame = ttk.Frame(main_frame)
        lora_frame.pack(fill=tk.X, pady=2, padx=5)
        
        ttk.Label(lora_frame, text="🔗 LoRA 模型:").pack(side=tk.LEFT, padx=5)
        
        self.lora_var = tk.StringVar(value="")
        self.lora_combo = ttk.Combobox(lora_frame, textvariable=self.lora_var, width=45)  # ✅ 固定宽度
        self.lora_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(lora_frame, text="权重:").pack(side=tk.LEFT, padx=5)
        self.lora_weight_var = tk.DoubleVar(value=1.0)
        self.lora_weight_spinbox = ttk.Spinbox(
            lora_frame,
            from_=0.0,
            to=2.0,
            increment=0.1,
            textvariable=self.lora_weight_var,
            width=6
        )
        self.lora_weight_spinbox.pack(side=tk.LEFT, padx=2)



        # ✅ 按钮放在右侧
        btn_container = ttk.Frame(lora_frame)
        btn_container.pack(side=tk.LEFT, padx=5)
        
        self.load_lora_btn = ttk.Button(btn_container, text="📦 加载 LoRA", command=self._load_lora_from_ui, width=12)
        self.load_lora_btn.pack(side=tk.LEFT, padx=2)
        
        self.unload_lora_btn = ttk.Button(btn_container, text="🗑️ 卸载 LoRA", command=self._unload_lora, state=tk.DISABLED, width=12)
        self.unload_lora_btn.pack(side=tk.LEFT, padx=2)
        
        self.clear_lora_btn = ttk.Button(btn_container, text="✖ 清除", command=self._clear_lora, width=8)
        self.clear_lora_btn.pack(side=tk.LEFT, padx=2)

        # ===== VAE 选择 =====
        vae_frame = ttk.Frame(main_frame)
        vae_frame.pack(fill=tk.X, pady=2, padx=5)
        
        ttk.Label(vae_frame, text="🎨 VAE 模型:").pack(side=tk.LEFT, padx=5)
        
        self.vae_var = tk.StringVar(value="")
        # ✅ 限制宽度
        self.vae_combo = ttk.Combobox(vae_frame, textvariable=self.vae_var, width=45)
        self.vae_combo.pack(side=tk.LEFT, padx=5)
        
        vae_btn_container = ttk.Frame(vae_frame)
        vae_btn_container.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(vae_btn_container, text="📦 加载 VAE", command=self._load_vae, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(vae_btn_container, text="🗑️ 卸载 VAE", command=self._unload_vae, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(vae_btn_container, text="✖ 清除 VAE", command=self._clear_vae, width=12).pack(side=tk.LEFT, padx=2)        
            
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


        # ✅ 扫描 LoRA
        self.lora_files, self.lora_paths = self._scan_loras()
        self.lora_combo['values'] = self.lora_files
        if self.lora_files:
            self.lora_var.set("")  # 默认不选择

        # ✅ 扫描 VAE
        self.vae_files, self.vae_paths = self._scan_vaes()
        self.vae_combo['values'] = self.vae_files
        if self.vae_files:
            self.vae_var.set("")  # 默认不选择
    
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
            
        # ✅ 获取 LoRA 信息
        lora_display = self.lora_var.get()
        lora_path = None
        lora_weight = 1.0
        if lora_display and lora_display in self.lora_paths:
            lora_path = self.lora_paths[lora_display]
            lora_weight = self.lora_weight_var.get()
            print(f"🔗 将加载 LoRA: {lora_display} (权重: {lora_weight})")
        
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
            model_type = self.model_manager.get_sd_model_type()
            self.update_status(f"✅ SD 模型加载完成 ({model_type.upper()}, 内存: {mem_gb:.1f} GB)")
            self.update_progress(1.0, "✅ SD 模型就绪")
            
            # ✅ 显示 LoRA 状态
            lora_status = self.model_manager.get_lora_status()
            if lora_status["loaded"]:
                lora_name = os.path.basename(lora_status["path"])
                lora_type = lora_status["type"] or "unknown"
                
                if lora_status["compatible"]:
                    self.update_status(f"✅ SD 模型加载完成 | 🔗 LoRA: {lora_name} ({lora_type.upper()})")
                else:
                    self.update_status(f"⚠️ LoRA 不兼容 ({lora_name})，已跳过")
                    # 弹窗提示
                    expected = "SDXL" if model_type == "sdxl" else "SD1.5"
                    messagebox.showwarning(
                        "LoRA 不兼容",
                        f"LoRA 与当前模型不兼容\n\n"
                        f"当前模型: {model_type.upper()}\n"
                        f"LoRA 类型: {lora_type.upper()}\n\n"
                        f"请将 LoRA 移动到正确的目录:\n"
                        f"• {expected} LoRA → {'sdxl-lora' if model_type == 'sdxl' else 'sd15-lora'}"
                    )
            
            # ✅ 更新 LoRA 状态
            self._update_lora_status()

            # ✅ VAE 加载状态（如果之前选过 VAE，自动加载）
            if hasattr(self, 'vae_var') and self.vae_var.get():
                self._load_vae()            
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

    def _scan_loras(self):
        """扫描所有 LoRA 文件"""
        lora_files = []
        lora_paths = {}
        
        for search_dir in app_config.paths.lora_base_paths:
            if not os.path.exists(search_dir):
                continue
            for item in os.listdir(search_dir):
                if item.endswith('.safetensors'):
                    file_path = os.path.join(search_dir, item)
                    size_mb = os.path.getsize(file_path) // (1024 * 1024)
                    display_name = f"{item} ({size_mb}MB)"
                    lora_files.append(display_name)
                    lora_paths[display_name] = file_path
        
        return lora_files, lora_paths


    def _load_lora_from_ui(self):
        """加载选中的 LoRA - 直接重新加载主模型"""
        lora_display = self.lora_var.get()
        if not lora_display:
            messagebox.showwarning("提示", "请先选择 LoRA 模型")
            return
        
        if lora_display not in self.lora_paths:
            messagebox.showwarning("提示", "找不到 LoRA 文件")
            return
        
        if not self.model_manager.is_sd_loaded:
            if messagebox.askyesno("提示", "主模型未加载，是否同时加载主模型和 LoRA？"):
                self._load_sd_model()
            return
        
        lora_path = self.lora_paths[lora_display]
        lora_weight = self.lora_weight_var.get()
        
        self.update_status(f"🔗 正在加载 LoRA: {lora_display}...")
        self.load_lora_btn.config(state=tk.DISABLED)
        
        app = self

        def load_thread():
            try:
                model_name = self.model_var.get()
                model_path = self._get_model_path(model_name)
                
                if not model_path:
                    app.root.after(0, lambda: app._on_lora_load_error("找不到模型文件"))
                    return
                
                def progress_cb(value, msg):
                    app.root.after(0, lambda: app.update_progress(value, msg))
                
                # ✅ 直接重新加载主模型，带上 LoRA
                success = app.model_manager.load_sd(
                    model_path, model_name, progress_cb,
                    lora_path=lora_path,
                    lora_weight=lora_weight
                )
                
                if success:
                    app._current_lora_path = lora_path
                    app.root.after(0, lambda: app._on_lora_load_success(lora_display))
                else:
                    app.root.after(0, lambda: app._on_lora_load_error("模型加载失败"))
                
            except Exception as e:
                app.root.after(0, lambda err=e: app._on_lora_load_error(str(err)))
        
        threading.Thread(target=load_thread, daemon=True).start()
        
    def _on_lora_already_loaded(self, lora_display):
        """LoRA 已经加载时的提示"""
        self.load_lora_btn.config(state=tk.NORMAL)
        self.unload_lora_btn.config(state=tk.NORMAL)  # ✅ 已经有了
        self.update_status(f"ℹ️ LoRA 已加载: {lora_display}")
        messagebox.showinfo(
            "提示", 
            f"LoRA 已经加载:\n{lora_display}\n\n"
            f"如需重新加载，请先点击「卸载 LoRA」"
        )
    
    def _on_lora_load_success(self, lora_display):
        """LoRA 加载成功"""
        self.load_lora_btn.config(state=tk.NORMAL)
        self.unload_lora_btn.config(state=tk.NORMAL)
        self.update_status(f"✅ LoRA 加载成功: {lora_display}")

    def _on_lora_load_error(self, error):
        """LoRA 加载失败"""
        self.load_lora_btn.config(state=tk.NORMAL)
        self.update_status(f"❌ LoRA 加载失败: {error}")
        messagebox.showerror("错误", f"LoRA 加载失败:\n{error}")

    def _unload_lora(self):
        """卸载 LoRA（重新加载主模型，不带 LoRA）"""
        if not self.model_manager.is_sd_loaded:
            return
        
        if not messagebox.askyesno("确认卸载", "卸载 LoRA 将重新加载主模型，确定吗？"):
            return
        
        self.update_status("🔄 正在卸载 LoRA...")
        self.unload_lora_btn.config(state=tk.DISABLED)
        
        self.lora_var.set("")
        self.lora_weight_var.set(1.0)
        self._current_lora_path = None
        
        model_name = self.model_var.get()
        if model_name and model_name in self.checkpoint_paths:
            model_path = self.checkpoint_paths[model_name]
            
            app = self
            
            def reload_thread():
                def progress_cb(value, msg):
                    app.root.after(0, lambda: app.update_progress(value, msg))
                
                # ✅ 重新加载时不带 LoRA
                success = app.model_manager.load_sd(
                    model_path, model_name, progress_cb,
                    lora_path=None, lora_weight=1.0
                )
                app.root.after(0, lambda: app._on_lora_unload_complete(success))
            
            threading.Thread(target=reload_thread, daemon=True).start()
        else:
            self.unload_lora_btn.config(state=tk.NORMAL)
            
    def _on_lora_unload_complete(self, success):
        """LoRA 卸载完成"""
        self.unload_lora_btn.config(state=tk.DISABLED)
        self.load_lora_btn.config(state=tk.NORMAL)
        
        if success:
            self.update_status("✅ LoRA 已卸载")
        else:
            self.update_status("❌ LoRA 卸载失败")
        
        
    def _clear_lora(self):
        """清除 LoRA 选择"""
        self.lora_var.set("")
        self.lora_weight_var.set(1.0)
        
        # ===== 清除记录的 LoRA 路径 =====
        self._current_lora_path = None
        
        self._update_lora_status()
        
        # 如果模型已加载，重新加载以移除 LoRA
        if self.model_manager.is_sd_loaded:
            model_name = self.model_var.get()
            if model_name and model_name in self.checkpoint_paths:
                self._load_sd_model()
            
    def _update_lora_status(self):
        """更新 LoRA 状态显示"""
        lora_name = self.lora_var.get()
        if lora_name:
            weight = self.lora_weight_var.get()
            self.update_status(f"🔗 LoRA: {lora_name} (权重: {weight:.1f})")
        else:
            self.update_status("🔗 未加载 LoRA")

    def _scan_vaes(self):
        """扫描所有 VAE 文件"""
        vae_files = []
        vae_paths = {}
        
        # 常见 VAE 存放位置
        vae_dirs = [
            "./models/vae",
            "../models/vae",
        ]
        
        for search_dir in vae_dirs:
            if not os.path.exists(search_dir):
                continue
            for item in os.listdir(search_dir):
                if item.endswith('.safetensors'):
                    file_path = os.path.join(search_dir, item)
                    size_mb = os.path.getsize(file_path) // (1024 * 1024)
                    display_name = f"{item} ({size_mb}MB)"
                    vae_files.append(display_name)
                    vae_paths[display_name] = file_path
        
        # 去重（如果多个目录有同名文件，保留第一个）
        seen = set()
        unique_files = []
        unique_paths = {}
        for f, p in zip(vae_files, vae_paths.values()):
            if f not in seen:
                seen.add(f)
                unique_files.append(f)
                unique_paths[f] = p
        
        return unique_files, unique_paths

    def _load_vae(self):
        """加载 VAE"""
        vae_display = self.vae_var.get()
        if not vae_display:
            messagebox.showwarning("提示", "请先选择 VAE 模型")
            return
        
        if vae_display not in self.vae_paths:
            messagebox.showwarning("提示", "找不到 VAE 文件")
            return
        
        if not self.model_manager.is_sd_loaded:
            messagebox.showwarning("提示", "请先加载主模型")
            return
        
        vae_path = self.vae_paths[vae_display]
        
        try:
            from utils.vae_utils import load_vae
            
            self.update_status(f"🎨 加载 VAE...")
            vae = load_vae(vae_path)
            self.model_manager._sd_pipe.vae = vae
            self.update_status(f"✅ VAE 加载成功: {vae_display}")
        except Exception as e:
            self.update_status(f"❌ VAE 加载失败: {e}")
            messagebox.showerror("错误", f"VAE 加载失败:\n{str(e)}")

    def _unload_vae(self):
        """卸载 VAE（恢复默认 VAE）"""
        if not self.model_manager.is_sd_loaded:
            messagebox.showwarning("提示", "请先加载主模型")
            return
        
        if not hasattr(self.model_manager, '_sd_pipe') or self.model_manager._sd_pipe is None:
            messagebox.showwarning("提示", "没有加载的模型")
            return
        
        try:
            # 重新加载主模型（不带 VAE）
            model_name = self.model_var.get()
            model_path = self._get_model_path(model_name)
            
            if model_name and model_path:
                self.update_status("🔄 正在卸载 VAE...")
                
                # 清除 VAE 选择
                self.vae_var.set("")
                
                # 重新加载模型（不带 VAE）
                def progress_cb(value, msg):
                    self.root.after(0, lambda: self.update_progress(value, msg))
                
                # 使用当前模型重新加载，不带 VAE
                success = self.model_manager.load_sd(
                    model_path, model_name, progress_cb,
                    lora_path=None, lora_weight=1.0
                )
                
                if success:
                    self.update_status("✅ VAE 已卸载（使用默认 VAE）")
                else:
                    self.update_status("❌ VAE 卸载失败")
                    
        except Exception as e:
            self.update_status(f"❌ VAE 卸载失败: {e}")
            messagebox.showerror("错误", f"VAE 卸载失败:\n{str(e)}")
        
    def _clear_vae(self):
        """清除 VAE（恢复默认）"""
        if not self.model_manager.is_sd_loaded:
            return
        
        self.vae_var.set("")
        self.update_status("🔄 清除 VAE...")
        
        # 重新加载主模型（不带 VAE）
        model_name = self.model_var.get()
        model_path = self._get_model_path(model_name)
        if model_name and model_path:
            self._load_sd_model()
        
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
        from gui.tabs.lora_manager_tab import LoraManagerTab  # ✅ 新增
        
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

        # ✅ 新增 LoRA 管理标签页
        self.lora_manager_tab = LoraManagerTab(self.notebook, self)
        self.notebook.add(self.lora_manager_tab.get_frame(), text="🔧 LoRA 管理")
        
        # ✅ 新增智能会话标签页
        self.chat_tab = ChatTab(self.notebook, self)
        self.notebook.add(self.chat_tab.get_frame(), text="💬 智能生图")        
    
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

        if hasattr(self, 'lora_manager_tab') and self.lora_manager_tab:  # ✅ 新增
            if hasattr(self.lora_manager_tab, 'is_testing') and self.lora_manager_tab.is_testing:
                messagebox.showwarning("提示", "LoRA 测试正在进行中，请等待完成后再重载")
                return
            if hasattr(self.lora_manager_tab, 'is_scanning') and self.lora_manager_tab.is_scanning:
                messagebox.showwarning("提示", "LoRA 扫描正在进行中，请等待完成后再重载")
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
            "gui.tabs.lora_manager_tab",  # ✅ 新增
            "gui.tabs.chat_tab",  # ✅ 新增
            
            
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

            "utils.pipeline_pool",  # ✅ 新增
            
            "utils.vae_utils", 
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
        from gui.tabs.lora_manager_tab import LoraManagerTab  # ✅ 新增
        from gui.tabs.chat_tab import ChatTab  # ✅ 新增
        
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

        # ✅ 新增 LoRA 管理标签页
        self.lora_manager_tab = LoraManagerTab(self.notebook, self)
        self.notebook.add(self.lora_manager_tab.get_frame(), text="🔧 LoRA 管理")
        
        # ✅ 新增智能会话标签页
        self.chat_tab = ChatTab(self.notebook, self)
        self.notebook.add(self.chat_tab.get_frame(), text="💬 智能生图")        
        
    
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