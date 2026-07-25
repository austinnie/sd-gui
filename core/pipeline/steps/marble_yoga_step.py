# core/pipeline/steps/marble_yoga_step.py
"""大理石瑜伽雕像风格 - 组合 Marble 材质 + Yoga 姿势 (完整版)"""

import os
import torch
from PIL import Image
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from ..step import PipelineStep, StepContext, StepResult, StepStatus
from .controlnet_mixin import ControlNetMixin


class MarbleYogaStep(PipelineStep, ControlNetMixin):
    """大理石瑜伽雕像转换步骤 - 支持 ControlNet"""
    
    def __init__(self):
        super().__init__("marble_yoga", "将人物转换为大理石雕像瑜伽姿势")
        self._config = {
            "strength": 0.40,
            "cfg": 7.0,
            "steps": 25,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "canny",
            "controlnet_strength": 0.6,
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.40, "min": 0.2, "max": 0.6},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 25, "min": 15, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {"type": "str", "default": "canny", 
                               "choices": ["canny", "hed", "lineart", "depth", "openpose"]},
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }

    def _generate_marble_yoga_jobs(self) -> list:
        """生成大理石瑜伽雕像的 jobs 列表 (包含完整提示词)"""
        return [
            {
                "name": "大理石瑜伽_单腿鸽王式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing king pigeon pose, one leg bent back, body arched gracefully, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_战士二式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing warrior pose II, lunge, arms extended parallel to the ground, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_弓式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing bow pose, lying on stomach, hands pulling feet, body arched like a bow, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_树式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing tree pose, standing on one leg, hands clasped above head, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_金刚坐冥想",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing thunderbolt pose, kneeling, hands resting on knees, meditating, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_上犬式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing upward facing dog pose, chest open, arms straight, legs extended, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_舞王式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing dancer pose, standing on one leg, holding back foot with hand, body arched gracefully, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_头倒立",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing headstand, balancing on forearms, legs straight up in the air, inverted pose, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_半月式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing half moon pose, balancing on one leg and one hand, body extended sideways, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_头倒立变体",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing headstand with legs crossed, balancing on forearms, legs intertwined in air, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_鹤禅式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing crane pose, balancing on hands, knees resting on upper arms, focused look, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_双人支撑",
                "prompt": "masterpiece, best quality, photorealistic, 8k, two beautiful women, pure white marble statues, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing partner acroyoga, one standing on the other's back, balancing beautifully, full bodies visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_骆驼式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing camel pose, kneeling, arching back, hands reaching heels, chest open, intense stretch, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_战士一式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing warrior pose I, lunge stance, arms raised straight up, looking forward, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_站立前屈",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing standing forward fold, bending forward from the hips, hands reaching to the ground, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            },
            {
                "name": "大理石瑜伽_轮式",
                "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, pure white marble statue, flawless white marble, monochrome white, classical sculpture, intricate carving details, smooth stone texture, dramatic lighting, doing wheel pose, hands and feet on the ground, body arched like a bridge, full body visible, high quality, photorealistic, masterpiece",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, color, skin tone, warm tones, beige, yellow, gray, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, clothes, fabric, different person"
            }
            ]
    
    def execute(self, context: StepContext) -> StepResult:
        """执行大理石瑜伽转换 - 支持 ControlNet"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, "marble_yoga")
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
            all_jobs = self._generate_marble_yoga_jobs()
            if max_scenes is not None and max_scenes > 0:
                jobs = self._limit_prompts(all_jobs, max_scenes)
                print(f"   📊 场景限制: 只生成前 {len(jobs)}/{len(all_jobs)} 个姿势")
            else:
                jobs = all_jobs
            
            steps_override = config.get("steps", 25)
            cfg_override = config.get("cfg", 7.0)
            strength_override = config.get("strength", 0.40)
            
            print(f"\n🎨 执行大理石瑜伽转换: {len(jobs)} 个姿势")
            print(f"   步数: {steps_override}, CFG: {cfg_override}, 强度: {strength_override}")
            if control_image is not None:
                print(f"   🧠 ControlNet: {config.get('controlnet_type', 'canny')} (强度: {config.get('controlnet_strength', 0.6)})")
            
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
                    
                    output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'marble_yoga')}.png")
                    result.images[0].save(output_path)
                    success_count += 1
                    print(f"      ✅ 已保存: {os.path.basename(output_path)}")
                    
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