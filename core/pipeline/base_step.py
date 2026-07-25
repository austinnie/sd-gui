# core/pipeline/base_step.py
"""
风格转换步骤基类 - 减少 30+ 个 Step 文件的重复代码
"""

import os
import gc
import torch
from abc import abstractmethod
from typing import List, Dict, Any, Optional
from PIL import Image
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from .step import PipelineStep, StepContext, StepResult, StepStatus
from .steps.controlnet_mixin import ControlNetMixin


from utils.logger import get_logger

logger = get_logger(__name__)

class BaseStyleStep(PipelineStep, ControlNetMixin):
    """
    风格转换步骤基类
    
    子类只需实现:
    1. get_prompts() -> 返回提示词列表 [{"name": "", "prompt": "", "negative": ""}]
    2. 可选: 重写 get_default_config() 修改默认配置
    3. 可选: 重写 get_config_schema() 修改 UI 配置
    4. 可选: 重写 get_output_dir_name() 修改输出子目录名
    """
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
        self._config = self.get_default_config()
        # ✅ 缓存 ControlNet 相关对象，避免重复创建
        self._cached_controlnet_pipe = None
        self._cached_control_image = None
        self._cached_controlnet_config = None
    
    def get_default_config(self) -> Dict[str, Any]:
        """默认配置 - 子类可重写"""
        return {
            "strength": 0.40,
            "cfg": 7.5,
            "steps": 28,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "canny",
            "controlnet_strength": 0.6,
        }
    
    def get_config_schema(self) -> Dict[str, Any]:
        """配置参数 Schema - 子类可重写"""
        return {
            "strength": {"type": "float", "default": 0.40, "min": 0.15, "max": 0.75},
            "cfg": {"type": "float", "default": 7.5, "min": 5.0, "max": 12.0},
            "steps": {"type": "int", "default": 28, "min": 10, "max": 60},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "canny",
                "choices": ["canny", "hed", "lineart", "scribble", "openpose", "depth", "normal", "mlsd"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    @abstractmethod
    def get_prompts(self) -> List[Dict[str, str]]:
        """
        获取提示词列表
        
        返回格式:
        [
            {"name": "场景名称", "prompt": "正面提示词", "negative": "负面提示词"},
            ...
        ]
        """
        pass
    
    def get_output_dir_name(self) -> str:
        """获取输出子目录名称 - 默认使用 step name"""
        return self.name

    # ============================================================
    # ✅ 新增：内存检查工具
    # ============================================================
    def _check_memory(self, threshold_gb: float = 8.0) -> bool:
        """检查内存是否超过阈值"""
        try:
            import psutil
            mem = psutil.Process().memory_info().rss / 1024 / 1024 / 1024
            if mem > threshold_gb:
                logger.info(f"   🧹 内存 {mem:.1f}GB 超过阈值 {threshold_gb:.1f}GB，执行清理...")
                return True
            return False
        except:
            return False
    
    def _force_cleanup(self):
        """强制内存清理"""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            
    def execute(self, context: StepContext) -> StepResult:
        """执行风格转换 - 通用逻辑"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, self.get_output_dir_name())
        os.makedirs(output_dir, exist_ok=True)
        
        # ✅ 用于跟踪成功数量
        success_count = 0
        
        try:
            pipe = context.global_config.get('pipe')
            model_path = context.global_config.get('model_path')
            
            init_image = Image.open(image_path).convert('RGB')
            w, h = init_image.size
            width = ((w + 31) // 64) * 64
            height = ((h + 31) // 64) * 64
            if w != width or h != height:
                init_image = init_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # ============================================================
            # ✅ 修改：ControlNet 只加载一次（在循环之前）
            # ============================================================
            controlnet_pipe = None
            control_image = None
            use_controlnet = config.get("use_controlnet", False)
            
            if use_controlnet and model_path:
                # ✅ 检查缓存，避免重复加载
                cache_key = f"{model_path}_{config.get('controlnet_type', 'canny')}"
                
                if (self._cached_controlnet_pipe is not None and 
                    self._cached_controlnet_config == cache_key):
                    # 使用缓存的 ControlNet
                    controlnet_pipe = self._cached_controlnet_pipe
                    control_image = self._cached_control_image
                    logger.info(f"   🧠 复用已缓存的 ControlNet")
                else:
                    # 加载新的 ControlNet
                    logger.info(f"   📦 加载 ControlNet (首次)...")
                    controlnet_pipe, control_image, _ = self._setup_controlnet(
                        config, model_path, image_path, init_image, context
                    )
                    # 缓存
                    if controlnet_pipe is not None and control_image is not None:
                        self._cached_controlnet_pipe = controlnet_pipe
                        self._cached_control_image = control_image
                        self._cached_controlnet_config = cache_key
                        logger.info(f"   ✅ ControlNet 已缓存")
                
                if controlnet_pipe is not None:
                    pipe = controlnet_pipe
                    logger.info(f"   🧠 使用 ControlNet: {config.get('controlnet_type', 'canny')} (强度: {config.get('controlnet_strength', 0.6)})")
            
            # 如果没有 pipe，加载模型
            if pipe is None and model_path:
                common_args = {
                    "torch_dtype": torch.float32,
                    "safety_checker": None,
                    "requires_safety_checker": False,
                    "use_safetensors": True,
                    "low_cpu_mem_usage": True,
                }
                pipe = StableDiffusionPipeline.from_single_file(model_path, **common_args)
                pipe.to("cpu")
                pipe.enable_vae_slicing()
                pipe.enable_attention_slicing()
                pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
            
            if pipe is None:
                return StepResult(
                    status=StepStatus.FAILED,
                    error="无法获取 Pipeline"
                )
            
            # 获取提示词
            max_scenes = self._get_scene_limit(config)
            all_prompts = self.get_prompts()
            if max_scenes is not None and max_scenes > 0:
                prompts = self._limit_prompts(all_prompts, max_scenes)
                logger.info(f"   📊 场景限制: 只生成前 {len(prompts)}/{len(all_prompts)} 个场景")
            else:
                prompts = all_prompts
            
            strength = config.get("strength", 0.40)
            steps = config.get("steps", 28)
            cfg = config.get("cfg", 7.5)
            
            generator = torch.Generator("cpu").manual_seed(42)
            
            # ✅ 进度日志：每 5 张输出一次内存状态
            last_memory_log = 0
            
            # ============================================================
            # ✅ 循环生成
            # ============================================================
            for idx, job in enumerate(prompts):
                # 检查取消
                if context.is_cancelled():
                    logger.info(f"   ⏹️ 用户取消，已生成 {idx} 张")
                    return StepResult(
                        status=StepStatus.FAILED,
                        error="用户取消",
                        output_path=output_dir,
                        metadata={
                            "output_count": idx,
                            "output_dir": output_dir,
                            "success_count": success_count,
                            "cancelled": True,
                        }
                    )
                
                logger.info(f"   [{idx+1}/{len(prompts)}] {job.get('name', 'unknown')}")
                
                gen_kwargs = {
                    "prompt": job.get("prompt", ""),
                    "negative_prompt": job.get("negative", ""),
                    "image": init_image,
                    "strength": strength,
                    "num_inference_steps": steps,
                    "guidance_scale": cfg,
                    "generator": generator,
                }
                
                # ✅ 复用 ControlNet（已在外层加载）
                if control_image is not None and controlnet_pipe is not None:
                    gen_kwargs["control_image"] = control_image
                    gen_kwargs["controlnet_conditioning_scale"] = config.get("controlnet_strength", 0.6)
                    if idx == 0:
                        logger.info(f"      🎛️ ControlNet 强度: {config.get('controlnet_strength', 0.6)}")
                
                try:
                    result = pipe(**gen_kwargs)
                    
                    output_path = os.path.join(
                        output_dir, 
                        f"{idx+1:02d}_{job.get('name', self.name)}.png"
                    )
                    result.images[0].save(output_path)
                    success_count += 1
                    logger.info(f"      ✅ 已保存: {os.path.basename(output_path)}")
                    
                    # ✅ 立即释放 result
                    del result
                    
                    # ✅ 每生成 2 张图片后检查内存
                    if (idx + 1) % 2 == 0:
                        if self._check_memory(threshold_gb=8.0):
                            self._force_cleanup()
                            logger.info(f"      🧹 内存已清理")
                    
                    # ✅ 每 5 张图片输出内存状态
                    if (idx + 1) % 5 == 0:
                        try:
                            import psutil
                            mem = psutil.Process().memory_info().rss / 1024 / 1024 / 1024
                            logger.info(f"      📊 当前内存: {mem:.1f} GB")
                        except:
                            pass
                    
                except Exception as e:
                    error_msg = str(e)
                    if "取消" in error_msg or "cancelled" in error_msg.lower():
                        logger.info(f"      ⏹️ 生成被取消")
                        return StepResult(
                            status=StepStatus.FAILED,
                            error="用户取消",
                            output_path=output_dir,
                            metadata={
                                "output_count": idx,
                                "output_dir": output_dir,
                                "success_count": success_count,
                                "cancelled": True,
                            }
                        )
                    logger.info(f"      ❌ 失败: {e}")
                    import traceback
                    traceback.print_exc()
            
            # ✅ 最终清理
            self._force_cleanup()
            
            return StepResult(
                status=StepStatus.SUCCESS if success_count > 0 else StepStatus.FAILED,
                output_path=output_dir,
                metadata={
                    "output_count": len(prompts),
                    "output_dir": output_dir,
                    "success_count": success_count,
                    "controlnet_used": control_image is not None,
                }
            )
                    
        except Exception as e:
            error_msg = str(e)
            if "取消" in error_msg or "cancelled" in error_msg.lower():
                return StepResult(
                    status=StepStatus.FAILED,
                    error="用户取消",
                    output_path=output_dir,
                    metadata={"cancelled": True}
                )
            logger.info(f"      ❌ 失败: {e}")
            import traceback
            traceback.print_exc()
            return StepResult(status=StepStatus.FAILED, error=str(e))