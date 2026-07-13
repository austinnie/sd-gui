# core/pipeline/steps/couple_step.py
"""情侣场景步骤 - 拥抱/接吻"""

import os
import torch
from PIL import Image
from datetime import datetime

from ..step import PipelineStep, StepContext, StepResult, StepStatus


class CoupleStep(PipelineStep):
    """情侣场景转换步骤"""
    
    def __init__(self):
        super().__init__("couple", "生成情侣拥抱/接吻场景")
        self._config = {
            "strength": 0.45,
            "cfg": 7.0,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors"
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.3, "max": 0.7},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"}
        }
    
    def execute(self, context: StepContext) -> StepResult:
        """执行情侣场景生成"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(context.output_dir, "couple")
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
            
            # 情侣场景提示词
            couple_prompts = [
                {
                    "name": "深情拥抱",
                    "prompt": "masterpiece, best quality, photorealistic, 8k, a man and woman hugging each other, warm embrace, intimate moment, loving couple, affectionate, close up, soft lighting, emotional expression, romantic atmosphere, tender touch, cozy environment, natural pose, both faces visible",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, extra limbs, missing limbs"
                },
                {
                    "name": "浪漫接吻",
                    "prompt": "masterpiece, best quality, photorealistic, 8k, couple kissing, romantic moment, passionate kiss, close up shot, soft focus, dreamy atmosphere, warm lighting, intimate expression, beautiful composition, love story, emotional connection, tender moment, both faces visible",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, extra limbs"
                },
                {
                    "name": "夕阳拥抱",
                    "prompt": "masterpiece, best quality, photorealistic, 8k, couple hugging in sunset, golden hour, warm romantic atmosphere, embracing each other, loving couple, silhouette, dramatic sky, emotional moment, beautiful lighting",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"
                },
                {
                    "name": "街头接吻",
                    "prompt": "masterpiece, best quality, photorealistic, 8k, couple kissing on street, urban romance, city background, passionate moment, intimate couple, soft lighting, romantic atmosphere, modern love",
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
            
            for idx, job in enumerate(couple_prompts):
                print(f"   [{idx+1}/{len(couple_prompts)}] {job.get('name', 'unknown')}")
                
                result = pipe(
                    prompt=job.get("prompt", ""),
                    negative_prompt=job.get("negative", ""),
                    image=init_image,
                    strength=config.get("strength", 0.45),
                    num_inference_steps=config.get("steps", 30),
                    guidance_scale=config.get("cfg", 7.0),
                    generator=generator,
                )
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'couple')}.png")
                result.images[0].save(output_path)
                print(f"      ✅ 已保存: {os.path.basename(output_path)}")
            
            return StepResult(
                status=StepStatus.SUCCESS,
                output_path=output_dir,
                metadata={
                    "output_count": len(couple_prompts),
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