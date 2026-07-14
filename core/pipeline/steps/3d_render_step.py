# core/pipeline/steps/3d_render_step.py
"""3D渲染风格转换步骤"""

import os
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from ..step import PipelineStep, StepContext, StepResult, StepStatus


class ThreeDRenderStep(PipelineStep):
    """3D渲染风格转换步骤"""
    
    def __init__(self):
        super().__init__("3d_render", "转换为3D渲染风格")
        self._config = {
            "strength": 0.50,
            "cfg": 8.5,
            "steps": 35,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors"
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.50, "min": 0.3, "max": 0.7},
            "cfg": {"type": "float", "default": 8.5, "min": 6, "max": 12},
            "steps": {"type": "int", "default": 35, "min": 25, "max": 60},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"}
        }
    
    def _generate_3d_render_prompts(self) -> list:
        """生成3D渲染风格提示词"""
        return [
            {
                "name": "3D人物",
                "prompt": "3d render, beautiful woman, realistic cgi, detailed, high quality, octane render, cinema 4d, blender, soft lighting, high detail, masterpiece, digital art",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, 2d, painting, sketch, photorealistic"
            },
            {
                "name": "3D场景",
                "prompt": "3d render, beautiful scene, realistic cgi, detailed, high quality, octane render, cinema 4d, blender, soft lighting, high detail, masterpiece, digital art",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, 2d, painting, sketch"
            },
            {
                "name": "3D角色",
                "prompt": "3d render, fantasy character, beautiful woman, realistic cgi, detailed, high quality, octane render, cinema 4d, blender, soft lighting, high detail, masterpiece, digital art",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, 2d, painting, sketch"
            }
        ]
    
    def execute(self, context: StepContext) -> StepResult:
        """执行3D渲染风格转换"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, "3d_render")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            pipe = context.global_config.get('pipe')
            model_path = context.global_config.get('model_path')
            
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
            
            prompts = self._generate_3d_render_prompts()
            strength = config.get("strength", 0.50)
            steps = config.get("steps", 35)
            cfg = config.get("cfg", 8.5)
            
            init_image = Image.open(image_path).convert('RGB')
            w, h = init_image.size
            width = ((w + 31) // 64) * 64
            height = ((h + 31) // 64) * 64
            if w != width or h != height:
                init_image = init_image.resize((width, height), Image.Resampling.LANCZOS)
            
            generator = torch.Generator("cpu").manual_seed(42)
            success_count = 0
            
            for idx, job in enumerate(prompts):
                print(f"   [{idx+1}/{len(prompts)}] {job.get('name', 'unknown')}")
                
                result = pipe(
                    prompt=job.get("prompt", ""),
                    negative_prompt=job.get("negative", ""),
                    image=init_image,
                    strength=strength,
                    num_inference_steps=steps,
                    guidance_scale=cfg,
                    generator=generator,
                )
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', '3d_render')}.png")
                result.images[0].save(output_path)
                success_count += 1
                print(f"      ✅ 已保存: {os.path.basename(output_path)}")
            
            return StepResult(
                status=StepStatus.SUCCESS if success_count > 0 else StepStatus.FAILED,
                output_path=output_dir,
                metadata={
                    "output_count": len(prompts),
                    "output_dir": output_dir,
                    "success_count": success_count
                }
            )
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e)
            )