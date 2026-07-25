# utils/image_cache.py
"""
图片缓存 - 避免重复加载
"""

from PIL import Image
from typing import Dict, Optional, Tuple
from collections import OrderedDict
import hashlib
import os
from utils.logger import get_logger

logger = get_logger(__name__)


class ImageCache:
    """图片缓存 - LRU 策略"""
    
    _instance = None
    _cache: OrderedDict = OrderedDict()
    _max_size: int = 50
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = OrderedDict()
        return cls._instance
    
    def _get_key(self, image_path: str, size: Optional[Tuple[int, int]] = None) -> str:
        """生成缓存键"""
        key = image_path
        if size:
            key = f"{image_path}_{size[0]}x{size[1]}"
        return key
    
    def get(self, image_path: str, size: Optional[Tuple[int, int]] = None) -> Optional[Image.Image]:
        """获取缓存的图片"""
        key = self._get_key(image_path, size)
        if key in self._cache:
            self._cache.move_to_end(key)
            logger.debug(f"📦 缓存命中: {os.path.basename(image_path)}")
            return self._cache[key].copy()
        return None
    
    def put(self, image_path: str, image: Image.Image, size: Optional[Tuple[int, int]] = None):
        """缓存图片"""
        key = self._get_key(image_path, size)
        
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache[key] = image.copy()
            return
        
        if len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"🗑️ 缓存溢出: {oldest_key}")
        
        self._cache[key] = image.copy()
        logger.debug(f"💾 缓存: {os.path.basename(image_path)}")
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("🗑️ 图片缓存已清空")
    
    def get_stats(self) -> dict:
        """获取缓存统计"""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "keys": list(self._cache.keys())[:10],
        }


image_cache = ImageCache()