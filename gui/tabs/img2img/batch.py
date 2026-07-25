# gui/tabs/img2img/batch.py
"""图生图批量生成"""

import time
import random
from datetime import datetime


class BatchGenerator:
    """图生图批量生成器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
    
    def run_batch(self, prompts_list):
        """运行批量生成"""
        if not self.tab.selected_images:
            self.tab.update_status("❌ 没有选择图片")
            return
        
        original_images = self.tab.selected_images.copy()
        
        try:
            for idx, prompt in enumerate(prompts_list):
                if self.tab.cancel_generation:
                    break
                
                img_idx = idx % len(original_images)
                img_path = original_images[img_idx]
                self.tab.selected_images = [img_path]
                
                self.tab.update_status(f"🔄 正在生成第 {idx+1}/{len(prompts_list)} 张...")
                self.tab.set_prompt(prompt, self.tab.default_negative)
                self.tab.start_generate()
                
                wait_count = 0
                while self.tab.is_generating and wait_count < 600:
                    time.sleep(0.5)
                    wait_count += 1
                
                time.sleep(0.5)
        finally:
            self.tab.selected_images = original_images
            self.tab.is_generating = False
            self.tab.update_status("✅ 批量生成完成")