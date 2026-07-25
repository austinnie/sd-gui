# core/pipeline/steps/bronze_statue_step.py
"""青铜雕像风格转换步骤 - 支持 ControlNet"""

import os
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from ..step import PipelineStep, StepContext, StepResult, StepStatus
from .controlnet_mixin import ControlNetMixin


class BronzeStatueStep(PipelineStep, ControlNetMixin):
    """青铜雕像转换步骤 - 支持 ControlNet"""
    
    def __init__(self):
        super().__init__("bronze_statue", "将人物转换为青铜雕像风格")
        self._config = {
            "strength": 0.45,
            "cfg": 7.0,
            "steps": 25,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "canny",
            "controlnet_strength": 0.6,
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 25, "min": 15, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {"type": "str", "default": "canny", 
                               "choices": ["canny", "hed", "lineart", "depth", "openpose"]},
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }

    def _generate_bronze_jobs(self, scene_count: int = 12) -> list:
        """生成青铜雕像场景的 jobs 列表"""
        all_scenes = [
            {"name": "青铜古典雕像", 
             "prompt": "same person, same pose, transform into ancient bronze statue, classical sculpture, rich green patina, weathered bronze texture, dark metallic finish, aged copper tone, intricate casting details, dramatic lighting, museum pedestal, high quality, masterpiece",
             "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"},
            
            {"name": "青铜希腊神像",
             "prompt": "same person, same pose, ancient Greek bronze god statue, dark patina, weathered bronze, classical Greek sculpture, flowing robes, temple background, dramatic shadow and light, metallic texture, high quality, masterpiece",
             "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"},
            
            {"name": "青铜战士雕像",
             "prompt": "same person, same pose, heroic bronze warrior statue, dark metal, battle armor, weathered copper tone, commanding pose, historical museum display, dramatic lighting, high quality, masterpiece",
             "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"},
            
            {"name": "青铜全身像",
             "prompt": "same person, same pose, full body bronze statue, rich patina, textured metal surface, dark bronze color, elegant pose, museum gallery display, dramatic spotlight, high quality, masterpiece",
             "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"},
            
            {"name": "青铜女神雕塑",
             "prompt": "same person, same pose, classical bronze goddess sculpture, ornate metalwork, flowing drapery, greenish patina, soft dramatic lighting, museum pedestal, intricate details, high quality, masterpiece",
             "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"},
            
            {"name": "青铜半身像",
             "prompt": "same person, same face, bronze bust, detailed facial features, dark metallic finish, weathered bronze texture, museum display, classical art style, dramatic lighting, high quality, masterpiece",
             "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"},
            
            {"name": "青铜坐像",
             "prompt": "same person, same pose, seated bronze statue, classic pose, dark metal, rich patina, elegant, museum gallery, dramatic lighting, high quality, masterpiece",
             "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"},
            
            {"name": "青铜骑士像",
             "prompt": "same person, same pose, medieval bronze knight statue, armored, holding a sword, dark metallic tone, weathered patina, castle background, dramatic lighting, high quality, masterpiece",
             "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"},
            
            {"name": "青铜天使像",
             "prompt": "same person, same pose, bronze angel statue, wings, ethereal pose, dark metallic patina, classical sculpture, dramatic lighting, museum display, high quality, masterpiece",
             "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"},
            
            {"name": "青铜舞蹈者",
             "prompt": "same person, same pose, bronze dancer statue, dynamic pose, elegant movement, dark patina, metallic texture, museum display, dramatic lighting, high quality, masterpiece",
             "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different person"},
            
            {"name": "青铜裸体艺术",
             "prompt": "same person, same pose, classical bronze nude statue, artistic nude, dark metallic finish, weathered bronze texture, museum display, dramatic lighting, high quality, fine art, masterpiece",
             "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, explicit, pornographic, different person"},
            
            {"name": "青铜母子像",
             "prompt": "same people, same pose, bronze mother and child statue, loving embrace, dark metal, rich patina, soft dramatic lighting, classical sculpture, museum pedestal, high quality, masterpiece",
             "negative": "color, modern, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, wood, gold, silver, different people"},
        ]
        
        return all_scenes[:scene_count]
        
    def execute(self, context: StepContext) -> StepResult:
        """执行青铜雕像转换 - 支持 ControlNet"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, "bronze_statue")
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
            if max_scenes is not None and max_scenes > 0:
                jobs = self._generate_bronze_jobs(max_scenes)
                print(f"   📊 场景限制: 只生成前 {len(jobs)} 个场景")
            else:
                jobs = self._generate_bronze_jobs()
            
            strength = config.get("strength", 0.45)
            steps = config.get("steps", 25)
            cfg = config.get("cfg", 7.0)
            
            generator = torch.Generator("cpu").manual_seed(42)
            success_count = 0
            
            for idx, job in enumerate(jobs):
                # ✅ 检查取消
                if context.is_cancelled():
                    print(f"   ⏹️ 用户取消，已生成 {idx}/{4} 张")
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
                print(f"   [{idx+1}/{len(jobs)}] {job.get('name', 'unknown')}")
                
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
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'bronze')}.png")
                result.images[0].save(output_path)
                success_count += 1
                print(f"      ✅ 已保存: {os.path.basename(output_path)}")
            
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