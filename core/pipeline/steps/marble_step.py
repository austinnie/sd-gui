# core/pipeline/steps/marble_step.py
"""大理石转换步骤 - 支持 ControlNet"""

import os
import json
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from ..step import PipelineStep, StepContext, StepResult, StepStatus
from .controlnet_mixin import ControlNetMixin


class MarbleStep(PipelineStep, ControlNetMixin):
    """大理石雕像转换步骤 - 支持 ControlNet"""
    
    def __init__(self):
        super().__init__("marble", "将人物转换为大理石雕像")
        self._config = {
            "strength": 0.45,
            "max_strength": 0.55,
            "cfg": 7.0,
            "steps": 20,
            "scenes": 14,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "canny",
            "controlnet_strength": 0.6,
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.1, "max": 0.8},
            "max_strength": {"type": "float", "default": 0.55, "min": 0.3, "max": 0.8},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 20, "min": 10, "max": 40},
            "scenes": {"type": "int", "default": 14, "choices": [6, 12, 14]},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {"type": "str", "default": "canny", 
                               "choices": ["canny", "hed", "lineart", "depth"]},
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def _generate_marble_jobs(self, scene_count: int) -> list:
        """生成大理石场景的 jobs 列表"""
        all_scenes = [
            {"name": "纯白大理石雕像", 
             "prompt": "same person, same pose, transform into pure white marble statue, classical sculpture, flawless white marble, smooth stone texture, elegant pose, dramatic lighting, no color, monochrome white, intricate carving details, high quality, masterpiece",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person, different face"},
            
            {"name": "纯白大理石半身像",
             "prompt": "same person, same face, pure white marble bust, classical sculpture, white stone, smooth texture, detailed face, elegant expression, museum pedestal, soft dramatic lighting, monochrome white, high quality, masterpiece",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"},
            
            {"name": "纯白希腊女神",
             "prompt": "same person, same pose, pure white Greek goddess statue, classical Greek sculpture, flawless marble, flowing robes, elegant pose, ancient temple background, dramatic lighting, monochrome white, intricate details, high quality, masterpiece",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"},
            
            {"name": "纯白大理石全身像",
             "prompt": "same person, same pose, pure white marble statue, full body sculpture, flawless white stone, classical pose, museum gallery, marble pedestal, soft dramatic lighting, monochrome white, intricate carving details, high quality, masterpiece",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"},
            
            {"name": "纯白大理石卧像",
             "prompt": "same person, same pose, pure white marble reclining statue, lying down, classical sculpture, smooth white stone, peaceful expression, elegant pose, museum display, soft lighting, monochrome white, high quality, masterpiece",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"},
            
            {"name": "纯白石膏雕像",
             "prompt": "same person, same pose, pure white plaster cast statue, matte white finish, classical sculpture, smooth surface, elegant pose, studio photography, dramatic lighting, monochrome white, high quality, masterpiece",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"},
            
            {"name": "纯白大理石坐像",
             "prompt": "same person, same pose, pure white marble seated statue, sitting gracefully, classical sculpture, flawless white stone, elegant posture, museum pedestal, dramatic lighting, monochrome white, intricate carving details, high quality, masterpiece",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"},
            
            {"name": "纯白大理石天使",
             "prompt": "same person, same pose, pure white marble angel statue, wings, heavenly, classical sculpture, flawless white stone, ethereal pose, soft dramatic lighting, monochrome white, intricate details, high quality, masterpiece",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"},
            
            {"name": "纯白大理石维纳斯",
             "prompt": "same person, same pose, pure white marble Venus statue, goddess of beauty, classical sculpture, flawless white stone, elegant pose, soft dramatic lighting, monochrome white, intricate details, high quality, masterpiece, timeless beauty",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"},
            
            {"name": "纯白大理石艺术裸体",
             "prompt": "same person, same pose, pure white marble nude statue, classical sculpture, artistic nude, flawless white stone, elegant pose, museum display, dramatic lighting, monochrome white, intricate carving details, high quality, fine art",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, explicit, pornographic, different person"},
            
            {"name": "纯白大理石思考者",
             "prompt": "same person, same pose, pure white marble thinker statue, classical sculpture, contemplative pose, flawless white stone, smooth texture, museum setting, dramatic lighting, monochrome white, high quality, masterpiece",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"},
            
            {"name": "纯白大理石舞者",
             "prompt": "same person, same pose, pure white marble dancer statue, dynamic pose, classical sculpture, flawless white stone, elegant movement, museum gallery, soft dramatic lighting, monochrome white, intricate details, high quality, masterpiece",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"},
            
            {"name": "纯白大理石战士",
             "prompt": "same person, same pose, pure white marble warrior statue, classical sculpture, heroic pose, flawless white stone, detailed armor, museum display, dramatic lighting, monochrome white, high quality, masterpiece",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different person"},
            
            {"name": "纯白大理石母与子",
             "prompt": "same people, same pose, pure white marble mother and child statue, classical sculpture, loving embrace, flawless white stone, smooth texture, museum setting, soft dramatic lighting, monochrome white, high quality, masterpiece",
             "negative": "color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, different people"},
        ]
        
        return all_scenes[:scene_count]
        
    def execute(self, context: StepContext) -> StepResult:
        """执行大理石转换 - 支持 ControlNet"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, "marble")
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
            
            scene_count = config.get("scenes", 14)
            jobs = self._generate_marble_jobs(scene_count)
            
            steps_override = config.get("steps", 20)
            cfg_override = config.get("cfg", 7.0)
            strength_override = config.get("strength", 0.45)
            
            print(f"\n🎨 执行大理石转换: {len(jobs)} 个场景")
            print(f"   步数: {steps_override}, CFG: {cfg_override}, 强度: {strength_override}")
            if control_image is not None:
                print(f"   🧠 ControlNet: {config.get('controlnet_type', 'canny')} (强度: {config.get('controlnet_strength', 0.6)})")
            
            generator = torch.Generator("cpu").manual_seed(42)
            success_count = 0
            
            for idx, job in enumerate(jobs):
                print(f"   [{idx+1}/{len(jobs)}] {job.get('name', 'unknown')}")
                
                try:
                    gen_kwargs = {
                        "prompt": job.get("prompt", ""),
                        "negative_prompt": job.get("negative", ""),
                        "image": init_image,
                        "strength": strength_override,
                        "num_inference_steps": steps_override,
                        "guidance_scale": cfg_override,
                        "generator": generator,
                    }
                    
                    if control_image is not None and controlnet_pipe is not None:
                        gen_kwargs["control_image"] = control_image
                        gen_kwargs["controlnet_conditioning_scale"] = config.get("controlnet_strength", 0.6)
                        if idx == 0:
                            print(f"      🎛️ ControlNet 强度: {config.get('controlnet_strength', 0.6)}")
                    
                    result = pipe(**gen_kwargs)
                    
                    output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'marble')}.png")
                    result.images[0].save(output_path)
                    success_count += 1
                    print(f"      ✅ 已保存: {os.path.basename(output_path)}")
                    
                except Exception as e:
                    print(f"      ❌ 失败: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            return StepResult(
                status=StepStatus.SUCCESS if success_count > 0 else StepStatus.FAILED,
                output_path=output_dir,
                metadata={
                    "output_count": len(jobs),
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