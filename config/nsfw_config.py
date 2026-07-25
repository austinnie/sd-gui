# config/nsfw_config.py
"""
NSFW 内容控制配置
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
import json
import os


from utils.logger import get_logger, info, warning, error, debug

logger = get_logger(__name__)
class ContentLevel(Enum):
    """内容等级"""
    SAFE = "safe"              # 安全 - 纯艺术/时尚
    SUGGESTIVE = "suggestive"  # 暗示性 - 性感但不露骨
    EXPLICIT = "explicit"      # 露骨 - 明确成人内容
    EXTREME = "extreme"        # 极端 - 所有内容


@dataclass
class NSFWConfig:
    """NSFW 配置"""
    # 主开关
    enabled: bool = True
    
    # 当前内容等级
    level: ContentLevel = ContentLevel.SAFE
    
    # 自动检测（如果检测到 NSFW 内容，自动调整等级）
    auto_detect: bool = False
    
    # 关键词过滤
    filter_keywords: bool = True
    
    # 模型切换（不同等级使用不同模型）
    use_dedicated_models: bool = False
    
    # 安全模型路径（等级 SAFE/SUGGESTIVE 使用）
    safe_model_path: str = "../models/sd-v1-5/aiiiiii01_v10.safetensors"
    
    # 成人模型路径（等级 EXPLICIT/EXTREME 使用）
    explicit_model_path: str = "../models/sd-v1-5/pony_diffusion_v6.safetensors"
    
    # 自动降级（如果生成被拦截，自动降级到安全模式）
    auto_downgrade: bool = True
    
    # NSFW 关键词列表（自动加载）
    nsfw_keywords: List[str] = field(default_factory=list)
    
    # 安全关键词列表（用于安全模式）
    safe_keywords: List[str] = field(default_factory=list)
    
    @classmethod
    def load(cls, config_path: str = "data/configs/nsfw_config.json") -> 'NSFWConfig':
        """加载配置"""
        default = cls()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 映射等级
                level_map = {
                    "safe": ContentLevel.SAFE,
                    "suggestive": ContentLevel.SUGGESTIVE,
                    "explicit": ContentLevel.EXPLICIT,
                    "extreme": ContentLevel.EXTREME
                }
                
                level_str = data.get("level", "safe")
                default.level = level_map.get(level_str, ContentLevel.SAFE)
                default.enabled = data.get("enabled", True)
                default.auto_detect = data.get("auto_detect", False)
                default.filter_keywords = data.get("filter_keywords", True)
                default.use_dedicated_models = data.get("use_dedicated_models", False)
                default.safe_model_path = data.get("safe_model_path", default.safe_model_path)
                default.explicit_model_path = data.get("explicit_model_path", default.explicit_model_path)
                default.auto_downgrade = data.get("auto_downgrade", True)
                default.nsfw_keywords = data.get("nsfw_keywords", default._get_default_nsfw_keywords())
                default.safe_keywords = data.get("safe_keywords", default._get_default_safe_keywords())
                
                logger.info(f"✅ NSFW 配置已加载: 等级={default.level.value}")
            except Exception as e:
                logger.info(f"⚠️ NSFW 配置加载失败: {e}，使用默认配置")
        else:
            # 创建默认配置
            default._save_default_config(config_path)
        
        return default
    
    def _get_default_nsfw_keywords(self) -> List[str]:
        """默认 NSFW 关键词"""
        return [
            # 英文
            'nude', 'naked', 'sex', 'sexual', 'penetration',
            'oral', 'orgasm', 'erotic', 'porn', 'explicit',
            'fuck', 'fucking', 'cock', 'pussy', 'dick',
            'vagina', 'penis', 'breast', 'nipple',
            'intercourse', 'masturbation', 'fetish',
            'bdsm', 'bondage', 'dominance', 'submission',
            # 中文
            '裸体', '性交', '插入', '口交', '做爱', '色情',
            '阴茎', '阴道', '乳房', '乳头', '性爱',
            '高潮', '射精', '自慰', '肛交', '性行为',
            '束缚', '支配', '顺从', '鞭打',
        ]
    
    def _get_default_safe_keywords(self) -> List[str]:
        """默认安全关键词（用于强制安全模式）"""
        return [
            'modest', 'elegant', 'graceful', 'refined',
            'tasteful', 'appropriate', 'dressed',
            '端庄', '优雅', '得体', '着装整齐'
        ]
    
    def _save_default_config(self, config_path: str):
        """保存默认配置"""
        data = {
            "enabled": True,
            "level": "safe",
            "auto_detect": False,
            "filter_keywords": True,
            "use_dedicated_models": False,
            "safe_model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "explicit_model_path": "../models/sd-v1-5/pony_diffusion_v6.safetensors",
            "auto_downgrade": True,
            "nsfw_keywords": self._get_default_nsfw_keywords(),
            "safe_keywords": self._get_default_safe_keywords()
        }
        
        os.makedirs(os.path.dirname(config_path) or '.', exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"📄 已创建默认 NSFW 配置: {config_path}")
    
    def save(self, config_path: str = "data/configs/nsfw_config.json"):
        """保存配置"""
        data = {
            "enabled": self.enabled,
            "level": self.level.value,
            "auto_detect": self.auto_detect,
            "filter_keywords": self.filter_keywords,
            "use_dedicated_models": self.use_dedicated_models,
            "safe_model_path": self.safe_model_path,
            "explicit_model_path": self.explicit_model_path,
            "auto_downgrade": self.auto_downgrade,
            "nsfw_keywords": self.nsfw_keywords,
            "safe_keywords": self.safe_keywords
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 全局 NSFW 配置实例
nsfw_config = NSFWConfig.load()