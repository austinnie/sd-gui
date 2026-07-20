# lora_info_gui.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LoRA 信息查看器 - 独立运行版本
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.components.lora_info_viewer import LoraInfoViewer


class LoraInfoApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔍 LoRA 信息查看器")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        
        # 模拟 app 对象
        self.app = self
        self.lora_files = []
        self.lora_paths = {}
        self.lora_types = {}
        self.lora_var = tk.StringVar(value="")
        
        # 模拟 model_manager
        self.model_manager = self._MockModelManager()
        
        # 扫描 LoRA
        self._scan_loras()
        
        # 创建主界面
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.viewer = LoraInfoViewer(main_frame, self)
        self.viewer.get_frame().pack(fill=tk.BOTH, expand=True)
    
    class _MockModelManager:
        """模拟 ModelManager（独立运行时没有模型）"""
        @property
        def is_sd_loaded(self):
            return False
        
        def is_janus_loaded(self):
            return False
        
        def get_sd_model_type(self):
            return "unknown"
        
        def get_status_text(self):
            return "🔴 独立模式"
    
    def _scan_loras(self):
        """扫描 LoRA 文件（区分类型）"""
        lora_dirs = [
            ("../models/sd15-lora", "sd15"),
            ("../models/sdxl-lora", "sdxl"),
            ("../models/loras", "unknown"),
        ]
        
        for dir_path, lora_type in lora_dirs:
            if os.path.exists(dir_path):
                for item in os.listdir(dir_path):
                    if item.endswith('.safetensors'):
                        file_path = os.path.join(dir_path, item)
                        size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        
                        if lora_type == "sd15":
                            prefix = "🟢 [SD1.5] "
                        elif lora_type == "sdxl":
                            prefix = "🔵 [SDXL] "
                        else:
                            prefix = "📁 "
                        
                        display_name = f"{prefix}{item} ({size_mb:.1f}MB)"
                        self.lora_files.append(display_name)
                        self.lora_paths[display_name] = file_path
                        self.lora_types[display_name] = lora_type
        
        self.lora_files.sort(key=lambda x: 0 if '[SD1.5]' in x else 1 if '[SDXL]' in x else 2)
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = LoraInfoApp()
    app.run()