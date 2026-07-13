# core/pipeline/steps/marble_step.py
"""大理石转换步骤 - 复用现有 run_marble.py"""

import os
import json
import subprocess
import shutil
from PIL import Image
from datetime import datetime
from ..step import PipelineStep, StepContext, StepResult, StepStatus
import torch

class MarbleStep(PipelineStep):
    """大理石雕像转换步骤 - 复用现有脚本"""
    
    def __init__(self):
        super().__init__("marble", "将人物转换为大理石雕像")
        # 默认配置
        self._config = {
            "strength": 0.25,
            "max_strength": 0.55,
            "cfg": 7.0,
            "steps": 15,
            "scenes": 14,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors"
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.25, "min": 0.1, "max": 0.5},
            "max_strength": {"type": "float", "default": 0.55, "min": 0.3, "max": 0.8},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 15, "min": 10, "max": 40},
            "scenes": {"type": "int", "default": 14, "choices": [6, 12, 14]},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"}
        }
        
    # core/pipeline/steps/marble_step.py
    def execute(self, context: StepContext) -> StepResult:
        """执行大理石转换（使用上下文中的 pipe）"""
        
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(context.output_dir, "marble")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # ===== 从上下文获取 pipe =====
            pipe = context.global_config.get('pipe')
            model_path = context.global_config.get('model_path')
            
            if pipe is None and model_path:
                # 如果没有传入 pipe，独立加载（兼容旧逻辑）
                from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

                
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
            
            # ============================================================
            # 步骤 1: 生成配置文件
            # ============================================================
            config_cmd = (
                f'python gen_config_marble_v2.py '
                f'--target-image "{image_path}" '
                f'--strength {config["strength"]} '
                f'--max-strength {config["max_strength"]} '
                f'--cfg {config["cfg"]} '
                f'--steps {config["steps"]} '
                f'--scenes {config["scenes"]}'
            )
            
            print(f"\n📦 生成配置: {config_cmd}")
            
            result = subprocess.run(
                config_cmd,
                shell=True,
                capture_output=False
            )
            
            if result.returncode != 0:
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"配置生成失败，返回码: {result.returncode}"
                )
            
            # ============================================================
            # 步骤 2: 查找最新生成的配置文件
            # ============================================================
            config_dir = "output/configs"
            if not os.path.exists(config_dir):
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"配置目录不存在: {config_dir}"
                )
            
            config_files = sorted(
                [f for f in os.listdir(config_dir) if f.startswith("marble_batch_config_")],
                key=lambda x: os.path.getmtime(os.path.join(config_dir, x)),
                reverse=True
            )
            
            if not config_files:
                return StepResult(
                    status=StepStatus.FAILED,
                    error="未找到生成的配置文件"
                )
            
            latest_config = os.path.join(config_dir, config_files[0])
            print(f"✅ 配置文件: {latest_config}")
            
            # ============================================================
            # 步骤 3: 使用 pipe 执行生成（直接调用，不用 subprocess）
            # ============================================================
            with open(latest_config, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            jobs = config_data.get('jobs', [])
            target_image = config_data.get('target_image', image_path)
            steps_override = config.get("steps", 15)
            cfg_override = config.get("cfg", 7.0)
            strength_override = config.get("strength", 0.25)
            
            print(f"\n🎨 执行生成: {len(jobs)} 个场景")
            
            for idx, job in enumerate(jobs):
                print(f"   [{idx+1}/{len(jobs)}] {job.get('name', 'unknown')}")
                
                try:
                    # 加载图片
                    init_image = Image.open(target_image).convert('RGB')
                    w, h = init_image.size
                    width = ((w + 31) // 64) * 64
                    height = ((h + 31) // 64) * 64
                    if w != width or h != height:
                        init_image = init_image.resize((width, height), Image.Resampling.LANCZOS)
                    
                    generator = torch.Generator("cpu").manual_seed(42)
                    
                    result = pipe(
                        prompt=job.get("prompt", ""),
                        negative_prompt=job.get("negative", ""),
                        image=init_image,
                        strength=job.get("strength", strength_override),
                        num_inference_steps=steps_override,
                        guidance_scale=cfg_override,
                        generator=generator,
                    )
                    
                    # 后处理为大理石效果
                    temp_path = os.path.join(output_dir, f"temp_{idx}.png")
                    result.images[0].save(temp_path)
                    
                    from run_marble import post_process_to_marble
                    output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'marble')}.png")
                    post_process_to_marble(temp_path, output_path, brightness_enhance=1.0)
                    
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    print(f"      ✅ 已保存: {os.path.basename(output_path)}")
                    
                except Exception as e:
                    print(f"      ❌ 失败: {e}")
                    continue
            
            # 返回结果
            return StepResult(
                status=StepStatus.SUCCESS,
                output_path=output_dir,
                metadata={
                    "config_file": latest_config,
                    "output_count": len(jobs),
                    "output_dir": output_dir,
                    "success_count": len(jobs)
                }
            )
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e)
            )
        