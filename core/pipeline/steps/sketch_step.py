# core/pipeline/steps/sketch_step.py
"""素描风格转换步骤 - 支持 ControlNet"""

import os
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from ..step import PipelineStep, StepContext, StepResult, StepStatus


class SketchStep(PipelineStep):
    """素描风格转换步骤 - 支持 ControlNet"""
    
    def __init__(self):
        super().__init__("sketch", "转换为素描风格 (ControlNet增强)")
        self._config = {
            "strength": 0.25,
            "cfg": 7.0,
            "steps": 25,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": True,           # ✅ 新增：ControlNet 开关
            "controlnet_type": "canny",       # ✅ 新增：ControlNet 类型
            "controlnet_strength": 0.6,       # ✅ 新增：ControlNet 控制强度
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.25, "min": 0.15, "max": 0.45},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 9},
            "steps": {"type": "int", "default": 20, "min": 15, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": True},
            "controlnet_type": {"type": "str", "default": "canny", "choices": ["canny", "hed", "lineart", "scribble"]},
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.3, "max": 1.0},
        }
    
    def _generate_sketch_prompts(self) -> list:
        """生成素描风格提示词 - 扩展版 8种场景"""
        return [
            # ===== 人物素描（重点保留身份） =====
            {
                "name": "素描肖像_精细",
                "prompt": "pencil sketch, same person, same face, same pose, ultra detailed portrait drawing, fine art, realistic pencil shading, high contrast, monochrome, texture, masterpiece, best quality",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, cartoon, anime"
            },
            {
                "name": "炭笔素描",
                "prompt": "charcoal drawing, same person, same face, same pose, rich dark tones, smudged texture, dramatic shading, fine art, monochrome, high quality, masterpiece, realistic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, clean lines"
            },
            {
                "name": "素描人体_艺术",
                "prompt": "pencil sketch, detailed drawing, beautiful woman nude, fine art, charcoal drawing, shading, texture, monochrome, high quality, masterpiece, realistic sketch, artistic nude",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, explicit"
            },
            {
                "name": "速写风格",
                "prompt": "quick pencil sketch, same person, same face, same pose, loose expressive lines, gestural drawing, artistic, monochrome, high quality, sketchy style, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, over-detailed"
            },
            
            # ===== 动物素描 =====
            {
                "name": "素描动物",
                "prompt": "pencil sketch, detailed drawing of an animal, fine art, charcoal drawing, shading, texture, monochrome, high quality, masterpiece, realistic sketch, animal portrait",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, cartoon"
            },
            
            # ===== 风景素描 =====
            {
                "name": "素描风景",
                "prompt": "pencil sketch, detailed landscape drawing, mountains and nature, fine art, charcoal drawing, shading, texture, monochrome, high quality, masterpiece, realistic sketch",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, color, photorealistic, oil painting, 3d render, cartoon"
            },
            {
                "name": "素描城市",
                "prompt": "pencil sketch, detailed cityscape drawing, urban architecture, fine art, charcoal drawing, shading, texture, monochrome, high quality, masterpiece, realistic sketch",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, color, photorealistic, oil painting, 3d render, cartoon"
            },
            
            # ===== 特殊风格 =====
            {
                "name": "交叉排线素描",
                "prompt": "cross-hatching pencil sketch, detailed drawing, fine art, intricate line work, shading, texture, monochrome, high quality, masterpiece, realistic sketch, artistic technique",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, photorealistic, oil painting, 3d render, smooth shading"
            }
        ]
    
    def _get_controlnet_pipeline(self, model_path: str, controlnet_type: str = "canny"):
        """获取 ControlNet Pipeline"""
        try:
            from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
            from utils.controlnet_helper import get_controlnet_info
            
            info = get_controlnet_info(controlnet_type)
            print(f"   📦 加载 ControlNet: {info['name']}")
            
            # 加载 ControlNet 模型
            controlnet = ControlNetModel.from_pretrained(
                info["model_id"],
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            
            # 加载主模型 + ControlNet
            pipe = StableDiffusionControlNetPipeline.from_single_file(
                model_path,
                controlnet=controlnet,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                use_safetensors=True,
                low_cpu_mem_usage=True
            )
            
            pipe.to("cpu")
            pipe.enable_vae_slicing()
            pipe.enable_attention_slicing()
            if hasattr(pipe.vae, 'enable_tiling'):
                pipe.vae.enable_tiling()
            pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
            
            print(f"   ✅ ControlNet Pipeline 加载完成: {info['name']}")
            return pipe
            
        except Exception as e:
            print(f"   ⚠️ ControlNet 加载失败: {e}，回退到普通模式")
            return None
    
    def _preprocess_for_controlnet(self, image_path: str, controlnet_type: str = "canny", 
                                    target_size: tuple = None):
        """预处理图片生成 ControlNet 控制图"""
        try:
            from utils.controlnet_helper import preprocess_image_for_controlnet
            return preprocess_image_for_controlnet(
                image_path,
                controlnet_type=controlnet_type,
                output_size=target_size
            )
        except Exception as e:
            print(f"   ⚠️ ControlNet 预处理失败: {e}")
            return None
    
    def execute(self, context: StepContext) -> StepResult:
        """执行素描风格转换 - 支持 ControlNet"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, "sketch")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # ===== 获取 ControlNet 配置 =====
            use_controlnet = config.get("use_controlnet", True)
            controlnet_type = config.get("controlnet_type", "canny")
            controlnet_strength = config.get("controlnet_strength", 0.6)
            
            # ===== 获取模型路径 =====
            pipe = context.global_config.get('pipe')
            model_path = context.global_config.get('model_path')
            
            # ===== 如果启用 ControlNet，尝试加载 ControlNet Pipeline =====
            controlnet_pipe = None
            if use_controlnet and model_path:
                controlnet_pipe = self._get_controlnet_pipeline(model_path, controlnet_type)
                if controlnet_pipe:
                    pipe = controlnet_pipe
                    print(f"   🧠 使用 ControlNet: {controlnet_type} (强度: {controlnet_strength})")
                else:
                    print("   ⚠️ ControlNet 不可用，使用普通模式")
            
            # ===== 如果没有 pipe，加载普通模型 =====
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
            
            # ===== 加载原图 =====
            init_image = Image.open(image_path).convert('RGB')
            w, h = init_image.size
            width = ((w + 31) // 64) * 64
            height = ((h + 31) // 64) * 64
            if w != width or h != height:
                init_image = init_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # ===== 如果启用 ControlNet，生成控制图 =====
            control_image = None
            if use_controlnet and controlnet_pipe is not None:
                control_image = self._preprocess_for_controlnet(
                    image_path, 
                    controlnet_type=controlnet_type,
                    target_size=(width, height)
                )
                if control_image:
                    print(f"   ✅ 控制图已生成: {control_image.size}")
                else:
                    print("   ⚠️ 控制图生成失败，使用普通模式")
            
            # ===== 获取参数 =====
            prompts = self._generate_sketch_prompts()
            strength = config.get("strength", 0.25)
            steps = config.get("steps", 30)
            cfg = config.get("cfg", 7.0)
            
            generator = torch.Generator("cpu").manual_seed(42)
            success_count = 0
            
            # ===== 执行生成 =====
            for idx, job in enumerate(prompts):
                print(f"   [{idx+1}/{len(prompts)}] {job.get('name', 'unknown')}")
                
                # 构建生成参数
                gen_kwargs = {
                    "prompt": job.get("prompt", ""),
                    "negative_prompt": job.get("negative", ""),
                    "image": init_image,
                    "strength": strength,
                    "num_inference_steps": steps,
                    "guidance_scale": cfg,
                    "generator": generator,
                }
                
                # ===== 如果是 ControlNet 模式，添加控制图参数 =====
                if control_image is not None and controlnet_pipe is not None:
                    gen_kwargs["control_image"] = control_image
                    gen_kwargs["controlnet_conditioning_scale"] = controlnet_strength
                    print(f"      🎛️ ControlNet 强度: {controlnet_strength}")
                
                result = pipe(**gen_kwargs)
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'sketch')}.png")
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
                    "controlnet_type": controlnet_type if control_image else None,
                }
            )
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e)
            )