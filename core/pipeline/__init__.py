# core/pipeline/__init__.py

from .step import PipelineStep, StepResult, StepContext, StepStatus
from .pipeline import Pipeline, PipelineRegistry
from .steps import (
    MarbleStep,
    QipaoStep,
    CoupleStep,
    YogaStep,
    OilPaintingStep,
    AnimeXxxStep,
    RemoveClothesStep,  # ✅ 新增
)

# 注册所有步骤
def register_all_steps():
    PipelineRegistry.register_step("marble", MarbleStep)
    PipelineRegistry.register_step("qipao", QipaoStep)
    PipelineRegistry.register_step("couple", CoupleStep)
    PipelineRegistry.register_step("yoga", YogaStep)
    PipelineRegistry.register_step("oil_painting", OilPaintingStep)
    PipelineRegistry.register_step("anime_xxx", AnimeXxxStep)
    PipelineRegistry.register_step("remove_clothes", RemoveClothesStep)  # ✅ 新增