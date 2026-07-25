# utils/pipeline_pool.py
"""
Pipeline 池 - 管理多个 pipeline 实例
增加内存感知和自动清理
"""

import os
import gc
import threading
import psutil
import torch
from typing import Dict, Optional, Tuple
from collections import OrderedDict
from datetime import datetime
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    EulerDiscreteScheduler,
)
from config.app_config import app_config
import logging

logger = logging.getLogger(__name__)


class PipelinePool:
    """
    Pipeline 池 - 管理多个 pipeline 实例
    
    特性:
    - 引用计数管理
    - 内存感知自动清理
    - 最大实例数限制
    - LRU 淘汰策略
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._pipelines: OrderedDict = OrderedDict()
        self._lock = threading.Lock()
        self._max_instances = getattr(app_config, 'max_pipeline_instances', 3)
        self._total_created = 0
        
        # 内存阈值 (GB)
        self._memory_threshold = 12.0
        self._cleanup_threshold = 85  # 内存使用百分比
    
    def _get_memory_usage(self) -> tuple:
        """获取内存使用情况"""
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            used_gb = mem_info.rss / 1024 / 1024 / 1024
            
            # 系统内存使用率
            vm = psutil.virtual_memory()
            percent = vm.percent
            
            return used_gb, percent
        except:
            return 0, 0
    
    def _should_cleanup(self) -> bool:
        """检查是否需要清理"""
        used_gb, percent = self._get_memory_usage()
        return used_gb > self._memory_threshold or percent > self._cleanup_threshold
    
    def _force_cleanup(self):
        """强制清理内存"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
        
        used_gb, _ = self._get_memory_usage()
        logger.info(f"🧹 内存清理完成，当前: {used_gb:.1f} GB")
    
    def get_pipeline(
        self,
        model_path: str,
        model_name: str,
        lora_path: str = None,
        lora_weight: float = 1.0,
        device: str = "cpu",
        task_id: str = None
    ) -> Tuple[object, bool]:
        """获取 pipeline 实例"""
        key = self._get_key(model_path, lora_path, task_id)
        
        with self._lock:
            # 检查是否已存在
            if key in self._pipelines:
                self._pipelines[key]["ref_count"] += 1
                self._pipelines.move_to_end(key)
                logger.debug(f"🔗 复用 Pipeline: {os.path.basename(model_path)} (引用: {self._pipelines[key]['ref_count']})")
                return self._pipelines[key]["pipe"], False
            
            # 检查内存压力
            if self._should_cleanup():
                logger.warning("⚠️ 内存压力大，执行清理...")
                self._cleanup_old_pipelines()
                self._force_cleanup()
            
            # 检查是否已达最大实例数
            if len(self._pipelines) >= self._max_instances:
                oldest_key, oldest_data = self._pipelines.popitem(last=False)
                self._release_pipe_internal(oldest_data)
                logger.info(f"🗑️ 释放旧的 Pipeline (达到上限 {self._max_instances})")
                gc.collect()
            
            # 创建新 pipeline
            logger.info(f"📦 创建新的 Pipeline ({self._total_created + 1}): {os.path.basename(model_path)}")
            
            is_sdxl = 'xl' in model_name.lower() or 'sdxl' in model_name.lower()
            
            common_kwargs = {
                "torch_dtype": torch.float32,
                "safety_checker": None,
                "requires_safety_checker": False,
                "use_safetensors": True,
                "low_cpu_mem_usage": True,
            }
            
            try:
                if is_sdxl:
                    pipe = StableDiffusionXLPipeline.from_single_file(model_path, **common_kwargs)
                else:
                    pipe = StableDiffusionPipeline.from_single_file(model_path, **common_kwargs)
                
                pipe.to(device)
                pipe.enable_vae_slicing()
                pipe.enable_attention_slicing()
                
                try:
                    if hasattr(pipe.vae, 'enable_tiling'):
                        pipe.vae.enable_tiling()
                except:
                    pass
                
                # 加载 LoRA
                if lora_path and os.path.exists(lora_path):
                    try:
                        logger.info(f"   🔗 加载 LoRA: {os.path.basename(lora_path)} (权重: {lora_weight})")
                        pipe.load_lora_weights(lora_path)
                    except Exception as e:
                        logger.warning(f"   ⚠️ LoRA 加载失败: {e}")
                
                # 配置调度器
                pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
                
                self._pipelines[key] = {
                    "pipe": pipe,
                    "ref_count": 1,
                    "model_path": model_path,
                    "lora_path": lora_path,
                    "lora_loaded": lora_path is not None,
                    "lora_name": os.path.basename(lora_path) if lora_path else None,
                    "lora_weight": lora_weight if lora_path else None,
                    "created": datetime.now(),
                    "last_used": datetime.now(),
                    "task_id": task_id,
                    "memory_usage": self._get_memory_usage()[0],
                }
                self._total_created += 1
                
                used_gb, _ = self._get_memory_usage()
                logger.info(f"✅ Pipeline 创建完成，当前内存: {used_gb:.1f} GB")
                
                return pipe, True
                
            except Exception as e:
                logger.error(f"❌ Pipeline 创建失败: {e}")
                import traceback
                traceback.print_exc()
                raise
    
    def _cleanup_old_pipelines(self):
        """清理引用计数为 0 的旧 Pipeline"""
        with self._lock:
            to_remove = []
            for key, data in self._pipelines.items():
                if data["ref_count"] <= 0:
                    to_remove.append(key)
            
            for key in to_remove:
                data = self._pipelines.pop(key)
                self._release_pipe_internal(data)
                logger.info(f"🗑️ 清理闲置 Pipeline")
    
    def release_pipeline(self, model_path: str, lora_path: str = None, task_id: str = None):
        """释放 pipeline 实例"""
        key = self._get_key(model_path, lora_path, task_id)
        
        with self._lock:
            if key not in self._pipelines:
                return
            
            self._pipelines[key]["ref_count"] -= 1
            self._pipelines[key]["last_used"] = datetime.now()
            
            if self._pipelines[key]["ref_count"] <= 0:
                data = self._pipelines.pop(key)
                self._release_pipe_internal(data)
                logger.info(f"🗑️ 释放 Pipeline: {os.path.basename(model_path)}")
                
                # 检查内存，必要时触发 GC
                used_gb, _ = self._get_memory_usage()
                if used_gb > self._memory_threshold:
                    self._force_cleanup()
    
    def _release_pipe_internal(self, data: dict):
        """内部释放 pipeline"""
        pipe = data.get("pipe")
        if pipe is not None:
            try:
                if hasattr(pipe, 'to'):
                    try:
                        pipe.to("cpu")
                    except:
                        pass
                del pipe
            except:
                pass
    
    def _get_key(self, model_path: str, lora_path: str = None, task_id: str = None) -> str:
        """生成唯一 key"""
        base = f"{model_path}|{lora_path}"
        if task_id:
            base = f"{base}|{task_id}"
        return base
    
    def get_status(self) -> dict:
        """获取当前状态"""
        with self._lock:
            used_gb, percent = self._get_memory_usage()
            return {
                "total_created": self._total_created,
                "active_count": len(self._pipelines),
                "max_instances": self._max_instances,
                "memory_usage_gb": round(used_gb, 1),
                "memory_percent": percent,
                "pipes": [
                    {
                        "key": k,
                        "ref_count": v["ref_count"],
                        "model": os.path.basename(v["model_path"]),
                        "lora": os.path.basename(v["lora_path"]) if v["lora_path"] else None,
                        "created": v.get("created", "").strftime("%H:%M:%S") if v.get("created") else "",
                    }
                    for k, v in self._pipelines.items()
                ]
            }


# 全局单例
pipeline_pool = PipelinePool()