# core/pipeline/steps/couple_step.py
"""情侣场景转换步骤 - 支持 ControlNet"""

import os
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from ..step import PipelineStep, StepContext, StepResult, StepStatus
from .controlnet_mixin import ControlNetMixin


class CoupleStep(PipelineStep, ControlNetMixin):
    """情侣场景转换步骤 - 支持 ControlNet"""
    
    def __init__(self):
        super().__init__("couple", "生成情侣拥抱/接吻场景")
        self._config = {
            "strength": 0.45,
            "cfg": 7.0,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "openpose",
            "controlnet_strength": 0.6,
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.3, "max": 0.7},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {"type": "str", "default": "openpose", 
                               "choices": ["openpose", "canny", "hed", "lineart"]},
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def _generate_couple_prompts(self) -> list:
        """生成情侣场景提示词"""
        return [
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
    
    def execute(self, context: StepContext) -> StepResult:
        """执行情侣场景转换 - 支持 ControlNet"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, "couple")
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
            
            prompts = self._generate_couple_prompts()
            strength = config.get("strength", 0.45)
            steps = config.get("steps", 30)
            cfg = config.get("cfg", 7.0)
            
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
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'couple')}.png")
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