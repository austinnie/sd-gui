# gui/tabs/txt2img/batch.py
"""文生图批量生成"""

import random
import threading
import time
from datetime import datetime
import gc

from .utils import get_smart_size, get_smart_params, log


class BatchGenerator:
    """批量生成器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.params = tab.params
    
    def run_batch(self, prompts: list, negs: list):
        """运行批量生成"""
        self.tab.batch_running = True
        self.tab.batch_prompts = prompts
        self.tab.batch_negs = negs
        self.tab.batch_current = 0
        self.tab.batch_total = len(prompts)
        
        self.tab.update_status(f"🚀 开始批量生成，共 {len(prompts)} 组...")
        
        def run_thread():
            for idx, prompt in enumerate(self.tab.batch_prompts):
                if not self.tab.batch_running or self.tab.cancel_generation:
                    self.tab.update_status("⏹️ 批量生成已停止")
                    break
                
                negative = self.tab.batch_negs[idx] if idx < len(self.tab.batch_negs) else self.tab.default_negative
                self.tab.batch_current = idx + 1
                
                self.tab.update_status(f"🔄 正在生成: 第 {self.tab.batch_current}/{self.tab.batch_total} 组")
                
                seed = self.params.seed_var.get()
                if seed == -1:
                    seed = random.randint(1, 2**32 - 1)
                seed = seed + idx
                
                self.tab._generate_single_image(
                    prompt, negative,
                    seed=seed,
                    index=idx+1,
                    total=self.tab.batch_total
                )
                
                time.sleep(0.5)
            
            self.tab.batch_running = False
            self.tab.update_status(f"✅ 批量生成完成！共生成 {self.tab.batch_current} 张")
        
        threading.Thread(target=run_thread, daemon=True).start()