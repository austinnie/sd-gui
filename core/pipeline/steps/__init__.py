# core/pipeline/steps/__init__.py

import torch  # ✅ 在这里导入一次

from .controlnet_mixin import ControlNetMixin

from .marble_step import MarbleStep
from .qipao_step import QipaoStep
from .couple_step import CoupleStep
from .yoga_step import YogaStep
from .oil_painting_step import OilPaintingStep
from .anime_xxx_step import AnimeXxxStep
from .remove_clothes_step import RemoveClothesStep  # ✅ 新增
from .hanfu_step import HanfuStep  # ✅ 新增

# ✅ 风格转换类
from .watercolor_step import WatercolorStep
from .ink_wash_step import InkWashStep
from .sketch_step import SketchStep
from .cyberpunk_step import CyberpunkStep
from .vaporwave_step import VaporwaveStep
from .three_d_render_step import ThreeDRenderStep

# ✅ 场景/主题类
from .beach_step import BeachStep
from .forest_step import ForestStep
from .space_step import SpaceStep
from .castle_step import CastleStep
from .wedding_step import WeddingStep

# ✅ 服装/造型类
from .lolita_step import LolitaStep
from .kimono_step import KimonoStep
from .evening_gown_step import EveningGownStep
from .vintage_step import VintageStep
from .cinematic_step import CinematicStep

# ✅ 多人场景类
from .couple_watercolor_step import CoupleWatercolorStep
from .couple_oil_painting_step import CoupleOilPaintingStep
from .family_sketch_step import FamilySketchStep
from .friends_style_step import FriendsStyleStep
from .group_photo_step import GroupPhotoStep
from .couple_wedding_step import CoupleWeddingStep

# ✅ 新增：赛博古风
from .cyber_hanfu_step import CyberHanfuStep  # <-- 新增这行
from .marble_yoga_step import MarbleYogaStep  

__all__ = [
    'ControlNetMixin',  # ✅ 新增
    'MarbleStep',
    'QipaoStep',
    'CoupleStep',
    'YogaStep',
    'OilPaintingStep',
    'AnimeXxxStep',
    'RemoveClothesStep',  # ✅ 新增
    'HanfuStep',  # ✅ 新增
    # 风格转换类
    'WatercolorStep', 'InkWashStep', 'SketchStep', 'CyberpunkStep',
    'VaporwaveStep', 'ThreeDRenderStep',
    # 场景/主题类
    'BeachStep', 'ForestStep', 'SpaceStep', 'CastleStep', 'WeddingStep',
    # 服装/造型类
    'LolitaStep', 'KimonoStep', 'EveningGownStep', 'VintageStep', 'CinematicStep',  
    # ✅ 多人场景类
    'CoupleWatercolorStep', 'CoupleOilPaintingStep', 'FamilySketchStep',
    'FriendsStyleStep', 'GroupPhotoStep', 'CoupleWeddingStep' ,
    # ✅ 新增：赛博古风
    'CyberHanfuStep',  # <-- 新增这行
    'MarbleYogaStep',      
]