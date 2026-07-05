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
        self.config_entry = ttk.Entry(config_frame, textvariable=self.config_path_var, width=50)
        self.config_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
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
    
    def _open_config_dir(self):
        """打开配置目录"""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "grid_configs")
        if os.path.exists(config_dir):
            os.startfile(config_dir)
        else:
            messagebox.showinfo("提示", f"配置目录不存在:\n{config_dir}\n请先运行 generate_grid_configs.py 生成配置")
    
    def _select_config(self):
        """选择配置文件"""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "grid_configs")
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
        """在后台线程运行测试"""
        def update_progress(current, total, name):
            self.app.root.after(0, lambda: self._update_progress(current, total, name))
        
        def update_log(msg):
            self.app.root.after(0, lambda: self._append_log(msg))
        
        try:
            update_log("🚀 开始运行网格测试...")
            
            # 获取选择的模型
            model_choice = self.model_choice_var.get()
            model_type = self.model_type_var.get()
            
            # 读取配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 如果模型类型是 janus，设置 runner
            if model_type == "janus":
                config['model_type'] = 'janus'
                self.runner.model_type = 'janus'
            else:
                # SD/SDXL 模型
                if model_choice and hasattr(self.app, 'checkpoint_paths'):
                    if model_choice in self.app.checkpoint_paths:
                        model_path = self.app.checkpoint_paths[model_choice]
                        config['model'] = model_path
                
                self.runner.model_type = 'sd'
            
            # 加载模型到 runner
            if model_type == "janus":
                self.runner.load_model(None, "janus")
            else:
                model_path = config.get('model')
                if model_path:
                    self.runner.load_model(model_path, "sd")
            
            results = self.runner.run_grid(config_path, update_progress)
            
            success = sum(1 for r in results if r.get('success', False))
            total = len(results)
            
            update_log(f"\n✅ 完成! 成功: {success}/{total}")
            self.app.root.after(0, self._on_finish)
            
        except Exception as e:
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
        
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "grid_configs")
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