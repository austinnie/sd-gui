# config/janus_config.py
"""
Janus-Pro 独立配置
不依赖 gui_config.json
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass


def resolve_path(path: str, base_dir: str = None) -> str:
    """解析路径为绝对路径"""
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if os.path.isabs(path):
        return path
    
    resolved = os.path.normpath(os.path.join(base_dir, path))
    return resolved


@dataclass
class JanusPathsConfig:
    """Janus 路径配置"""
    output_dir: str = "./output/janus"
    _resolved_output_dir: str = ""
    
    @classmethod
    def from_dict(cls, data: dict, base_dir: str = None) -> 'JanusPathsConfig':
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        instance = cls(
            output_dir=data.get("output_dir", "./output/janus")
        )
        instance._resolved_output_dir = resolve_path(instance.output_dir, base_dir)
        return instance
    
    def get_resolved_output_dir(self) -> str:
        return self._resolved_output_dir


@dataclass
class JanusModelConfig:
    """Janus 模型配置"""
    model_1b_path: str = "../models/janus/janus-pro-1b"
    model_7b_path: str = "../models/janus/janus-pro-7b"
    device: str = "cpu"
    temperature: float = 0.8
    max_tokens: int = 2048
    
    _resolved_1b_path: str = ""
    _resolved_7b_path: str = ""
    
    @classmethod
    def from_dict(cls, data: dict, base_dir: str = None) -> 'JanusModelConfig':
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        instance = cls(
            model_1b_path=data.get("model_1b_path", "../models/janus/janus-pro-1b"),
            model_7b_path=data.get("model_7b_path", "../models/janus/janus-pro-7b"),
            device=data.get("device", "cpu"),
            temperature=data.get("temperature", 0.8),
            max_tokens=data.get("max_tokens", 2048)
        )
        instance._resolved_1b_path = resolve_path(instance.model_1b_path, base_dir)
        instance._resolved_7b_path = resolve_path(instance.model_7b_path, base_dir)
        return instance
    
    def get_resolved_1b_path(self) -> str:
        return self._resolved_1b_path
    
    def get_resolved_7b_path(self) -> str:
        return self._resolved_7b_path


@dataclass
class JanusUIConfig:
    """Janus UI 配置"""
    window_width: int = 850
    window_height: int = 750
    
    @classmethod
    def from_dict(cls, data: dict) -> 'JanusUIConfig':
        return cls(
            window_width=data.get("window_width", 850),
            window_height=data.get("window_height", 750)
        )


@dataclass
class JanusAppConfig:
    """Janus 应用总配置"""
    janus: JanusModelConfig
    paths: JanusPathsConfig
    ui: JanusUIConfig
    
    _instance = None
    
    @classmethod
    def get_instance(cls, config_path: str = None) -> 'JanusAppConfig':
        if cls._instance is None:
            cls._instance = cls.load(config_path)
        return cls._instance
    
    @classmethod
    def load(cls, config_path: str = None) -> 'JanusAppConfig':
        default_config = cls._get_default_dict()
        
        if config_path is None:
            config_path = cls._find_config()
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config = cls._merge_config(default_config, user_config)
                print(f"✅ 已加载 Janus 配置: {config_path}")
            except Exception as e:
                print(f"⚠️ 加载配置失败: {e}，使用默认配置")
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        return cls(
            janus=JanusModelConfig.from_dict(default_config.get("janus", {}), base_dir),
            paths=JanusPathsConfig.from_dict(default_config.get("paths", {}), base_dir),
            ui=JanusUIConfig.from_dict(default_config.get("ui", {}))
        )
    
    @classmethod
    def reload(cls, config_path: str = None):
        """重新加载配置"""
        cls._instance = None
        return cls.load(config_path)
    
    @classmethod
    def _get_default_dict(cls) -> dict:
        return {
            "janus": {
                "model_1b_path": "../models/janus/janus-pro-1b",
                "model_7b_path": "../models/janus/janus-pro-7b",
                "device": "cpu",
                "temperature": 0.8,
                "max_tokens": 2048
            },
            "paths": {
                "output_dir": "./output/janus"
            },
            "ui": {
                "window_width": 850,
                "window_height": 750
            }
        }
    
    @classmethod
    def _find_config(cls) -> str:
        """查找配置文件"""
        possible_paths = [
            "data/configs/janus_config.json",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/configs/janus_config.json")
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    @classmethod
    def _merge_config(cls, default: dict, user: dict) -> dict:
        """递归合并配置"""
        for key in default:
            if key not in user:
                user[key] = default[key]
            elif isinstance(default[key], dict) and isinstance(user[key], dict):
                user[key] = cls._merge_config(default[key], user[key])
        return user


# 全局配置实例
janus_config = JanusAppConfig.get_instance()

print("\n📁 Janus 配置路径:")
print(f"   Janus 1B: {janus_config.janus.get_resolved_1b_path()}")
print(f"   Janus 7B: {janus_config.janus.get_resolved_7b_path()}")
print(f"   输出目录: {janus_config.paths.get_resolved_output_dir()}")
print()