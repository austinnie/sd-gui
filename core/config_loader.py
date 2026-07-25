#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置加载器 - 统一管理所有配置文件的加载
"""

import json
import os
from typing import Dict, List, Any, Optional


from utils.logger import get_logger

logger = get_logger(__name__)
class ConfigLoader:
    """配置加载器 - 单例模式"""
    
    _instance = None
    _configs = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化，设置模板路径"""
        self.base_path = os.path.dirname(os.path.dirname(__file__))
        self.templates_path = os.path.join(self.base_path, "templates")
    
    def load(self, config_name: str) -> dict:
        """
        加载配置文件
        
        参数:
            config_name: 配置文件名 (如 'persons', 'scenes', 'relationships', 'presets')
        
        返回:
            配置字典
        """
        if config_name in self._configs:
            return self._configs[config_name]
        
        file_path = os.path.join(self.templates_path, f"{config_name}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._configs[config_name] = json.load(f)
                return self._configs[config_name]
            except Exception as e:
                logger.info(f"❌ 加载配置失败 {config_name}: {e}")
                return {}
        else:
            logger.info(f"⚠️ 配置文件不存在: {file_path}")
            return {}
    
    def get_category(self, config_name: str, category: str) -> dict:
        """获取配置中的某个分类"""
        config = self.load(config_name)
        return config.get(category, {})
    
    def get_item(self, config_name: str, category: str, item_key: str) -> dict:
        """获取配置中的某个项目"""
        category_dict = self.get_category(config_name, category)
        return category_dict.get(item_key, {})
    
    def get_prompt(self, config_name: str, category: str, item_key: str) -> str:
        """获取项目的 prompt 字段"""
        item = self.get_item(config_name, category, item_key)
        return item.get("prompt", "")
    
    def get_negative(self, config_name: str, category: str, item_key: str) -> str:
        """获取项目的 negative 字段"""
        item = self.get_item(config_name, category, item_key)
        return item.get("negative", "")
    
    def list_categories(self, config_name: str) -> List[str]:
        """列出配置中的所有分类"""
        config = self.load(config_name)
        return list(config.keys())
    
    def list_items(self, config_name: str, category: str) -> List[str]:
        """列出分类中的所有项目"""
        category_dict = self.get_category(config_name, category)
        return list(category_dict.keys())
    
    def reload(self, config_name: str = None):
        """重新加载配置"""
        if config_name:
            if config_name in self._configs:
                del self._configs[config_name]
            self.load(config_name)
        else:
            self._configs.clear()
            self._initialize()


# 全局配置加载器实例
config = ConfigLoader()