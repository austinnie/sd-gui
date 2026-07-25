#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一配置管理 - 整合所有配置
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


def resolve_path(path: str, base_dir: str = None) -> str:
    """
    将相对路径解析为绝对路径
    
    参数:
        path: 原始路径（可能是相对路径或绝对路径）
        base_dir: 基准目录（默认为项目根目录）
    
    返回:
        解析后的绝对路径
    """
    if base_dir is None:
        # 获取项目根目录（app_config.py 所在目录的父目录）
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 如果已经是绝对路径，直接返回
    if os.path.isabs(path):
        return path
    
    # 否则，相对于项目根目录解析
    resolved = os.path.normpath(os.path.join(base_dir, path))
    return resolved
    
@dataclass
class PathsConfig:
    """路径配置"""
    model_base_paths: list = field(default_factory=lambda: ["./models"])
    lora_base_paths: list = field(default_factory=lambda: ["./loras"])
    output_dir: str = "./output"
    janus_model_path: str = "./models/janus-pro-7b"
    janus_model_1b_path: str = "./models/janus-pro-1b"
    janus_model_7b_path: str = "./models/janus-pro-7b"

    # ✅ 新增：LoRA 类型路径映射
    _resolved_sd15_lora_paths: list = field(default_factory=list, repr=False)
    _resolved_sdxl_lora_paths: list = field(default_factory=list, repr=False)
    
    # 解析后的绝对路径（运行时计算）
    _resolved_model_base_paths: list = field(default_factory=list, repr=False)
    _resolved_lora_base_paths: list = field(default_factory=list, repr=False)
    _resolved_output_dir: str = ""
    _resolved_janus_1b_path: str = ""
    _resolved_janus_7b_path: str = ""
    
    @classmethod
    def from_dict(cls, data: dict, base_dir: str = None) -> 'PathsConfig':
        """从字典创建配置，并解析路径"""
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 解析路径
        model_paths = data.get("model_base_paths", ["./models"])
        resolved_model_paths = [resolve_path(p, base_dir) for p in model_paths]
        
        lora_paths = data.get("lora_base_paths", ["./loras"])
        resolved_lora_paths = [resolve_path(p, base_dir) for p in lora_paths]
        
        resolved_output = resolve_path(data.get("output_dir", "./output"), base_dir)
        resolved_janus_1b = resolve_path(data.get("janus_model_1b_path", "./models/janus-pro-1b"), base_dir)
        resolved_janus_7b = resolve_path(data.get("janus_model_7b_path", "./models/janus-pro-7b"), base_dir)

        # ✅ 解析 SD1.5 和 SDXL 的 LoRA 路径
        sd15_lora_paths = data.get("sd15_lora_paths", [])
        sdxl_lora_paths = data.get("sdxl_lora_paths", [])
        
        # 如果没有单独配置，从 lora_base_paths 中推断
        if not sd15_lora_paths and not sdxl_lora_paths:
            for p in resolved_lora_paths:
                if "sd15" in p.lower() or "sd-1.5" in p.lower():
                    sd15_lora_paths.append(p)
                elif "sdxl" in p.lower():
                    sdxl_lora_paths.append(p)
                else:
                    # 默认全部当作 SD1.5
                    sd15_lora_paths.append(p)
        
        resolved_sd15 = [resolve_path(p, base_dir) for p in sd15_lora_paths]
        resolved_sdxl = [resolve_path(p, base_dir) for p in sdxl_lora_paths]
        
        # 创建实例，同时保存解析后的路径
        instance = cls(
            model_base_paths=model_paths,
            lora_base_paths=lora_paths,
            output_dir=data.get("output_dir", "./output"),
            janus_model_path=data.get("janus_model_path", "./models/janus-pro-7b"),
            janus_model_1b_path=data.get("janus_model_1b_path", "./models/janus-pro-1b"),
            janus_model_7b_path=data.get("janus_model_7b_path", "./models/janus-pro-7b")
        )
        
        # 存储解析后的绝对路径
        instance._resolved_model_base_paths = resolved_model_paths
        instance._resolved_lora_base_paths = resolved_lora_paths
        instance._resolved_output_dir = resolved_output
        instance._resolved_janus_1b_path = resolved_janus_1b
        instance._resolved_janus_7b_path = resolved_janus_7b
        instance._resolved_sd15_lora_paths = resolved_sd15
        instance._resolved_sdxl_lora_paths = resolved_sdxl        
        
        return instance
    
    def get_resolved_model_paths(self) -> list:
        """获取解析后的模型路径列表"""
        return self._resolved_model_base_paths
    
    def get_resolved_lora_paths(self) -> list:
        """获取解析后的 Lora 路径列表"""
        return self._resolved_lora_base_paths
    
    def get_resolved_output_dir(self) -> str:
        """获取解析后的输出目录"""
        return self._resolved_output_dir
    
    def get_resolved_janus_1b_path(self) -> str:
        """获取解析后的 Janus 1B 模型路径"""
        return self._resolved_janus_1b_path
    
    def get_resolved_janus_7b_path(self) -> str:
        """获取解析后的 Janus 7B 模型路径"""
        return self._resolved_janus_7b_path

    def get_resolved_sd15_lora_paths(self) -> list:
        """获取解析后的 SD1.5 LoRA 路径列表"""
        return self._resolved_sd15_lora_paths
    
    def get_resolved_sdxl_lora_paths(self) -> list:
        """获取解析后的 SDXL LoRA 路径列表"""
        return self._resolved_sdxl_lora_paths
    
    def get_lora_paths_by_type(self, model_type: str) -> list:
        """根据模型类型获取对应的 LoRA 路径列表"""
        if model_type == "sdxl":
            return self._resolved_sdxl_lora_paths
        else:
            return self._resolved_sd15_lora_paths        

