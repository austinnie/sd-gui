#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提示词引擎 - 组合生成最终的提示词
"""

from typing import Dict, List, Optional, Tuple
from .config_loader import config


from utils.logger import get_logger, info, warning, error, debug

logger = get_logger(__name__)
class PromptEngine:
    """提示词引擎 - 负责组合和优化提示词"""
    
    def __init__(self):
        self.max_prompt_length = 350
        self.max_negative_length = 500
    
    def combine_prompts(self, parts: List[str], separator: str = ", ") -> str:
        """组合提示词片段"""
        if not parts:
            return ""
        result = separator.join(parts)
        
        if len(result) > self.max_prompt_length:
            result = result[:self.max_prompt_length]
            last_comma = result.rfind(',')
            if last_comma > self.max_prompt_length * 0.8:
                result = result[:last_comma]
        
        return result
    
    def combine_negatives(self, parts: List[str]) -> str:
        """组合负面提示词"""
        if not parts:
            return ""
        
        unique_parts = list(dict.fromkeys(parts))
        result = ", ".join(unique_parts)
        
        if len(result) > self.max_negative_length:
            result = result[:self.max_negative_length]
        
        return result
    
    def add_quality_tags(self, prompt: str, quality: str = "standard") -> str:
        """添加质量标签"""
        quality_tags = {
            "standard": "high quality, detailed",
            "photorealistic": "photorealistic, 8k, ultra HD, highly detailed, sharp focus",
            "artistic": "artistic, masterpiece, beautiful composition",
            "anime": "anime style, vibrant colors, clean lines",
            "cinematic": "cinematic, movie still, film grain, dramatic"
        }
        
        tag = quality_tags.get(quality, quality_tags["standard"])
        return self.combine_prompts([tag, prompt])
    
    def add_composition(self, prompt: str, composition: str = "full_body") -> str:
        """添加构图描述"""
        composition_tags = {
            "full_body": "full body shot, entire body visible",
            "half_body": "half body shot, from waist up",
            "headshot": "headshot, face only, close up on face",
            "close_up": "close up shot, detailed view",
            "wide_shot": "wide shot, establishing shot"
        }
        
        tag = composition_tags.get(composition, composition_tags["full_body"])
        return self.combine_prompts([prompt, tag])
    
    def optimize_prompt(self, prompt: str) -> str:
        """优化提示词（去重、精简）"""
        if not prompt:
            return prompt
        
        parts = [p.strip() for p in prompt.split(',') if p.strip()]
        
        seen = set()
        unique_parts = []
        for p in parts:
            if p not in seen:
                seen.add(p)
                unique_parts.append(p)
        
        result = ", ".join(unique_parts)
        
        if len(result) > self.max_prompt_length:
            result = result[:self.max_prompt_length]
        
        if len(result) < len(prompt):
            logger.info(f"✂️ 提示词已精简: {len(prompt)} -> {len(result)} 字符")
        
        return result
    
    def build_from_template(self, 
                           template_type: str,
                           selections: Dict[str, str],
                           base_quality: Optional[str] = None) -> Tuple[str, str]:
        """
        从模板构建提示词
        """
        prompt_parts = []
        negative_parts = []
        
        if base_quality:
            prompt_parts.append(base_quality)
        else:
            prompt_parts.append("masterpiece, best quality, 8k")
        
        for category, item_key in selections.items():
            if item_key:
                if template_type == "person":
                    cfg_name = "persons"
                elif template_type == "couple":
                    cfg_name = "relationships"
                else:
                    cfg_name = "scenes"
                
                prompt_text = config.get_prompt(cfg_name, category, item_key)
                if prompt_text:
                    prompt_parts.append(prompt_text)
                
                negative_text = config.get_negative(cfg_name, category, item_key)
                if negative_text:
                    negative_parts.append(negative_text)
        
        full_prompt = self.combine_prompts(prompt_parts)
        full_negative = self.combine_negatives(negative_parts)
        
        return full_prompt, full_negative


# 全局提示词引擎实例
prompt_engine = PromptEngine()