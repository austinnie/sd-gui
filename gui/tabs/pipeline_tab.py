# gui/tabs/pipeline_tab.py
"""流水线标签页 - 精简版"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import json
from datetime import datetime
from pathlib import Path

from .base_tab import BaseTab
from core.pipeline import PipelineRegistry
from core.pipeline.presets import BUILTIN_PIPELINES
from core.pipeline.runner import PipelineRunner
from core.pipeline.batch_runner import BatchPipelineRunner
from core.pipeline.scene_counter import get_total_scenes
from gui.tabs.pipeline_ui import PipelineUI


class PipelineTab(BaseTab):
    """流水线标签页 - 精简版"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        
        self._init_vars()
        self._init_steps()
        
        # ===== 初始化运行器 =====
        self.runner = PipelineRunner(self)
        self.batch_runner = BatchPipelineRunner(self)
        
        # ===== 设置 UI =====
        self.ui = PipelineUI(self)
        self.ui.build()
        
        # ===== 加载流水线 =====
        self._load_pipelines()
        
        # ===== 状态 =====
        self.is_running = False
        self.cancel_flag = False
    
    def _init_vars(self):
        """初始化变量"""
        self.pipeline_var = tk.StringVar()
        self.image_path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="就绪")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_text_var = tk.StringVar(value="等待开始...")
        
        self.strength_var = tk.DoubleVar(value=0.35)
        self.steps_var = tk.IntVar(value=25)
        self.cfg_var = tk.DoubleVar(value=7.0)
        self.scenes_limit_var = tk.StringVar(value="全部")
        
        # ControlNet
        self.use_controlnet_var = tk.BooleanVar(value=False)
        self.controlnet_type_var = tk.StringVar(value="canny")
        self.controlnet_strength_var = tk.DoubleVar(value=0.6)
        
        # 批量处理
        self.batch_dir_var = tk.StringVar(value="output/good")
        self.batch_skip_existing_var = tk.BooleanVar(value=True)
        self.batch_status_var = tk.StringVar(value="就绪")
    
    def _init_steps(self):
        """注册所有步骤"""
        from core.pipeline import register_all_steps
        register_all_steps()
    
    def _load_pipelines(self):
        """加载流水线配置"""
        self.pipelines_config = {"pipelines": BUILTIN_PIPELINES}
        names = list(self.pipelines_config.get("pipelines", {}).keys())
        self.pipeline_combo['values'] = names
        if names:
            self.pipeline_var.set(names[0])
            self._update_info()
    
    def _reload_pipelines(self):
        """重新加载流水线"""
        self._load_pipelines()
        self._append_log("🔄 流水线已重新加载")
        self.update_status("✅ 流水线已重新加载")
    
    def _update_info(self):
        """更新流水线信息"""
        name = self.pipeline_var.get()
        pipelines = self.pipelines_config.get("pipelines", {})
        pipeline = pipelines.get(name, {})
        self.ui.update_info(name, pipeline)

        # ✅ 更新场景数信息
        self._update_scenes_info()


    def _update_scenes_info(self):
        """更新场景数信息显示"""
        from core.pipeline.scene_counter import get_total_scenes
        
        name = self.pipeline_var.get()
        pipelines = self.pipelines_config.get("pipelines", {})
        pipeline = pipelines.get(name, {})
        steps = pipeline.get("steps", [])
        
        total_scenes, scene_details = get_total_scenes(steps)
        
        if scene_details:
            self.scenes_info_var.set(f"共 {len(scene_details)} 个步骤, 总计 {total_scenes} 个场景")
            # 可选：在日志中输出详细信息
            print(f"📊 场景统计: {', '.join(scene_details)}")
        else:
            self.scenes_info_var.set("无场景数据")
        
    # ==================== 核心方法 ====================
    
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
        
        pipeline_config = self.pipelines_config.get("pipelines", {}).get(name)
        if not pipeline_config:
            messagebox.showerror("错误", "流水线配置无效")
            return
        
        # 应用覆盖参数
        self._apply_overrides(pipeline_config)
        
        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_dir = f"./output/pipeline_{base_name}_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        self.is_running = True
        self.cancel_flag = False
        self.run_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.progress_text_var.set("🚀 开始运行流水线...")
        self._append_log(f"🚀 开始运行流水线: {name}")
        self._append_log(f"📷 输入图片: {os.path.basename(image_path)}")
        self._append_log(f"📁 输出目录: {output_dir}")
        
        def run_thread():
            def progress_cb(current, total, msg):
                self.app.root.after(0, lambda: self.app.progress_bar.update(
                    current / total,
                    f"{msg} ({current}/{total})",
                    "流水线"
                ))
            
            result = self.runner.run(
                image_path=image_path,
                pipeline_config=pipeline_config,
                output_dir=output_dir,
                progress_callback=progress_cb,
                cancel_flag=lambda: self.cancel_flag,
                task_id=f"pipeline_{datetime.now().strftime('%H%M%S')}"
            )
            
            self.app.root.after(0, lambda: self._on_run_complete(result))
        
        threading.Thread(target=run_thread, daemon=True).start()
    
    def _on_run_complete(self, result: dict):
        """运行完成"""
        self.is_running = False
        self.run_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        
        if result.get("success"):
            results = result.get("results", {})
            success_count = sum(1 for r in results.values() if r.success)
            total = len(results)
            self.progress_var.set(100)
            self.progress_text_var.set(f"✅ 流水线完成! 成功: {success_count}/{total}")
            self._append_log(f"\n📊 完成: 成功 {success_count}/{total}")
            self._append_log(f"📁 输出目录: {result.get('output_dir', '')}")
            self.update_status(f"✅ 流水线完成! 成功: {success_count}/{total}")
        else:
            self.progress_text_var.set(f"❌ 错误: {result.get('error', '未知错误')}")
            self._append_log(f"❌ 错误: {result.get('error', '未知错误')}")
            self.update_status(f"❌ 流水线失败: {result.get('error', '未知错误')}")
    
    # ==================== 批量处理 ====================
    
    def _run_batch_pipeline(self):
        """批量运行流水线"""
        if self.is_running:
            return
        
        dir_path = self.batch_dir_var.get()
        if not os.path.exists(dir_path):
            messagebox.showwarning("提示", f"目录不存在: {dir_path}")
            return
        
        images = self._get_batch_images(dir_path)
        if not images:
            messagebox.showwarning("提示", "目录中没有图片文件")
            return
        
        if self.app.pipeline is None:
            messagebox.showwarning("提示", "请先加载模型")
            return
        
        name = self.pipeline_var.get()
        if not name:
            messagebox.showwarning("提示", "请选择流水线")
            return
        
        pipeline_config = self.pipelines_config.get("pipelines", {}).get(name)
        if not pipeline_config:
            messagebox.showerror("错误", "流水线配置无效")
            return
        
        if not messagebox.askyesno("确认批量处理",
            f"将处理 {len(images)} 张图片\n"
            f"目录: {dir_path}\n"
            f"流水线: {name}\n\n确定继续吗？"
        ):
            return
        
        self._apply_overrides(pipeline_config)
        
        self.is_running = True
        self.cancel_flag = False
        self.batch_run_btn.config(state=tk.DISABLED)
        self.batch_cancel_btn.config(state=tk.NORMAL)
        self.batch_status_var.set(f"🚀 开始批量处理...")
        self._append_log(f"🚀 开始批量处理，共 {len(images)} 张图片")
        
        def run_thread():
            def progress_cb(current, total, msg):
                self.app.root.after(0, lambda: self.app.progress_bar.update(
                    current / total,
                    msg,
                    "批量流水线"
                ))
            
            result = self.batch_runner.run(
                images=images,
                dir_path=dir_path,
                pipeline_config=pipeline_config,
                progress_callback=progress_cb,
                cancel_flag=lambda: self.cancel_flag,
                skip_existing=self.batch_skip_existing_var.get(),
                task_id=f"batch_{datetime.now().strftime('%H%M%S')}"
            )
            
            self.app.root.after(0, lambda: self._on_batch_complete(result))
        
        threading.Thread(target=run_thread, daemon=True).start()
    
    def _on_batch_complete(self, result: dict):
        """批量处理完成"""
        self.is_running = False
        self.batch_run_btn.config(state=tk.NORMAL)
        self.batch_cancel_btn.config(state=tk.DISABLED)
        
        success = result.get("success_count", 0)
        total = result.get("total", 0)
        skipped = result.get("skipped_count", 0)
        
        self.batch_status_var.set(f"✅ 批量处理完成! 成功: {success}/{total} (跳过: {skipped})")
        self._append_log(f"📊 批量完成: 成功 {success}/{total}, 跳过 {skipped}")
        self.update_status(f"✅ 批量处理完成! 成功: {success}/{total}")
    
    def _cancel_batch(self):
        """取消批量处理"""
        self.cancel_flag = True
        self.batch_cancel_btn.config(state=tk.DISABLED)
        self.batch_status_var.set("⏹️ 正在取消...")
    
    def _get_batch_images(self, directory):
        """获取目录下所有图片"""
        extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
        images = []
        for f in os.listdir(directory):
            if Path(f).suffix.lower() in extensions:
                images.append(os.path.join(directory, f))
        return sorted(images)
    
    def _select_batch_dir(self):
        """选择批量目录"""
        dir_path = filedialog.askdirectory(title="选择图片目录")
        if dir_path:
            self.batch_dir_var.set(dir_path)
    
    # ==================== 辅助方法 ====================
    
    def _apply_overrides(self, pipeline_config):
        """应用参数覆盖"""
        scenes_limit = self.scenes_limit_var.get()
        override_scenes = None if scenes_limit == "全部" else int(scenes_limit)
        
        for step in pipeline_config.get("steps", []):
            config = step.get("config", {})
            config["strength"] = self.strength_var.get()
            config["steps"] = self.steps_var.get()
            config["cfg"] = self.cfg_var.get()
            config["use_controlnet"] = self.use_controlnet_var.get()
            config["controlnet_type"] = self.controlnet_type_var.get()
            config["controlnet_strength"] = self.controlnet_strength_var.get()
            if override_scenes is not None:
                config["max_scenes"] = override_scenes
                config["scene_limit"] = override_scenes
                config["scenes"] = override_scenes
    
    def _select_image(self):
        """选择图片"""
        file = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("所有文件", "*.*")]
        )
        if file:
            self.image_path_var.set(file)
            self.ui.show_preview(file)
    
    def _clear_image(self):
        """清除图片"""
        self.image_path_var.set("")
        self.ui.clear_preview()
    
    def _open_output(self):
        """打开输出文件夹"""
        output_base = "./output"
        if os.path.exists(output_base):
            dirs = [d for d in os.listdir(output_base) if d.startswith("pipeline_")]
            if dirs:
                dirs.sort(key=lambda d: os.path.getmtime(os.path.join(output_base, d)), reverse=True)
                latest = os.path.join(output_base, dirs[0])
                try:
                    os.startfile(latest)
                    return
                except:
                    pass
        
        if os.path.exists(output_base):
            try:
                os.startfile(output_base)
            except:
                pass
    
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
    
    def get_frame(self):
        return self.frame