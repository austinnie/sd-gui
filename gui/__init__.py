#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI 模块
"""

from .app import SDApp, main
from .scene_manager import SceneManager

# ✅ 新增：导出 chat 子模块
from .chat import (
    IntentAnalyzer,
    IntentResult,
    UnsafeContentDetector,
    LLMClient,
    PromptBuilder,
    ContextManager,
)


__all__ = [
    'SDApp',
    'main',
    'SceneManager',
    # ✅ 新增
    'IntentAnalyzer',
    'IntentResult',
    'UnsafeContentDetector',
    'LLMClient',
    'PromptBuilder',
    'ContextManager',
]