@dataclass
class GenerationConfig:
    """生成参数配置"""
    # ✅ 修改 1：把简单的 int/float 改成字典结构，用于读取 min/max/default
    steps: dict = field(default_factory=lambda: {"min": 1, "max": 150, "default": 20})
    cfg: dict = field(default_factory=lambda: {"min": 1.0, "max": 30.0, "default": 7.0})
    
    # 以下参数保持不变（或者你也可以把宽高也加上 min/max）
    # 👇 【新增】尺寸配置字典
    size: dict = field(default_factory=lambda: {
        "min_width": 256, "max_width": 2048,
        "min_height": 256, "max_height": 2048,
        "default_width": 512, "default_height": 768,
         "cpu_safe_max_width": 1024,
        "cpu_safe_max_height": 1024
    })
    
    max_images: int = 4
    positive_prompt: str = ""
    negative_prompt: str = ""
    img2img_prompt: str = ""

    # 👇 【新增】水印去除默认开关
    default_remove_watermark: bool = True  # 默认启用
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GenerationConfig':
        # 读取 steps (兼容旧版纯数字)
        steps_data = data.get("steps", {})
        if isinstance(steps_data, int):
            steps_data = {"min": 1, "max": 150, "default": steps_data}
            
        # 读取 cfg (兼容旧版纯数字)
        cfg_data = data.get("cfg", {})
        if isinstance(cfg_data, (int, float)):
            cfg_data = {"min": 1.0, "max": 30.0, "default": float(cfg_data)}
            
        # 👇 【新增】读取 size
        size_data = data.get("size", {})
        # 判断是否是旧版的纯数字（如果 JSON 里只有 default_width 和 default_height）
        if "default_width" in data and "default_height" in data:
            # 从旧版顶层字段读取
            size_data = {
                "min_width": 256,
                "max_width": 2048,
                "min_height": 256,
                "max_height": 2048,
                "default_width": data.get("default_width", 512),
                "default_height": data.get("default_height", 768),
                "cpu_safe_max_width": data.get("cpu_safe_max_width", 1024),
                "cpu_safe_max_height": data.get("cpu_safe_max_height", 1024)                
            }
        # 或者检查 JSON 里是否还是纯数字
        elif isinstance(size_data, dict) and "min_width" not in size_data:
            # 如果用户还没更新配置，给一个安全的默认回退
            pass 
        
        return cls(
            steps=steps_data,
            cfg=cfg_data,
            size=size_data, # 👈 这里加上 size
            max_images=data.get("max_images", 4),
            positive_prompt=data.get("positive_prompt", ""),
            negative_prompt=data.get("negative_prompt", ""),
            img2img_prompt=data.get("img2img_prompt", ""),
            default_remove_watermark=data.get("default_remove_watermark", True) 
        )


