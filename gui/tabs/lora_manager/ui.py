# gui/tabs/lora_manager/ui.py
"""LoRA 管理 UI 构建"""

import tkinter as tk
from tkinter import ttk, filedialog


class LoraManagerUI:
    """LoRA 管理 UI 构建器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.frame = tab.frame
    
    def build(self):
        """构建 UI"""
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 子标签页1: 批量测试
        self.test_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.test_frame, text="🚀 批量测试")
        self._build_test_tab()
        
        # 子标签页2: 分析管理
        self.analyze_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analyze_frame, text="📊 分析管理")
        self._build_analyze_tab()
    
    def _build_test_tab(self):
        """构建批量测试子标签页"""
        frame = self.test_frame
        row = 0
        
        # 标题
        ttk.Label(frame, text="🚀 LoRA 批量预览测试", font=("", 12, "bold")).grid(
            row=row, column=0, columnspan=4, sticky=tk.W, pady=5, padx=5)
        row += 1
        
        # 模型路径配置
        model_frame = ttk.LabelFrame(frame, text="📦 模型配置", padding=5)
        model_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # SD 1.5 模型
        ttk.Label(model_frame, text="SD 1.5 模型:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.tab.sd15_model_path_var, width=50).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(model_frame, text="浏览", command=lambda: self._browse_file(self.tab.sd15_model_path_var)).grid(
            row=0, column=2, padx=5)
        
        # SDXL 模型
        ttk.Label(model_frame, text="SDXL 模型:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.tab.sdxl_model_path_var, width=50).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(model_frame, text="浏览", command=lambda: self._browse_file(self.tab.sdxl_model_path_var)).grid(
            row=1, column=2, padx=5)
        
        # LoRA 目录
        ttk.Label(model_frame, text="LoRA 目录:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.tab.test_lora_dir_var, width=50).grid(
            row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(model_frame, text="浏览", command=lambda: self._browse_dir(self.tab.test_lora_dir_var)).grid(
            row=2, column=2, padx=5)
        
        # 输出目录
        ttk.Label(model_frame, text="输出目录:").grid(row=3, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.tab.output_previews_dir_var, width=50).grid(
            row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(model_frame, text="浏览", command=lambda: self._browse_dir(self.tab.output_previews_dir_var)).grid(
            row=3, column=2, padx=5)
        
        row += 1
        
        # 基础参数
        param_frame = ttk.LabelFrame(frame, text="⚙️ 基础参数", padding=5)
        param_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1

        # ✅ 新增：模型类型选择
        type_row = ttk.Frame(param_frame)
        type_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(type_row, text="模型类型:").pack(side=tk.LEFT, padx=5)
        
        self.tab.test_model_type_var = tk.StringVar(value="both")
        ttk.Radiobutton(type_row, text="🟢 SD1.5", variable=self.tab.test_model_type_var,
                        value="sd15").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_row, text="🔵 SDXL", variable=self.tab.test_model_type_var,
                        value="sdxl").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_row, text="🟣 全部", variable=self.tab.test_model_type_var,
                        value="both").pack(side=tk.LEFT, padx=5)
                    
        # 参数行1
        param_row1 = ttk.Frame(param_frame)
        param_row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(param_row1, text="SD 1.5 步数:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(param_row1, from_=1, to=50, textvariable=self.tab.test_steps_sd15_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(param_row1, text="SDXL 步数:").pack(side=tk.LEFT, padx=15)
        ttk.Spinbox(param_row1, from_=1, to=50, textvariable=self.tab.test_steps_sdxl_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(param_row1, text="筛选:").pack(side=tk.LEFT, padx=15)
        ttk.Combobox(param_row1, textvariable=self.tab.test_filter_var,
                     values=["all", "small", "medium", "large"], width=8, state="readonly").pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(param_row1, text="强制重跑", variable=self.tab.test_re_run_var).pack(side=tk.LEFT, padx=15)
        
        # 尺寸配置
        size_row = ttk.Frame(param_frame)
        size_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(size_row, text="SD 1.5 尺寸:").pack(side=tk.LEFT, padx=5)
        ttk.Combobox(size_row, textvariable=self.tab.test_size_sd15_var,
                     values=["512x768", "512x1024", "576x1024", "640x960", "640x1024", "768x768", "768x1024"],
                     width=10, state="readonly").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(size_row, text="SDXL 尺寸:").pack(side=tk.LEFT, padx=15)
        ttk.Combobox(size_row, textvariable=self.tab.test_size_sdxl_var,
                     values=["1024x1024", "896x1152", "832x1216", "768x1344", "1152x896", "1216x832"],
                     width=10, state="readonly").pack(side=tk.LEFT, padx=5)
        
        # 提示词
        param_row2 = ttk.Frame(param_frame)
        param_row2.pack(fill=tk.X, pady=2)
        ttk.Label(param_row2, text="SD 1.5 提示词:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(param_row2, textvariable=self.tab.test_prompt_sd15_var, width=45).pack(side=tk.LEFT, padx=5)
        
        param_row3 = ttk.Frame(param_frame)
        param_row3.pack(fill=tk.X, pady=2)
        ttk.Label(param_row3, text="SDXL 提示词:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(param_row3, textvariable=self.tab.test_prompt_sdxl_var, width=45).pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # 操作按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=10)
        row += 1
        
        self.tab.test_btn = ttk.Button(btn_frame, text="🚀 开始测试", command=self.tab._start_batch_test)
        self.tab.test_btn.pack(side=tk.LEFT, padx=5)
        
        self.tab.test_cancel_btn = ttk.Button(btn_frame, text="⏹️ 取消", command=self.tab._cancel_operation, state=tk.DISABLED)
        self.tab.test_cancel_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="📁 打开输出", command=self.tab._open_previews_output).pack(side=tk.LEFT, padx=5)
        
        # 状态和日志
        status_frame = ttk.Frame(frame)
        status_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        self.tab.test_status_var = tk.StringVar(value="就绪")
        self.tab.test_status_label = ttk.Label(status_frame, textvariable=self.tab.test_status_var, foreground="blue")
        self.tab.test_status_label.pack(side=tk.LEFT)
        
        self.tab.test_progress_bar = ttk.Progressbar(status_frame, length=300, mode='determinate')
        self.tab.test_progress_bar.pack(side=tk.RIGHT, padx=5)
        
        log_frame = ttk.LabelFrame(frame, text="📝 测试日志", padding=5)
        log_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        row += 1
        
        self.tab.test_log_text = tk.Text(log_frame, height=10, width=70, wrap=tk.WORD, state=tk.DISABLED)
        self.tab.test_log_text.pack(fill=tk.BOTH, expand=True)
        
        # 设置权重
        frame.rowconfigure(row, weight=1)
        frame.columnconfigure(1, weight=1)
    
    def _build_analyze_tab(self):
        """构建分析管理子标签页"""
        frame = self.analyze_frame
        row = 0
        
        # 标题
        ttk.Label(frame, text="📊 LoRA 分析管理", font=("", 12, "bold")).grid(
            row=row, column=0, columnspan=4, sticky=tk.W, pady=5, padx=5)
        row += 1
        
        # 路径配置
        path_frame = ttk.LabelFrame(frame, text="📁 路径配置", padding=5)
        path_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(path_frame, text="图片目录:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(path_frame, textvariable=self.tab.image_dir_var, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(path_frame, text="浏览", command=lambda: self._browse_dir(self.tab.image_dir_var)).grid(row=0, column=2, padx=5)
        
        ttk.Label(path_frame, text="输出列表:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(path_frame, textvariable=self.tab.output_file_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Label(path_frame, text="Top K:").grid(row=1, column=2, sticky=tk.E, padx=5)
        ttk.Spinbox(path_frame, from_=10, to=100, textvariable=self.tab.top_k_var, width=8).grid(row=1, column=3, padx=5)
        
        ttk.Label(path_frame, text="提取目录:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(path_frame, textvariable=self.tab.extract_dir_var, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        
        row += 1
        
        # 模型目录配置
        model_frame = ttk.LabelFrame(frame, text="📂 模型目录配置", padding=5)
        model_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(model_frame, text="test_lora 目录:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.tab.test_lora_dir_var, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(model_frame, text="浏览", command=lambda: self._browse_dir(self.tab.test_lora_dir_var)).grid(row=0, column=2, padx=5)
        
        ttk.Label(model_frame, text="sd15-lora 目录:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.tab.sd15_lora_dir_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Label(model_frame, text="sdxl-lora 目录:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(model_frame, textvariable=self.tab.sdxl_lora_dir_var, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        
        row += 1
        
        # 操作按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=10)
        row += 1
        
        ttk.Button(btn_frame, text="🔍 扫描分析", command=self.tab._start_scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📋 显示排行", command=self.tab._show_ranking).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📂 提取高分", command=self.tab._extract_high_loras).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 过滤删除", command=self.tab._filter_low_loras).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📝 重命名", command=self.tab._rename_loras).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 同步目录", command=self.tab._sync_loras).pack(side=tk.LEFT, padx=5)
        
        self.tab.analyze_cancel_btn = ttk.Button(btn_frame, text="⏹️ 取消", command=self.tab._cancel_operation, state=tk.DISABLED)
        self.tab.analyze_cancel_btn.pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # 状态
        status_frame = ttk.Frame(frame)
        status_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        self.tab.analyze_status_var = tk.StringVar(value="就绪")
        self.tab.analyze_status_label = ttk.Label(status_frame, textvariable=self.tab.analyze_status_var, foreground="blue")
        self.tab.analyze_status_label.pack(side=tk.LEFT)
        
        self.tab.analyze_progress_bar = ttk.Progressbar(status_frame, length=300, mode='determinate')
        self.tab.analyze_progress_bar.pack(side=tk.RIGHT, padx=5)
        
        # LoRA 列表
        list_frame = ttk.LabelFrame(frame, text="📋 LoRA 列表", padding=5)
        list_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        row += 1
        
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.tab.tree = ttk.Treeview(
            list_container,
            columns=("rank", "name", "score", "size_mb", "status"),
            show="headings",
            height=12
        )
        
        self.tab.tree.heading("rank", text="排名")
        self.tab.tree.heading("name", text="LoRA 名称")
        self.tab.tree.heading("score", text="评分")
        self.tab.tree.heading("size_mb", text="大小 (MB)")
        self.tab.tree.heading("status", text="状态")
        
        self.tab.tree.column("rank", width=50, anchor=tk.CENTER)
        self.tab.tree.column("name", width=300, anchor=tk.W)
        self.tab.tree.column("score", width=80, anchor=tk.CENTER)
        self.tab.tree.column("size_mb", width=80, anchor=tk.CENTER)
        self.tab.tree.column("status", width=80, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.tab.tree.yview)
        self.tab.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tab.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右键菜单
        self._create_context_menu()
        
        # 日志
        log_frame = ttk.LabelFrame(frame, text="📝 操作日志", padding=5)
        log_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        self.tab.analyze_log_text = tk.Text(log_frame, height=6, width=70, wrap=tk.WORD, state=tk.DISABLED)
        self.tab.analyze_log_text.pack(fill=tk.BOTH, expand=True)
        
        frame.rowconfigure(row, weight=1)
        frame.columnconfigure(1, weight=1)
    
    def _create_context_menu(self):
        """创建右键菜单"""
        self.tab.context_menu = tk.Menu(self.tab.tree, tearoff=0)
        self.tab.context_menu.add_command(label="📋 复制名称", command=self.tab._copy_selected_name)
        self.tab.context_menu.add_command(label="📂 打开所在目录", command=self.tab._open_selected_dir)
        self.tab.tree.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        item = self.tab.tree.identify_row(event.y)
        if item:
            self.tab.tree.selection_set(item)
            self.tab.context_menu.post(event.x_root, event.y_root)
    
    def _browse_dir(self, var):
        dir_path = filedialog.askdirectory(title="选择目录")
        if dir_path:
            var.set(dir_path)
    
    def _browse_file(self, var):
        file_path = filedialog.askopenfilename(
            title="选择模型文件",
            filetypes=[("模型文件", "*.safetensors *.ckpt"), ("所有文件", "*.*")]
        )
        if file_path:
            var.set(file_path)