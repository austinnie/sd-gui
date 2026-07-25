# gui/tabs/txt2img/templates.py
"""提示词模板管理"""

import json
import os
from typing import Dict, List, Optional

from services.prompt_template_service import prompt_service


class TemplateManager:
    """提示词模板管理器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.templates: Dict[str, List[Dict]] = {}
        self.template_icons: Dict[str, str] = {}
        self.template_priority: Dict[str, int] = {}
    
    def load(self):
        """加载模板"""
        self.templates = {}
        self.template_icons = {}
        self.template_priority = {}
        
        prompt_service.reload()
        
        for cat in prompt_service.get_categories():
            templates = prompt_service.get_templates(cat.id)
            self.templates[cat.name] = [
                {"name": t.name, "prompt": t.prompt, "negative": t.negative}
                for t in templates
            ]
            self.template_icons[cat.name] = cat.icon
            self.template_priority[cat.name] = cat.priority
            print(f"📁 {cat.name}: {len(templates)} 个模板")
        
        total = sum(len(t) for t in self.templates.values())
        print(f"✅ 总计加载 {len(self.templates)} 个分类, {total} 个模板")
        
        return self.templates
    
    def get_names(self, category: str) -> List[str]:
        """获取分类下的模板名称"""
        templates = self.templates.get(category, [])
        return [t.get("name", "未命名") for t in templates]
    
    def get_template(self, category: str, name: str) -> Optional[Dict]:
        """获取指定模板"""
        templates = self.templates.get(category, [])
        for t in templates:
            if t.get("name") == name:
                return t
        return None
    
    def get_categories(self) -> List[str]:
        """获取所有分类名称"""
        return list(self.templates.keys())
    
    def get_icon(self, category: str) -> str:
        """获取分类图标"""
        return self.template_icons.get(category, "📁")