@dataclass
class MemoryConfig:
    """内存优化配置"""
    cleanup_interval: int = 4
    threshold_gb: float = 8.0
    rest_time: float = 0.5
    use_half_precision: bool = False
    enable_cpu_offload: bool = True
    enable_sequential_offload: bool = False
    vae_slicing: bool = True
    vae_tiling: bool = True
    attention_slicing: bool = True
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MemoryConfig':
        return cls(
            cleanup_interval=data.get("cleanup_interval", 4),
            threshold_gb=data.get("threshold_gb", 8.0),
            rest_time=data.get("rest_time", 0.5),
            use_half_precision=data.get("use_half_precision", False),
            enable_cpu_offload=data.get("enable_cpu_offload", True),
            enable_sequential_offload=data.get("enable_sequential_offload", False),
            vae_slicing=data.get("vae_slicing", True),
            vae_tiling=data.get("vae_tiling", True),
            attention_slicing=data.get("attention_slicing", True)
        )


@dataclass
class ModelConfig:
    """模型配置"""
    use_recommended_sort: bool = True
    auto_load_first: bool = True
    min_size_mb: int = 2000
    priority_keywords: list = field(default_factory=lambda: [
        "perfectionAsianILXL", "xlAsianRealisticMix", "t3_sdVer3",
        "realisticmix", "anycharactermix", "anytimeRealistic",
        "asianrealistic", "aiiiiiii01"
    ])
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ModelConfig':
        default_keywords = [
            "perfectionAsianILXL", "xlAsianRealisticMix", "t3_sdVer3",
            "realisticmix", "anycharactermix", "anytimeRealistic",
            "asianrealistic", "aiiiiiii01"
        ]
        return cls(
            use_recommended_sort=data.get("use_recommended_sort", True),
            auto_load_first=data.get("auto_load_first", True),
            min_size_mb=data.get("min_size_mb", 2000),
            priority_keywords=data.get("priority_keywords", default_keywords)
        )

@dataclass
class UIConfig:
    """UI配置"""
    window_width: int = 1000
    window_height: int = 900
    show_memory_monitor: bool = True
    memory_update_interval: int = 5000
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UIConfig':
        return cls(
            window_width=data.get("window_width", 1000),
            window_height=data.get("window_height", 900),
            show_memory_monitor=data.get("show_memory_monitor", True),
            memory_update_interval=data.get("memory_update_interval", 5000)
        )

# ============ 🆕 Janus 配置 ============

@dataclass
class JanusConfig:
    """Janus-Pro 配置 - 纯 CPU 模式"""
    model_1b_path: str = "../models/janus/janus-pro-1b"
    model_7b_path: str = "../models/janus/janus-pro-7b"
    device: str = "cpu"
    temperature: float = 0.8
    max_tokens: int = 2048
    
    # 解析后的绝对路径（运行时计算）
    _resolved_1b_path: str = ""
    _resolved_7b_path: str = ""
    
    @classmethod
    def from_dict(cls, data: dict, base_dir: str = None) -> 'JanusConfig':
        """从字典创建配置，并解析路径"""
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        instance = cls(
            model_1b_path=data.get("model_1b_path", "../models/janus/janus-pro-1b"),
            model_7b_path=data.get("model_7b_path", "../models/janus/janus-pro-7b"),
            device="cpu",  # 强制 CPU
            temperature=data.get("temperature", 0.8),
            max_tokens=data.get("max_tokens", 2048)
        )
        
        # 存储解析后的绝对路径
        instance._resolved_1b_path = resolve_path(instance.model_1b_path, base_dir)
        instance._resolved_7b_path = resolve_path(instance.model_7b_path, base_dir)
        
        return instance
    
    def get_resolved_1b_path(self) -> str:
        """获取解析后的 1B 模型路径"""
        return self._resolved_1b_path
    
    def get_resolved_7b_path(self) -> str:
        """获取解析后的 7B 模型路径"""
        return self._resolved_7b_path


# ============ 主配置 ============
        
