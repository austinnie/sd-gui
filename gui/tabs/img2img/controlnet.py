# gui/tabs/img2img/controlnet.py
"""ControlNet 处理"""

from utils.controlnet import controlnet_config


class ControlNetHandler:
    """ControlNet 处理器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
    
    def toggle(self):
        """切换 ControlNet"""
        enabled = self.tab.use_controlnet_var.get()
        controlnet_config.set_enabled(enabled)
    
    def get_combo_info(self):
        """获取当前 ControlNet 组合信息"""
        from utils.controlnet import get_recommended_multi_controlnet_combos
        
        combos = get_recommended_multi_controlnet_combos()
        selected = self.tab.controlnet_combo_var.get()
        return combos.get(selected, {})
    
    def get_types_and_scales(self):
        """获取 ControlNet 类型和权重"""
        info = self.get_combo_info()
        return info.get("types", []), info.get("scales", [])