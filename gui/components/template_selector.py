# gui/components/template_selector.py
"""
通用的模板选择器组件 - 可在任何 Tab 中复用
"""

import tkinter as tk
from tkinter import ttk
from services.prompt_template_service import prompt_service


class TemplateSelector(ttk.Frame):
    """模板选择器 - 可嵌入任何 Tab"""
    
    def __init__(self, parent, on_select=None, show_apply_button=True, **kwargs):
        # ✅ 正确初始化 ttk.Frame
        super().__init__(parent, **kwargs)
        self.on_select = on_select
        self.show_apply_button = show_apply_button
        self._init_ui()
    
    def _init_ui(self):
        # 分类下拉
        ttk.Label(self, text="分类:").pack(side=tk.LEFT, padx=5)
        self.category_var = tk.StringVar()
        
        categories = prompt_service.get_category_names()
        self.category_combo = ttk.Combobox(
            self,
            textvariable=self.category_var,
            values=categories,
            width=12,
            state="readonly"
        )
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', self._on_category_changed)
        
        # 模板下拉
        ttk.Label(self, text="模板:").pack(side=tk.LEFT, padx=5)
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(
            self,
            textvariable=self.template_var,
            values=[],
            width=25,
            state="readonly"
        )
        self.template_combo.pack(side=tk.LEFT, padx=5)
        self.template_combo.bind('<<ComboboxSelected>>', self._on_template_selected)
        
        # 应用按钮（可选）
        if self.show_apply_button:
            ttk.Button(self, text="应用", command=self._apply).pack(side=tk.LEFT, padx=5)
        
        # 如果有分类，默认选择第一个
        if categories:
            self.category_combo.set(categories[0])
            self._on_category_changed(None)
    
    def _on_category_changed(self, event):
        category_name = self.category_var.get()
        cat = prompt_service.get_category_by_name(category_name)
        if cat:
            templates = prompt_service.get_templates(cat.id)
            self.template_combo['values'] = [t.name for t in templates]
            if templates:
                self.template_combo.set(templates[0].name)
                # 如果 on_select 存在且 show_apply_button 为 False，自动应用
                if self.on_select and not self.show_apply_button:
                    template = prompt_service.get_template(cat.id, templates[0].name)
                    if template:
                        self.on_select(template)
    
    def _on_template_selected(self, event):
        # 如果 on_select 存在且 show_apply_button 为 False，自动应用
        if self.on_select and not self.show_apply_button:
            template = self.get_selected()
            if template:
                self.on_select(template)
    
    def _apply(self):
        if self.on_select:
            template = self.get_selected()
            if template:
                self.on_select(template)
    
    def get_selected(self):
        """获取当前选中的模板"""
        template_name = self.template_var.get()
        category_name = self.category_var.get()
        cat = prompt_service.get_category_by_name(category_name)
        if cat:
            return prompt_service.get_template(cat.id, template_name)
        return None