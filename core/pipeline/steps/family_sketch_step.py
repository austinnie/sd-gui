# core/pipeline/steps/family_sketch_step.py
"""家庭素描风格 - 支持 ControlNet"""

import os
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from ..step import PipelineStep, StepContext, StepResult, StepStatus
from .controlnet_mixin import ControlNetMixin


class FamilySketchStep(PipelineStep, ControlNetMixin):
    """家庭素描风格 - 支持 ControlNet"""
    
    def __init__(self):
        super().__init__("family_sketch", "家庭素描风格")
        self._config = {
            "strength": 0.35,
            "cfg": 7.0,
            "steps": 25,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "lineart",
            "controlnet_strength": 0.6,
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.35, "min": 0.2, "max": 0.55},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 9},
            "steps": {"type": "int", "default": 25, "min": 15, "max": 40},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {"type": "str", "default": "lineart", 
                               "choices": ["lineart", "canny", "hed", "scribble"]},
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def _generate_prompts(self) -> list:
        """生成家庭素描风格提示词"""
        return [
            {
                "name": "家庭素描_全家福",
                "prompt": "pencil sketch, family portrait, multiple people, parents and children, detailed drawing, fine art, shading, texture, monochrome, high quality, masterpiece, realistic sketch",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, single person"
            },
            {
                "name": "家庭素描_温馨",
                "prompt": "pencil sketch, loving family, parents and children, warm atmosphere, detailed drawing, fine art, shading, texture, monochrome, high quality, masterpiece, realistic sketch",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render"
            },
            {
                "name": "家庭素描_合影",
                "prompt": "pencil sketch, family group photo, multiple people, detailed drawing, fine art, shading, texture, monochrome, high quality, masterpiece, realistic sketch",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render"
            }
        ]
    
    def execute(self, context: StepContext) -> StepResult:
        """执行家庭素描风格转换 - 支持 ControlNet"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, "family_sketch")
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
            all_prompts = self._generate_prompts()
            if max_scenes is not None and max_scenes > 0:
                prompts = self._limit_prompts(all_prompts, max_scenes)
                print(f"   📊 场景限制: 只生成前 {len(prompts)}/{len(all_prompts)} 个场景")
            else:
                prompts = all_prompts
    
            strength = config.get("strength", 0.35)
            steps = config.get("steps", 25)
            cfg = config.get("cfg", 7.0)
            
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
                    gen_kwargs["controlnet_conditioning_scale"] = config.get("controlnet_strength", 0.6)
                    if idx == 0:
                        print(f"      🎛️ ControlNet 强度: {config.get('controlnet_strength', 0.6)}")
                
                result = pipe(**gen_kwargs)
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'family_sketch')}.png")
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