# gui/chat/lora_manager.py
"""LoRA 管理器"""

import os


class LoraManager:
    """LoRA 管理器"""
    
    DEFAULT_LORAS = [
        "busty_slider.safetensors",
        "beauty_masters.safetensors",
        "boobs.safetensors",
        "chunli.safetensors",
    ]
    
    def __init__(self, tab):
        self.tab = tab
        self.lora_paths = {}
        self.lora_loaded = False
        self.current_lora_path = None
    
    def scan_files(self) -> list:
        """扫描 LoRA 文件"""
        lora_dir = r"..\models\sd15-lora"
        if not os.path.exists(lora_dir):
            return []

        lora_files = []
        self.lora_paths = {}

        for f in os.listdir(lora_dir):
            if f.endswith('.safetensors'):
                is_default = f in self.DEFAULT_LORAS
                display_name = f"{'⭐ ' if is_default else ''}{f}"
                lora_files.append(display_name)
                self.lora_paths[display_name] = os.path.join(lora_dir, f)

        lora_files.sort(key=lambda x: 0 if x.startswith('⭐') else 1)
        return lora_files
    
    def load_to_pipe(self, lora_path: str, lora_name: str) -> bool:
        """加载 LoRA"""
        if not self.tab.app.model_manager.is_sd_loaded:
            self.tab._append_message("system", "⚠️ 模型未加载，请先加载模型")
            return False

        try:
            self.tab._append_message("system", f"📦 重新加载模型并加载 LoRA: {lora_name}")
            
            model_name = self.tab.app.model_var.get()
            model_path = self.tab.app._get_model_path(model_name)
            
            if not model_path:
                self.tab._append_message("system", "❌ 找不到模型文件")
                return False
            
            success = self.tab.app.model_manager.load_sd(
                model_path, model_name, None,
                lora_path=lora_path,
                lora_weight=1.0
            )
            
            if success:
                self.lora_loaded = True
                self.current_lora_path = lora_path
                self.tab.lora_var.set(lora_name)
                self.tab._append_message("system", f"✅ LoRA 加载成功: {lora_name}")
                self.update_status()
                return True
            else:
                self.tab._append_message("system", f"❌ LoRA 加载失败")
                return False
                
        except Exception as e:
            self.tab._append_message("system", f"❌ LoRA 加载失败: {str(e)}")
            return False
    
    def unload(self):
        """卸载 LoRA"""
        if not self.lora_loaded:
            self.tab._append_message("system", "ℹ️ 没有已加载的 LoRA")
            return

        try:
            self.tab.app.model_manager.unload_lora_from_pipe()
            self.lora_loaded = False
            self.current_lora_path = None
            self.tab._append_message("system", "🗑️ LoRA 已卸载")
            self.update_status()
        except Exception as e:
            self.tab._append_message("system", f"❌ 卸载失败: {str(e)}")
    
    def toggle(self):
        """切换启用/禁用"""
        if self.tab.lora_enabled_var.get():
            self.auto_load_default()
        else:
            self.unload()
    
    def auto_load_default(self):
        """自动加载默认 LoRA"""
        if not self.tab.app.model_manager.is_sd_loaded:
            self.tab._append_message("system", "⏳ 等待模型加载后自动加载 LoRA...")
            self.tab.app.root.after(3000, self.auto_load_default)
            return

        if not self.tab.lora_enabled_var.get():
            return

        lora_files = self.scan_files()
        if not lora_files:
            return

        default_lora = lora_files[0]
        lora_path = self.lora_paths.get(default_lora)

        if lora_path and os.path.exists(lora_path):
            self.tab._append_message("system", f"📦 自动加载 LoRA: {default_lora.replace('⭐ ', '')}")
            self.load_to_pipe(lora_path, default_lora)
    
    def on_selected(self, event=None):
        """选择事件"""
        selected = self.tab.lora_var.get()
        if not selected:
            return

        lora_path = self.lora_paths.get(selected)
        if not lora_path:
            self.tab._append_message("system", "❌ 找不到 LoRA 文件")
            return

        if not self.tab.app.model_manager.is_sd_loaded:
            self.tab._append_message("system", "⚠️ 请先加载模型")
            return

        self.load_to_pipe(lora_path, selected)
    
    def update_status(self):
        """更新状态显示"""
        if self.lora_loaded and self.current_lora_path:
            name = os.path.basename(self.current_lora_path)
            self.tab.lora_status_label.config(text=f"🟢 {name}", foreground="green")
        else:
            self.tab.lora_status_label.config(text="🔴 未加载", foreground="red")
    
    def refresh_list(self):
        """刷新列表"""
        lora_files = self.scan_files()
        self.tab.lora_combo['values'] = lora_files
        if lora_files and not self.tab.lora_var.get():
            self.tab.lora_var.set(lora_files[0])
        self.tab._append_message("system", f"🔄 LoRA 列表已刷新 ({len(lora_files)} 个)")