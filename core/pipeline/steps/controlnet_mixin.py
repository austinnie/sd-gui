# core/pipeline/steps/controlnet_mixin.py
"""
ControlNet 混入类 - 为流水线步骤添加 ControlNet 支持
"""

import os
import torch
from PIL import Image
from diffusers import ControlNetModel, StableDiffusionControlNetPipeline, EulerDiscreteScheduler
from utils.controlnet_helper import get_controlnet_info, preprocess_image_for_controlnet


class ControlNetMixin:
    """ControlNet 混入类 - 提供 ControlNet 加载和预处理功能"""
    
    def __init__(self):
        self._controlnet_pipe = None
        self._control_image = None
    
    def _get_controlnet_pipeline(self, model_path: str, controlnet_type: str = "canny"):
        """获取 ControlNet Pipeline"""
        try:
            info = get_controlnet_info(controlnet_type)
            print(f"   📦 加载 ControlNet: {info['name']}")
            
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
            
            print(f"   ✅ ControlNet Pipeline 加载完成: {info['name']}")
            return pipe
            
        except Exception as e:
            print(f"   ⚠️ ControlNet 加载失败: {e}，回退到普通模式")
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
                print(f"   ✅ 控制图已生成: {result.size}")
            return result
        except Exception as e:
            print(f"   ⚠️ ControlNet 预处理失败: {e}")
            return None
    
    def _setup_controlnet(self, config: dict, model_path: str, image_path: str, 
                          init_image: Image.Image) -> tuple:
        """
        设置 ControlNet
        
        参数:
            config: 步骤配置
            model_path: 模型路径
            image_path: 原图路径
            init_image: 已加载的原图 PIL Image
        
        返回:
            (pipe, control_image, use_controlnet)
        """
        use_controlnet = config.get("use_controlnet", False)
        controlnet_type = config.get("controlnet_type", "canny")
        controlnet_strength = config.get("controlnet_strength", 0.6)
        
        pipe = None
        control_image = None
        
        if use_controlnet and model_path:
            pipe = self._get_controlnet_pipeline(model_path, controlnet_type)
            if pipe:
                # 生成控制图
                w, h = init_image.size
                control_image = self._preprocess_for_controlnet(
                    image_path,
                    controlnet_type=controlnet_type,
                    target_size=(w, h)
                )
                if control_image:
                    print(f"   🧠 使用 ControlNet: {controlnet_type} (强度: {controlnet_strength})")
                else:
                    print("   ⚠️ 控制图生成失败，使用普通模式")
                    pipe = None
                    control_image = None
            else:
                print("   ⚠️ ControlNet 不可用，使用普通模式")
        
        return pipe, control_image, use_controlnet
    
    def _get_controlnet_gen_kwargs(self, config: dict, pipe, control_image):
        """获取 ControlNet 生成参数"""
        gen_kwargs = {}
        
        if control_image is not None and pipe is not None:
            gen_kwargs["control_image"] = control_image
            gen_kwargs["controlnet_conditioning_scale"] = config.get("controlnet_strength", 0.6)
        
        return gen_kwargs