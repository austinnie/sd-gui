# utils/performance.py
"""
性能优化工具
"""

import time
import functools
import threading
from typing import Callable, Any, Dict, List
from collections import defaultdict
from utils.logger import get_logger

logger = get_logger(__name__)


def timer(func: Callable) -> Callable:
    """装饰器：测量函数执行时间"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        if elapsed > 1.0:
            logger.info(f"⏱️ {func.__name__} 耗时: {elapsed:.2f}s")
        elif elapsed > 0.1:
            logger.debug(f"⏱️ {func.__name__} 耗时: {elapsed:.3f}s")
        return result
    return wrapper


def async_task(func: Callable) -> Callable:
    """装饰器：异步执行任务"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread
    return wrapper


class PerformanceMonitor:
    """性能监控器 - 单例"""
    
    _instance = None
    _timings: Dict[str, List[float]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._timings = defaultdict(list)
        return cls._instance
    
    def record(self, name: str, elapsed: float):
        """记录耗时"""
        self._timings[name].append(elapsed)
        if len(self._timings[name]) > 1000:
            self._timings[name] = self._timings[name][-500:]
    
    def get_stats(self, name: str) -> dict:
        """获取统计信息"""
        timings = self._timings.get(name, [])
        if not timings:
            return {}
        return {
            "count": len(timings),
            "avg": sum(timings) / len(timings),
            "min": min(timings),
            "max": max(timings),
            "p95": sorted(timings)[int(len(timings) * 0.95)] if len(timings) > 20 else timings[-1],
        }
    
    def report(self):
        """打印报告"""
        logger.info("=" * 50)
        logger.info("📊 性能报告")
        for name, timings in sorted(self._timings.items()):
            if timings:
                avg = sum(timings) / len(timings)
                logger.info(f"   {name}: avg={avg:.3f}s, count={len(timings)}")
        logger.info("=" * 50)


perf_monitor = PerformanceMonitor()


# 启动计时
_start_time = None

def start_timer():
    """开始计时"""
    global _start_time
    _start_time = time.perf_counter()

def get_elapsed() -> float:
    """获取经过时间"""
    if _start_time is None:
        return 0
    return time.perf_counter() - _start_time

def log_startup(msg: str):
    """记录启动信息"""
    elapsed = get_elapsed()
    logger.info(f"⏱️ [{elapsed:.2f}s] {msg}")