# gui/tabs/txt2img/ui.py
"""文生图 UI 构建"""

import tkinter as tk
from tkinter import ttk


class Txt2ImgUI:
    """文生图 UI 构建器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.frame = tab.frame
        self.template_manager = tab.template_manager
    
    def build(self):
        """构建 UI"""
        frame = self.frame
        row = 0
        
        # 模板选择
        self._build_template_selector(frame, row)
        row += 3
        
        # 提示词区域
        self._build_prompt_area(frame, row)
        row += 3
        
        # 参数提示
        self._build_hint(frame, row)
        row += 1
        
        # 按钮
        self._build_buttons(frame, row)
        row += 1
    
    def _build_template_selector(self, frame, row):
        """构建模板选择器"""
        template_frame = ttk.Frame(frame)
        template_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(template_frame, text="📋 提示词模板:").pack(side=tk.LEFT, padx=5)
        
        categories = self.template_manager.get_categories()
        self.tab.category_combo = ttk.Combobox(
            template_frame,
            textvariable=self.tab.template_category_var,
            values=categories,
            width=10,
            state="readonly"
        )
        self.tab.category_combo.pack(side=tk.LEFT, padx=5)
        self.tab.category_combo.bind('<<ComboboxSelected>>', self.tab._update_template_list)
        
        self.tab.template_combo = ttk.Combobox(
            template_frame,
            textvariable=self.tab.template_var,
            values=[],
            width=20,
            state="readonly"
        )
        self.tab.template_combo.pack(side=tk.LEFT, padx=5)
        self.tab.template_combo.bind('<<ComboboxSelected>>', self.tab._apply_template)
        
        ttk.Button(template_frame, text="🔄 刷新模板", command=self.tab._refresh_templates).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            template_frame,
            text="💡 选择模板后自动填充，可在此基础上修改",
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=15)
        
        ttk.Button(template_frame, text="💾 保存模板", command=self.tab._save_custom_template).pack(side=tk.LEFT, padx=5)
    
    def _build_prompt_area(self, frame, row):
        """构建提示词区域"""
        ttk.Separator(frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(frame, text="正面提示词:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.tab.prompt_text = tk.Text(frame, height=5, width=70)
        self.tab.prompt_text.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(frame, text="负面提示词:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.tab.neg_text = tk.Text(frame, height=4, width=70)
        self.tab.neg_text.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
    
    def _build_hint(self, frame, row):
        """构建参数提示"""
        hint_frame = ttk.Frame(frame)
        hint_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2, padx=5)
        ttk.Label(
            hint_frame,
            text="💡 参数（步数、CFG、种子、尺寸等）请在顶部的「共享参数面板」调整 | 尺寸会根据提示词智能优化",
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=5)
    
    def _build_buttons(self, frame, row):
        """构建按钮"""
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        self.tab.generate_btn = ttk.Button(btn_frame, text="🚀 文生图", command=self.tab.start_generate)
        self.tab.generate_btn.pack(side=tk.LEFT, padx=10)
        
        self.tab.batch_templates_btn = ttk.Button(
            btn_frame,
            text="📋 批量运行所有模板",
            command=self.tab._batch_run_all_templates
        )
        self.tab.batch_templates_btn.pack(side=tk.LEFT, padx=5)
        
        self.tab.cancel_btn = ttk.Button(btn_frame, text="⏹️ 取消", command=self.tab.cancel_generation_cmd, state=tk.DISABLED)
        self.tab.cancel_btn.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(btn_frame, text="📁 打开输出文件夹", command=self.app.open_output_folder).pack(side=tk.LEFT, padx=10)