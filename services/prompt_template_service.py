# services/prompt_template_service.py
"""
提示词模板服务 - 所有 Tab 共享
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Template:
    """模板数据类"""
    name: str
    prompt: str
    negative: str = ""
    category: str = ""
    category_id: str = ""
    icon: str = "📁"


@dataclass
class Category:
    """分类数据类"""
    id: str
    name: str
    icon: str
    priority: int
    file: str


class PromptTemplateService:
    """提示词模板服务 - 单例"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if PromptTemplateService._initialized:
            return
        PromptTemplateService._initialized = True
        
        self._categories: List[Category] = []
        self._templates: Dict[str, List[Template]] = {}
        self._loaded = False
        self._base_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates", "prompts"
        )
    
    def load(self):
        """加载所有模板"""
        if self._loaded:
            return
        
        # 1. 加载分类
        categories_path = os.path.join(self._base_dir, "categories.json")
        if os.path.exists(categories_path):
            with open(categories_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for cat_data in data.get("categories", []):
                    self._categories.append(Category(
                        id=cat_data["id"],
                        name=cat_data["name"],
                        icon=cat_data.get("icon", "📁"),
                        priority=cat_data.get("priority", 99),
                        file=cat_data.get("file", "")
                    ))
        
        # 2. 加载每个分类的模板
        for cat in self._categories:
            file_path = os.path.join(self._base_dir, cat.file)
            templates = []
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for t in data.get("templates", []):
                        templates.append(Template(
                            name=t.get("name", ""),
                            prompt=t.get("prompt", ""),
                            negative=t.get("negative", ""),
                            category=cat.name,
                            category_id=cat.id,
                            icon=cat.icon
                        ))
            self._templates[cat.id] = templates
        
        self._loaded = True
    
    def reload(self):
        """重新加载"""
        self._loaded = False
        self._categories = []
        self._templates = {}
        self.load()
    
    # ==================== 查询接口 ====================
    
    def get_categories(self) -> List[Category]:
        """获取所有分类"""
        self.load()
        return self._categories
    
    def get_category_names(self) -> List[str]:
        """获取所有分类名称"""
        self.load()
        return [c.name for c in self._categories]
    
    def get_category_ids(self) -> List[str]:
        """获取所有分类 ID"""
        self.load()
        return [c.id for c in self._categories]
    
    def get_category_by_id(self, category_id: str) -> Optional[Category]:
        """根据 ID 获取分类"""
        self.load()
        for c in self._categories:
            if c.id == category_id:
                return c
        return None
    
    def get_category_by_name(self, name: str) -> Optional[Category]:
        """根据名称获取分类"""
        self.load()
        for c in self._categories:
            if c.name == name:
                return c
        return None
    
    def get_templates(self, category_id: str) -> List[Template]:
        """获取某分类的所有模板"""
        self.load()
        return self._templates.get(category_id, [])
    
    def get_templates_by_name(self, category_name: str) -> List[Template]:
        """根据分类名称获取模板"""
        self.load()
        for c in self._categories:
            if c.name == category_name:
                return self._templates.get(c.id, [])
        return []
    
    def get_template_names(self, category_id: str) -> List[str]:
        """获取某分类的模板名称列表"""
        templates = self.get_templates(category_id)
        return [t.name for t in templates]
    
    def get_template(self, category_id: str, template_name: str) -> Optional[Template]:
        """获取指定的模板"""
        templates = self.get_templates(category_id)
        for t in templates:
            if t.name == template_name:
                return t
        return None
    
    def get_all_templates(self) -> Dict[str, List[Template]]:
        """获取所有模板"""
        self.load()
        return self._templates
    
    def get_all_templates_flat(self) -> List[Template]:
        """获取所有模板（平铺列表）"""
        self.load()
        result = []
        for templates in self._templates.values():
            result.extend(templates)
        return result
    
    # ==================== 搜索接口 ====================
    
    def search(self, keyword: str) -> List[Template]:
        """搜索模板（名称或提示词包含关键词）"""
        self.load()
        keyword_lower = keyword.lower()
        results = []
        for templates in self._templates.values():
            for t in templates:
                if keyword_lower in t.name.lower() or keyword_lower in t.prompt.lower():
                    results.append(t)
        return results
    
    def search_by_category(self, category_id: str, keyword: str) -> List[Template]:
        """在指定分类中搜索"""
        templates = self.get_templates(category_id)
        keyword_lower = keyword.lower()
        return [
            t for t in templates
            if keyword_lower in t.name.lower() or keyword_lower in t.prompt.lower()
        ]
    
    # ==================== 统计接口 ====================
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        self.load()
        total = sum(len(t) for t in self._templates.values())
        return {
            "total_categories": len(self._categories),
            "total_templates": total,
            "categories": [
                {"id": c.id, "name": c.name, "count": len(self._templates.get(c.id, []))}
                for c in self._categories
            ]
        }
    
    # ==================== 转换接口（兼容旧格式） ====================
    
    def to_old_format(self) -> Dict[str, List[Dict]]:
        """转换为旧格式（兼容）"""
        self.load()
        result = {}
        for cat in self._categories:
            templates = self._templates.get(cat.id, [])
            result[cat.name] = [
                {"name": t.name, "prompt": t.prompt, "negative": t.negative}
                for t in templates
            ]
        return result


# 全局实例
prompt_service = PromptTemplateService()