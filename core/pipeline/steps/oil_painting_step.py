# core/pipeline/steps/oil_painting_step.py
"""油画风格转换步骤 - 支持 ControlNet"""

import os
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from ..step import PipelineStep, StepContext, StepResult, StepStatus
from .controlnet_mixin import ControlNetMixin


class OilPaintingStep(PipelineStep, ControlNetMixin):
    """油画风格转换步骤 - 支持 ControlNet"""
    
    def __init__(self):
        super().__init__("oil_painting", "转换为油画风格")
        self._config = {
            "strength": 0.35,
            "cfg": 8.0,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "hed",
            "controlnet_strength": 0.5,
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.35, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 8.0, "min": 6, "max": 12},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 60},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {"type": "str", "default": "hed", 
                               "choices": ["canny", "hed", "lineart", "scribble"]},
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def _generate_oil_prompts(self) -> list:
        """生成油画风格提示词"""
        return [
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
    
    def execute(self, context: StepContext) -> StepResult:
        """执行油画转换 - 支持 ControlNet"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, "oil_painting")
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
            
            # ===== 场景数限制 =====
            max_scenes = self._get_scene_limit(config)
            all_prompts = self._generate_oil_prompts()
            if max_scenes is not None and max_scenes > 0:
                prompts = self._limit_prompts(all_prompts, max_scenes)
                print(f"   📊 场景限制: 只生成前 {len(prompts)}/{len(all_prompts)} 个场景")
            else:
                prompts = all_prompts
    
            strength = config.get("strength", 0.35)
            steps = config.get("steps", 30)
            cfg = config.get("cfg", 8.0)
            
            generator = torch.Generator("cpu").manual_seed(42)
            success_count = 0
            
            for idx, job in enumerate(prompts):
                # ✅ 检查取消
                if context.is_cancelled():
                    print(f"   ⏹️ 用户取消，已生成 {idx}/{7} 张")
                    return StepResult(
                        status=StepStatus.FAILED,
                        error="用户取消",
                        output_path=output_dir,
                        metadata={
                            "output_count": idx,
                            "output_dir": output_dir,
                            "success_count": success_count,
                            "cancelled": True,
                        }
                    )
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
                    gen_kwargs["controlnet_conditioning_scale"] = config.get("controlnet_strength", 0.5)
                    if idx == 0:
                        print(f"      🎛️ ControlNet 强度: {config.get('controlnet_strength', 0.5)}")
                
                result = pipe(**gen_kwargs)
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'oil')}.png")
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
            error_msg = str(e)
            if "取消" in error_msg or "cancelled" in error_msg.lower():
                print(f"      ⏹️ 生成被取消")
                return StepResult(
                    status=StepStatus.FAILED,
                    error="用户取消",
                    output_path=output_dir,
                    metadata={
                        "output_count": idx,
                        "output_dir": output_dir,
                        "success_count": success_count,
                        "cancelled": True,
                    }
                )
            print(f"      ❌ 失败: {e}")
            import traceback
            traceback.print_exc()
            # continue (已移除，不在循环中)