# core/pipeline/steps/vaporwave_step.py
"""蒸汽波风格转换步骤"""

import os
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from ..step import PipelineStep, StepContext, StepResult, StepStatus


class VaporwaveStep(PipelineStep):
    """蒸汽波风格转换步骤"""
    
    def __init__(self):
        super().__init__("vaporwave", "转换为蒸汽波风格")
        self._config = {
            "strength": 0.45,
            "cfg": 8.0,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors"
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.25, "max": 0.65},
            "cfg": {"type": "float", "default": 8.0, "min": 6, "max": 12},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"}
        }
    
    def _generate_vaporwave_prompts(self) -> list:
        """生成蒸汽波风格提示词"""
        return [
            {
                "name": "蒸汽波女郎",
                "prompt": "vaporwave style, aesthetic, beautiful woman, pastel colors, pink and cyan, neon glow, 90s retro, synthwave, dreamy atmosphere, statues, tropical elements, high quality, masterpiece, detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, realistic, photorealistic, dark"
            },
            {
                "name": "蒸汽波风景",
                "prompt": "vaporwave aesthetic, pastel colors, pink and cyan, neon glow, 90s retro, synthwave, dreamy atmosphere, sunset, palm trees, grid, high quality, masterpiece, detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, realistic, photorealistic, dark"
            },
            {
                "name": "蒸汽波都市",
                "prompt": "vaporwave city, aesthetic, pastel colors, pink and cyan, neon glow, 90s retro, synthwave, dreamy atmosphere, sunset, high quality, masterpiece, detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, realistic, photorealistic, dark"
            }
        ]
    
    def execute(self, context: StepContext) -> StepResult:
        """执行蒸汽波风格转换"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, "vaporwave")
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
            
            prompts = self._generate_vaporwave_prompts()
            strength = config.get("strength", 0.45)
            steps = config.get("steps", 30)
            cfg = config.get("cfg", 8.0)
            
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
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'vaporwave')}.png")
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