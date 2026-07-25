# core/pipeline/steps/controlnet_mixin.py
"""
ControlNet 混入类 - 为流水线步骤添加 ControlNet 支持和场景数限制
"""

import os
import torch
from PIL import Image
from typing import Optional, List, Any
from diffusers import ControlNetModel, StableDiffusionControlNetPipeline, EulerDiscreteScheduler
from utils.controlnet import get_controlnet_info, preprocess_image_for_controlnet


from utils.logger import get_logger, info, warning, error, debug

logger = get_logger(__name__)
class ControlNetMixin:
    """ControlNet 混入类 - 提供 ControlNet 加载、预处理和场景数限制功能"""
    
    def __init__(self):
        self._controlnet_pipe = None
        self._control_image = None
    
    # ============================================================
    # ControlNet 相关方法
    # ============================================================
    
    def _get_controlnet_pipeline(self, model_path: str, controlnet_type: str = "canny"):
        """获取 ControlNet Pipeline"""
        try:
            info = get_controlnet_info(controlnet_type)
            logger.info(f"   📦 加载 ControlNet: {info['name']}")
            
            controlnet = ControlNetModel.from_pretrained(
                info["model_id"],
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            
            pipe = StableDiffusionControlNetPipeline.from_single_file(
                model_path,
                controlnet=controlnet,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                use_safetensors=True,
                low_cpu_mem_usage=True
            )
            
            pipe.to("cpu")
            pipe.enable_vae_slicing()
            pipe.enable_attention_slicing()
            if hasattr(pipe.vae, 'enable_tiling'):
                pipe.vae.enable_tiling()
            pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
            
            logger.info(f"   ✅ ControlNet Pipeline 加载完成: {info['name']}")
            return pipe
            
        except Exception as e:
            logger.info(f"   ⚠️ ControlNet 加载失败: {e}，回退到普通模式")
            return None
    
    def _preprocess_for_controlnet(self, image_path: str, controlnet_type: str = "canny", 
                                    target_size: tuple = None):
        """预处理图片生成 ControlNet 控制图"""
        try:
            result = preprocess_image_for_controlnet(
                image_path,
                controlnet_type=controlnet_type,
                output_size=target_size
            )
            if result:
                logger.info(f"   ✅ 控制图已生成: {result.size}")
            return result
        except Exception as e:
            logger.info(f"   ⚠️ ControlNet 预处理失败: {e}")
            return None
    
    # ============================================================
    # ✅ 修改：添加 context 参数支持取消
    # ============================================================
    def _setup_controlnet(self, config: dict, model_path: str, image_path: str, 
                          init_image: Image.Image, context=None) -> tuple:
        """
        设置 ControlNet
        
        参数:
            config: 步骤配置
            model_path: 模型路径
            image_path: 原图路径
            init_image: 已加载的原图 PIL Image
            context: StepContext（用于检查取消）
        
        返回:
            (pipe, control_image, use_controlnet)
        """
        use_controlnet = config.get("use_controlnet", False)
        controlnet_type = config.get("controlnet_type", "canny")
        controlnet_strength = config.get("controlnet_strength", 0.6)
        
        pipe = None
        control_image = None
        
        if use_controlnet and model_path:
            # ✅ 检查取消
            if context and context.is_cancelled():
                logger.info(f"   ⏹️ 用户在加载 ControlNet 前取消了")
                return None, None, False
            
            try:
                # ✅ 检查取消
                if context and context.is_cancelled():
                    logger.info(f"   ⏹️ 用户在加载 ControlNet 时取消了")
                    return None, None, False
                
                pipe = self._get_controlnet_pipeline(model_path, controlnet_type)
                
                # ✅ 检查取消
                if context and context.is_cancelled():
                    logger.info(f"   ⏹️ 用户在加载 ControlNet 后取消了")
                    return None, None, False
                
                if pipe:
                    w, h = init_image.size
                    control_image = self._preprocess_for_controlnet(
                        image_path,
                        controlnet_type=controlnet_type,
                        target_size=(w, h)
                    )
                    if control_image:
                        logger.info(f"   🧠 使用 ControlNet: {controlnet_type} (强度: {controlnet_strength})")
                    else:
                        logger.info(f"   ⚠️ 控制图生成失败，使用普通模式")
                        pipe = None
                        control_image = None
                else:
                    logger.info(f"   ⚠️ ControlNet 不可用，使用普通模式")
            except Exception as e:
                logger.info(f"   ⚠️ ControlNet 设置失败: {e}，使用普通模式")
                pipe = None
                control_image = None
        
        return pipe, control_image, use_controlnet
    
    def _get_controlnet_gen_kwargs(self, config: dict, pipe, control_image):
        """获取 ControlNet 生成参数"""
        gen_kwargs = {}
        if control_image is not None and pipe is not None:
            gen_kwargs["control_image"] = control_image
            gen_kwargs["controlnet_conditioning_scale"] = config.get("controlnet_strength", 0.6)
        return gen_kwargs

    # ============================================================
    # 场景数限制方法（所有步骤自动获得）
    # ============================================================
    
    def _get_scene_limit(self, config: dict) -> Optional[int]:
        """
        从配置中获取场景数限制
        
        支持多个键名:
            - max_scenes: 通用键名（由 pipeline_tab.py 传入）
            - scene_limit: 通用键名
            - scenes: 兼容旧配置（marble 等）
        
        参数:
            config: 步骤配置字典
        
        返回:
            场景数限制，None 表示不限制
        """
        for key in ["max_scenes", "scene_limit", "scenes"]:
            if key in config:
                try:
                    value = int(config[key])
                    if value > 0:
                        return value
                except (ValueError, TypeError):
                    pass
        return None
    
    def _limit_prompts(self, prompts: List[Any], max_scenes: Optional[int]) -> List[Any]:
        """
        根据场景数限制裁剪提示词列表
        
        参数:
            prompts: 完整提示词列表
            max_scenes: 最大场景数（None 表示不限制）
        
        返回:
            裁剪后的提示词列表
        """
        if max_scenes is None or max_scenes <= 0:
            return prompts
        
        if len(prompts) <= max_scenes:
            return prompts
        
        limited = prompts[:max_scenes]
        logger.info(f"   📊 场景限制: 只生成前 {len(limited)}/{len(prompts)} 个场景")
        return limited
    
    def _get_prompt_count(self, prompts: List[Any]) -> int:
        """获取提示词数量（用于统计）"""
        return len(prompts)