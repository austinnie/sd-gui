# core/pipeline/steps/oil_painting_step.py
"""油画风格转换步骤 - 包含世界名画裸体画风格"""

import os
import torch
from PIL import Image
from datetime import datetime

from ..step import PipelineStep, StepContext, StepResult, StepStatus


class OilPaintingStep(PipelineStep):
    """油画风格转换步骤"""
    
    def __init__(self):
        super().__init__("oil_painting", "转换为油画风格")
        self._config = {
            "strength": 0.35,
            "cfg": 8.0,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors"
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.35, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 8.0, "min": 6, "max": 12},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 60},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"}
        }
    
    def execute(self, context: StepContext) -> StepResult:
        """执行油画转换"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(context.output_dir, "oil_painting")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            pipe = context.global_config.get('pipe')
            model_path = context.global_config.get('model_path')
            
            if pipe is None and model_path:
                from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler
                import torch
                
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
            
            # 油画风格提示词
            oil_prompts = [
                {
                    "name": "文艺复兴裸体",
                    "prompt": "masterpiece, best quality, oil painting, renaissance style, a beautiful European woman, classical nude, soft lighting, warm skin tones, rich colors, elegant pose, velvet drapery, renaissance background, fine art, high quality, detailed, timeless beauty, classical painting style",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, explicit, pornographic"
                },
                {
                    "name": "维纳斯诞生",
                    "prompt": "masterpiece, best quality, oil painting, botticelli style, venus rising from sea, classical beauty, nude goddess, flowing hair, renaissance painting, shell, soft warm lighting, rich colors, fine art, masterpiece, timeless beauty",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, explicit, pornographic"
                },
                {
                    "name": "古典油画裸体",
                    "prompt": "masterpiece, best quality, oil painting, classical art, a beautiful European woman, nude, soft warm lighting, rich golden tones, elegant reclining pose, luxurious fabrics, classical background, baroque style, fine art, high quality, detailed, masterpiece painting",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, explicit, pornographic"
                },
                {
                    "name": "巴洛克裸体",
                    "prompt": "masterpiece, best quality, oil painting, baroque style, a beautiful European woman, classical nude, dramatic chiaroscuro lighting, rich dark background, elegant pose, luxurious fabrics, fine art, high quality, detailed, masterpiece, old masters style",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, explicit, pornographic"
                },
                {
                    "name": "洛可可裸体",
                    "prompt": "masterpiece, best quality, oil painting, rococo style, a beautiful European woman, classical nude, soft pastel colors, elegant pose, luxurious boudoir, ornate background, fine art, high quality, detailed, masterpiece, feminine beauty, 18th century style",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, explicit, pornographic"
                },
                {
                    "name": "新古典主义裸体",
                    "prompt": "masterpiece, best quality, oil painting, neoclassical style, a beautiful European woman, classical nude, soft lighting, marble background, elegant pose, ancient Greek inspiration, fine art, high quality, detailed, masterpiece, timeless beauty",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cartoon, anime, modern, photography, photorealistic, 3d render, explicit, pornographic"
                }
            ]
            
            init_image = Image.open(image_path).convert('RGB')
            w, h = init_image.size
            width = ((w + 31) // 64) * 64
            height = ((h + 31) // 64) * 64
            if w != width or h != height:
                init_image = init_image.resize((width, height), Image.Resampling.LANCZOS)
            
            generator = torch.Generator("cpu").manual_seed(42)
            
            for idx, job in enumerate(oil_prompts):
                print(f"   [{idx+1}/{len(oil_prompts)}] {job.get('name', 'unknown')}")
                
                result = pipe(
                    prompt=job.get("prompt", ""),
                    negative_prompt=job.get("negative", ""),
                    image=init_image,
                    strength=config.get("strength", 0.35),
                    num_inference_steps=config.get("steps", 30),
                    guidance_scale=config.get("cfg", 8.0),
                    generator=generator,
                )
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'oil')}.png")
                result.images[0].save(output_path)
                print(f"      ✅ 已保存: {os.path.basename(output_path)}")
            
            return StepResult(
                status=StepStatus.SUCCESS,
                output_path=output_dir,
                metadata={
                    "output_count": len(oil_prompts),
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