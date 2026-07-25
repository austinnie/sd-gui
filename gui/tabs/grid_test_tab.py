# gui/tabs/grid_test_tab.py
"""
网格测试标签页 - 批量参数测试
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
from datetime import datetime

from .base_tab import BaseTab
from core.grid_runner import GridRunner


class GridTestTab(BaseTab):
    """网格测试标签页"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.runner = GridRunner(app)
        self._init_vars()
        self.setup_ui()
    
    def _init_vars(self):
        self.config_path_var = tk.StringVar(value="")
        self.config_dropdown_var = tk.StringVar(value="")  # ✅ 新增：下拉框变量
        self.status_var = tk.StringVar(value="就绪")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_text_var = tk.StringVar(value="等待开始...")
        self.is_running = False
        self.model_type_var = tk.StringVar(value="sd")
        self.model_choice_var = tk.StringVar(value="")
        
    def setup_ui(self):
        frame = self.frame
        row = 0
        
        # ===== 标题 =====
        title = ttk.Label(frame, text="🧪 网格参数测试", font=("", 14, "bold"))
        title.grid(row=row, column=0, columnspan=4, pady=10, sticky=tk.W)
        row += 1
        
        # ===== 模型类型选择 =====
        type_frame = ttk.Frame(frame)
        type_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(type_frame, text="模型类型:").pack(side=tk.LEFT, padx=5)
        
        self.model_type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.model_type_var,
            values=["sd", "janus"],
            width=10,
            state="readonly"
        )
        self.model_type_combo.pack(side=tk.LEFT, padx=5)
        self.model_type_combo.set("sd")
        self.model_type_combo.bind('<<ComboboxSelected>>', self._on_model_type_changed)
        
        # ✅ 当前模型状态提示
        self.model_status_label = ttk.Label(
            type_frame,
            text="",
            foreground="blue",
            font=("", 8)
        )
        self.model_status_label.pack(side=tk.LEFT, padx=15)
        
        ttk.Label(
            type_frame,
            text="💡 切换类型会自动切换模型",
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # ===== 模型选择 =====
        model_frame = ttk.Frame(frame)
        model_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(model_frame, text="选择模型:").pack(side=tk.LEFT, padx=5)
        
        self.model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_choice_var,
            width=45
        )
        self.model_combo.pack(side=tk.LEFT, padx=5)
        
        self._refresh_model_list()
        
        ttk.Button(model_frame, text="🔄 刷新", command=self._refresh_model_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(model_frame, text="使用当前", command=self._use_current_model).pack(side=tk.LEFT, padx=5)
        
        # ✅ 新增：自动切换模型按钮
        self.switch_model_btn = ttk.Button(
            model_frame,
            text="🔄 切换模型",
            command=self._switch_to_selected_model
        )
        self.switch_model_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            model_frame,
            text="💡 点击切换模型，会自动卸载另一个",
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=15)
        row += 1
        
        # ===== 配置文件选择 =====
        config_frame = ttk.Frame(frame)
        config_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)

        ttk.Label(config_frame, text="配置文件:").pack(side=tk.LEFT, padx=5)

        # ✅ 改为下拉框 + 输入框组合
        self.config_combo = ttk.Combobox(
            config_frame, 
            textvariable=self.config_path_var, 
            width=40,
            state="normal"  # 允许手动输入
        )
        self.config_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # ✅ 绑定选择事件
        self.config_combo.bind('<<ComboboxSelected>>', self._on_config_selected)

        # ✅ 刷新下拉列表（确保这行存在）
        self._refresh_config_dropdown()

        ttk.Button(config_frame, text="浏览", command=self._select_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_frame, text="📁 打开配置目录", command=self._open_config_dir).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # ===== 配置文件预览 =====
        self.preview_text = tk.Text(frame, height=10, width=70, state=tk.DISABLED)
        self.preview_text.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # ===== 控制按钮 =====
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=10)
        
        self.run_btn = ttk.Button(btn_frame, text="🚀 运行测试", command=self._start_run)
        self.run_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹️ 停止", command=self._stop_run, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_btn = ttk.Button(btn_frame, text="📁 打开输出", command=self._open_output)
        self.open_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="📝 创建配置模板", command=self._create_template).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # ===== 进度条 =====
        ttk.Label(frame, text="进度:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.grid(row=row, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # ===== 状态信息 =====
        self.status_label = ttk.Label(frame, textvariable=self.progress_text_var, foreground="blue")
        self.status_label.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5, padx=5)
        row += 1
        
        # ===== 日志输出 =====
        ttk.Label(frame, text="运行日志:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        row += 1
        self.log_text = tk.Text(frame, height=8, width=70, state=tk.DISABLED)
        self.log_text.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # ===== 底部提示 =====
        ttk.Label(
            frame, 
            text="💡 提示: 在 grid_configs/ 目录下选择配置文件，一键批量生成", 
            foreground="gray"
        ).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5, padx=5)
        
        # 初始化状态显示
        self._update_model_status()
        
        # ===== 配置生成器 =====
        generator_frame = ttk.LabelFrame(self.frame, text="🔧 配置生成器", padding=5)
        generator_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # 模型选择
        gen_row1 = ttk.Frame(generator_frame)
        gen_row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(gen_row1, text="模型类型:").pack(side=tk.LEFT, padx=5)
        self.gen_model_types = tk.StringVar(value="all")
        ttk.Combobox(gen_row1, textvariable=self.gen_model_types,
                     values=["all", "sd15", "sdxl", "lightning", "janus"],
                     width=10, state="readonly").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(gen_row1, text="配置类型:").pack(side=tk.LEFT, padx=15)
        self.gen_config_type = tk.StringVar(value="full")
        ttk.Combobox(gen_row1, textvariable=self.gen_config_type,
                     values=["full", "quick", "multi_prompt", "combined"],
                     width=12, state="readonly").pack(side=tk.LEFT, padx=5)
        
        # 生成按钮
        gen_row2 = ttk.Frame(generator_frame)
        gen_row2.pack(fill=tk.X, pady=2)
        
        ttk.Button(gen_row2, text="📝 生成配置", 
                   command=self._generate_grid_configs).pack(side=tk.LEFT, padx=5)
        ttk.Button(gen_row2, text="📁 打开配置目录", 
                   command=self._open_config_dir).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(gen_row2, text="💡 生成后可在上方选择配置文件运行测试", 
                  foreground="gray", font=("", 8)).pack(side=tk.LEFT, padx=15)
        
        row += 1
        
    
    def _update_model_status(self):
        """更新模型状态显示"""
        if self.app.model_manager.is_sd_loaded:
            self.model_status_label.config(
                text="🟢 SD 模型已加载",
                foreground="green"
            )
        elif self.app.model_manager.is_janus_loaded:
            self.model_status_label.config(
                text="🟢 Janus 模型已加载",
                foreground="green"
            )
        elif self.app.model_manager.is_loading:
            self.model_status_label.config(
                text="🟡 加载中...",
                foreground="orange"
            )
        else:
            self.model_status_label.config(
                text="🔴 未加载模型",
                foreground="red"
            )
    
    def _refresh_model_list(self):
        """刷新模型列表"""
        model_type = self.model_type_var.get()
        models = []
        
        if model_type == "janus":
            models = ["Janus-Pro-1B", "Janus-Pro-7B"]
            if not self.model_choice_var.get() or self.model_choice_var.get() not in models:
                self.model_choice_var.set("Janus-Pro-1B")
        else:
            if hasattr(self.app, 'checkpoints') and self.app.checkpoints:
                models = self.app.checkpoints
            if models and not self.model_choice_var.get():
                self.model_choice_var.set(models[0])
        
        self.model_combo['values'] = models
    
    def _on_model_type_changed(self, event):
        """模型类型切换时更新模型列表"""
        self._refresh_model_list()
        self._update_model_status()
    
    def _use_current_model(self):
        """使用主界面当前加载的模型"""
        if self.app.model_manager.is_sd_loaded:
            model_name = self.app.model_manager.get_sd_model_name()
            if model_name:
                # 从完整名称中提取纯模型名
                for display_name in self.app.checkpoints:
                    if model_name in display_name or display_name.startswith(model_name):
                        self.model_choice_var.set(display_name)
                        self.update_status(f"✅ 使用当前 SD 模型: {model_name}")
                        return
                self.model_choice_var.set(model_name)
                self.update_status(f"✅ 使用当前 SD 模型: {model_name}")
        elif self.app.model_manager.is_janus_loaded:
            self.model_type_var.set("janus")
            self._refresh_model_list()
            self.model_choice_var.set("Janus-Pro-1B")
            self.update_status("✅ 使用当前 Janus 模型")
        else:
            messagebox.showwarning("提示", "请先在主界面加载模型")
    
    def _switch_to_selected_model(self):
        """切换到选择的模型"""
        if self.app.model_manager.is_loading:
            messagebox.showwarning("提示", "正在加载中，请等待")
            return
        
        model_type = self.model_type_var.get()
        model_choice = self.model_choice_var.get()
        
        if not model_choice:
            messagebox.showwarning("提示", "请选择模型")
            return
        
        if model_type == "janus":
            # 切换到 Janus
            model_key = "1B" if "1B" in model_choice else "7B"
            if self.app.model_manager.is_janus_loaded:
                messagebox.showinfo("提示", "Janus 已加载")
                return
            
            if self.app.model_manager.is_sd_loaded:
                if not messagebox.askyesno("切换模型", "加载 Janus 将自动卸载 SD 模型，继续吗？"):
                    return
            
            self.update_status(f"🔄 切换到 Janus-{model_key}...")
            self.switch_model_btn.config(state=tk.DISABLED)
            
            def load_thread():
                def progress_cb(value, msg):
                    self.app.root.after(0, lambda: self._update_progress(value, msg))
                
                success = self.app.model_manager.load_janus(model_key, progress_cb)
                self.app.root.after(0, lambda: self._on_switch_complete(success, "Janus"))
            
            threading.Thread(target=load_thread, daemon=True).start()
            
        else:
            # 切换到 SD
            if self.app.model_manager.is_sd_loaded:
                messagebox.showinfo("提示", "SD 模型已加载")
                return
            
            model_path = self.app._get_model_path(model_choice)
            if not model_path:
                messagebox.showwarning("提示", "找不到模型文件")
                return
            
            if self.app.model_manager.is_janus_loaded:
                if not messagebox.askyesno("切换模型", "加载 SD 将自动卸载 Janus 模型，继续吗？"):
                    return
            
            self.update_status(f"🔄 切换到 SD...")
            self.switch_model_btn.config(state=tk.DISABLED)
            
            def load_thread():
                def progress_cb(value, msg):
                    self.app.root.after(0, lambda: self._update_progress(value, msg))
                
                success = self.app.model_manager.load_sd(model_path, model_choice, progress_cb)
                self.app.root.after(0, lambda: self._on_switch_complete(success, "SD"))
            
            threading.Thread(target=load_thread, daemon=True).start()
    
    def _on_switch_complete(self, success: bool, model_type: str):
        """切换完成回调"""
        self.switch_model_btn.config(state=tk.NORMAL)
        self._update_model_status()
        self.app._update_model_ui()
        
        if success:
            self.update_status(f"✅ 已切换到 {model_type}")
            self._append_log(f"✅ 模型切换成功: {model_type}")
        else:
            self.update_status(f"❌ 切换到 {model_type} 失败")
            self._append_log(f"❌ 模型切换失败: {model_type}")
            messagebox.showerror("错误", f"{model_type} 模型加载失败")
            
            
    def _generate_grid_configs(self):
        """生成网格测试配置文件"""
        import threading
        
        if self.is_running:
            messagebox.showwarning("提示", "测试正在运行中，请等待完成")
            return
        
        self._append_log("📝 开始生成配置文件...")
        self._append_log(f"   模型类型: {self.gen_model_types.get()}")
        self._append_log(f"   配置类型: {self.gen_config_type.get()}")
        
        threading.Thread(target=self._run_generate_configs, daemon=True).start()
    

    def _run_generate_configs(self):
        """后台生成配置（自动扫描模型）"""
        try:
            import os
            import json
            from itertools import product
            from config.app_config import app_config
            
            # ========== 动态获取项目配置路径 ==========
            model_base_paths = app_config.paths.get_resolved_model_paths()
            sd15_folder = model_base_paths[0] if len(model_base_paths) > 0 else "../models/sd-v1-5"
            sdxl_folder = model_base_paths[1] if len(model_base_paths) > 1 else "../models/sdxl"
            
            # ========== 自动扫描模型 ==========
            def scan_models(folder):
                if not os.path.exists(folder):
                    return []
                return [f for f in os.listdir(folder) if f.endswith(('.safetensors', '.ckpt'))]
            
            SD15_MODELS = scan_models(sd15_folder)
            SDXL_MODELS = scan_models(sdxl_folder)
            
            # Lightning 模型（从 SDXL 目录中筛选）
            LIGHTNING_MODELS = [m for m in SDXL_MODELS if 'lightning' in m.lower()]
            
            if not SD15_MODELS and not SDXL_MODELS:
                self.app.root.after(0, lambda: self._append_log("❌ 未找到任何模型文件"))
                return
            
            self.app.root.after(0, lambda: self._append_log(f"📦 找到 SD 1.5: {len(SD15_MODELS)} 个, SDXL: {len(SDXL_MODELS)} 个"))
            
            JANUS_MODELS = ["1B", "7B"]
            
            # ========== 预设尺寸 ==========
            PRESET_SIZES = {
                "标全(512x768)": {"width": 512, "height": 768},
                "标全_横(768x512)": {"width": 768, "height": 512},
                "细全(512x1024)": {"width": 512, "height": 1024},
                "高全(640x960)": {"width": 640, "height": 960},
                "极全(640x1024)": {"width": 640, "height": 1024},
                "超长(576x1024)": {"width": 576, "height": 1024},
                "方图(768x768)": {"width": 768, "height": 768},
                "横图(896x512)": {"width": 896, "height": 512},
                "SDXL方图(1024x1024)": {"width": 1024, "height": 1024},
                "SDXL竖图(896x1152)": {"width": 896, "height": 1152},
                "SDXL竖图(832x1216)": {"width": 832, "height": 1216},
                "SDXL竖图(768x1344)": {"width": 768, "height": 1344},
                "SDXL横图(1152x896)": {"width": 1152, "height": 896},
                "SDXL横图(1216x832)": {"width": 1216, "height": 832},
                "SDXL宽屏(1344x768)": {"width": 1344, "height": 768},
                "SDXL超宽(1536x640)": {"width": 1536, "height": 640},
            }
            
            QUALITY_PROMPTS = {
                "sd15": "masterpiece, best quality, highly detailed, sharp focus",
                "sdxl": "masterpiece, best quality, highly detailed, sharp focus",
                "janus": "masterpiece, best quality, highly detailed",
            }
            
            NEGATIVE_PROMPT = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature"
            
            STEPS_SD15 = [20, 25, 30]
            STEPS_SDXL = [30, 35, 40]
            STEPS_LIGHTNING = [1, 4, 8, 10]
            CFG_VALUES = [7.0, 7.5, 8.0]
            
            SIZES_SD15 = ["标全(512x768)", "标全_横(768x512)", "高全(640x960)", "方图(768x768)", "横图(896x512)"]
            SIZES_SDXL = ["SDXL方图(1024x1024)", "SDXL竖图(896x1152)", "SDXL竖图(832x1216)", "SDXL横图(1152x896)", "SDXL宽屏(1344x768)"]
            SIZES_LIGHTNING = ["SDXL方图(1024x1024)", "SDXL竖图(896x1152)"]
            HIRES_VALUES = [False, True]
            JANUS_TEMPS = [0.4, 0.6, 0.8, 1.0, 1.2]
            JANUS_TOKENS = [1024, 2048, 4096]
            
            output_dir = "data/configs/grid_configs"
            os.makedirs(output_dir, exist_ok=True)
            
            config_type = self.gen_config_type.get()
            model_type_filter = self.gen_model_types.get()
            
            # ===== 生成 SD 配置 =====
            def generate_sd_grid_configs():
                all_models = []
                for m in SD15_MODELS:
                    all_models.append({"name": m, "type": "sd15", "folder": sd15_folder})
                for m in SDXL_MODELS:
                    all_models.append({"name": m, "type": "sdxl", "folder": sdxl_folder})
                for m in LIGHTNING_MODELS:
                    all_models.append({"name": m, "type": "lightning", "folder": sdxl_folder})
                
                if not all_models:
                    return 0
                
                configs = []
                for model_info in all_models:
                    model_name = model_info["name"]
                    model_type = model_info["type"]
                    model_folder = model_info["folder"]
                    
                    if model_type_filter not in ["all", model_type]:
                        continue
                    
                    if model_type == "lightning":
                        steps_list = STEPS_LIGHTNING
                        size_list = SIZES_LIGHTNING
                        quality_tag = QUALITY_PROMPTS["sdxl"]
                    elif model_type == "sdxl":
                        steps_list = STEPS_SDXL
                        size_list = SIZES_SDXL
                        quality_tag = QUALITY_PROMPTS["sdxl"]
                    else:
                        steps_list = STEPS_SD15
                        size_list = SIZES_SD15
                        quality_tag = QUALITY_PROMPTS["sd15"]
                    
                    prompt = f"{quality_tag}, a beautiful Asian woman, wearing elegant dress, full body shot, detailed face, natural lighting"
                    
                    grid_combos = []
                    for steps, cfg, size_name, hires in product(steps_list, CFG_VALUES, size_list, HIRES_VALUES):
                        size = PRESET_SIZES[size_name]
                        combo = {
                            "name": f"s{steps}_c{cfg}_{size_name}_h{str(hires)[0]}",
                            "params": {
                                "steps": steps, "cfg": cfg,
                                "width": size["width"], "height": size["height"],
                                "seed": 42, "hires": hires
                            }
                        }
                        grid_combos.append(combo)
                    
                    model_short = model_name.replace('.safetensors', '').replace('.ckpt', '')[:30]
                    full_config = {
                        "name": f"{model_type.upper()}_{model_short}_全参数测试",
                        "description": f"{model_type.upper()}: {model_name} | 共 {len(grid_combos)} 种组合",
                        "model_type": "sd",
                        "model": f"{model_folder}/{model_name}",
                        "prompt": prompt,
                        "negative": NEGATIVE_PROMPT,
                        "output_dir": f"./output/grid_tests/{model_type}_{model_short}",
                        "grid": grid_combos
                    }
                    configs.append(full_config)
                
                for config in configs:
                    filename = f"{config['name']}.json"
                    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
                    filepath = os.path.join(output_dir, safe_filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                
                return len(configs)
            
            # ===== 生成 Janus 配置 =====
            def generate_janus_grid_configs():
                if model_type_filter not in ["all", "janus"]:
                    return 0
                configs = []
                for model_name in JANUS_MODELS:
                    for temp, max_tokens in product(JANUS_TEMPS, JANUS_TOKENS):
                        config = {
                            "name": f"Janus_{model_name}_t{temp}_tk{max_tokens}",
                            "description": f"Janus-Pro-{model_name} | 温度{temp} Token{max_tokens}",
                            "model_type": "janus",
                            "prompt": f"{QUALITY_PROMPTS['janus']}, a beautiful Asian woman, wearing elegant dress, full body shot, detailed face",
                            "negative": NEGATIVE_PROMPT,
                            "output_dir": f"./output/janus_grid_tests/{model_name}",
                            "grid": [{
                                "name": f"t{temp}_tk{max_tokens}",
                                "params": {
                                    "temperature": temp,
                                    "max_tokens": max_tokens,
                                    "seed": 42
                                }
                            }]
                        }
                        configs.append(config)
                
                for config in configs:
                    filename = f"{config['name']}.json"
                    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
                    filepath = os.path.join(output_dir, safe_filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                
                return len(configs)
            
            # ===== 生成快速测试配置 =====
            def generate_quick_test_config():
                # 使用第一个可用的模型
                first_sd15 = SD15_MODELS[0] if SD15_MODELS else None
                first_sdxl = SDXL_MODELS[0] if SDXL_MODELS else None
                
                quick_params = []
                if first_sd15:
                    quick_params.extend([
                        {"model": "sd15", "steps": 20, "cfg": 7.5, "size": "标全(512x768)", "hires": False, "model_path": f"{sd15_folder}/{first_sd15}"},
                        {"model": "sd15", "steps": 25, "cfg": 7.5, "size": "高全(640x960)", "hires": False, "model_path": f"{sd15_folder}/{first_sd15}"},
                        {"model": "sd15", "steps": 30, "cfg": 8.0, "size": "方图(768x768)", "hires": False, "model_path": f"{sd15_folder}/{first_sd15}"},
                        {"model": "sd15", "steps": 25, "cfg": 7.5, "size": "横图(896x512)", "hires": False, "model_path": f"{sd15_folder}/{first_sd15}"},
                        {"model": "sd15", "steps": 25, "cfg": 7.5, "size": "标全(512x768)", "hires": True, "model_path": f"{sd15_folder}/{first_sd15}"},
                    ])
                if first_sdxl:
                    quick_params.extend([
                        {"model": "sdxl", "steps": 30, "cfg": 7.5, "size": "SDXL方图(1024x1024)", "hires": False, "model_path": f"{sdxl_folder}/{first_sdxl}"},
                        {"model": "sdxl", "steps": 35, "cfg": 8.0, "size": "SDXL竖图(896x1152)", "hires": False, "model_path": f"{sdxl_folder}/{first_sdxl}"},
                        {"model": "sdxl", "steps": 30, "cfg": 7.5, "size": "SDXL横图(1152x896)", "hires": False, "model_path": f"{sdxl_folder}/{first_sdxl}"},
                        {"model": "sdxl", "steps": 35, "cfg": 7.5, "size": "SDXL方图(1024x1024)", "hires": True, "model_path": f"{sdxl_folder}/{first_sdxl}"},
                    ])
                
                if not quick_params:
                    return 0
                
                grid = []
                for params in quick_params:
                    size = PRESET_SIZES[params["size"]]
                    grid.append({
                        "name": f"{params['model']}_s{params['steps']}_c{params['cfg']}_{params['size']}_h{str(params['hires'])[0]}",
                        "params": {
                            "steps": params["steps"], "cfg": params["cfg"],
                            "width": size["width"], "height": size["height"],
                            "seed": 42, "hires": params["hires"]
                        }
                    })
                
                # 使用第一个可用的模型作为默认
                default_model = f"{sd15_folder}/{first_sd15}" if first_sd15 else (f"{sdxl_folder}/{first_sdxl}" if first_sdxl else "")
                
                config = {
                    "name": "快速测试_9组合",
                    "description": "快速验证 SD1.5 和 SDXL 的关键参数组合",
                    "model_type": "sd",
                    "model": default_model,
                    "prompt": f"{QUALITY_PROMPTS['sd15']}, a beautiful Asian woman, wearing elegant dress, full body shot, detailed face, natural lighting",
                    "negative": NEGATIVE_PROMPT,
                    "output_dir": "./output/grid_tests/quick_test",
                    "grid": grid
                }
                
                filepath = os.path.join(output_dir, "quick_test_config.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                return 1
            
            # ===== 生成多提示词配置 =====
            def generate_multi_prompt_config():
                first_sd15 = SD15_MODELS[0] if SD15_MODELS else None
                if not first_sd15:
                    return 0
                
                prompts = [
                    "a beautiful Asian woman, wearing elegant dress, full body shot, detailed face, natural lighting",
                    "a beautiful Japanese woman in kimono, traditional garden, full body, soft sunlight",
                    "a beautiful Korean woman in hanbok, palace background, full body, elegant pose",
                    "a beautiful Chinese woman in qipao, modern city background, full body, fashion photography",
                    "a beautiful woman in casual clothes, street photography, full body, urban setting",
                ]
                
                grid = []
                for i, prompt in enumerate(prompts):
                    grid.append({
                        "name": f"prompt_{i+1}",
                        "params": {
                            "steps": 25, "cfg": 7.5,
                            "width": 512, "height": 768,
                            "seed": 42 + i, "hires": False,
                            "prompt": f"{QUALITY_PROMPTS['sd15']}, {prompt}"
                        }
                    })
                
                config = {
                    "name": "多提示词对比测试",
                    "description": "同一参数下测试5种不同提示词",
                    "model_type": "sd",
                    "model": f"{sd15_folder}/{first_sd15}",
                    "negative": NEGATIVE_PROMPT,
                    "output_dir": "./output/grid_tests/prompt_comparison",
                    "grid": grid
                }
                
                filepath = os.path.join(output_dir, "multi_prompt_config.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                return 1
            
            # ===== 生成组合配置 =====
            def generate_combined_grid_config():
                first_sd15 = SD15_MODELS[0] if SD15_MODELS else None
                if not first_sd15:
                    return 0
                
                grid = []
                for steps, cfg, size_name, hires in product(STEPS_SD15, CFG_VALUES, list(PRESET_SIZES.keys()), HIRES_VALUES):
                    size = PRESET_SIZES[size_name]
                    if size["width"] > 1024 or size["height"] > 1024:
                        continue
                    grid.append({
                        "name": f"SD15_s{steps}_c{cfg}_{size_name}_h{str(hires)[0]}",
                        "params": {"steps": steps, "cfg": cfg, "width": size["width"], "height": size["height"], "seed": 42, "hires": hires}
                    })
                
                for steps, cfg, size_name, hires in product(STEPS_SDXL, CFG_VALUES, SIZES_SDXL, HIRES_VALUES):
                    size = PRESET_SIZES[size_name]
                    grid.append({
                        "name": f"SDXL_s{steps}_c{cfg}_{size_name}_h{str(hires)[0]}",
                        "params": {"steps": steps, "cfg": cfg, "width": size["width"], "height": size["height"], "seed": 42, "hires": hires}
                    })
                
                config = {
                    "name": "综合参数网格测试_全部组合",
                    "description": f"包含 SD1.5 和 SDXL 的所有参数组合，共 {len(grid)} 种",
                    "model_type": "sd",
                    "model": f"{sd15_folder}/{first_sd15}",
                    "prompt": f"{QUALITY_PROMPTS['sd15']}, a beautiful Asian woman, wearing elegant dress, full body shot, detailed face, natural lighting",
                    "negative": NEGATIVE_PROMPT,
                    "output_dir": "./output/grid_tests/combined_all",
                    "grid": grid
                }
                
                filepath = os.path.join(output_dir, "combined_grid_config.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                return 1
            
            # ===== 执行生成 =====
            total_generated = 0
            
            if config_type == "full":
                total_generated += generate_sd_grid_configs()
                total_generated += generate_janus_grid_configs()
            elif config_type == "quick":
                total_generated += generate_quick_test_config()
            elif config_type == "multi_prompt":
                total_generated += generate_multi_prompt_config()
            elif config_type == "combined":
                total_generated += generate_combined_grid_config()
            
            if total_generated == 0:
                self.app.root.after(0, lambda: self._append_log("⚠️ 没有生成任何配置文件，请检查模型目录"))
            else:
                self.app.root.after(0, lambda: self._append_log(f"✅ 配置文件生成完成！共生成 {total_generated} 个配置文件"))
                self.app.root.after(0, lambda: self._refresh_config_list())
            
        except Exception as e:
            self.app.root.after(0, lambda: self._append_log(f"❌ 生成失败: {e}"))
            import traceback
            traceback.print_exc()
        

    def _refresh_config_list(self):
        """刷新配置文件列表（生成配置后调用）"""
        self._refresh_config_dropdown()  # ✅ 复用下拉刷新
        
        # 自动选择第一个配置文件并预览
        config_dir = "data/configs/grid_configs"
        if os.path.exists(config_dir):
            configs = [f for f in os.listdir(config_dir) if f.endswith('.json')]
            if configs:
                first_config = os.path.join(config_dir, configs[0])
                self.config_path_var.set(first_config)
                self._preview_config(first_config)
                self._append_log(f"📋 已加载配置文件: {configs[0]}")
                
    def _open_config_dir(self):
        """打开配置目录"""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "configs", "grid_configs")
        if os.path.exists(config_dir):
            os.startfile(config_dir)
        else:
            messagebox.showinfo("提示", f"配置目录不存在:\n{config_dir}\n请先运行 generate_grid_configs.py 生成配置")

    def _refresh_config_dropdown(self):
        """刷新配置文件下拉列表"""
        config_dir = "data/configs/grid_configs"
        configs = []
        if os.path.exists(config_dir):
            configs = [f for f in os.listdir(config_dir) if f.endswith('.json')]
            configs.sort()  # 按名称排序
        
        self.config_combo['values'] = configs
        
        # 如果当前路径在列表中，自动选中
        current = self.config_path_var.get()
        if current:
            # 提取文件名
            current_name = os.path.basename(current)
            if current_name in configs:
                self.config_combo.set(current_name)
            else:
                self.config_combo.set("")
        elif configs:
            # 默认选择第一个
            first_config = os.path.join(config_dir, configs[0])
            self.config_path_var.set(first_config)
            self.config_combo.set(configs[0])
            self._preview_config(first_config)
            
            
    def _on_config_selected(self, event):
        """下拉框选择事件"""
        selected = self.config_combo.get()
        if selected:
            config_dir = "data/configs/grid_configs"
            config_path = os.path.join(config_dir, selected)
            if os.path.exists(config_path):
                self.config_path_var.set(config_path)
                self._preview_config(config_path)
                self._append_log(f"📋 已选择配置文件: {selected}")
            
    def _select_config(self):
        """选择配置文件"""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "configs", "grid_configs")
        if not os.path.exists(config_dir):
            config_dir = os.getcwd()
        
        file = filedialog.askopenfilename(
            title="选择配置文件",
            initialdir=config_dir,
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file:
            self.config_path_var.set(file)
            self._preview_config(file)
            self._refresh_config_dropdown()  # ✅ 新增：刷新下拉列表
    
    def _preview_config(self, filepath):
        """预览配置文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            preview = f"📋 名称: {config.get('name', '未命名')}\n"
            preview += f"📝 描述: {config.get('description', '无')}\n"
            preview += f"📦 模型类型: {config.get('model_type', 'sd')}\n"
            preview += f"📁 输出目录: {config.get('output_dir', '默认')}\n"
            preview += f"📊 组合数: {len(config.get('grid', []))}\n\n"
            preview += "━" * 50 + "\n"
            preview += "📌 参数组合:\n"
            for i, item in enumerate(config.get('grid', [])):
                name = item.get('name', f'组合{i+1}')
                params = item.get('params', {})
                params_str = []
                for k, v in params.items():
                    if k in ['prompt', 'negative']:
                        v = str(v)[:30] + "..." if len(str(v)) > 30 else v
                    params_str.append(f"{k}={v}")
                preview += f"  {i+1:2d}. {name[:20]:20} | {', '.join(params_str[:6])}\n"
            
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", preview)
            self.preview_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", f"❌ 加载失败: {e}")
            self.preview_text.config(state=tk.DISABLED)
    
    def _start_run(self):
        """开始运行测试"""
        config_path = self.config_path_var.get()
        if not config_path or not os.path.exists(config_path):
            messagebox.showwarning("提示", "请先选择有效的配置文件")
            return
        
        if self.is_running:
            return
        
        # ===== 检查模型是否匹配 =====
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config_model_type = config.get('model_type', 'sd')
        except:
            config_model_type = 'sd'
        
        # 检查当前加载的模型类型是否匹配
        if config_model_type == "janus":
            if not self.app.model_manager.is_janus_loaded:
                if messagebox.askyesno("提示", "当前未加载 Janus 模型，是否自动切换？"):
                    model_key = "1B"
                    if self.app.model_manager.is_sd_loaded:
                        if not messagebox.askyesno("提示", "将自动卸载 SD 模型，继续吗？"):
                            return
                    
                    self.update_status("🔄 正在加载 Janus...")
                    self._switch_to_selected_model()
                    # 等待切换完成后再启动测试（简化处理：提示用户手动切换）
                    messagebox.showinfo("提示", "请等待模型切换完成后，再次点击运行测试")
                    return
                else:
                    return
        else:
            if not self.app.model_manager.is_sd_loaded:
                # 尝试使用当前选中的 SD 模型
                model_choice = self.model_choice_var.get()
                if model_choice and model_choice in self.app.checkpoints:
                    if messagebox.askyesno("提示", f"当前未加载 SD 模型，是否自动加载 {model_choice[:40]}？"):
                        self._switch_to_selected_model()
                        messagebox.showinfo("提示", "请等待模型加载完成后，再次点击运行测试")
                        return
                else:
                    messagebox.showwarning("提示", "请先在主界面加载 SD 模型")
                    return
        
        self.is_running = True
        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        
        threading.Thread(target=self._run_in_thread, args=(config_path,), daemon=True).start()
    
    def _run_in_thread(self, config_path):
        """在后台线程运行测试（使用独立 pipeline）"""

        # ✅ 生成 task_id
        task_id = f"txt2img_{datetime.now().strftime('%H%M%S')}" 
        
        from utils.pipeline_pool import pipeline_pool
        from PIL import Image
        import os
        
        def update_progress(current, total, name):
            # ✅ 带 source
            self.app.root.after(0, lambda: self.app.progress_bar.update(
                current / total,
                f"{name} ({current}/{total})",
                "网格测试"
            ))
            self._append_log(f"[{current}/{total}] {name}")
        
        def update_log(msg):
            self.app.root.after(0, lambda: self._append_log(msg))
        
        model_path = None
        lora_path = None
        model_type = "sd"
        
        try:
            update_log("🚀 开始运行网格测试...")
            
            model_choice = self.model_choice_var.get()
            model_type = self.model_type_var.get()
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if model_type == "janus":
                config['model_type'] = 'janus'
                self.runner.model_type = 'janus'
                self.runner.load_model(None, "janus")
            else:
                if model_choice and hasattr(self.app, 'checkpoint_paths'):
                    model_path = self.app.checkpoint_paths.get(model_choice)
                else:
                    model_path = config.get('model')
                
                if not model_path:
                    update_log("❌ 找不到模型文件")
                    self.app.root.after(0, self._on_finish)
                    return
                
                lora_path = None
                lora_weight = 1.0
                if hasattr(self.app, 'lora_var') and hasattr(self.app, 'lora_paths'):
                    lora_display = self.app.lora_var.get()
                    if lora_display:
                        lora_path = self.app.lora_paths.get(lora_display)
                        lora_weight = self.app.lora_weight_var.get() if hasattr(self.app, 'lora_weight_var') else 1.0
                
                pipe, is_new = pipeline_pool.get_pipeline(
                    model_path=model_path,
                    model_name=os.path.basename(model_path),
                    lora_path=lora_path,
                    lora_weight=lora_weight,
                    task_id=task_id
                )
                
                self.runner.pipe = pipe
                self.runner.model_type = 'sd'
                self.runner._loaded = True
                
                config['model'] = model_path
                update_log(f"📦 获取 Pipeline: {os.path.basename(model_path)}")
            
            results = self.runner.run_grid(config_path, update_progress)
            
            # ===== 图片后期处理 =====
            from utils.image_post_processor import post_process_image
            
            output_dir = config.get('output_dir', './output/grid_tests')
            if os.path.exists(output_dir):
                for filename in os.listdir(output_dir):
                    if filename.endswith('.png'):
                        filepath = os.path.join(output_dir, filename)
                        try:
                            final_path = post_process_image(
                                filepath,
                                self.app.params_panel,
                                log_prefix="[网格测试]"
                            )
                            if final_path != filepath:
                                os.remove(filepath)
                        except Exception as e:
                            update_log(f"⚠️ 后期处理失败: {e}")
            
            if model_type != "janus" and model_path:
                pipeline_pool.release_pipeline(model_path, lora_path, task_id)
                update_log("🗑️ Pipeline 已释放")
            
            success = sum(1 for r in results if r.get('success', False))
            total = len(results)
            
            update_log(f"\n✅ 完成! 成功: {success}/{total}")
            self.app.root.after(0, self._on_finish)
            
        except Exception as e:
            # ✅ 标记错误
            self.app.progress_bar.error_task(task_id, str(e))
            
            if model_type != "janus" and model_path:
                try:
                    pipeline_pool.release_pipeline(model_path, lora_path, task_id)  # ✅ 传入 task_id
                except:
                    pass
            
            update_log(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            self.app.root.after(0, self._on_finish)

        
        
    def _update_progress(self, current, total, name):
        """更新进度"""
        progress = (current / total) * 100
        self.progress_var.set(progress)
        self.progress_text_var.set(f"正在生成: {name} ({current}/{total})")
        self._append_log(f"[{current}/{total}] {name}")
    
    def _append_log(self, msg):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _on_finish(self):
        """完成"""
        self.is_running = False
        self.run_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_text_var.set("✅ 所有测试完成!")
        self._update_model_status()
    
    def _stop_run(self):
        """停止运行"""
        self.runner.cancel_run()
        self._append_log("⏹️ 用户取消")
        self.stop_btn.config(state=tk.DISABLED)
    
    def _open_output(self):
        """打开输出目录"""
        config_path = self.config_path_var.get()
        if config_path:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                output_dir = config.get('output_dir', './output/grid_tests')
                if os.path.exists(output_dir):
                    os.startfile(output_dir)
                else:
                    messagebox.showinfo("提示", "输出目录尚未创建")
            except:
                os.startfile('./output/grid_tests')
        else:
            os.startfile('./output/grid_tests')
    
    def _create_template(self):
        """创建配置模板"""
        template = {
            "name": "我的测试",
            "description": "描述这个测试的目的",
            "model_type": "sd",
            "model": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "prompt": "masterpiece, best quality, highly detailed, sharp focus, a beautiful woman",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text",
            "output_dir": "./output/grid_tests",
            "grid": [
                {
                    "name": "标准参数",
                    "params": {
                        "steps": 20,
                        "cfg": 7.5,
                        "width": 512,
                        "height": 768,
                        "seed": 42
                    }
                },
                {
                    "name": "高细节",
                    "params": {
                        "steps": 30,
                        "cfg": 8.0,
                        "width": 512,
                        "height": 768,
                        "seed": 43
                    }
                },
                {
                    "name": "大尺寸",
                    "params": {
                        "steps": 25,
                        "cfg": 7.5,
                        "width": 640,
                        "height": 960,
                        "seed": 44
                    }
                }
            ]
        }
        
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "configs", "grid_configs")
        os.makedirs(config_dir, exist_ok=True)
        
        filepath = filedialog.asksaveasfilename(
            title="保存配置模板",
            defaultextension=".json",
            initialdir=config_dir,
            filetypes=[("JSON文件", "*.json")],
            initialfile="grid_config_template.json"
        )
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", f"配置模板已保存:\n{filepath}")
            self.config_path_var.set(filepath)
            self._preview_config(filepath)