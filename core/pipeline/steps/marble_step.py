# core/pipeline/steps/marble_step.py
"""大理石转换步骤 - 复用现有 run_marble.py"""

import os
import json
import subprocess
import shutil
from PIL import Image
from datetime import datetime

from ..step import PipelineStep, StepContext, StepResult, StepStatus


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

    def execute(self, context: StepContext) -> StepResult:
        """执行大理石转换"""
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
            # ✅ 设置环境变量
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
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
            
            # ✅ 方案 1：不捕获输出，直接显示在控制台
            result = subprocess.run(
                config_cmd,
                shell=True,
                env=env
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
            # 步骤 3: 执行生成（直接输出到控制台）
            # ============================================================
            run_cmd = f'python run_marble.py -c "{latest_config}"'
            print(f"\n🎨 执行生成: {run_cmd}")
            print("-" * 60)
            
            # ✅ 方案 1：不捕获输出，直接显示在控制台
            result = subprocess.run(
                run_cmd,
                shell=True,
                env=env
            )
            
            print("-" * 60)
            
            if result.returncode != 0:
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"生成失败，返回码: {result.returncode}"
                )
            
            # ============================================================
            # 步骤 4: 收集输出图片
            # ============================================================
            output_images_dir = "output/batch_marble"
            if os.path.exists(output_images_dir):
                output_images = [f for f in os.listdir(output_images_dir) if f.endswith(".png")]
                if output_images:
                    output_images.sort(
                        key=lambda x: os.path.getmtime(os.path.join(output_images_dir, x)),
                        reverse=True
                    )
                    first_image_path = os.path.join(output_images_dir, output_images[0])
                    
                    dest_path = os.path.join(output_dir, os.path.basename(first_image_path))
                    shutil.copy2(first_image_path, dest_path)
                    
                    print(f"\n📁 第一张输出: {dest_path}")
                    
                    return StepResult(
                        status=StepStatus.SUCCESS,
                        output_path=dest_path,
                        output_image=Image.open(dest_path),
                        metadata={
                            "config_file": latest_config,
                            "output_count": len(output_images),
                            "output_dir": output_images_dir,
                            "first_image": output_images[0] if output_images else None
                        }
                    )
            
            return StepResult(
                status=StepStatus.SUCCESS,
                output_path=output_dir,
                metadata={"message": "生成完成", "output_dir": output_images_dir}
            )
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e)
            )