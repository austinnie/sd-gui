# gui/tabs/interrogate/backends/tag.py
"""TAG 反推后端 - 使用图像分类模型"""

import os
import time
from PIL import Image
from .base import InterrogateBackend

# 全局缓存
_classifiers = {}


def get_classifier(model_name):
    """获取图像分类器（单例）"""
    global _classifiers
    
    if model_name not in _classifiers:
        from transformers import pipeline
        model_paths = {
            "ViT-Base (快速)": "google/vit-base-patch16-224",
            "ViT-Large (准确)": "google/vit-large-patch16-224",
            "CLIP-B-32 (推荐)": "laion/CLIP-ViT-B-32-laion2B-s34B-b79K",
        }
        actual_model = model_paths.get(model_name, "google/vit-base-patch16-224")
        _classifiers[model_name] = pipeline(
            "image-classification",
            model=actual_model,
            device=-1,
            use_fast=True
        )
    return _classifiers[model_name]


class TagBackend(InterrogateBackend):
    """TAG 快速标签模式"""
    
    def interrogate(self, image_path: str, **kwargs) -> str:
        model_name = kwargs.get('model_name', 'ViT-Large (准确)')
        threshold = kwargs.get('threshold', 0.02)
        
        if self.tab.cancel_interrogate:
            return "已取消"
        
        image = Image.open(image_path).convert('RGB')
        if max(image.size) > 448:
            image.thumbnail((448, 448))
        
        classifier = get_classifier(model_name)
        results = classifier(image)
        
        if self.tab.cancel_interrogate:
            return "已取消"
        
        tags = []
        for r in results:
            if r['score'] > threshold:
                label = r['label'].replace('_', ' ')
                if not label.isdigit():
                    tags.append(label)
        
        tags = tags[:20]
        if not tags:
            tags = ["photo", "high quality"]
        if len(tags) < 3:
            tags.extend(["photo", "high quality"])
        
        return ", ".join(tags)