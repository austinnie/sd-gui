# core/pipeline/steps/yoga_step.py
"""瑜伽姿势转换步骤"""

import os

from PIL import Image
from datetime import datetime

from ..step import PipelineStep, StepContext, StepResult, StepStatus


class YogaStep(PipelineStep):
    """瑜伽姿势转换步骤"""
    
    def __init__(self):
        super().__init__("yoga", "转换为瑜伽姿势")
        self._config = {
            "strength": 0.40,
            "cfg": 7.5,
            "steps": 25,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors"
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.40, "min": 0.25, "max": 0.65},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 25, "min": 15, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"}
        }
    
    def execute(self, context: StepContext) -> StepResult:
        """执行瑜伽转换"""
        import torch
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(context.output_dir, "yoga")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            pipe = context.global_config.get('pipe')
            model_path = context.global_config.get('model_path')
            
            if pipe is None and model_path:
                from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler
                
                
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
            
            # 瑜伽提示词
            yoga_prompts = [
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
            
            init_image = Image.open(image_path).convert('RGB')
            w, h = init_image.size
            width = ((w + 31) // 64) * 64
            height = ((h + 31) // 64) * 64
            if w != width or h != height:
                init_image = init_image.resize((width, height), Image.Resampling.LANCZOS)
            
            generator = torch.Generator("cpu").manual_seed(42)
            
            for idx, job in enumerate(yoga_prompts):
                print(f"   [{idx+1}/{len(yoga_prompts)}] {job.get('name', 'unknown')}")
                
                result = pipe(
                    prompt=job.get("prompt", ""),
                    negative_prompt=job.get("negative", ""),
                    image=init_image,
                    strength=config.get("strength", 0.40),
                    num_inference_steps=config.get("steps", 25),
                    guidance_scale=config.get("cfg", 7.5),
                    generator=generator,
                )
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'yoga')}.png")
                result.images[0].save(output_path)
                print(f"      ✅ 已保存: {os.path.basename(output_path)}")
            
            return StepResult(
                status=StepStatus.SUCCESS,
                output_path=output_dir,
                metadata={
                    "output_count": len(yoga_prompts),
                    "output_dir": output_dir
                }
            )
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e)
            )