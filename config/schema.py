# config/schema.py
"""
配置文件 Schema 验证
"""

from typing import Dict, Any, Optional, List, Union
import logging

logger = logging.getLogger(__name__)


class ConfigValidator:
    """配置验证器"""
    
    # ============================================================
    # GUI 配置 Schema
    # ============================================================
    GUI_CONFIG_SCHEMA = {
        "paths": {
            "model_base_paths": {"type": "list", "required": False},
            "lora_base_paths": {"type": "list", "required": False},
            "output_dir": {"type": "str", "required": False},
        },
        "generation": {
            "steps": {"type": "dict", "required": False},
            "cfg": {"type": "dict", "required": False},
            "size": {"type": "dict", "required": False},
            "max_images": {"type": "int", "required": False, "min": 1, "max": 10},
            "default_remove_watermark": {"type": "bool", "required": False},
        },
        "memory": {
            "cleanup_interval": {"type": "int", "required": False, "min": 1},
            "threshold_gb": {"type": "float", "required": False, "min": 1},
            "use_half_precision": {"type": "bool", "required": False},
            "enable_cpu_offload": {"type": "bool", "required": False},
            "vae_slicing": {"type": "bool", "required": False},
            "vae_tiling": {"type": "bool", "required": False},
            "attention_slicing": {"type": "bool", "required": False},
        },
        "ui": {
            "window_width": {"type": "int", "required": False, "min": 400},
            "window_height": {"type": "int", "required": False, "min": 400},
            "show_memory_monitor": {"type": "bool", "required": False},
        },
        "model": {
            "use_recommended_sort": {"type": "bool", "required": False},
            "auto_load_first": {"type": "bool", "required": False},
            "min_size_mb": {"type": "int", "required": False, "min": 500},
            "priority_keywords": {"type": "list", "required": False},
        },
        "janus": {
            "model_1b_path": {"type": "str", "required": False},
            "model_7b_path": {"type": "str", "required": False},
            "device": {"type": "str", "required": False},
            "temperature": {"type": "float", "required": False, "min": 0.1, "max": 2.0},
            "max_tokens": {"type": "int", "required": False, "min": 64, "max": 8192},
        }
    }
    
    # ============================================================
    # NSFW 配置 Schema
    # ============================================================
    NSFW_CONFIG_SCHEMA = {
        "enabled": {"type": "bool", "required": False},
        "level": {"type": "str", "required": False, "choices": ["safe", "suggestive", "explicit", "extreme"]},
        "auto_detect": {"type": "bool", "required": False},
        "filter_keywords": {"type": "bool", "required": False},
        "use_dedicated_models": {"type": "bool", "required": False},
        "auto_downgrade": {"type": "bool", "required": False},
        "nsfw_keywords": {"type": "list", "required": False},
        "safe_keywords": {"type": "list", "required": False},
    }
    
    # ============================================================
    # Janus 配置 Schema
    # ============================================================
    JANUS_CONFIG_SCHEMA = {
        "janus": {
            "model_1b_path": {"type": "str", "required": False},
            "model_7b_path": {"type": "str", "required": False},
            "device": {"type": "str", "required": False, "choices": ["cpu", "cuda", "mps"]},
            "temperature": {"type": "float", "required": False, "min": 0.1, "max": 2.0},
            "max_tokens": {"type": "int", "required": False, "min": 64, "max": 8192},
        },
        "paths": {
            "output_dir": {"type": "str", "required": False},
        },
        "ui": {
            "window_width": {"type": "int", "required": False, "min": 400},
            "window_height": {"type": "int", "required": False, "min": 400},
        }
    }
    
    # ============================================================
    # 验证方法
    # ============================================================
    
    @classmethod
    def validate(cls, config: Dict[str, Any], schema: Dict[str, Any], name: str = "") -> bool:
        """
        验证配置是否符合 Schema
        
        参数:
            config: 待验证的配置字典
            schema: Schema 定义
            name: 配置名称 (用于日志)
        
        返回:
            是否验证通过
        """
        if not config:
            logger.warning(f"⚠️ {name}: 配置为空")
            return True  # 空配置也允许，会使用默认值
        
        valid = True
        
        for key, rules in schema.items():
            # 检查必需字段
            if rules.get("required", False) and key not in config:
                logger.warning(f"⚠️ {name}: 缺少必需字段 '{key}'")
                valid = False
                continue
            
            if key not in config:
                continue
            
            value = config[key]
            
            # 检查类型
            expected_type = rules.get("type")
            if expected_type:
                if not cls._check_type(value, expected_type):
                    logger.warning(f"⚠️ {name}.{key}: 类型错误 (期望 {expected_type}, 实际 {type(value).__name__})")
                    valid = False
                    continue
            
            # 检查选择范围
            choices = rules.get("choices")
            if choices and value not in choices:
                logger.warning(f"⚠️ {name}.{key}: 值 '{value}' 不在允许范围 {choices}")
                valid = False
            
            # 检查数值范围
            if isinstance(value, (int, float)):
                min_val = rules.get("min")
                max_val = rules.get("max")
                if min_val is not None and value < min_val:
                    logger.warning(f"⚠️ {name}.{key}: 值 {value} 小于最小值 {min_val}")
                    valid = False
                if max_val is not None and value > max_val:
                    logger.warning(f"⚠️ {name}.{key}: 值 {value} 大于最大值 {max_val}")
                    valid = False
            
            # 递归验证嵌套字典
            if isinstance(value, dict) and "type" not in rules:
                if not cls.validate(value, rules, f"{name}.{key}" if name else key):
                    valid = False
        
        return valid
    
    @classmethod
    def _check_type(cls, value: Any, expected_type: str) -> bool:
        """检查值类型"""
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "number": (int, float), 
            "bool": bool,
            "list": list,
            "dict": dict,
        }
        expected = type_map.get(expected_type)
        if expected is None:
            return True
        return isinstance(value, expected)
    
    @classmethod
    def validate_gui_config(cls, config: Dict[str, Any]) -> bool:
        """验证 GUI 配置"""
        return cls.validate(config, cls.GUI_CONFIG_SCHEMA, "gui_config")
    
    @classmethod
    def validate_nsfw_config(cls, config: Dict[str, Any]) -> bool:
        """验证 NSFW 配置"""
        return cls.validate(config, cls.NSFW_CONFIG_SCHEMA, "nsfw_config")
    
    @classmethod
    def validate_janus_config(cls, config: Dict[str, Any]) -> bool:
        """验证 Janus 配置"""
        return cls.validate(config, cls.JANUS_CONFIG_SCHEMA, "janus_config")