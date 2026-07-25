# gui/tabs/txt2img/tab.py
"""文生图标签页主类"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import random
import time
from datetime import datetime

import json
import os

from ..base_tab import BaseTab
from .ui import Txt2ImgUI
from .generator import ImageGenerator
from .batch import BatchGenerator
from .templates import TemplateManager
from .utils import get_smart_size, get_smart_params, log

from core.nsfw_filter import nsfw_filter
from config.nsfw_config import nsfw_config
from utils.pipeline_pool import pipeline_pool


from utils.logger import get_logger, info, warning, error, debug

logger = get_logger(__name__)
class Txt2ImgTab(BaseTab):
    """文生图标签页 - 完整版"""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.params = self.app.params_panel
        self._init_vars()
        
        self.template_manager = TemplateManager(self)
        self.template_manager.load()
        
        self.generator = ImageGenerator(self)
        self.batch_generator = BatchGenerator(self)
        
        self.ui = Txt2ImgUI(self)
        self.ui.build()
    
    def _init_vars(self):
        """初始化变量"""
        from config.app_config import app_config
        
        self.default_negative = (
            "worst quality, low quality, ugly, deformed, blurry, "
            "bad anatomy, bad hands, missing fingers, extra digits, "
            "watermark, text, signature"
        )
        
        self.default_positive = (
            "masterpiece, best quality, photorealistic, 8k, "
            "a beautiful Asian woman, Chinese, hanfu dress, "
            "traditional Chinese garden, East Asian architecture, "
            "full body shot, standing, smiling, looking at viewer"
        )
        
        self.cancel_generation = False
        self.is_generating = False
        
        self.batch_running = False
        self.batch_current = 0
        self.batch_total = 0
        self.batch_prompts = []
        self.batch_negs = []
        
        self.template_var = tk.StringVar(value="")
        self.template_category_var = tk.StringVar(value="美女")
        
        self.use_controlnet = False
        
        # 结果文本框（用于批量日志）
        self.result_text = None
    
    def _update_template_list(self, event=None):
        """更新模板下拉列表"""
        category = self.template_category_var.get()
        names = self.template_manager.get_names(category)
        self.template_combo['values'] = names
        if names:
            self.template_combo.set(names[0])
            self._apply_template()
        else:
            self.template_combo.set("")
    
    def _apply_template(self, event=None):
        """应用选中的模板"""
        category = self.template_category_var.get()
        template_name = self.template_var.get()
        if not template_name:
            return
        
        template = self.template_manager.get_template(category, template_name)
        if template:
            self.prompt_text.delete("1.0", tk.END)
            self.prompt_text.insert("1.0", template.get("prompt", ""))
            self.neg_text.delete("1.0", tk.END)
            self.neg_text.insert("1.0", template.get("negative", self.default_negative))
            self.update_status(f"✅ 已应用模板: {category} → {template_name}")
    
    def _refresh_templates(self):
        """重新加载模板"""
        self.template_manager.load()
        categories = self.template_manager.get_categories()
        self.category_combo['values'] = categories
        if categories:
            self.template_category_var.set(categories[0])
            self._update_template_list()
        self.update_status("✅ 模板已刷新")
    
    def _save_custom_template(self):
        """保存自定义模板"""
        category = self.template_category_var.get()
        name = simpledialog.askstring("模板名称", "输入模板名称:", parent=self.frame)
        if not name:
            return
        
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        negative = self.neg_text.get("1.0", tk.END).strip()
        
        if not prompt:
            messagebox.showwarning("提示", "提示词不能为空")
            return
        
        # 添加到当前分类
        if category not in self.template_manager.templates:
            self.template_manager.templates[category] = []
        
        self.template_manager.templates[category].append({
            "name": name,
            "prompt": prompt,
            "negative": negative
        })
        
        # 保存到文件
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "templates", "prompt_templates.json"
        )
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(self.template_manager.templates, f, ensure_ascii=False, indent=2)
            self._refresh_templates()
            self.update_status(f"✅ 已保存模板: {name}")
        except Exception as e:
            messagebox.showerror("错误", f"保存模板失败: {e}")
    
    def start_generate(self):
        """开始生成"""
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        negative = self.neg_text.get("1.0", tk.END).strip()
        
        if not prompt:
            messagebox.showwarning("提示", "请输入正面提示词")
            return
        
        if nsfw_config.enabled:
            has_nsfw, matched = nsfw_filter.detect_nsfw(prompt)
            if has_nsfw:
                logger.info(f"🔞 检测到 NSFW 关键词: {matched}")
            prompt, negative = nsfw_filter.filter_prompt(prompt, negative)
        
        self.cancel_generation = False
        self.is_generating = True
        
        params = self.params.get_params()
        steps = params["steps"]
        cfg = params["cfg"]
        seed = params["seed"]
        width = params["width"]
        height = params["height"]
        num_images = params["num_images"]
        
        smart_w, smart_h, size_msg = get_smart_size(width, height, prompt)
        logger.info(f"📐 {size_msg}")
        
        smart_steps, smart_cfg, _, param_msg = get_smart_params(prompt, steps, cfg, None)
        if smart_steps != steps or smart_cfg != cfg:
            logger.info(f"⚙️ {param_msg}")
        
        self.update_status("🚀 开始文生图...")
        self.generate_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        
        threading.Thread(
            target=self._generate_images,
            args=(prompt, negative, smart_steps, smart_cfg, seed, smart_h, smart_w, num_images),
            daemon=True
        ).start()
    
    def _generate_images(self, prompt, negative, steps, cfg, seed, height, width, num_images):
        """在后台线程中生成多张图片"""
        from config.app_config import app_config
        from utils.pipeline_pool import pipeline_pool
        
        max_allowed = app_config.generation.max_images
        num_images = max(1, min(max_allowed, num_images))
        
        task_id = f"txt2img_{datetime.now().strftime('%H%M%S')}"
        
        model_name = self.app.model_var.get()
        model_path = self.app._get_model_path(model_name)
        
        lora_display = self.app.lora_var.get() if hasattr(self.app, 'lora_var') else ""
        lora_path = None
        lora_weight = 1.0
        if lora_display and hasattr(self.app, 'lora_paths'):
            lora_path = self.app.lora_paths.get(lora_display)
            lora_weight = self.app.lora_weight_var.get() if hasattr(self.app, 'lora_weight_var') else 1.0
        
        pipe, is_new = pipeline_pool.get_pipeline(
            model_path=model_path,
            model_name=model_name,
            lora_path=lora_path,
            lora_weight=lora_weight,
            task_id=task_id
        )
        
        if pipe is None:
            self.app.root.after(0, lambda: self._on_generation_error("无法获取 Pipeline"))
            return
        
        try:
            for i in range(num_images):
                if self.cancel_generation:
                    break
                
                current_seed = seed if seed != -1 else random.randint(1, 2**32 - 1)
                current_seed = current_seed + i
                
                self.generator.generate_single(
                    prompt, negative,
                    steps=steps, cfg=cfg, seed=current_seed,
                    height=height, width=width,
                    index=i+1, total=num_images,
                    pipe=pipe
                )
            
            self.app.root.after(0, self._on_generation_complete)
            
        except Exception as e:
            self.app.root.after(0, lambda err=e: self._on_generation_error(err))
        finally:
            if 'model_path' in locals() and 'lora_path' in locals():
                pipeline_pool.release_pipeline(model_path, lora_path, task_id)
    
    def _on_generation_complete(self):
        """生成完成"""
        self.is_generating = False
        self.generate_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.update_progress(1.0, "✅ 生成完成！")
        self.update_status("✅ 文生图完成")
        from gui.components.memory_monitor import force_memory_cleanup
        force_memory_cleanup()
    
    def _on_generation_error(self, error):
        """生成出错"""
        self.is_generating = False
        self.generate_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.update_status(f"❌ 生成出错: {error}")
        messagebox.showerror("错误", f"生成失败:\n{error}")
    
    def cancel_generation_cmd(self):
        """取消生成"""
        self.cancel_generation = True
        self.is_generating = False
        self.update_status("⏹️ 正在取消...")
        self.cancel_btn.config(state=tk.DISABLED)
    
    # ==================== 批量生成 ====================
    
    def batch_generate(self, prompts):
        """批量生成"""
        if self.batch_running:
            messagebox.showwarning("提示", "批量生成正在运行中")
            return
        
        negs = self._get_batch_negs_from_panel()
        while len(negs) < len(prompts):
            negs.append(self.default_negative)
        negs = negs[:len(prompts)]
        
        self.batch_generator.run_batch(prompts, negs)
    
    def _get_batch_negs_from_panel(self):
        """从批量面板获取负面词"""
        if hasattr(self.app, 'batch_panel'):
            return self.app.batch_panel.get_negatives()
        return []
    
    # ==================== 批量模板 ====================
    
    def _batch_run_all_templates(self):
        """批量运行所有模板"""
        all_templates = []
        for category, templates in self.template_manager.templates.items():
            for t in templates:
                if isinstance(t, dict):
                    all_templates.append({
                        "category": category,
                        "name": t.get("name", "未命名"),
                        "prompt": t.get("prompt", ""),
                        "negative": t.get("negative", self.default_negative)
                    })
                elif isinstance(t, str):
                    all_templates.append({
                        "category": category,
                        "name": t[:30] + "..." if len(t) > 30 else t,
                        "prompt": t,
                        "negative": self.default_negative
                    })
        
        if not all_templates:
            messagebox.showwarning("提示", "没有可用的模板")
            return
        
        if not messagebox.askyesno("批量运行所有模板",
            f"将依次运行所有 {len(all_templates)} 个模板\n\n确定开始吗？"
        ):
            return
        
        self.update_status(f"🚀 开始批量运行所有模板，共 {len(all_templates)} 个...")
        self.generate_btn.config(state=tk.DISABLED)
        
        threading.Thread(
            target=self._run_batch_templates,
            args=(all_templates,),
            daemon=True
        ).start()
    
    def _run_batch_templates(self, templates):
        """运行批量模板"""
        total = len(templates)
        success_count = 0
        
        model_name = self.app.model_var.get()
        model_path = self.app._get_model_path(model_name)
        
        if not model_path:
            self._append_batch_log("❌ 未找到模型文件")
            self.app.root.after(0, lambda: self._on_batch_templates_error("未找到模型文件"))
            return
        
        try:
            for idx, template in enumerate(templates):
                if self.cancel_generation:
                    self._append_batch_log(f"⏹️ 已取消，已处理 {idx}/{total}")
                    break
                
                category = template.get("category", "未知")
                name = template.get("name", f"模板_{idx+1}")
                prompt = template.get("prompt", "")
                negative = template.get("negative", self.default_negative)
                
                if not prompt:
                    self._append_batch_log(f"⚠️ [{idx+1}/{total}] {category}/{name} - 提示词为空，跳过")
                    self.app.root.after(0, lambda: self.update_progress((idx+1)/total, f"跳过 {idx+1}/{total}"))
                    continue
                
                self._append_batch_log(f"🎨 [{idx+1}/{total}] {category}/{name}")
                self.app.root.after(0, lambda: self.update_progress((idx+1)/total, f"{category}/{name} ({idx+1}/{total})"))
                
                params = self.params.get_params()
                smart_w, smart_h, _ = get_smart_size(params["width"], params["height"], prompt)
                smart_steps, smart_cfg, _, _ = get_smart_params(prompt, params["steps"], params["cfg"], None)
                
                seed = params["seed"]
                if seed == -1:
                    seed = random.randint(1, 2**32 - 1)
                seed = seed + idx
                
                try:
                    pipe, is_new = pipeline_pool.get_pipeline(
                        model_path=model_path,
                        model_name=model_name,
                        lora_path=None,
                        lora_weight=1.0,
                        task_id=f"batch_template_{idx}"
                    )
                    
                    if pipe is None:
                        self._append_batch_log(f"❌ [{idx+1}/{total}] 模型未加载")
                        continue
                    
                    generator = torch.Generator("cpu").manual_seed(seed)
                    result = pipe(
                        prompt=prompt,
                        negative_prompt=negative,
                        num_inference_steps=smart_steps,
                        guidance_scale=smart_cfg,
                        height=smart_h,
                        width=smart_w,
                        num_images_per_prompt=1,
                        generator=generator,
                    )
                    
                    image = result.images[0]
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = "".join(c for c in name if c.isalnum() or c in " _-")[:30]
                    safe_category = "".join(c for c in category if c.isalnum() or c in " _-")[:20]
                    filename = f"{timestamp}_模板_{safe_category}_{safe_name}.png"
                    
                    from config.app_config import app_config
                    output_dir = app_config.paths.output_dir
                    os.makedirs(output_dir, exist_ok=True)
                    filepath = os.path.join(output_dir, filename)
                    image.save(filepath)
                    
                    from utils.image_post_processor import post_process_image
                    final_path = post_process_image(filepath, self.params, prompt=prompt, log_prefix="[批量模板]")
                    if final_path != filepath:
                        try:
                            os.remove(filepath)
                        except:
                            pass
                        filepath = final_path
                    
                    self.app.root.after(0, lambda fp=filepath, img=image: self.app.add_to_preview(fp, img))
                    
                    success_count += 1
                    self._append_batch_log(f"✅ [{idx+1}/{total}] 已保存: {os.path.basename(filepath)}")
                    
                    pipeline_pool.release_pipeline(model_path, None, f"batch_template_{idx}")
                    del result
                    del generator
                    gc.collect()
                    
                except Exception as e:
                    self._append_batch_log(f"❌ [{idx+1}/{total}] 生成失败: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
                
                time.sleep(0.3)
            
            self.app.root.after(0, lambda: self._on_batch_templates_complete(success_count, total))
            
        except Exception as e:
            self.app.root.after(0, lambda err=str(e): self._on_batch_templates_error(err))
    
    def _on_batch_templates_complete(self, success_count, total):
        """批量模板完成"""
        self.is_generating = False
        self.generate_btn.config(state=tk.NORMAL)
        self.batch_templates_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.update_progress(1.0, f"✅ 批量模板完成！成功: {success_count}/{total}")
        self.update_status(f"✅ 批量模板完成！成功: {success_count}/{total}")
        self._append_batch_log(f"\n📊 完成: 成功 {success_count}/{total}")
        from gui.components.memory_monitor import force_memory_cleanup
        force_memory_cleanup()
    
    def _on_batch_templates_error(self, error):
        """批量模板出错"""
        self.is_generating = False
        self.generate_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.update_status(f"❌ 批量模板出错: {error}")
    
    def _append_batch_log(self, msg):
        """添加批量日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        def update():
            try:
                if hasattr(self, 'result_text') and self.result_text:
                    self.result_text.insert(tk.END, f"[{timestamp}] {msg}\n")
                    self.result_text.see(tk.END)
            except:
                pass
        self.app.root.after(0, update)
    
    # ==================== 外部接口 ====================
    
    def set_prompt(self, prompt: str, negative: str):
        """设置提示词"""
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", prompt)
        if negative:
            self.neg_text.delete("1.0", tk.END)
            self.neg_text.insert("1.0", negative)
    
    def set_params(self, steps=None, cfg=None, seed=None, width=None, height=None, num_images=None):
        """设置参数"""
        if steps is not None:
            self.params.steps_var.set(steps)
        if cfg is not None:
            self.params.cfg_var.set(cfg)
        if seed is not None:
            self.params.seed_var.set(seed)
        if width is not None:
            self.params.width_var.set(width)
        if height is not None:
            self.params.height_var.set(height)
        if num_images is not None:
            self.params.num_images_var.set(num_images)
    
    def generate(self):
        """外部调用生成"""
        self.start_generate()