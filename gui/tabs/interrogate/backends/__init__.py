# gui/tabs/interrogate/backends/__init__.py

from .base import InterrogateBackend
from .tag import TagBackend
from .clip import ClipBackend
from .blip import BlipBackend
from .combined import CombinedBackend
from .llm import LLMBackend  # ✅ 新增

__all__ = [
    'InterrogateBackend',
    'TagBackend',
    'ClipBackend',
    'BlipBackend',
    'CombinedBackend',
    'LLMBackend',  # ✅ 新增
]