# gui/chat/__init__.py
"""
Chat 模块 - 智能会话相关功能
提供意图分析、LLM调用、提示词构建、上下文管理、生成处理器等
"""

from .intent_analyzer import IntentAnalyzer, IntentResult, UnsafeContentDetector
from .llm_client import LLMClient
from .prompt_builder import PromptBuilder
from .context_manager import ContextManager

# 新增导出
from .handlers import (
    BaseHandler,
    TextToImageHandler,
    ImageToImageHandler,
    CoupleHandler,
    ChatHandler,
)
from .lora_manager import LoraManager
from .controlnet_manager import ControlNetManager
from .ollama_manager import OllamaManager
from .utils import PromptCleaner, ParamEstimator, ImageAnalyzer, SafetyChecker

__all__ = [
    'IntentAnalyzer',
    'IntentResult',
    'UnsafeContentDetector',
    'LLMClient',
    'PromptBuilder',
    'ContextManager',
    # 新增
    'BaseHandler',
    'TextToImageHandler',
    'ImageToImageHandler',
    'CoupleHandler',
    'ChatHandler',
    'LoraManager',
    'ControlNetManager',
    'OllamaManager',
    'PromptCleaner',
    'ParamEstimator',
    'ImageAnalyzer',
    'SafetyChecker',
]