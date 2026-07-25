# config/config_manager.py
"""
统一配置管理器 - 第一阶段
所有 JSON 配置文件的加载入口
"""
import json
import os
from typing import Dict, Any, Optional

class ConfigManager:
    """统一配置管理器（单例）"""
    
    _instance = None
    _configs: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._load_all()
    
    def _load_all(self):
        """加载所有配置文件"""
        # 1. 加载 gui_config.json
        self._configs['gui'] = self._load_json('data/configs/gui_config.json')
        
        # 2. 加载 nsfw_config.json
        self._configs['nsfw'] = self._load_json('data/configs/nsfw_config.json')
        
        # 3. 加载 scene_patterns.json
        self._configs['scene'] = self._load_json('data/configs/scene_patterns.json')
        
        # 4. 加载 templates/persons.json
        self._configs['persons'] = self._load_json('data/templates/persons.json')
        
        # 5. 加载 templates/relationships.json
        self._configs['relationships'] = self._load_json('data/templates/relationships.json')
        
        # 6. 加载 templates/prompt_templates.json
        self._configs['prompt_templates'] = self._load_json('data/templates/prompt_templates.json')
    
    def _load_json(self, relative_path: str) -> dict:
        """加载 JSON 文件"""
        full_path = os.path.join(self._project_root, relative_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 加载配置失败 {relative_path}: {e}")
                return {}
        return {}
    
    def get(self, name: str) -> dict:
        """获取配置"""
        return self._configs.get(name, {})
    
    def get_gui_config(self) -> dict:
        """获取 GUI 配置"""
        return self._configs.get('gui', {})
    
    def get_nsfw_config(self) -> dict:
        """获取 NSFW 配置"""
        return self._configs.get('nsfw', {})
    
    def get_scene_config(self) -> dict:
        """获取场景配置"""
        return self._configs.get('scene', {})
    
    def get_persons_config(self) -> dict:
        """获取人物配置"""
        return self._configs.get('persons', {})
    
    def get_relationships_config(self) -> dict:
        """获取关系配置"""
        return self._configs.get('relationships', {})
    
    def get_prompt_templates(self) -> dict:
        """获取提示词模板"""
        return self._configs.get('prompt_templates', {})
    
    def reload(self, name: str = None):
        """重新加载配置"""
        if name:
            self._configs[name] = self._load_json(f'{name}.json')
        else:
            self._load_all()

# 全局单例
config_manager = ConfigManager()