# gui/tabs/pipeline_tab.py
"""
流水线标签页 - 支持预设流水线和自定义流水线
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
from datetime import datetime
from PIL import Image, ImageTk

from .base_tab import BaseTab
from core.pipeline import PipelineRegistry, Pipeline, StepContext
from core.pipeline.steps.marble_step import MarbleStep


class PipelineTab(BaseTab):
    """流水线标签页"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._init_vars()
        self._init_steps()
        self.setup_ui()
        self._load_pipelines()
        self.is_running = False
        self.cancel_flag = False
    
    def _init_vars(self):
        """初始化变量"""
        self.pipeline_var = tk.StringVar()
        self.image_path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="就绪")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_text_var = tk.StringVar(value="等待开始...")
        self.config_path_var = tk.StringVar(value="pipelines_config.json")
        # 【新增】批量处理变量
        self.batch_dir_var = tk.StringVar(value="output/good")
        self.batch_status_var = tk.StringVar(value="就绪")
        self.batch_use_inpaint_var = tk.BooleanVar(value=False)
        self.batch_skip_existing_var = tk.BooleanVar(value=True)
        
        self.is_running = False
        self.cancel_flag = False        
    
    def _init_steps(self):
        """注册所有步骤"""
        from core.pipeline import register_all_steps
        register_all_steps()
    
    def _load_pipelines(self):
        """加载流水线配置"""
        config_path = self.config_path_var.get()
        
        if not os.path.exists(config_path):
            # 如果配置文件不存在，使用默认配置
            self.pipelines_config = self._get_default_config()
            self._save_default_config(config_path)
        else:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.pipelines_config = json.load(f)
            except Exception as e:
                print(f"⚠️ 加载流水线配置失败: {e}")
                self.pipelines_config = self._get_default_config()
        
        # 更新下拉列表
        names = list(self.pipelines_config.get("pipelines", {}).keys())
        self.pipeline_combo['values'] = names
        if names:
            self.pipeline_var.set(names[0])
            self._update_info()
    
    def _get_default_config(self) -> dict:
        """获取默认流水线配置"""
        return {
            "pipelines": {
                "大理石雕像": {
                    "description": "将人物转换为大理石雕像风格（14种场景）",
                    "steps": [
                        {
                            "type": "marble",
                            "config": {
                                "strength": 0.25,
                                "max_strength": 0.55,
                                "cfg": 7.0,
                                "steps": 15,
                                "scenes": 14
                            }
                        }
                    ]
                },
                "大理石雕像_快速": {
                    "description": "快速版 - 只生成6种场景",
                    "steps": [
                        {
                            "type": "marble",
                            "config": {
                                "strength": 0.25,
                                "max_strength": 0.55,
                                "cfg": 7.0,
                                "steps": 15,
                                "scenes": 6
                            }
                        }
                    ]
                }
            }
        }
    
    def _save_default_config(self, config_path: str):
        """保存默认配置"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._get_default_config(), f, ensure_ascii=False, indent=2)
            print(f"✅ 已创建默认流水线配置: {config_path}")
        except Exception as e:
            print(f"⚠️ 创建默认配置失败: {e}")
    
    def setup_ui(self):
        """设置 UI"""
        frame = self.frame
        row = 0
        
        # ===== 标题 =====
        title = ttk.Label(frame, text="🔧 流水线处理", font=("", 14, "bold"))
        title.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=10, padx=5)
        row += 1
        
        # ===== 流水线选择 =====
        ttk.Label(frame, text="选择流水线:").grid(row=row, column=0, sticky=tk.W, padx=5)
        
        self.pipeline_combo = ttk.Combobox(
            frame,
            textvariable=self.pipeline_var,
            width=35,
            state="readonly"
        )
        self.pipeline_combo.grid(row=row, column=1, sticky=tk.W, padx=5)
        self.pipeline_combo.bind('<<ComboboxSelected>>', lambda e: self._update_info())
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=2, sticky=tk.W, padx=5)
        ttk.Button(btn_frame, text="🔄 刷新", command=self._reload_pipelines).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📁 编辑配置", command=self._edit_config).pack(side=tk.LEFT, padx=2)
        row += 1
        
        # ===== 流水线信息 =====
        info_frame = ttk.LabelFrame(frame, text="📋 流水线信息", padding=5)
        info_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.info_text = tk.Text(info_frame, height=4, width=80, bg='#f0f0f0', wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        row += 1
        
        # ===== 图片选择（单张模式） =====
        image_frame = ttk.LabelFrame(frame, text="📷 输入图片", padding=5)
        image_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        img_row = ttk.Frame(image_frame)
        img_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(img_row, text="图片:").pack(side=tk.LEFT, padx=5)
        self.path_label = ttk.Label(
            img_row,
            textvariable=self.image_path_var,
            foreground="gray",
            background="white",
            relief="sunken"
        )
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(img_row, text="浏览", command=self._select_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(img_row, text="清除", command=self._clear_image).pack(side=tk.LEFT, padx=5)
        
        # 预览
        self.preview_label = ttk.Label(image_frame)
        self.preview_label.pack(pady=5)
        row += 1
        
        # ===== 参数覆盖 =====
        param_frame = ttk.LabelFrame(frame, text="⚙️ 参数覆盖 (可选)", padding=5)
        param_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # 强度
        strength_row = ttk.Frame(param_frame)
        strength_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(strength_row, text="强度:").pack(side=tk.LEFT, padx=5)
        self.strength_var = tk.DoubleVar(value=0.25)
        scale = ttk.Scale(
            strength_row,
            from_=0.1, to=0.6,
            variable=self.strength_var,
            orient=tk.HORIZONTAL,
            length=150
        )
        scale.pack(side=tk.LEFT, padx=5)
        self.strength_label = ttk.Label(strength_row, text="0.25", width=5)
        self.strength_label.pack(side=tk.LEFT, padx=5)
        self.strength_var.trace('w', lambda *_: self.strength_label.config(
            text=f"{self.strength_var.get():.2f}"
        ))
        
        # 步数
        steps_row = ttk.Frame(param_frame)
        steps_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(steps_row, text="步数:").pack(side=tk.LEFT, padx=5)
        self.steps_var = tk.IntVar(value=25)
        ttk.Spinbox(steps_row, from_=10, to=50, textvariable=self.steps_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(steps_row, text="CFG:").pack(side=tk.LEFT, padx=15)
        self.cfg_var = tk.DoubleVar(value=7.0)
        ttk.Spinbox(steps_row, from_=5.0, to=10.0, textvariable=self.cfg_var, width=5, increment=0.5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(steps_row, text="场景数:").pack(side=tk.LEFT, padx=15)
        self.scenes_var = tk.IntVar(value=14)
        ttk.Combobox(
            steps_row,
            textvariable=self.scenes_var,
            values=[6, 12, 14],
            width=5,
            state="readonly"
        ).pack(side=tk.LEFT, padx=5)
        row += 1

        # ===== 【新增】批量处理模式 =====
        batch_frame = ttk.LabelFrame(frame, text="📁 批量处理模式 (处理目录下所有图片)", padding=5)
        batch_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        row += 1
        
        # 目录选择
        batch_row1 = ttk.Frame(batch_frame)
        batch_row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(batch_row1, text="图片目录:").pack(side=tk.LEFT, padx=5)
        self.batch_dir_var = tk.StringVar(value="output/good")
        ttk.Entry(batch_row1, textvariable=self.batch_dir_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(batch_row1, text="浏览", command=self._select_batch_dir).pack(side=tk.LEFT, padx=5)
        
        # 批量选项
        batch_row2 = ttk.Frame(batch_frame)
        batch_row2.pack(fill=tk.X, pady=2)
        
        self.batch_use_inpaint_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(batch_row2, text="启用局部重绘 (去除衣物)", variable=self.batch_use_inpaint_var).pack(side=tk.LEFT, padx=5)
        
        self.batch_skip_existing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(batch_row2, text="跳过已存在的图片", variable=self.batch_skip_existing_var).pack(side=tk.LEFT, padx=15)
        
        ttk.Label(batch_row2, text=f"图片数: 0", foreground="gray").pack(side=tk.RIGHT, padx=5)
        
        # 批量按钮
        batch_row3 = ttk.Frame(batch_frame)
        batch_row3.pack(fill=tk.X, pady=5)
        
        self.batch_run_btn = ttk.Button(batch_row3, text="📦 批量处理目录", command=self._run_batch_pipeline)
        self.batch_run_btn.pack(side=tk.LEFT, padx=5)
        
        self.batch_cancel_btn = ttk.Button(batch_row3, text="⏹️ 取消", command=self._cancel_batch, state=tk.DISABLED)
        self.batch_cancel_btn.pack(side=tk.LEFT, padx=5)
        
        self.batch_status_var = tk.StringVar(value="就绪")
        ttk.Label(batch_row3, textvariable=self.batch_status_var, foreground="blue").pack(side=tk.LEFT, padx=15)
        
        # ===== 控制按钮 =====
        btn_frame2 = ttk.Frame(frame)
        btn_frame2.grid(row=row, column=0, columnspan=3, pady=10)
        
        self.run_btn = ttk.Button(btn_frame2, text="🚀 运行流水线", command=self._run_pipeline)
        self.run_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(btn_frame2, text="⏹️ 取消", command=self._cancel_pipeline, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame2, text="📁 打开输出", command=self._open_output).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # ===== 进度条 =====
        progress_frame = ttk.Frame(frame)
        progress_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=2)
        
        self.status_label = ttk.Label(progress_frame, textvariable=self.progress_text_var, foreground="blue")
        self.status_label.pack(anchor=tk.W, pady=2)
        row += 1
        
        # ===== 日志 =====
        log_frame = ttk.LabelFrame(frame, text="📝 运行日志", padding=5)
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, width=80, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        row += 1
        
        # ===== 底部提示 =====
        ttk.Label(
            frame,
            text="💡 支持多步流水线组合，当前已支持: 大理石转换",
            foreground="gray",
            font=("", 8)
        ).grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
    
    def _update_info(self):
        """更新流水线信息"""
        name = self.pipeline_var.get()
        pipelines = self.pipelines_config.get("pipelines", {})
        pipeline = pipelines.get(name, {})
        
        info = f"📌 {name}\n"
        info += f"📝 {pipeline.get('description', '无描述')}\n"
        steps = pipeline.get("steps", [])
        info += f"📊 共 {len(steps)} 步\n"
        for i, step in enumerate(steps, 1):
            step_type = step.get("type", "unknown")
            config = step.get("config", {})
            config_str = ", ".join(f"{k}={v}" for k, v in config.items() if k != "model_path")
            info += f"   {i}. {step_type} ({config_str})\n"
        
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", info)
    
    def _reload_pipelines(self):
        """重新加载流水线配置"""
        self._load_pipelines()
        self._append_log("🔄 流水线配置已重新加载")
        self.update_status("✅ 流水线配置已重新加载")
    
    def _edit_config(self):
        """编辑配置文件"""
        config_path = self.config_path_var.get()
        if os.path.exists(config_path):
            try:
                os.startfile(config_path)
            except:
                messagebox.showinfo("提示", f"请手动打开配置文件:\n{os.path.abspath(config_path)}")
        else:
            messagebox.showwarning("提示", f"配置文件不存在:\n{config_path}")
    
    def _select_image(self):
        """选择图片"""
        file = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                ("所有文件", "*.*")
            ]
        )
        if file:
            self.image_path_var.set(file)
            self._show_preview(file)
    
    def _clear_image(self):
        """清除图片"""
        self.image_path_var.set("")
        self.preview_label.config(image='')
        self.preview_label.image = None
    
    def _show_preview(self, filepath):
        """显示图片预览"""
        try:
            img = Image.open(filepath)
            # 限制最大尺寸
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
        except Exception as e:
            print(f"⚠️ 预览失败: {e}")
    
    def _run_pipeline(self):
        """运行流水线"""
        if self.is_running:
            messagebox.showwarning("提示", "流水线正在运行中")
            return
        
        name = self.pipeline_var.get()
        if not name:
            messagebox.showwarning("提示", "请选择流水线")
            return
        
        image_path = self.image_path_var.get()
        if not image_path or not os.path.exists(image_path):
            messagebox.showwarning("提示", "请选择有效的图片")
            return
        
        # 获取流水线配置
        pipelines = self.pipelines_config.get("pipelines", {})
        pipeline_config = pipelines.get(name)
        if not pipeline_config:
            messagebox.showerror("错误", "流水线配置无效")
            return
        
        # 覆盖参数
        override_strength = self.strength_var.get()
        override_steps = self.steps_var.get()
        override_cfg = self.cfg_var.get()
        override_scenes = self.scenes_var.get()
        
        for step in pipeline_config.get("steps", []):
            config = step.get("config", {})
            if "strength" in config:
                config["strength"] = override_strength
            if "steps" in config:
                config["steps"] = override_steps
            if "cfg" in config:
                config["cfg"] = override_cfg
            if "scenes" in config:
                config["scenes"] = override_scenes
        
        self.is_running = True
        self.cancel_flag = False
        self.run_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.progress_text_var.set("🚀 开始运行流水线...")
        self._append_log(f"🚀 开始运行流水线: {name}")
        self._append_log(f"📷 输入图片: {os.path.basename(image_path)}")
        
        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_dir = f"./output/pipeline_{base_name}_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        self._append_log(f"📁 输出目录: {output_dir}")
        
        # 在后台线程运行
        threading.Thread(
            target=self._run_pipeline_thread,
            args=(image_path, pipeline_config, output_dir),
            daemon=True
        ).start()
    

    # gui/tabs/pipeline_tab.py

    def _run_pipeline_thread(self, image_path, pipeline_config, output_dir):
        """在后台线程运行流水线（使用独立 pipeline）"""
        from utils.pipeline_pool import pipeline_pool
        # ✅ 生成 task_id
        task_id = f"txt2img_{datetime.now().strftime('%H%M%S')}"        
        try:
            # ===== 获取独立的 pipeline =====
            model_name = self.app.model_var.get()
            model_path = self.app._get_model_path(model_name)
            
            # 获取 LoRA 信息
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
                task_id=task_id  # ✅ 添加 task_id
            )
            
            self._append_log(f"📦 获取 Pipeline: {os.path.basename(model_path)}")
            
            # 创建流水线
            pipeline = PipelineRegistry.create_pipeline_from_config(pipeline_config)
            
            # 将 pipe 注入到流水线的上下文中
            def on_progress(current, total, msg):
                # ✅ 带 source
                self.app.root.after(0, lambda: self.app.progress_bar.update(
                    current / total,
                    f"{msg} ({current}/{total})",
                    "流水线"
                ))
            
            
            pipeline.set_progress_callback(on_progress)
            
            # 加载图片
            image = Image.open(image_path).convert('RGB')
            
            # 创建上下文（传入 pipe）
            context = StepContext(
                input_image=image,
                input_path=image_path,
                output_dir=output_dir,
                global_config={
                    "model_path": model_path,
                    "pipe": pipe,  # ✅ 传入独立 pipeline
                    "lora_path": lora_path,
                    "lora_weight": lora_weight
                }
            )
            
            # 运行流水线
            results = pipeline.run(context)
            
            # ===== 释放 pipeline =====
            pipeline_pool.release_pipeline(model_path, lora_path)
            self._append_log("🗑️ Pipeline 已释放")
            
            # 显示结果
            self.app.root.after(0, lambda: self._show_results(results, output_dir))
            
        except Exception as e:
           # ✅ 标记错误
            self.app.progress_bar.error_task(task_id, str(e))
            
            # 确保释放 pipeline
            if 'model_path' in locals() and model_path:
                try:
                    pipeline_pool.release_pipeline(model_path, lora_path, task_id)  # ✅ 传入 task_id
                except:
                    pass
            
            error_msg = str(e)
            self.app.root.after(0, lambda: self._on_error(error_msg))
            

        
    def _update_progress(self, current, total, msg):
        """更新进度"""
        progress = (current / total) * 100
        self.progress_var.set(progress)
        self.progress_text_var.set(f"{msg} ({current}/{total})")
        self._append_log(f"[{current}/{total}] {msg}")
    
    def _show_results(self, results, output_dir):
        """显示结果"""
        from utils.image_post_processor import post_process_image
        success_count = 0

        from utils.image_post_processor import post_process_image
        
        success_count = 0
        
        # ===== 【新增】对所有成功生成的图片进行后期处理 =====
        for name, result in results.items():
            if result.success and result.output_path and os.path.exists(result.output_path):
                try:
                    final_path = post_process_image(
                        result.output_path,
                        self.app.params_panel,  # 传入参数面板
                        log_prefix=f"[流水线-{name}]"
                    )
                    # 如果后期处理返回了不同路径，更新 result
                    if final_path != result.output_path:
                        # 删除原始文件
                        try:
                            os.remove(result.output_path)
                        except:
                            pass
                        result.output_path = final_path
                        self._append_log(f"🖼️ {name}: 已应用后期处理")
                except Exception as e:
                    self._append_log(f"⚠️ {name}: 后期处理失败 - {e}")
                
        for name, result in results.items():
            if result.success:
                success_count += 1
                self._append_log(f"✅ {name}: {os.path.basename(result.output_path) if result.output_path else '完成'}")
            else:
                self._append_log(f"❌ {name}: {result.error}")
        
        total = len(results)
        self.progress_var.set(100)
        self.progress_text_var.set(f"✅ 流水线完成! 成功: {success_count}/{total}")
        self.status_label.config(foreground="green")
        
        self._append_log(f"\n📊 完成: 成功 {success_count}/{total}")
        self._append_log(f"📁 输出目录: {output_dir}")
        
        self.is_running = False
        self.run_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.update_status(f"✅ 流水线完成! 成功: {success_count}/{total}")
    
    def _on_error(self, error_msg):
        """错误处理"""
        self.progress_text_var.set(f"❌ 错误: {error_msg}")
        self.status_label.config(foreground="red")
        self._append_log(f"❌ 错误: {error_msg}")
        
        self.is_running = False
        self.run_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.update_status(f"❌ 流水线失败: {error_msg}")
        messagebox.showerror("错误", f"流水线运行失败:\n{error_msg}")
    
    def _cancel_pipeline(self):
        """取消流水线"""
        self.cancel_flag = True
        self._append_log("⏹️ 用户取消")
        self.progress_text_var.set("⏹️ 正在取消...")
        self.cancel_btn.config(state=tk.DISABLED)
    
    def _append_log(self, msg):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _open_output(self):
        """打开输出文件夹"""
        # 查找最新的输出目录
        output_base = "./output"
        if os.path.exists(output_base):
            # 找最新的 pipeline 输出目录
            dirs = [d for d in os.listdir(output_base) if d.startswith("pipeline_")]
            if dirs:
                # 按修改时间排序
                dirs.sort(key=lambda d: os.path.getmtime(os.path.join(output_base, d)), reverse=True)
                latest = os.path.join(output_base, dirs[0])
                try:
                    os.startfile(latest)
                    return
                except:
                    pass
        
        # 如果找不到，打开 output 目录
        if os.path.exists(output_base):
            try:
                os.startfile(output_base)
            except:
                pass
    
    def get_frame(self):
        return self.frame
        
# gui/tabs/pipeline_tab.py

    def _select_batch_dir(self):
        """选择批量处理目录"""
        dir_path = filedialog.askdirectory(title="选择图片目录")
        if dir_path:
            self.batch_dir_var.set(dir_path)
            self._update_batch_count()
    
    def _update_batch_count(self):
        """更新批量图片数量"""
        dir_path = self.batch_dir_var.get()
        if os.path.exists(dir_path):
            images = self._get_batch_images(dir_path)
            count = len(images)
            # 更新标签
            for child in self.batch_frame.winfo_children():
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Label) and "图片数:" in str(subchild.cget("text")):
                        subchild.config(text=f"图片数: {count}")
                        break
    
    def _get_batch_images(self, directory):
        """获取目录下所有支持的图片"""
        extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
        images = []
        for f in os.listdir(directory):
            if Path(f).suffix.lower() in extensions:
                images.append(os.path.join(directory, f))
        return sorted(images)
    
    def _cancel_batch(self):
        """取消批量处理"""
        self.cancel_flag = True
        self.batch_cancel_btn.config(state=tk.DISABLED)
        self.batch_status_var.set("⏹️ 正在取消...")
    
    def _run_batch_pipeline(self):
        """运行批量流水线处理"""
        if self.is_running:
            messagebox.showwarning("提示", "流水线正在运行中")
            return
        
        dir_path = self.batch_dir_var.get()
        if not os.path.exists(dir_path):
            messagebox.showwarning("提示", f"目录不存在: {dir_path}")
            return
        
        images = self._get_batch_images(dir_path)
        if not images:
            messagebox.showwarning("提示", "目录中没有图片文件")
            return
        
        # 检查模型
        if self.app.pipeline is None:
            messagebox.showwarning("提示", "请先加载模型")
            return
        
        # 确认
        if not messagebox.askyesno("确认批量处理",
            f"将处理 {len(images)} 张图片\n"
            f"目录: {dir_path}\n"
            f"流水线: {self.pipeline_var.get()}\n\n"
            f"确定继续吗？"
        ):
            return
        
        self.is_running = True
        self.cancel_flag = False
        self.batch_run_btn.config(state=tk.DISABLED)
        self.batch_cancel_btn.config(state=tk.NORMAL)
        self.batch_status_var.set(f"🚀 开始批量处理...")
        
        threading.Thread(
            target=self._run_batch_pipeline_thread,
            args=(images, dir_path),
            daemon=True
        ).start()
    
    def _run_batch_pipeline_thread(self, images, dir_path):
        """后台线程运行批量处理"""
        # 生成任务 ID
        task_id = f"批量流水线_{datetime.now().strftime('%H%M%S')}"
        self.app.progress_bar.add_task(task_id, "批量流水线")
        
        try:
            total = len(images)
            success_count = 0
            
            for idx, image_path in enumerate(images):
                if self.cancel_flag:
                    self._append_log("⏹️ 批量处理已取消")
                    break
                
                # 检查是否跳过已存在的图片
                if self.batch_skip_existing_var.get():
                    # 检查输出目录是否已有对应图片
                    base_name = os.path.splitext(os.path.basename(image_path))[0]
                    output_dir = f"./output/pipeline_batch_{base_name}"
                    if os.path.exists(output_dir):
                        existing = [f for f in os.listdir(output_dir) if f.endswith('.png')]
                        if existing:
                            self._append_log(f"⏭️ [{idx+1}/{total}] 跳过 {os.path.basename(image_path)} (已存在)")
                            self.app.progress_bar.update_task(
                                task_id,
                                (idx + 1) / total,
                                f"跳过 {os.path.basename(image_path)}"
                            )
                            success_count += 1
                            continue
                
                self._append_log(f"🎨 [{idx+1}/{total}] 处理: {os.path.basename(image_path)}")
                self.app.progress_bar.update_task(
                    task_id,
                    (idx) / total,
                    f"处理 {os.path.basename(image_path)} ({idx+1}/{total})"
                )
                
                # 创建临时输出目录
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                output_dir = f"./output/pipeline_batch_{base_name}_{timestamp}"
                os.makedirs(output_dir, exist_ok=True)
                
                # 获取流水线配置
                pipeline_name = self.pipeline_var.get()
                pipelines = self.pipelines_config.get("pipelines", {})
                pipeline_config = pipelines.get(pipeline_name, {})
                
                if not pipeline_config:
                    self._append_log(f"❌ 流水线配置无效: {pipeline_name}")
                    continue
                
                # 覆盖参数
                override_strength = self.strength_var.get()
                override_steps = self.steps_var.get()
                override_cfg = self.cfg_var.get()
                override_scenes = self.scenes_var.get()
                
                for step in pipeline_config.get("steps", []):
                    config = step.get("config", {})
                    if "strength" in config:
                        config["strength"] = override_strength
                    if "steps" in config:
                        config["steps"] = override_steps
                    if "cfg" in config:
                        config["cfg"] = override_cfg
                    if "scenes" in config:
                        config["scenes"] = override_scenes
                
                # 加载图片
                image = Image.open(image_path).convert('RGB')
                
                # 创建上下文
                context = StepContext(
                    input_image=image,
                    input_path=image_path,
                    output_dir=output_dir,
                    global_config={
                        "pipe": self.app.pipeline,
                        "model_path": None,
                        "batch_mode": True
                    }
                )
                
                # 运行流水线
                pipeline = PipelineRegistry.create_pipeline_from_config(pipeline_config)
                
                # 进度回调
                def batch_progress(current, total_steps, msg):
                    progress = (idx + current / total_steps) / total
                    self.app.root.after(0, lambda: self.app.progress_bar.update_task(
                        task_id,
                        progress,
                        f"{os.path.basename(image_path)} ({idx+1}/{total}) - {msg}"
                    ))
                
                pipeline.set_progress_callback(batch_progress)
                results = pipeline.run(context)
                
                # 检查结果
                step_success = any(r.success for r in results.values())
                if step_success:
                    success_count += 1
                    self._append_log(f"✅ [{idx+1}/{total}] 完成: {os.path.basename(image_path)}")
                else:
                    self._append_log(f"❌ [{idx+1}/{total}] 失败: {os.path.basename(image_path)}")
                
                gc.collect()
            
            # 完成
            self.app.progress_bar.finish_task(task_id)
            self.app.root.after(0, lambda: self._on_batch_complete(success_count, total))
            
        except Exception as e:
            self.app.progress_bar.error_task(task_id, str(e))
            self.app.root.after(0, lambda: self._on_batch_error(str(e)))
    
    def _on_batch_complete(self, success_count, total):
        """批量处理完成"""
        self.is_running = False
        self.batch_run_btn.config(state=tk.NORMAL)
        self.batch_cancel_btn.config(state=tk.DISABLED)
        self.batch_status_var.set(f"✅ 批量处理完成! 成功: {success_count}/{total}")
        self.update_status(f"✅ 批量处理完成! 成功: {success_count}/{total}")
    
    def _on_batch_error(self, error):
        """批量处理错误"""
        self.is_running = False
        self.batch_run_btn.config(state=tk.NORMAL)
        self.batch_cancel_btn.config(state=tk.DISABLED)
        self.batch_status_var.set(f"❌ 错误: {error}")
        self.update_status(f"❌ 批量处理错误: {error}")        