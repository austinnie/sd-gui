# gui/__init__.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI 模块
"""

from .app import SDApp, main
from .scene_manager import SceneManager

# ✅ 新增：导出拆分后的模块
from .model_manager import ModelManager, ModelType
from .model_loader import scan_checkpoints, scan_loras, scan_vaes, get_optimization_info
from .ui_builder import UIBuilder
from .lora_handler import LoraHandler
from .vae_handler import VaeHandler
from .reloader import Reloader

__all__ = [
    'SDApp',
    'main',
    'SceneManager',
    # ✅ 新增
    'ModelManager',
    'ModelType',
    'scan_checkpoints',
    'scan_loras',
    'scan_vaes',
    'get_optimization_info',
    'UIBuilder',
    'LoraHandler',
    'VaeHandler',
    'Reloader',
]