# utils/batch_processor.py
"""
批量图片处理器 - 分批次处理，避免内存爆炸
"""

import gc
import time
from typing import List, Callable, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class BatchProcessor:
    """
    批量处理器 - 分批处理大量任务
    
    使用示例:
        processor = BatchProcessor(batch_size=4)
        results = processor.process(
            items=image_list,
            process_fn=generate_image,
            on_progress=progress_callback
        )
    """
    
    def __init__(self, batch_size: int = 4, delay: float = 0.5):
        """
        初始化
        
        参数:
            batch_size: 每批处理数量
            delay: 批次间延迟 (秒)
        """
        self.batch_size = batch_size
        self.delay = delay
        self.cancel = False
    
    def process(
        self,
        items: List,
        process_fn: Callable,
        on_progress: Optional[Callable] = None,
        on_batch_complete: Optional[Callable] = None,
    ) -> List:
        """
        分批处理
        
        参数:
            items: 要处理的项目列表
            process_fn: 处理函数
            on_progress: 进度回调 (current, total)
            on_batch_complete: 批次完成回调 (batch_results)
        
        返回:
            所有结果列表
        """
        total = len(items)
        results = []
        
        for i in range(0, total, self.batch_size):
            if self.cancel:
                logger.info("⏹️ 批量处理已取消")
                break
            
            batch = items[i:i + self.batch_size]
            batch_results = []
            
            for idx, item in enumerate(batch):
                if self.cancel:
                    break
                
                try:
                    result = process_fn(item)
                    batch_results.append(result)
                except Exception as e:
                    logger.error(f"❌ 处理失败: {e}")
                    batch_results.append(None)
                
                # 更新进度
                if on_progress:
                    on_progress(i + idx + 1, total)
            
            results.extend(batch_results)
            
            # 清理内存
            gc.collect()
            
            # 批次完成回调
            if on_batch_complete:
                on_batch_complete(batch_results)
            
            # 批次间延迟
            if i + self.batch_size < total:
                time.sleep(self.delay)
        
        return results
    
    def cancel_processing(self):
        """取消处理"""
        self.cancel = True
        logger.info("⏹️ 取消批量处理")