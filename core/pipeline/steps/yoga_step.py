# core/pipeline/steps/yoga_step.py
"""瑜伽姿势转换步骤 - 支持 ControlNet"""

import os
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from ..step import PipelineStep, StepContext, StepResult, StepStatus
from .controlnet_mixin import ControlNetMixin


class YogaStep(PipelineStep, ControlNetMixin):
    """瑜伽姿势转换步骤 - 支持 ControlNet"""
    
    def __init__(self):
        super().__init__("yoga", "转换为瑜伽姿势")
        self._config = {
            "strength": 0.40,
            "cfg": 7.5,
            "steps": 25,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "openpose",
            "controlnet_strength": 0.6,
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.40, "min": 0.25, "max": 0.65},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 25, "min": 15, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {"type": "str", "default": "openpose", 
                               "choices": ["openpose", "canny", "hed", "lineart"]},
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def _generate_yoga_prompts(self) -> list:
        """生成瑜伽风格提示词"""
        return [
            {
                "name": "瑜伽冥想",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing yoga pose, meditation, peaceful atmosphere, gym studio, yoga mat, fitness, healthy lifestyle, stretching, flexible body, calming environment, natural lighting, serene expression, athletic wear, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "树式瑜伽",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing tree pose yoga, balance pose, peaceful expression, yoga studio, natural lighting, fitness, healthy lifestyle, flexible body, serene atmosphere, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽伸展",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman stretching yoga pose, flexible body, yoga mat, peaceful atmosphere, gym studio, natural lighting, fitness, healthy lifestyle, serene expression, full body",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            },
            {
                "name": "瑜伽海滩",
                "prompt": "masterpiece, best quality, photorealistic, 8k, woman doing yoga on beach, sunrise, peaceful atmosphere, ocean background, fitness, healthy lifestyle, flexible body, serene expression, full body, golden lighting",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
            }
        ]
    
    def execute(self, context: StepContext) -> StepResult:
        """执行瑜伽转换 - 支持 ControlNet"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, "yoga")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            pipe = context.global_config.get('pipe')
            model_path = context.global_config.get('model_path')
            
            init_image = Image.open(image_path).convert('RGB')
            w, h = init_image.size
            width = ((w + 31) // 64) * 64
            height = ((h + 31) // 64) * 64
            if w != width or h != height:
                init_image = init_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # ===== 设置 ControlNet =====
            controlnet_pipe, control_image, use_controlnet = self._setup_controlnet(
                config, model_path, image_path, init_image
            )
            
            if controlnet_pipe is not None:
                pipe = controlnet_pipe
            
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
            
            prompts = self._generate_yoga_prompts()
            strength = config.get("strength", 0.40)
            steps = config.get("steps", 25)
            cfg = config.get("cfg", 7.5)
            
            generator = torch.Generator("cpu").manual_seed(42)
            success_count = 0
            
            for idx, job in enumerate(prompts):
                print(f"   [{idx+1}/{len(prompts)}] {job.get('name', 'unknown')}")
                
                gen_kwargs = {
                    "prompt": job.get("prompt", ""),
                    "negative_prompt": job.get("negative", ""),
                    "image": init_image,
                    "strength": strength,
                    "num_inference_steps": steps,
                    "guidance_scale": cfg,
                    "generator": generator,
                }
                
                if control_image is not None and controlnet_pipe is not None:
                    gen_kwargs["control_image"] = control_image
                    gen_kwargs["controlnet_conditioning_scale"] = config.get("controlnet_strength", 0.6)
                    if idx == 0:
                        print(f"      🎛️ ControlNet 强度: {config.get('controlnet_strength', 0.6)}")
                
                result = pipe(**gen_kwargs)
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'yoga')}.png")
                result.images[0].save(output_path)
                success_count += 1
                print(f"      ✅ 已保存: {os.path.basename(output_path)}")
            
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
            import traceback
            traceback.print_exc()
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e)
            )