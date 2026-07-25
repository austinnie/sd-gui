# gui/model_manager.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型管理器 - 管理 SD 和 Janus 模型的互斥加载
"""

import os
import threading
import torch
from enum import Enum
from typing import Optional, Callable
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    EulerDiscreteScheduler,
from utils.logger import get_logger, info, warning, error, debug

logger = get_logger(__name__)
)

from config.app_config import app_config
from gui.components.memory_monitor import force_memory_cleanup


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
        self._sd_model_type = None
        self._janus_loaded = False
        self._loading = False
        self._lock = threading.Lock()
        
        # LoRA 状态
        self._loaded_lora_path = None
        self._loaded_lora_type = None
        self._loaded_lora_compatible = True
        
        # 强制 CPU
        torch.device("cpu")
    
    # ==================== 属性 ====================
    
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
        return self._sd_model_type or "unknown"
    
    def get_status_text(self) -> str:
        """获取状态文本"""
        if self._current_type == ModelType.SD:
            name = self._sd_model_name[:40] if self._sd_model_name else "已加载"
            return f"🟢 SD: {name}"
        elif self._current_type == ModelType.JANUS:
            return "🟢 Janus-Pro"
        else:
            return "🔴 未加载模型"
    
    # ==================== SD 模型管理 ====================
    
    def load_sd(self, model_path: str, model_name: str,
                progress_callback: Optional[Callable] = None,
                lora_path: str = None, lora_weight: float = 1.0) -> bool:
        """加载 SD 模型"""
        with self._lock:
            if self._loading:
                return False
            self._loading = True

        try:
            # 卸载 Janus
            if self._current_type == ModelType.JANUS:
                self._unload_janus_internal()

            # 已加载相同模型
            if self._current_type == ModelType.SD and self._sd_model_name == model_name:
                return True

            if progress_callback:
                progress_callback(0.1, f"📦 加载模型...")

            # 判断模型类型
            model_name_lower = model_name.lower()
            is_sdxl = any(k in model_name_lower for k in ['xl', 'sdxl', 'sd_xl', 'pony'])
            
            if not is_sdxl and os.path.exists(model_path):
                file_size_gb = os.path.getsize(model_path) / (1024 ** 3)
                if file_size_gb > 4.0:
                    is_sdxl = True

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

            # 加载主模型
            if is_sdxl:
                pipe = StableDiffusionXLPipeline.from_single_file(model_path, **common_kwargs)
            else:
                pipe = StableDiffusionPipeline.from_single_file(model_path, **common_kwargs)

            if progress_callback:
                progress_callback(0.6, f"⚙️ 配置优化...")

            # 内存优化
            self._apply_memory_optimizations(pipe)

            # 配置调度器
            scheduler_name = self.app.params_panel.get_scheduler_type() if self.app else "dpm"
            self._configure_scheduler(pipe, scheduler_name, model_name_lower)

            # 加载 LoRA
            if lora_path and os.path.exists(lora_path):
                if progress_callback:
                    progress_callback(0.7, f"🔗 加载 LoRA...")
                success, is_compatible, detected_type = self._load_lora(
                    pipe, lora_path, lora_weight, is_sdxl
                )
                self._loaded_lora_path = lora_path if success else None
                self._loaded_lora_type = detected_type
                self._loaded_lora_compatible = is_compatible

            # CPU Offload
            if app_config.memory.enable_cpu_offload:
                try:
                    if torch.cuda.is_available():
                        if app_config.memory.enable_sequential_offload:
                            pipe.enable_sequential_cpu_offload()
                        else:
                            pipe.enable_model_cpu_offload()
                except Exception as e:
                    logger.info(f"⚠️ CPU Offload 启用失败: {e}")

            self._sd_pipe = pipe
            self._sd_model_name = model_name
            self._sd_model_type = "sdxl" if is_sdxl else "sd15"
            self._current_type = ModelType.SD

            if progress_callback:
                progress_callback(1.0, f"✅ SD 模型加载完成")

            force_memory_cleanup()
            return True

        except Exception as e:
            logger.info(f"❌ SD 模型加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            with self._lock:
                self._loading = False

    def _apply_memory_optimizations(self, pipe):
        """应用内存优化"""
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

    def _configure_scheduler(self, pipe, scheduler_name: str, model_name_lower: str):
        """配置调度器"""
        from utils.scheduler_factory import get_scheduler, get_scheduler_description
        
        is_lightning = "lightning" in model_name_lower
        
        if is_lightning:
            from diffusers import EulerDiscreteScheduler
            pipe.scheduler = EulerDiscreteScheduler.from_config(
                pipe.scheduler.config,
                timestep_spacing="trailing"
            )
            logger.info(f"⚡ Lightning 模型，已配置 EulerDiscreteScheduler (trailing)")
        else:
            try:
                pipe.scheduler = get_scheduler(scheduler_name, pipe.scheduler.config)
                desc = get_scheduler_description(scheduler_name)
                logger.info(f"✅ 使用调度器: {scheduler_name.upper()} ({desc})")
            except Exception as e:
                logger.info(f"⚠️ 调度器切换失败，使用默认: {e}")
                pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)

    def _detect_lora_type(self, lora_state_dict: dict) -> str:
        """检测 LoRA 类型"""
        keys = list(lora_state_dict.keys())
        
        if not keys:
            return 'unknown'
        
        sdxl_patterns = ['base_unet', 'lora_te1', 'text_encoder', 'time_embedding', 'transformer_blocks']
        sd15_patterns = ['lora_unet', 'lora_te', 'down_blocks', 'up_blocks', 'mid_block']
        
        keys_str = " ".join(keys).lower()
        
        sdxl_score = sum(1 for p in sdxl_patterns if p in keys_str)
        sd15_score = sum(1 for p in sd15_patterns if p in keys_str)
        
        has_sdxl_dim = any(k.startswith('base_unet') or k.startswith('lora_te1') for k in keys)
        has_sd15_dim = any(k.startswith('lora_unet') or k.startswith('lora_te') for k in keys)
        has_both_features = has_sdxl_dim and has_sd15_dim
        has_both_patterns = (sdxl_score >= 2 and sd15_score >= 2)
        
        if has_both_features or has_both_patterns:
            return 'both'
        if has_sdxl_dim or (sdxl_score > sd15_score and sdxl_score >= 2):
            return 'sdxl'
        elif has_sd15_dim or (sd15_score > sdxl_score and sd15_score >= 2):
            return 'sd15'
        else:
            return 'unknown'

    def _load_lora(self, pipe, lora_path: str, lora_weight: float, is_sdxl: bool,
                   skip_compatibility_check: bool = False) -> tuple:
        """加载 LoRA"""
        import safetensors.torch
        
        try:
            lora_name = os.path.basename(lora_path)
            logger.info(f"   🔗 加载 LoRA: {lora_name} (权重: {lora_weight})")
            logger.info(f"   📦 模型类型: {'SDXL' if is_sdxl else 'SD1.5'}")

            detected_type = 'unknown'
            lora_state_dict = None
            
            try:
                lora_state_dict = safetensors.torch.load_file(lora_path)
                detected_type = self._detect_lora_type(lora_state_dict)
                logger.info(f"   🏷️ 检测到 LoRA 类型: {detected_type.upper()}")
            except Exception as e:
                logger.info(f"   ⚠️ 无法检测 LoRA 类型: {e}")
                detected_type = 'unknown'

            is_compatible = True
            
            if not skip_compatibility_check:
                if detected_type == 'both':
                    logger.info(f"   ✅ 双兼容 LoRA (支持 SD1.5 和 SDXL)")
                elif detected_type == 'sdxl' and not is_sdxl:
                    logger.info(f"   ❌ 不兼容: LoRA 是 SDXL 格式，但当前模型是 SD1.5")
                    return False, False, detected_type
                elif detected_type == 'sd15' and is_sdxl:
                    logger.info(f"   ❌ 不兼容: LoRA 是 SD1.5 格式，但当前模型是 SDXL")
                    return False, False, detected_type

            # 尝试加载
            for method in self._get_lora_load_methods(pipe, lora_path, lora_weight, is_sdxl, lora_state_dict):
                try:
                    result = method()
                    if result:
                        logger.info(f"   ✅ LoRA 加载成功")
                        return True, is_compatible, detected_type
                except Exception as e:
                    logger.info(f"   ⚠️ 方法失败: {e}")
                    continue

            logger.info(f"   ❌ 所有 LoRA 加载方法均失败")
            return False, is_compatible, detected_type

        except Exception as e:
            logger.info(f"   ❌ LoRA 加载异常: {e}")
            import traceback
            traceback.print_exc()
            return False, False, 'unknown'

    def _get_lora_load_methods(self, pipe, lora_path, lora_weight, is_sdxl, lora_state_dict):
        """获取 LoRA 加载方法列表"""
        methods = []
        
        # 方法1: load_lora_weights + adapter_name
        methods.append(lambda: self._try_load_lora_method1(pipe, lora_path, lora_weight))
        
        # 方法2: load_lora_weights (无 adapter_name)
        methods.append(lambda: self._try_load_lora_method2(pipe, lora_path, lora_weight))
        
        # 方法3: 使用 state_dict 直接加载
        if lora_state_dict:
            methods.append(lambda: self._try_load_lora_method3(pipe, lora_state_dict, lora_weight))
        
        # 方法4: SDXL 专用 fuse_lora
        if is_sdxl:
            methods.append(lambda: self._try_load_lora_method4(pipe, lora_path, lora_weight))
        
        return methods

    def _try_load_lora_method1(self, pipe, lora_path, lora_weight):
        pipe.load_lora_weights(lora_path, adapter_name="lora_adapter")
        pipe.set_adapters(["lora_adapter"], adapter_weights=[lora_weight])
        return True

    def _try_load_lora_method2(self, pipe, lora_path, lora_weight):
        pipe.load_lora_weights(lora_path)
        if lora_weight != 1.0 and hasattr(pipe, 'set_adapters'):
            pipe.set_adapters(["default"], adapter_weights=[lora_weight])
        return True

    def _try_load_lora_method3(self, pipe, lora_state_dict, lora_weight):
        pipe.load_lora_weights(lora_state_dict)
        if lora_weight != 1.0 and hasattr(pipe, 'set_adapters'):
            pipe.set_adapters(["default"], adapter_weights=[lora_weight])
        return True

    def _try_load_lora_method4(self, pipe, lora_path, lora_weight):
        pipe.load_lora_weights(lora_path)
        pipe.fuse_lora(lora_weight)
        return True

    def load_lora_to_existing_pipe(self, lora_path: str, lora_weight: float = 1.0) -> tuple:
        """直接加载 LoRA 到现有 pipe"""
        if not self.is_sd_loaded or self._sd_pipe is None:
            return False, "主模型未加载"
        
        if not lora_path or not os.path.exists(lora_path):
            return False, f"LoRA 文件不存在: {lora_path}"
        
        is_sdxl = self._sd_model_type == "sdxl"
        
        success, is_compatible, detected_type = self._load_lora(
            self._sd_pipe, lora_path, lora_weight, is_sdxl
        )
        
        if success:
            self._loaded_lora_path = lora_path
            self._loaded_lora_type = detected_type
            self._loaded_lora_compatible = is_compatible
            return True, f"LoRA 加载成功 ({detected_type.upper()})"
        else:
            return False, f"LoRA 加载失败"

    def unload_lora_from_pipe(self) -> bool:
        """从当前 pipe 卸载 LoRA"""
        if not self.is_sd_loaded or self._sd_pipe is None:
            return False
        
        try:
            if hasattr(self._sd_pipe, 'unload_lora_weights'):
                self._sd_pipe.unload_lora_weights()
                self._loaded_lora_path = None
                self._loaded_lora_type = None
                self._loaded_lora_compatible = True
                return True
            
            if hasattr(self._sd_pipe, 'set_adapters'):
                self._sd_pipe.set_adapters([])
                self._loaded_lora_path = None
                return True
                
        except Exception as e:
            logger.info(f"   ⚠️ LoRA 卸载失败: {e}")
        
        return False

    # ==================== Janus 模型管理 ====================

    def load_janus(self, model_key: str = "1B", progress_callback=None) -> bool:
        """加载 Janus 模型"""
        with self._lock:
            if self._loading:
                return False
            self._loading = True
        
        try:
            if self._current_type == ModelType.SD:
                self._unload_sd_internal()
            
            if self._current_type == ModelType.JANUS and self._janus_loaded:
                return True
            
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
            logger.info(f"❌ Janus 模型加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            with self._lock:
                self._loading = False

    # ==================== 卸载方法 ====================

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

    def _unload_janus_internal(self):
        """内部卸载 Janus"""
        if self._janus_loaded:
            from core.janus_loader import janus_loader
            janus_loader.unload()
            self._janus_loaded = False
        if self._current_type == ModelType.JANUS:
            self._current_type = ModelType.NONE
        force_memory_cleanup()

    def unload_sd(self):
        """卸载 SD"""
        with self._lock:
            self._unload_sd_internal()

    def unload_janus(self):
        """卸载 Janus"""
        with self._lock:
            self._unload_janus_internal()

    def unload_all(self):
        """卸载所有模型"""
        with self._lock:
            self._unload_sd_internal()
            self._unload_janus_internal()

    def get_lora_status(self) -> dict:
        """获取 LoRA 状态"""
        return {
            "loaded": self._loaded_lora_path is not None,
            "path": self._loaded_lora_path,
            "type": self._loaded_lora_type,
            "compatible": self._loaded_lora_compatible
        }