# gui/chat/prompt_builder.py
"""提示词构建器 - 处理LLM响应和提示词优化"""

import re
from typing import Dict, List, Optional, Tuple


class PromptBuilder:
    """提示词构建器"""
    
    NEGATIVE_TEMPLATES = {
        "default": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, extra limbs",
        "portrait": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, extra limbs, bad face",
        "landscape": "worst quality, low quality, ugly, deformed, blurry, watermark, text, bad composition",
        "animal": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, extra legs, missing limbs, watermark, text, human"
    }
    
    def __init__(self):
        self.quality_words = ['masterpiece', 'best quality', 'photorealistic', '8k', 'highly detailed']
    
    def parse_llm_response(self, response: str) -> Dict[str, str]:
        """
        解析LLM响应，提取正面和负面提示词
        """
        result = {"prompt": "", "negative": ""}
        
        if not response:
            return result
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if '正面提示词' in line or 'Positive prompt' in line:
                content = self._extract_content(line, lines)
                if content:
                    result["prompt"] = content
            elif '负面提示词' in line or 'Negative prompt' in line:
                content = self._extract_content(line, lines)
                if content:
                    result["negative"] = content
        
        # 如果没有解析到提示词，整段处理
        if not result["prompt"]:
            clean = re.sub(r'(正面|正面提示词|Positive prompt)[：:]\s*', '', response, flags=re.IGNORECASE)
            clean = re.sub(r'(负面|负面提示词|Negative prompt)[：:]\s*', '', clean, flags=re.IGNORECASE)
            clean = clean.strip()
            
            if any(k in clean for k in ['负面', 'Negative']):
                parts = re.split(r'负面|Negative', clean, flags=re.IGNORECASE)
                result["prompt"] = parts[0].strip()
                if len(parts) > 1:
                    result["negative"] = parts[1].strip()
            else:
                result["prompt"] = clean
        
        # 清理并添加质量词
        if result["prompt"]:
            result["prompt"] = self._clean_prompt(result["prompt"])
            result["prompt"] = self._ensure_quality_words(result["prompt"])
        
        if not result["negative"]:
            result["negative"] = self.NEGATIVE_TEMPLATES["default"]
        else:
            result["negative"] = self._clean_prompt(result["negative"])
        
        return result
    
    def build_preserve_parts(self, image_features: Dict, user_text: str = "") -> List[str]:
        """构建保持原图特征的提示词片段"""
        preserve_parts = ["same person", "same face", "same identity"]
        
        face_count = image_features.get("face_count", 0)
        if face_count == 1:
            if user_text and any(k in user_text.lower() for k in ['男', '帅哥', '男孩']):
                preserve_parts.append("1boy")
            else:
                preserve_parts.append("1girl")
        elif face_count >= 2:
            preserve_parts.append("2people")
        
        preserve_parts.append("same pose")
        preserve_parts.append("same body language")
        
        if image_features.get("is_full_body", True):
            preserve_parts.append("full body")
        else:
            preserve_parts.append("half body")
        
        return preserve_parts
    
    def merge_with_features(self, prompt: str, preserve_parts: List[str]) -> str:
        """合并提示词和特征保持词"""
        prompt_lower = prompt.lower()
        
        # 检查是否已有保持词
        has_preserve = "same person" in prompt_lower and "same face" in prompt_lower
        
        if has_preserve:
            # 只添加缺失的部分
            parts_to_add = [p for p in preserve_parts if p.lower() not in prompt_lower]
            if parts_to_add:
                return prompt + ", " + ", ".join(parts_to_add)
            return prompt
        else:
            # 合并所有
            return ", ".join(preserve_parts + [prompt])
    
    def _extract_content(self, line: str, lines: List[str]) -> str:
        """提取冒号后的内容"""
        if '：' in line:
            content = line.split('：', 1)[-1].strip()
        elif ':' in line:
            content = line.split(':', 1)[-1].strip()
        else:
            content = line.replace('正面提示词', '').replace('负面提示词', '').strip()
        
        if not content:
            # 尝试从下一行获取
            idx = lines.index(line) if line in lines else -1
            if idx >= 0 and idx + 1 < len(lines):
                next_line = lines[idx + 1].strip()
                if next_line and not any(k in next_line for k in ['正面', '负面', 'Prompt', 'Negative']):
                    content = next_line
        
        return content
    
    def _clean_prompt(self, prompt: str) -> str:
        """清理提示词：去重、去标点"""
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
    
    def _ensure_quality_words(self, prompt: str) -> str:
        """确保质量词存在"""
        prompt_lower = prompt.lower()
        for q in self.quality_words:
            if q not in prompt_lower:
                prompt = f"{q}, {prompt}"
                break
        return prompt