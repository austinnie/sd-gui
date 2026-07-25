# gui/tabs/interrogate/backends/base.py
"""反推后端基类"""

from abc import ABC, abstractmethod


class InterrogateBackend(ABC):
    """反推后端基类"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
    
    @abstractmethod
    def interrogate(self, image_path: str, **kwargs) -> str:
        """执行反推"""
        pass
    
    def get_name(self) -> str:
        """后端名称"""
        return self.__class__.__name__