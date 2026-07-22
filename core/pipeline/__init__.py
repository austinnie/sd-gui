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
    HanfuStep,  # ✅ 新增
    WatercolorStep, InkWashStep, SketchStep, CyberpunkStep,
    VaporwaveStep, ThreeDRenderStep, BeachStep, ForestStep,
    SpaceStep, CastleStep, WeddingStep, LolitaStep, KimonoStep,
    EveningGownStep, VintageStep, CinematicStep,
    CoupleWatercolorStep, CoupleOilPaintingStep, FamilySketchStep,
    FriendsStyleStep, GroupPhotoStep, CoupleWeddingStep    
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
    PipelineRegistry.register_step("hanfu", HanfuStep)  # ✅ 新增
    
    # 风格转换类
    PipelineRegistry.register_step("watercolor", WatercolorStep)
    PipelineRegistry.register_step("ink_wash", InkWashStep)
    PipelineRegistry.register_step("sketch", SketchStep)
    PipelineRegistry.register_step("cyberpunk", CyberpunkStep)
    PipelineRegistry.register_step("vaporwave", VaporwaveStep)
    PipelineRegistry.register_step("three_d_render", ThreeDRenderStep)
    
    # 场景/主题类
    PipelineRegistry.register_step("beach", BeachStep)
    PipelineRegistry.register_step("forest", ForestStep)
    PipelineRegistry.register_step("space", SpaceStep)
    PipelineRegistry.register_step("castle", CastleStep)
    PipelineRegistry.register_step("wedding", WeddingStep)
    
    # 服装/造型类
    PipelineRegistry.register_step("lolita", LolitaStep)
    PipelineRegistry.register_step("kimono", KimonoStep)
    PipelineRegistry.register_step("evening_gown", EveningGownStep)
    PipelineRegistry.register_step("vintage", VintageStep)
    PipelineRegistry.register_step("cinematic", CinematicStep)   
    
    # ✅ 多人场景类
    PipelineRegistry.register_step("couple_watercolor", CoupleWatercolorStep)
    PipelineRegistry.register_step("couple_oil_painting", CoupleOilPaintingStep)
    PipelineRegistry.register_step("family_sketch", FamilySketchStep)
    PipelineRegistry.register_step("friends_style", FriendsStyleStep)
    PipelineRegistry.register_step("group_photo", GroupPhotoStep)
    PipelineRegistry.register_step("couple_wedding", CoupleWeddingStep) 

    PipelineRegistry.register_step("cyber_hanfu", CyberHanfuStep)  # <-- 新增这行    