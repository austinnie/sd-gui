# core/pipeline/steps/qipao_step.py
"""旗袍风格转换步骤"""

import os

from PIL import Image
from datetime import datetime

from ..step import PipelineStep, StepContext, StepResult, StepStatus


class QipaoStep(PipelineStep):
    """旗袍风格转换步骤"""
    
    def __init__(self):
        super().__init__("qipao", "将人物转换为旗袍风格")
        self._config = {
            "strength": 0.35,
            "cfg": 7.5,
            "steps": 25,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors"
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.35, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 25, "min": 15, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"}
        }
    
    def execute(self, context: StepContext) -> StepResult:
        """执行旗袍转换"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(context.output_dir, "qipao")
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
            
            # 旗袍提示词模板
            qipao_prompts = [
                {
                    "name": "传统旗袍",
                    "prompt": "masterpiece, best quality, photorealistic, 8k, beautiful woman wearing traditional Chinese qipao, elegant cheongsam, silk fabric, intricate embroidery, mandarin collar, side slit, classic Chinese style, vintage atmosphere, graceful pose, soft lighting, porcelain skin, red lipstick",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, modern clothes, casual"
                },
                {
                    "name": "现代旗袍",
                    "prompt": "masterpiece, best quality, photorealistic, 8k, beautiful woman wearing modern qipao, stylish cheongsam, silk satin fabric, elegant design, high slit, modern setting, confident pose, dramatic lighting, flawless skin, high fashion",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, traditional only"
                },
                {
                    "name": "旗袍花园",
                    "prompt": "masterpiece, best quality, photorealistic, 8k, beautiful woman wearing elegant qipao, traditional Chinese garden, blooming flowers, soft golden lighting, graceful pose, silk cheongsam, vintage beauty, serene atmosphere, detailed embroidery",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, modern setting"
                },
                {
                    "name": "旗袍夜景",
                    "prompt": "masterpiece, best quality, photorealistic, 8k, beautiful woman wearing qipao, night scene, city lights, elegant pose, silk cheongsam, dramatic lighting, sophisticated atmosphere, modern traditional fusion",
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
            
            for idx, job in enumerate(qipao_prompts):
                print(f"   [{idx+1}/{len(qipao_prompts)}] {job.get('name', 'unknown')}")
                
                result = pipe(
                    prompt=job.get("prompt", ""),
                    negative_prompt=job.get("negative", ""),
                    image=init_image,
                    strength=config.get("strength", 0.35),
                    num_inference_steps=config.get("steps", 25),
                    guidance_scale=config.get("cfg", 7.5),
                    generator=generator,
                )
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'qipao')}.png")
                result.images[0].save(output_path)
                print(f"      ✅ 已保存: {os.path.basename(output_path)}")
            
            return StepResult(
                status=StepStatus.SUCCESS,
                output_path=output_dir,
                metadata={
                    "output_count": len(qipao_prompts),
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