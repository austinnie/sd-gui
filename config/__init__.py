# config/__init__.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置模块 - 统一配置管理
推荐使用 config_manager 获取所有配置
"""

# ✅ 主要：统一配置管理器（推荐使用）
from .config_manager import config_manager, ConfigManager

# ✅ 保留：旧配置（兼容期，逐步废弃）
from .app_config import AppConfig, app_config
from .nsfw_config import NSFWConfig, ContentLevel, nsfw_config
from .janus_config import JanusAppConfig, janus_config

# 🆕 推荐使用 config_manager
__all__ = [
    # 新配置（推荐）
    'config_manager',
    'ConfigManager',
    # 旧配置（兼容）
    'AppConfig',
    'app_config',
    'NSFWConfig',
    'ContentLevel',
    'nsfw_config',
    'JanusAppConfig',
    'janus_config',
]