# gui/tabs/interrogate/backends/combined.py
"""组合反推后端 - BLIP + CLIP"""

import re
from .base import InterrogateBackend
from .blip import BlipBackend
from .clip import ClipBackend


class CombinedBackend(InterrogateBackend):
    """组合反推模式"""
    
    def interrogate(self, image_path: str, **kwargs) -> str:
        blip_model = kwargs.get('blip_model', 'BLIP-large (详细)')
        clip_model = kwargs.get('clip_model', 'ViT-L-14/openai')
        clip_mode = kwargs.get('clip_mode', 'fast')
        
        if self.tab.cancel_interrogate:
            return "已取消"
        
        # BLIP
        blip_backend = BlipBackend(self.tab)
        blip_result = blip_backend.interrogate(image_path, model_name=blip_model)
        
        if self.tab.cancel_interrogate:
            return "已取消"
        
        # CLIP
        clip_backend = ClipBackend(self.tab)
        clip_result = clip_backend.interrogate(image_path, mode=clip_mode, model=clip_model)
        
        # 过滤 CLIP 结果
        skip_patterns = [
            r'kim\s+\w+', r'jia\s+\w+', r'leslie\s+\w+',
            r'arafed', r'trending', r'cg society',
        ]
        skip_words = ['korean idol', 'korean girl', 'female actress']
        
        useful_tags = []
        for tag in clip_result.split(','):
            tag_clean = tag.strip()
            if not tag_clean:
                continue
            
            tag_lower = tag_clean.lower()
            is_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, tag_lower):
                    is_skip = True
                    break
            if is_skip:
                continue
            if any(skip in tag_lower for skip in skip_words):
                continue
            if len(tag_clean) > 25:
                continue
            useful_tags.append(tag_clean)
        
        useful_tags = useful_tags[:3]
        
        if useful_tags:
            return f"{blip_result}, {', '.join(useful_tags)}"
        return blip_result