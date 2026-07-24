# gui/chat/handlers/base_handler.py
"""处理器基类"""

import os
import random
import torch
from datetime import datetime
from PIL import Image
from typing import Optional

from utils.pipeline_pool import pipeline_pool
from config.app_config import app_config


class BaseHandler:
    """生成处理器基类"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.context_manager = tab.context_manager
        self.llm_client = tab.llm_client
        self.prompt_builder = tab.prompt_builder
    
    def handle(self, intent):
        """处理意图 - 子类必须实现"""
        raise NotImplementedError
    
    def _append_message(self, role: str, content: str):
        """添加消息到对话"""
        self.tab._append_message(role, content)
    
    def _append_image_result(self, filepath: str):
        """添加图片结果"""
        self.tab._append_image_result(filepath)
    
    def _update_status(self, msg: str, progress: float = None):
        """更新状态"""
        self.tab._update_status(msg, progress)
    
    def _clean_prompt_for_sd(self, prompt: str) -> str:
        """清理提示词"""
        return self.tab._clean_prompt_for_sd(prompt)
    
    def _get_pipeline(self, task_id: str = None):
        """获取 Pipeline"""
        model_name = self.app.model_var.get()
        model_path = self.app._get_model_path(model_name)
        
        lora_path = self.tab.lora_manager.current_lora_path if self.tab.lora_manager.lora_loaded else None
        
        if task_id is None:
            task_id = f"handler_{datetime.now().strftime('%H%M%S')}"
        
        pipe, is_new = pipeline_pool.get_pipeline(
            model_path=model_path,
            model_name=model_name,
            lora_path=lora_path,
            lora_weight=1.0,
            task_id=task_id
        )
        
        return pipe, model_path, lora_path, task_id
    
    def _release_pipeline(self, model_path: str, lora_path: str, task_id: str):
        """释放 Pipeline"""
        pipeline_pool.release_pipeline(model_path, lora_path, task_id)
    
    def _save_image(self, image, prompt: str, prefix: str = "chat") -> str:
        """保存图片"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        words = prompt.split()[:5]
        prompt_preview = "_".join(words).replace(",", "").replace(".", "")[:40]
        if not prompt_preview:
            prompt_preview = "image"
        filename = f"{timestamp}_{prefix}_{prompt_preview}.png"
        
        output_dir = app_config.paths.output_dir
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        image.save(filepath)
        
        # 后处理
        try:
            from utils.image_post_processor import post_process_image
            final_path = post_process_image(
                filepath,
                self.app.params_panel,
                prompt=prompt,
                log_prefix="[会话生图]"
            )
            if final_path != filepath:
                try:
                    os.remove(filepath)
                except:
                    pass
                filepath = final_path
        except:
            pass
        
        self._append_image_result(filepath)
        self.app.add_to_preview(filepath, image)
        
        return filepath
    
    def _get_seed(self, seed: int = -1) -> int:
        """获取种子"""
        if seed == -1:
            return random.randint(1, 2**32 - 1)
        return seed
    
    def _get_generator(self, seed: int):
        """获取生成器"""
        return torch.Generator("cpu").manual_seed(seed)
    
    @property
    def negative_templates(self):
        return self.tab._negative_templates
    
    @property
    def uploaded_images(self):
        return self.tab.uploaded_images
    
    @property
    def uploaded_image_paths(self):
        return self.tab.uploaded_image_paths