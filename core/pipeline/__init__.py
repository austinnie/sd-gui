# core/pipeline/__init__.py

from .step import PipelineStep, StepResult, StepContext, StepStatus
from .pipeline import Pipeline, PipelineRegistry
from .steps import MarbleStep

# 延迟导入步骤，避免循环依赖
def register_all_steps():
    from .steps.marble_step import MarbleStep
    PipelineRegistry.register_step("marble", MarbleStep)
    # 后续扩展:
    # from .steps.qipao_step import QipaoStep
    # PipelineRegistry.register_step("qipao", QipaoStep)
    # from .steps.remove_clothes_step import RemoveClothesStep
    # PipelineRegistry.register_step("remove_clothes", RemoveClothesStep)