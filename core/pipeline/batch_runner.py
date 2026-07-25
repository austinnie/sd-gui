# core/pipeline/batch_runner.py
"""批量流水线运行器 - 从 pipeline_tab.py 移出"""

import os
import gc
from datetime import datetime
from pathlib import Path
from PIL import Image
from typing import Optional, Callable, List

from core.pipeline import PipelineRegistry, StepContext
from core.pipeline.runner import PipelineRunner


class BatchPipelineRunner:
    """批量流水线运行器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.runner = PipelineRunner(tab)
    
    def run(self, images: List[str], dir_path: str, pipeline_config: dict,
            progress_callback: Optional[Callable] = None,
            cancel_flag: Optional[Callable] = None,
            skip_existing: bool = True,
            task_id: str = None) -> dict:
        """
        批量运行流水线
        
        参数:
            images: 图片路径列表
            dir_path: 图片目录路径
            pipeline_config: 流水线配置
            progress_callback: 进度回调
            cancel_flag: 取消标志
            skip_existing: 是否跳过已存在的
            task_id: 任务ID
        
        返回:
            运行结果
        """
        if task_id is None:
            task_id = f"batch_pipeline_{datetime.now().strftime('%H%M%S')}"
        
        total = len(images)
        success_count = 0
        skipped_count = 0
        failed_count = 0
        results = []
        
        for idx, image_path in enumerate(images):
            # ✅ 检查取消
            if cancel_flag and cancel_flag():
                break
            
            # 检查是否跳过已存在的图片
            if skip_existing:
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                output_dir = f"./output/pipeline_batch_{base_name}"
                if os.path.exists(output_dir):
                    existing = [f for f in os.listdir(output_dir) if f.endswith('.png')]
                    if existing:
                        skipped_count += 1
                        if progress_callback:
                            progress_callback(idx + 1, total, f"⏭️ 跳过 {os.path.basename(image_path)}")
                        continue
            
            if progress_callback:
                progress_callback(idx + 1, total, f"🎨 处理 {os.path.basename(image_path)}")
            
            # 创建输出目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_dir = f"./output/pipeline_batch_{base_name}_{timestamp}"
            os.makedirs(output_dir, exist_ok=True)
            
            try:
                # 运行单个流水线
                # ✅ 传递取消标志到单个运行
                result = self.runner.run(
                    image_path=image_path,
                    pipeline_config=pipeline_config,
                    output_dir=output_dir,
                    cancel_flag=cancel_flag,
                    task_id=f"{task_id}_{idx}"
                )

                if result.get("cancelled"):
                    # ✅ 如果被取消，停止批量
                    failed_count += 1
                    results.append(result)
                    break
                    
                if result.get("success"):
                    success_count += 1
                else:
                    failed_count += 1
                
                results.append(result)
                
            except Exception as e:
                failed_count += 1
                results.append({"success": False, "error": str(e)})
            
            gc.collect()
        
        return {
            "success": True,
            "total": total,
            "success_count": success_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "results": results,
            "task_id": task_id,
            "cancelled": cancel_flag and cancel_flag()
        }
    
    def _get_images(self, directory: str) -> List[str]:
        """获取目录下所有图片"""
        extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
        images = []
        for f in os.listdir(directory):
            if Path(f).suffix.lower() in extensions:
                images.append(os.path.join(directory, f))
        return sorted(images)