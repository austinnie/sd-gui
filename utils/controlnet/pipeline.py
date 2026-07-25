# utils/controlnet/pipeline.py
"""
ControlNet Pipeline 管理
"""

import torch
import gc
from diffusers import ControlNetModel, StableDiffusionControlNetPipeline, EulerDiscreteScheduler

from .types import get_controlnet_info


def get_controlnet_pipeline(
    model_path: str,
    controlnet_type: str = "openpose",
    controlnet_model_path: str = None,
    device: str = "cpu"
):
    """
    加载 ControlNet Pipeline
    """
    try:
        info = get_controlnet_info(controlnet_type)
        model_id = info["model_id"]
        
        # 加载 ControlNet 模型
        if controlnet_model_path and os.path.exists(controlnet_model_path):
            controlnet = ControlNetModel.from_single_file(
                controlnet_model_path,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            print(f"📦 加载 ControlNet (本地): {os.path.basename(controlnet_model_path)}")
        else:
            controlnet = ControlNetModel.from_pretrained(
                model_id,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            print(f"📦 加载 ControlNet: {info['name']}")
        
        # 加载主模型
        pipe = StableDiffusionControlNetPipeline.from_single_file(
            model_path,
            controlnet=controlnet,
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
            use_safetensors=True,
            low_cpu_mem_usage=True
        )
        
        # 优化配置
        pipe.to(device)
        pipe.enable_vae_slicing()
        pipe.enable_attention_slicing()
        if hasattr(pipe.vae, 'enable_tiling'):
            pipe.vae.enable_tiling()
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        
        print(f"✅ ControlNet Pipeline 加载完成: {info['name']}")
        print(f"   📝 {info['description']}")
        return pipe
        
    except Exception as e:
        print(f"❌ ControlNet Pipeline 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_multi_controlnet_pipeline(
    model_path: str,
    controlnet_types: list = None,
    device: str = "cpu"
):
    """
    加载多层 ControlNet Pipeline
    """
    if controlnet_types is None:
        controlnet_types = ["openpose", "canny", "depth"]
    
    try:
        from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
        from diffusers import EulerDiscreteScheduler
        
        controlnets = []
        print(f"\n📦 加载多层 ControlNet ({len(controlnet_types)} 层)...")
        
        for ctype in controlnet_types:
            info = get_controlnet_info(ctype)
            print(f"   📦 {info['name']}...")
            
            cn = ControlNetModel.from_pretrained(
                info["model_id"],
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            controlnets.append(cn)
            print(f"      ✅ 加载完成")
        
        print(f"   📦 加载主模型...")
        pipe = StableDiffusionControlNetPipeline.from_single_file(
            model_path,
            controlnet=controlnets,
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
            use_safetensors=True,
            low_cpu_mem_usage=True
        )
        
        pipe.to(device)
        pipe.enable_vae_slicing()
        pipe.enable_attention_slicing()
        if hasattr(pipe.vae, 'enable_tiling'):
            pipe.vae.enable_tiling()
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        
        print(f"   ✅ 多层 ControlNet Pipeline 加载完成")
        return pipe, controlnets
        
    except Exception as e:
        print(f"❌ 多层 ControlNet Pipeline 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None