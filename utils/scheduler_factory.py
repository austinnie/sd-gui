# utils/scheduler_factory.py
"""
调度器工厂 - 根据名称创建调度器
"""

from diffusers import (
    EulerDiscreteScheduler,
    EulerAncestralDiscreteScheduler,
    DPMSolverMultistepScheduler,
    DPMSolverSinglestepScheduler,
    LMSDiscreteScheduler,
    HeunDiscreteScheduler,
    PNDMScheduler,
    UniPCMultistepScheduler,
    DEISMultistepScheduler,
    DDIMScheduler,
    DDPMScheduler,
    KDPM2DiscreteScheduler,
    KDPM2AncestralDiscreteScheduler,
)


def get_scheduler(scheduler_name: str, config):
    """
    根据名称创建调度器
    
    参数:
        scheduler_name: 调度器名称
        config: 原始调度器的配置
    
    返回:
        调度器实例
    """
    scheduler_map = {
        # 基础调度器
        "euler": EulerDiscreteScheduler,
        "euler_ancestral": EulerAncestralDiscreteScheduler,
        "lms": LMSDiscreteScheduler,
        "heun": HeunDiscreteScheduler,
        "pndm": PNDMScheduler,
        "ddim": DDIMScheduler,
        "ddpm": DDPMScheduler,
        
        # DPM 系列
        "dpm": DPMSolverMultistepScheduler,
        "dpm++": DPMSolverSinglestepScheduler,
        
        # 快速求解器
        "unipc": UniPCMultistepScheduler,
        "deis": DEISMultistepScheduler,
        
        # Karras 系列
        "kdpm2": KDPM2DiscreteScheduler,
        "kdpm2_ancestral": KDPM2AncestralDiscreteScheduler,
    }
    
    scheduler_class = scheduler_map.get(scheduler_name, EulerDiscreteScheduler)
    
    # 特殊配置
    if scheduler_name in ["dpm", "dpm++"]:
        return scheduler_class.from_config(
            config,
            algorithm_type="dpmsolver++",
            solver_order=2,
            prediction_type="epsilon"
        )
    elif scheduler_name in ["kdpm2", "kdpm2_ancestral"]:
        return scheduler_class.from_config(
            config,
            prediction_type="epsilon"
        )
    elif scheduler_name == "unipc":
        return scheduler_class.from_config(
            config,
            solver_type="bh1",  # 或 "bh2"
            prediction_type="epsilon"
        )
    else:
        return scheduler_class.from_config(config)


def get_scheduler_description(scheduler_name: str) -> str:
    """获取调度器描述"""
    descriptions = {
        "euler": "稳定写实，细节丰富",
        "euler_ancestral": "创造性强，变体丰富",
        "dpm": "速度快，质量均衡",
        "dpm++": "DPM 增强版，更优",
        "lms": "线性多步，艺术风格",
        "heun": "二阶精度，更细腻",
        "pndm": "经典稳定，兼容性好",
        "unipc": "极速生成，高质量",
        "deis": "快速高质量",
        "ddim": "确定性，可复现",
        "ddpm": "标准扩散，学术用",
        "kdpm2": "Karras 高画质",
        "kdpm2_ancestral": "Karras 创意变体",
    }
    return descriptions.get(scheduler_name, "")


def get_scheduler_recommended_steps(scheduler_name: str) -> int:
    """获取调度器推荐步数"""
    steps_map = {
        "euler": 25,
        "euler_ancestral": 25,
        "dpm": 20,
        "dpm++": 20,
        "lms": 25,
        "heun": 25,
        "pndm": 25,
        "unipc": 15,
        "deis": 15,
        "ddim": 25,
        "ddpm": 30,
        "kdpm2": 20,
        "kdpm2_ancestral": 20,
    }
    return steps_map.get(scheduler_name, 25)


def get_scheduler_min_steps(scheduler_name: str) -> int:
    """获取调度器最少步数"""
    min_steps_map = {
        "euler": 10,
        "euler_ancestral": 10,
        "dpm": 5,
        "dpm++": 5,
        "lms": 10,
        "heun": 10,
        "pndm": 10,
        "unipc": 5,
        "deis": 5,
        "ddim": 10,
        "ddpm": 15,
        "kdpm2": 5,
        "kdpm2_ancestral": 5,
    }
    return min_steps_map.get(scheduler_name, 10)