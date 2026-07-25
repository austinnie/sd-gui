# services/__init__.py
"""服务模块"""

from .cache_config import (
    CACHE_ROOT,
    HF_HUB_CACHE,
    U2NET_HOME,
    DEEPFACE_HOME,
)
from .llm_service import LLMService, llm_service
from .ollama_service import OllamaManager, ollama_manager

__all__ = [
    'CACHE_ROOT',
    'HF_HUB_CACHE',
    'U2NET_HOME',
    'DEEPFACE_HOME',
    'LLMService',
    'llm_service',
    'OllamaManager',
    'ollama_manager',
]