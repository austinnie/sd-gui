# core/pipeline/steps/__init__.py

from .marble_step import MarbleStep
from .qipao_step import QipaoStep
from .couple_step import CoupleStep
from .yoga_step import YogaStep
from .oil_painting_step import OilPaintingStep
from .anime_xxx_step import AnimeXxxStep
from .remove_clothes_step import RemoveClothesStep  # ✅ 新增

__all__ = [
    'MarbleStep',
    'QipaoStep',
    'CoupleStep',
    'YogaStep',
    'OilPaintingStep',
    'AnimeXxxStep',
    'RemoveClothesStep',  # ✅ 新增
]