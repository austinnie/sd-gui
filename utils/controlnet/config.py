# utils/controlnet/config.py
"""
ControlNet 全局配置
"""

# 全局配置
CONTROLNET_CONFIG = {
    "max_size": 512,        # 最大尺寸（CPU 模式推荐 512）
}

# 预处理模式
# 可选值: "pil", "skeleton", "np", "auto"
CONTROLNET_PREPROCESS_MODE = "skeleton"


class ControlNetConfig:
    """全局 ControlNet 配置"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.enabled = False
        self.type = "openpose"
        self.strength = 0.8
        self._listeners = []
    
    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        self._notify()
    
    def set_type(self, controlnet_type: str):
        self.type = controlnet_type
        self._notify()
    
    def add_listener(self, callback):
        self._listeners.append(callback)
    
    def _notify(self):
        for cb in self._listeners:
            try:
                cb(self.enabled, self.type)
            except:
                pass


# 全局实例
controlnet_config = ControlNetConfig()