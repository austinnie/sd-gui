# utils/scheduler_factory.py
"""
调度器工厂 - 根据名称创建调度器
"""

from diffusers import (
    EulerDiscreteScheduler,
    DPMSolverMultistepScheduler,
    LMSDiscreteScheduler,
    PNDMScheduler,
)


def get_scheduler(scheduler_name: str, config):
    """
    根据名称创建调度器
    
    参数:
        scheduler_name: 调度器名称 (euler, dpm, lms, pndm)
        config: 原始调度器的配置
    
    返回:
        调度器实例
    """
    scheduler_map = {
        "euler": EulerDiscreteScheduler,
        "dpm": DPMSolverMultistepScheduler,
        "lms": LMSDiscreteScheduler,
        "pndm": PNDMScheduler,
    }
    
    scheduler_class = scheduler_map.get(scheduler_name, EulerDiscreteScheduler)
    
    # 特殊配置
    if scheduler_name == "dpm":
        # DPMSolver 可以使用更少的步数
        return scheduler_class.from_config(
            config,
            algorithm_type="dpmsolver++",
            solver_order=2,
            prediction_type="epsilon"
        )
    elif scheduler_name == "euler":
        return scheduler_class.from_config(config)
    else:
        return scheduler_class.from_config(config)


def get_scheduler_description(scheduler_name: str) -> str:
    """获取调度器描述"""
    descriptions = {
        "euler": "稳定通用，细节丰富",
        "dpm": "速度快，步数少",
        "lms": "清晰度高，边缘锐利",
        "pndm": "经典稳定",
    }
    return descriptions.get(scheduler_name, "")