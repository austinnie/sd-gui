# core/janus/loader.py
"""
Janus-Pro 模型加载器 - 使用独立配置
"""

import os
import sys
import torch
import time
from typing import Optional
from config.janus_config import janus_config


class JanusLoader:
    """Janus-Pro 模型加载器（单例）"""
    
    _instance = None
    _model = None
    _processor = None
    _tokenizer = None
    _loaded = False
    _current_model_name = None
    _loading = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _log(self, msg: str):
        from datetime import datetime
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    
    def load(self, model_name: str = "1B", progress_callback=None) -> bool:
        """加载模型"""
        if self._loading:
            self._log("⏳ 正在加载中...")
            return False
        
        if self._loaded and self._current_model_name == model_name:
            self._log(f"✅ 模型已加载 ({model_name})")
            if progress_callback:
                progress_callback(1.0, "✅ 已加载")
            return True
        
        self._loading = True
        
        if model_name == "1B":
            model_path = janus_config.janus.get_resolved_1b_path()
        else:
            model_path = janus_config.janus.get_resolved_7b_path()
        
        if not os.path.exists(model_path):
            self._log(f"❌ 模型路径不存在: {model_path}")
            self._loading = False
            return False
        
        try:
            if progress_callback:
                progress_callback(0.1, "📦 准备加载...")
            
            self._log(f"📦 加载 Janus-Pro-{model_name}")
            self._log(f"   路径: {model_path}")
            
            if model_path not in sys.path:
                sys.path.insert(0, model_path)
            
            janus_path = os.path.join(model_path, "janus")
            if os.path.exists(janus_path) and janus_path not in sys.path:
                sys.path.insert(0, janus_path)
            
            from janus.models import VLChatProcessor
            from transformers import AutoModelForCausalLM
            
            if progress_callback:
                progress_callback(0.3, "📋 加载处理器...")
            
            self._processor = VLChatProcessor.from_pretrained(model_path)
            self._tokenizer = self._processor.tokenizer
            
            if progress_callback:
                progress_callback(0.5, "🧠 加载模型权重...")
            
            dtype = torch.bfloat16
            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=dtype,
                low_cpu_mem_usage=True
            ).to("cpu").eval()
            
            self._loaded = True
            self._current_model_name = model_name
            self._loading = False
            
            self._log(f"✅ 模型加载完成")
            if progress_callback:
                progress_callback(1.0, "✅ 加载完成")
            
            return True
            
        except Exception as e:
            self._log(f"❌ 加载失败: {e}")
            import traceback
            traceback.print_exc()
            self._loading = False
            return False
    
    def unload(self):
        """卸载模型"""
        if self._model is not None:
            del self._model
            self._model = None
        if self._processor is not None:
            del self._processor
            self._processor = None
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        self._loaded = False
        self._current_model_name = None
        import gc
        gc.collect()
        self._log("✅ 模型已卸载")
    
    def is_loaded(self) -> bool:
        return self._loaded
    
    def is_loading(self) -> bool:
        return self._loading
    
    def get_model(self):
        return self._model
    
    def get_processor(self):
        return self._processor
    
    def get_tokenizer(self):
        return self._tokenizer
    
    def get_current_model(self) -> str:
        return self._current_model_name or "未加载"
    
    def get_device(self) -> str:
        return "cpu"


# 全局实例
janus_loader = JanusLoader()# core/janus/loader.py
"""
Janus-Pro 模型加载器 - 使用独立配置
"""

import os
import sys
import torch
import time
from typing import Optional
from config.janus_config import janus_config


class JanusLoader:
    """Janus-Pro 模型加载器（单例）"""
    
    _instance = None
    _model = None
    _processor = None
    _tokenizer = None
    _loaded = False
    _current_model_name = None
    _loading = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _log(self, msg: str):
        from datetime import datetime
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    
    def load(self, model_name: str = "1B", progress_callback=None) -> bool:
        """加载模型"""
        if self._loading:
            self._log("⏳ 正在加载中...")
            return False
        
        if self._loaded and self._current_model_name == model_name:
            self._log(f"✅ 模型已加载 ({model_name})")
            if progress_callback:
                progress_callback(1.0, "✅ 已加载")
            return True
        
        self._loading = True
        
        if model_name == "1B":
            model_path = janus_config.janus.get_resolved_1b_path()
        else:
            model_path = janus_config.janus.get_resolved_7b_path()
        
        if not os.path.exists(model_path):
            self._log(f"❌ 模型路径不存在: {model_path}")
            self._loading = False
            return False
        
        try:
            if progress_callback:
                progress_callback(0.1, "📦 准备加载...")
            
            self._log(f"📦 加载 Janus-Pro-{model_name}")
            self._log(f"   路径: {model_path}")
            
            if model_path not in sys.path:
                sys.path.insert(0, model_path)
            
            janus_path = os.path.join(model_path, "janus")
            if os.path.exists(janus_path) and janus_path not in sys.path:
                sys.path.insert(0, janus_path)
            
            from janus.models import VLChatProcessor
            from transformers import AutoModelForCausalLM
            
            if progress_callback:
                progress_callback(0.3, "📋 加载处理器...")
            
            self._processor = VLChatProcessor.from_pretrained(model_path)
            self._tokenizer = self._processor.tokenizer
            
            if progress_callback:
                progress_callback(0.5, "🧠 加载模型权重...")
            
            dtype = torch.bfloat16
            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=dtype,
                low_cpu_mem_usage=True
            ).to("cpu").eval()
            
            self._loaded = True
            self._current_model_name = model_name
            self._loading = False
            
            self._log(f"✅ 模型加载完成")
            if progress_callback:
                progress_callback(1.0, "✅ 加载完成")
            
            return True
            
        except Exception as e:
            self._log(f"❌ 加载失败: {e}")
            import traceback
            traceback.print_exc()
            self._loading = False
            return False
    
    def unload(self):
        """卸载模型"""
        if self._model is not None:
            del self._model
            self._model = None
        if self._processor is not None:
            del self._processor
            self._processor = None
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        self._loaded = False
        self._current_model_name = None
        import gc
        gc.collect()
        self._log("✅ 模型已卸载")
    
    def is_loaded(self) -> bool:
        return self._loaded
    
    def is_loading(self) -> bool:
        return self._loading
    
    def get_model(self):
        return self._model
    
    def get_processor(self):
        return self._processor
    
    def get_tokenizer(self):
        return self._tokenizer
    
    def get_current_model(self) -> str:
        return self._current_model_name or "未加载"
    
    def get_device(self) -> str:
        return "cpu"


# 全局实例
janus_loader = JanusLoader()