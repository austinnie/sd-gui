# gui/chat/controlnet_manager.py
"""ControlNet 管理器"""

import os
from datetime import datetime


from utils.logger import get_logger

logger = get_logger(__name__)
class ControlNetManager:
    """ControlNet 管理器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.is_available = False
        self.pipe = None
        self.controlnet_enabled = False
    
    def toggle(self):
        """开关切换"""
        enabled = self.tab.use_controlnet_var.get()
        self.controlnet_enabled = enabled
        
        if enabled:
            self.tab.controlnet_status_label.config(text="🟢 已启用", foreground="green")
            if not self.is_available:
                self.setup()
        else:
            self.tab.controlnet_status_label.config(text="⚪ 已禁用", foreground="gray")
            if self.pipe:
                del self.pipe
                self.pipe = None
                self.is_available = False
    
    def on_type_changed(self, event):
        """类型切换"""
        from utils.controlnet import get_controlnet_info
        
        selected = self.tab.controlnet_type_var.get()
        key = selected.split(" ")[0] if " " in selected else selected
        info = get_controlnet_info(key)
        self.tab.controlnet_status_label.config(text=f"💡 {info['description']}", foreground="blue")
        
        if self.controlnet_enabled:
            self.setup()
    
    def setup(self):
        """加载 ControlNet"""
        if not self.controlnet_enabled:
            return

        if self.is_available:
            return

        try:
            from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
            from utils.controlnet import get_controlnet_info
            from utils.pipeline_pool import pipeline_pool

            selected = self.tab.controlnet_type_var.get()
            controlnet_type = selected.split(" ")[0] if " " in selected else "openpose"
            info = get_controlnet_info(controlnet_type)

            logger.info(f"📦 正在加载 ControlNet: {info['name']}...")

            controlnet = ControlNetModel.from_pretrained(
                info["model_id"],
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True,
                cache_dir=os.environ.get("HF_HOME", r"E:\hf_cache\.cache")
            )

            model_name = self.tab.app.model_var.get() if hasattr(self.tab.app, 'model_var') else None
            if not model_name:
                self.is_available = False
                return

            model_path = self.tab.app._get_model_path(model_name)
            if not model_path:
                self.is_available = False
                return

            lora_path = self.tab.lora_manager.current_lora_path if self.tab.lora_manager.lora_loaded else None

            task_id = f"chat_controlnet_{datetime.now().strftime('%H%M%S')}"
            pipe, _ = pipeline_pool.get_pipeline(
                model_path=model_path,
                model_name=model_name,
                lora_path=lora_path,
                lora_weight=1.0,
                task_id=task_id
            )

            if pipe:
                self.pipe = StableDiffusionControlNetPipeline(
                    vae=pipe.vae,
                    text_encoder=pipe.text_encoder,
                    tokenizer=pipe.tokenizer,
                    unet=pipe.unet,
                    controlnet=controlnet,
                    scheduler=pipe.scheduler,
                    safety_checker=None,
                    feature_extractor=None,
                    requires_safety_checker=False,
                )
                self.pipe.to("cpu")
                self.pipe.enable_vae_slicing()
                self.pipe.enable_attention_slicing()
                self.is_available = True
                self.tab.controlnet_status_label.config(text=f"✅ {info['name']} 就绪", foreground="green")
                logger.info(f"✅ ControlNet 已加载: {info['name']}")

        except Exception as e:
            logger.info(f"⚠️ ControlNet 加载失败: {e}")
            self.is_available = False
            self.tab.controlnet_status_label.config(text="❌ 加载失败", foreground="red")
    
    def is_cached(self) -> bool:
        """检查是否已缓存"""
        cache_dir = os.environ.get("HF_HOME", r"E:\hf_cache\.cache")
        model_path = os.path.join(cache_dir, "hub", "models--lllyasviel--sd-controlnet-openpose")
        return os.path.exists(model_path)
    
    def get_cache_size(self) -> str:
        """获取缓存大小"""
        cache_dir = os.environ.get("HF_HOME", r"E:\hf_cache\.cache")
        if not os.path.exists(cache_dir):
            return "未缓存"

        total_size = 0
        for dirpath, _, filenames in os.walk(cache_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)

        if total_size > 1024**3:
            return f"{total_size / 1024**3:.1f} GB"
        elif total_size > 1024**2:
            return f"{total_size / 1024**2:.1f} MB"
        else:
            return f"{total_size / 1024:.1f} KB"