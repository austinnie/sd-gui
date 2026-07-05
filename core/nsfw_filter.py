# core/nsfw_filter.py
"""
NSFW 内容过滤器
"""

import re
from typing import Tuple, List, Optional
from config.nsfw_config import NSFWConfig, ContentLevel, nsfw_config


class NSFWFilter:
    """NSFW 内容过滤器"""
    
    def __init__(self, config: NSFWConfig = None):
        self.config = config or nsfw_config
        self._compiled_nsfw_patterns = None
        self._compiled_safe_patterns = None
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式"""
        if self.config.nsfw_keywords:
            pattern = r'\b(' + '|'.join(
                re.escape(k) for k in self.config.nsfw_keywords
            ) + r')\b'
            self._compiled_nsfw_patterns = re.compile(pattern, re.IGNORECASE)
        
        if self.config.safe_keywords:
            pattern = r'\b(' + '|'.join(
                re.escape(k) for k in self.config.safe_keywords
            ) + r')\b'
            self._compiled_safe_patterns = re.compile(pattern, re.IGNORECASE)
    
    def detect_nsfw(self, text: str) -> Tuple[bool, List[str]]:
        """
        检测文本中的 NSFW 内容
        
        返回:
            (是否包含 NSFW, 匹配的关键词列表)
        """
        if not self.config.enabled or not self.config.auto_detect:
            return False, []
        
        if not text or not self._compiled_nsfw_patterns:
            return False, []
        
        matches = self._compiled_nsfw_patterns.findall(text)
        return len(matches) > 0, list(set(matches))
    
    def filter_prompt(self, prompt: str, negative: str = "") -> Tuple[str, str]:
        """
        根据当前配置过滤提示词
        
        返回:
            (过滤后的 prompt, 过滤后的 negative)
        """
        if not self.config.enabled:
            return prompt, negative
        
        level = self.config.level
        
        if level == ContentLevel.SAFE:
            # 安全模式：移除 NSFW 关键词，添加强制安全词
            prompt = self._remove_nsfw_keywords(prompt)
            negative = self._remove_nsfw_keywords(negative)
            
            # 添加强制安全词
            if self.config.safe_keywords:
                safe_tags = ', '.join(self.config.safe_keywords[:3])
                prompt = f"{prompt}, {safe_tags}"
        
        elif level == ContentLevel.SUGGESTIVE:
            # 暗示模式：移除极端 NSFW 词，保留性感词
            prompt = self._remove_extreme_keywords(prompt)
            negative = self._remove_extreme_keywords(negative)
        
        # EXPLICIT 和 EXTREME 模式：不过滤
        
        return prompt, negative
    
    def _remove_nsfw_keywords(self, text: str) -> str:
        """移除 NSFW 关键词"""
        if not text or not self._compiled_nsfw_patterns:
            return text
        
        result = self._compiled_nsfw_patterns.sub('', text)
        # 清理多余的逗号
        result = re.sub(r',\s*,', ',', result)
        result = re.sub(r'^,\s*', '', result)
        result = re.sub(r',\s*$', '', result)
        return result
    
    def _remove_extreme_keywords(self, text: str) -> str:
        """移除极端 NSFW 关键词"""
        extreme_keywords = [
            'fuck', 'fucking', 'penetration', 'explicit',
            '极端', '露骨', '插入', '性交', '射精'
        ]
        
        for kw in extreme_keywords:
            text = re.sub(rf'\b{kw}\b', '', text, flags=re.IGNORECASE)
        
        # 清理多余的逗号
        text = re.sub(r',\s*,', ',', text)
        text = re.sub(r'^,\s*', '', text)
        text = re.sub(r',\s*$', '', text)
        return text
    
    def get_level_description(self) -> str:
        """获取当前等级的详细描述"""
        descriptions = {
            ContentLevel.SAFE: "🔒 安全模式 - 移除所有 NSFW 内容，适合公开演示",
            ContentLevel.SUGGESTIVE: "💋 暗示模式 - 保留性感内容，移除极端露骨内容",
            ContentLevel.EXPLICIT: "🔞 露骨模式 - 允许明确的成人内容",
            ContentLevel.EXTREME: "⚠️ 极端模式 - 所有内容不受限制"
        }
        return descriptions.get(self.config.level, "未知模式")
    
    def get_model_path(self) -> str:
        """
        根据当前等级获取推荐的模型路径
        """
        if not self.config.use_dedicated_models:
            return self.config.safe_model_path
        
        if self.config.level in [ContentLevel.SAFE, ContentLevel.SUGGESTIVE]:
            return self.config.safe_model_path
        else:
            return self.config.explicit_model_path


# 全局过滤器实例
nsfw_filter = NSFWFilter()