# gui/chat/utils/prompt_cleaner.py
"""提示词清理工具"""

import re


class PromptCleaner:
    """提示词清理器"""
    
    QUALITY_WORDS = ['masterpiece', 'best quality', 'photorealistic', '8k', 'highly detailed']
    
    @staticmethod
    def clean_for_sd(prompt: str) -> str:
        """清理 LLM 生成的提示词，使其符合 SD 格式要求"""
        if not prompt:
            return "masterpiece, best quality, photorealistic, 8k, a beautiful image"
        
        # 移除中文和特殊字符
        prompt = re.sub(r'[\u4e00-\u9fff]+', '', prompt)
        prompt = re.sub(r'[（(][^）)]*[）)]', '', prompt)
        prompt = re.sub(r'\*\*', '', prompt)
        prompt = re.sub(r'[，、。！？]', ',', prompt)
        
        # 分割并清理
        parts = [p.strip() for p in prompt.split(',') if p.strip()]
        parts = [p for p in parts if len(p) > 1]
        
        # 去重
        seen = set()
        unique_parts = []
        for p in parts:
            p_lower = p.lower()
            if p_lower not in seen and len(p) > 1:
                seen.add(p_lower)
                unique_parts.append(p)
        
        # 确保质量词在开头
        final_parts = []
        for q in PromptCleaner.QUALITY_WORDS:
            if q not in seen:
                final_parts.append(q)
                seen.add(q)
        
        for p in unique_parts:
            if p.lower() not in PromptCleaner.QUALITY_WORDS:
                final_parts.append(p)
        
        result = ', '.join(final_parts)
        
        # 限制长度
        if len(result) > 380:
            result = result[:350]
            last_comma = result.rfind(',')
            if last_comma > 280:
                result = result[:last_comma]
        
        if len(result) < 20:
            result = "masterpiece, best quality, photorealistic, 8k, " + result
        
        return result
    
    @staticmethod
    def clean(prompt: str) -> str:
        """通用提示词清理"""
        if not prompt:
            return prompt
        
        prompt = prompt.replace('。', ', ').replace('！', ', ').replace('?', ', ')
        prompt = prompt.replace('.', ', ').replace('!', ', ').replace('?', ', ')
        
        parts = [p.strip() for p in prompt.split(',') if p.strip()]
        seen = set()
        unique_parts = []
        for p in parts:
            if len(p) > 50:
                p = p[:50]
            if p.lower() not in seen:
                seen.add(p.lower())
                unique_parts.append(p)
        
        result = ", ".join(unique_parts)
        if len(result) > 200:
            result = result[:200]
            last_comma = result.rfind(',')
            if last_comma > 150:
                result = result[:last_comma]
        
        return result