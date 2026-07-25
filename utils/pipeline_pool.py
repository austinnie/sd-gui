# utils/pipeline_pool.py
"""
Pipeline 池 - 管理多个 pipeline 实例
支持多个并发任务，每个任务使用独立的 pipeline
"""

import os
import gc
import threading
import torch
from typing import Dict, Optional, Tuple
from collections import OrderedDict
from datetime import datetime

from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    EulerDiscreteScheduler,
from utils.logger import get_logger, info, warning, error, debug

logger = get_logger(__name__)
)
import psutil  # 顶部添加导入
from config.app_config import app_config

class PipelinePool:
    """Pipeline 池 - 管理多个 pipeline 实例，每个任务独立"""
    
    _instance = None
    
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
    
    def get_pipeline(self, model_path: str, model_name: str,
                     lora_path: str = None, lora_weight: float = 1.0,
                     device: str = "cpu", task_id: str = None) -> Tuple[object, bool]:
        """
        获取 pipeline 实例（引用计数 +1）
        参数:
            model_path: 模型路径
            model_name: 模型名称
            lora_path: LoRA 路径（可选）
            lora_weight: LoRA 权重（可选）
            device: 设备（默认 cpu）
            task_id: 任务 ID，用于区分不同任务（可选）
            
        返回:
            (pipeline, is_new) 是否是新创建的
        """
        key = self._get_key(model_path, lora_path, task_id)  # ✅ 传入 task_id
        
        with self._lock:
            # 检查是否已存在
            if key in self._pipelines:
                self._pipelines[key]["ref_count"] += 1
                self._pipelines.move_to_end(key)
                logger.info(f"🔗 复用 Pipeline: {os.path.basename(model_path)} (引用: {self._pipelines[key]['ref_count']})")
                return self._pipelines[key]["pipe"], False
            
            # 检查是否已达最大实例数
            if len(self._pipelines) >= self._max_instances:
                oldest_key, oldest_data = self._pipelines.popitem(last=False)
                self._release_pipe_internal(oldest_data)
                logger.info(f"🗑️ 释放旧的 Pipeline (达到上限 {self._max_instances})")
                gc.collect()
            
            # 创建新 pipeline
            logger.info(f"📦 创建新的 Pipeline ({self._total_created + 1}): {os.path.basename(model_path)} (任务: {task_id})")
            
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
                        logger.info(f"   ⚠️ LoRA 加载失败: {e}")
                
                # 配置调度器
                pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
                
                self._pipelines[key] = {
                    "pipe": pipe,
                    "ref_count": 1,
                    "model_path": model_path,
                    "lora_path": lora_path,
                    "lora_loaded": lora_path is not None,  # ← 新增
                    "lora_name": os.path.basename(lora_path) if lora_path else None,  # ← 新增
                    "lora_weight": lora_weight if lora_path else None,  # ← 新增                    
                    "created": datetime.now(),
                    "last_used": datetime.now(),  # ← 新增
                    "task_id": task_id  # ← 新增                    
                }
                self._total_created += 1
                
                # ✅ 添加内存信息
                import psutil
                mem_gb = psutil.Process().memory_info().rss / 1024 / 1024 / 1024
                logger.info(f"✅ Pipeline 创建完成 (任务: {task_id})")  # ← 加这行
                
                return pipe, True
                
            except Exception as e:
                logger.info(f"❌ Pipeline 创建失败: {e}")
                import traceback
                traceback.print_exc()
                raise
    
    def release_pipeline(self, model_path: str, lora_path: str = None, task_id: str = None):
        """释放 pipeline 实例（引用计数 -1）"""
        key = self._get_key(model_path, lora_path, task_id)  # ✅ 传入 task_id
        logger.info(f"🔧 release_pipeline: task_id={task_id}, key={key}")
        with self._lock:
            if key not in self._pipelines:
                logger.info(f"⚠️ Pipeline 不存在: {key}")
                # 列出所有现有的 key
                logger.info(f"   现有 keys: {list(self._pipelines.keys())}")            
                return
            
            self._pipelines[key]["ref_count"] -= 1
            logger.info(f"📊 Pipeline 引用计数: {self._pipelines[key]['ref_count']}")
            
            if self._pipelines[key]["ref_count"] <= 0:
                data = self._pipelines.pop(key)
                self._release_pipe_internal(data)
                logger.info(f"🗑️ 释放 Pipeline: {os.path.basename(model_path)} (任务: {task_id})")

                # ✅ 推荐：先回收，再打印
                gc.collect()
                # ✅ 添加内存信息
                import psutil
                mem_gb = psutil.Process().memory_info().rss / 1024 / 1024 / 1024
                logger.info(f"   💾 释放后内存: {mem_gb:.1f} GB")
            

    
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
            return {
                "total_created": self._total_created,
                "active_count": len(self._pipelines),
                "max_instances": self._max_instances,
                "pipes": [
                    {
                        "key": k,
                        "ref_count": v["ref_count"],
                        "model": os.path.basename(v["model_path"]),
                        "model_name": v.get("model_name", ""),
                        "lora_loaded": v.get("lora_loaded", False),                        
                        "lora": os.path.basename(v["lora_path"]) if v["lora_path"] else None,
                        "lora_name": v.get("lora_name"),
                        "lora_weight": v.get("lora_weight"),
                        "task_id": v.get("task_id"),
                        "created": v.get("created", "").strftime("%H:%M:%S") if v.get("created") else "",
                        "last_used": v.get("last_used", "").strftime("%H:%M:%S") if v.get("last_used") else ""                        
                    }
                    for k, v in self._pipelines.items()
                ]
            }

    def update_lora_status(self, key: str, lora_path: str, lora_weight: float = 1.0):
        """
        更新 Pipeline 的 LoRA 状态
        用于外部加载 LoRA 后同步状态
        """
        with self._lock:
            if key in self._pipelines:
                self._pipelines[key]["lora_path"] = lora_path
                self._pipelines[key]["lora_loaded"] = lora_path is not None
                self._pipelines[key]["lora_name"] = os.path.basename(lora_path) if lora_path else None
                self._pipelines[key]["lora_weight"] = lora_weight if lora_path else None
                self._pipelines[key]["last_used"] = datetime.now()
                logger.info(f"🔗 更新 LoRA 状态: {self._pipelines[key]['lora_name'] or '无'}")
                
    def clear_all(self):
        """强制释放所有 pipeline"""
        with self._lock:
            for key, data in list(self._pipelines.items()):
                self._release_pipe_internal(data)
            self._pipelines.clear()
            gc.collect()
            logger.info(f"🗑️ 所有 Pipeline 已清理")


# 全局单例
pipeline_pool = PipelinePool()