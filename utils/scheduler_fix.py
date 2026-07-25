# utils/scheduler_fix.py
"""
调度器修复工具 - 解决 Euler 调度器在图生图中的索引越界问题
"""

from diffusers import EulerDiscreteScheduler


from utils.logger import get_logger

logger = get_logger(__name__)
def fix_euler_scheduler_for_img2img(pipe, steps, strength):
    """
    修复 Euler 调度器在图生图中的索引越界问题
    
    参数:
        pipe: diffusers pipeline
        steps: 推理步数
        strength: 重绘强度
    
    返回:
        (修复后的 pipe, 修正后的 steps, 修正后的 strength)
    """
    if not hasattr(pipe, 'scheduler'):
        return pipe, steps, strength
    
    if isinstance(pipe.scheduler, EulerDiscreteScheduler):
        # 重置调度器
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        logger.info(f"   🔄 Euler 调度器已重置")
        
        # 确保步数至少为 10
        if steps < 10:
            steps = 10
            logger.info(f"   ⚠️ 步数太少，已自动调整为 {steps}")
        
        # 确保实际步数至少为 2
        actual_steps = int(steps * strength)
        if actual_steps < 2:
            old_strength = strength
            strength = max(0.2, 2.0 / steps)
            logger.info(f"   ⚠️ strength {old_strength:.2f} 导致步数太少，已调整为 {strength:.2f}")
    
    return pipe, steps, strength


def fix_scheduler_before_step(pipe):
    """
    在每次 step 调用前重置调度器状态
    
    参数:
        pipe: diffusers pipeline
    
    返回:
        修复后的 pipe
    """
    if hasattr(pipe, 'scheduler') and isinstance(pipe.scheduler, EulerDiscreteScheduler):
        try:
            pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
            logger.info(f"   🔄 调度器状态已重置")
        except Exception as e:
            logger.info(f"   ⚠️ 调度器重置失败: {e}")
    
    return pipe