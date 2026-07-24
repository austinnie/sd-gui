# core/config_loader.py
"""
配置加载器 - 使用 ConfigManager
保持原有 API 不变，确保兼容性
"""
import json
import os
from typing import Dict, List, Any, Optional
from config.config_manager import config_manager


class ConfigLoader:
    """配置加载器 - 单例模式，基于 ConfigManager"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化"""
        self.base_path = os.path.dirname(os.path.dirname(__file__))
        self.templates_path = os.path.join(self.base_path, "templates")
    
    def load(self, config_name: str) -> dict:
        """
        加载配置文件
        
        参数:
            config_name: 配置文件名 (如 'persons', 'scenes', 'relationships')
        
        返回:
            配置字典
        """
        # 映射到 ConfigManager 的 key
        mapping = {
            'persons': 'persons',
            'scenes': 'scene',
            'relationships': 'relationships',
            'presets': 'gui',  # presets 在 gui_config 中
        }
        
        key = mapping.get(config_name, config_name)
        return config_manager.get(key)
    
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
            # 映射到 ConfigManager 的 key
            mapping = {
                'persons': 'persons',
                'scenes': 'scene',
                'relationships': 'relationships',
            }
            key = mapping.get(config_name, config_name)
            config_manager.reload(key)
        else:
            config_manager.reload()

# 全局配置加载器实例（保持原有接口）
config = ConfigLoader()