@dataclass
class AppConfig:
    """应用总配置"""
    paths: PathsConfig
    generation: GenerationConfig
    memory: MemoryConfig
    ui: UIConfig
    model: ModelConfig
    janus: JanusConfig   # ✅ 新增
    
    _instance: Optional['AppConfig'] = None
    
    @classmethod
    def get_instance(cls, config_path: str = None) -> 'AppConfig':
        """单例模式获取配置"""
        if cls._instance is None:
            cls._instance = cls.load(config_path)
        return cls._instance
    
    @classmethod
    def load(cls, config_path: str = None) -> 'AppConfig':
        """加载配置文件"""
        default_config = cls._get_default_dict()
        
        if config_path is None:
            config_path = cls._find_config()
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config = cls._merge_config(default_config, user_config)
                print(f"✅ 已加载配置: {config_path}")
            except Exception as e:
                print(f"⚠️ 加载配置失败: {e}，使用默认配置")
        
        return cls(
            paths=PathsConfig.from_dict(default_config.get("paths", {})),
            generation=GenerationConfig.from_dict(default_config.get("generation", {})),
            memory=MemoryConfig.from_dict(default_config.get("memory", {})),
            ui=UIConfig.from_dict(default_config.get("ui", {})),
            model=ModelConfig.from_dict(default_config.get("model", {})),
            janus=JanusConfig.from_dict(default_config.get("janus", {}))   # ✅ 新增
        )

    @classmethod
    def reload(cls):
        """重新加载配置文件"""
        print("🔄 尝试重新加载 gui_config.json ...")
        cls._instance = None  # 销毁单例实例
        cls._instance = cls.load()  # 重新加载
        
        # ✅ 【修复】从字典中读取 default，而不是读取不存在的 default_steps
        # 同时，为了防止报错，这里改为读取我们新加的 default 值
        current_steps = cls._instance.generation.steps["default"]
        print(f"✅ 配置已重新加载！当前步数: {current_steps}")
        
    @classmethod
    def _get_default_dict(cls) -> dict:
        return {
            "paths": {
                "model_base_paths": ["./models"],
                "lora_base_paths": ["./loras"],
                "output_dir": "./output",
                "janus_model_path": "./models/janus-pro-7b",
                "janus_model_1b_path": "./models/janus-pro-1b",
                "janus_model_7b_path": "./models/janus-pro-7b"
            },
            "generation": {
                "steps": {"min": 1, "max": 150, "default": 25},
                "cfg": {"min": 1.0, "max": 30.0, "default": 7.5},
                # 👇 【新增】尺寸配置
                "size": {
                    "min_width": 256, "max_width": 2048,
                    "min_height": 256, "max_height": 2048,
                    "default_width": 640, "default_height": 896
                },
                "max_images": 4,
                "default_remove_watermark": False, 
                "negative_prompt": "worst quality, low quality, ugly, deformed, blurry, bad anatomy..."
            },
            "memory": {
                "cleanup_interval": 4,
                "threshold_gb": 8,
                "rest_time": 0.5,
                "use_half_precision": False,
                "enable_cpu_offload": True,
                "enable_sequential_offload": False,
                "vae_slicing": True,
                "vae_tiling": True,
                "attention_slicing": True
            },
            "ui": {
                "window_width": 1000,
                "window_height": 900,
                "show_memory_monitor": True,
                "memory_update_interval": 5000
            },
            "model": {
                "use_recommended_sort": True,
                "auto_load_first": True,
                "min_size_mb": 2000,
                "priority_keywords": [
                    "perfectionAsianILXL", "xlAsianRealisticMix", "t3_sdVer3",
                    "realisticmix", "anycharactermix", "anytimeRealistic",
                    "asianrealistic", "aiiiiiii01"
                ]
            },
            "janus": {
                "model_1b_path": "../models/janus/janus-pro-1b",
                "model_7b_path": "../models/janus/janus-pro-7b",
                "device": "cpu",
                "temperature": 0.8,
                "max_tokens": 2048
            }
        }
    
    @classmethod
    def _find_config(cls) -> str:
        """查找配置文件"""
        possible_paths = [
            "data/configs/gui_config.json",
            "templates/gui_config.json",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/configs/gui_config.json")
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
app_config = AppConfig.get_instance()

# 打印解析后的路径（方便调试）
print("\n📁 解析后的路径:")
print(f"   Janus 1B: {app_config.janus.get_resolved_1b_path()}")
print(f"   Janus 7B: {app_config.janus.get_resolved_7b_path()}")
print(f"   输出目录: {app_config.paths.get_resolved_output_dir()}")
print()