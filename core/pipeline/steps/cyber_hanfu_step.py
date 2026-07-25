# core/pipeline/steps/cyber_hanfu_step.py
"""
赛博古风场景转换步骤 - 汉服 + 赛博朋克融合风格
支持 ControlNet
"""

import os
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from ..step import PipelineStep, StepContext, StepResult, StepStatus
from .controlnet_mixin import ControlNetMixin


class CyberHanfuStep(PipelineStep, ControlNetMixin):
    """赛博古风转换步骤 - 汉服 + 赛博朋克融合"""
    
    def __init__(self):
        super().__init__("cyber_hanfu", "赛博古风 - 汉服+赛博朋克融合")
        self._config = {
            "strength": 0.40,
            "cfg": 7.5,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "hed",
            "controlnet_strength": 0.5,
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.40, "min": 0.2, "max": 0.65},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {"type": "str", "default": "hed", 
                               "choices": ["hed", "canny", "lineart", "openpose"]},
            "controlnet_strength": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0},
        }
    
    def _generate_cyber_hanfu_prompts(self) -> list:
        """生成赛博古风场景提示词"""
        return [
            # ===== 经典赛博古风 =====
            {
                "name": "赛博汉服_霓虹", 
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman wearing futuristic hanfu, cyberpunk traditional Chinese clothing, glowing neon patterns on flowing silk robes, holographic embroidery, digital phoenix motifs, neon lights reflecting on silk, cyberpunk city background, rain, holographic elements, high tech traditional fusion, full body shot, dramatic lighting, high quality, detailed",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull, dark, gloomy, medieval, primitive"
            },
            {
                "name": "赛博汉服_古风都会",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman in cyberpunk hanfu, traditional Chinese robes with LED trim, glowing jade ornaments, digital cloud patterns on silk, futuristic city skyline with Chinese architecture, holographic lanterns, neon signs with Chinese characters, cyberpunk atmosphere, full body shot, high quality, detailed, cinematic lighting",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull, dark"
            },
            {
                "name": "赛博汉服_夜雨",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman wearing glowing hanfu in rain, neon reflections on wet silk, cyberpunk traditional dress, holographic lotus patterns, umbrella with LED rim, rain at night, cyberpunk city with Chinese elements, dramatic lighting, full body shot, high quality, detailed, atmospheric",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull, dark, gloomy"
            },
            {
                "name": "赛博汉服_数据飞花",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman in futuristic hanfu, digital cherry blossoms falling, glowing silk robes, cyberpunk traditional wear, holographic butterflies, glass and steel pavilion, neon lights, sci-fi ancient fusion, full body shot, high quality, detailed, ethereal, cyberpunk fantasy",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull"
            },
            {
                "name": "赛博汉服_云端",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman in cyber hanfu, glowing flowing robes, holographic cloud patterns, futuristic Chinese palace floating in sky, neon aurora, cyberpunk traditional aesthetics, full body shot, high quality, detailed, dreamy, cyberpunk fairy tale",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull"
            },
            
            # ===== 角色扮演 =====
            {
                "name": "赛博汉服_侠女",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful female swordsman in cyberpunk hanfu, glowing traditional armor, LED sword, holographic cape, cyberpunk city rooftop, neon lights, dramatic pose, full body shot, high quality, detailed, cyberpunk wuxia, powerful, majestic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull"
            },
            {
                "name": "赛博汉服_仙女",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful celestial being in cyber hanfu, glowing flowing ribbons, holographic wings, digital star patterns on silk, cyberpunk heavenly palace, neon galaxy background, full body shot, high quality, detailed, ethereal, cyberpunk goddess",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull"
            },
            {
                "name": "赛博汉服_琴师",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman playing a futuristic guqin, wearing cyber hanfu, glowing silk robes, holographic musical notes floating, cyberpunk traditional tea house, neon lights, full body shot, high quality, detailed, artistic, cyberpunk classical fusion",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull"
            },
            
            # ===== 双人场景 =====
            {
                "name": "赛博汉服_双人_并肩",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a man and woman in cyberpunk hanfu, traditional Chinese robes with glowing neon trim, standing side by side, cyberpunk city background with Chinese architecture, holographic lanterns, full body shot, high quality, detailed, dramatic lighting, cyberpunk couple, elegant and futuristic",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull, single person"
            },
            {
                "name": "赛博汉服_双人_对视",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a man and woman in cyber hanfu, traditional fusion attire, glowing silk robes, facing each other intimately, cyberpunk Chinese garden, neon flowers, romantic atmosphere, full body shot, high quality, detailed, dramatic lighting, cyberpunk romance",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, vintage, rustic, plain, simple, boring, dull, single person"
            }
        ]
    
    def execute(self, context: StepContext) -> StepResult:
        """执行赛博古风转换 - 支持 ControlNet"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, "cyber_hanfu")
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
            all_prompts = self._generate_cyber_hanfu_prompts()
            if max_scenes is not None and max_scenes > 0:
                prompts = self._limit_prompts(all_prompts, max_scenes)
                print(f"   📊 场景限制: 只生成前 {len(prompts)}/{len(all_prompts)} 个场景")
            else:
                prompts = all_prompts
            
            strength = config.get("strength", 0.40)
            steps = config.get("steps", 30)
            cfg = config.get("cfg", 7.5)
            
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
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'cyber_hanfu')}.png")
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