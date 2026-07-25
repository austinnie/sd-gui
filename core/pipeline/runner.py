# core/pipeline/runner.py
"""流水线运行器 - 从 pipeline_tab.py 移出"""

import os
from datetime import datetime
from PIL import Image
from typing import Optional, Callable

from core.pipeline import PipelineRegistry, StepContext
from utils.pipeline_pool import pipeline_pool
from utils.image_post_processor import post_process_image


from utils.logger import get_logger

logger = get_logger(__name__)
class PipelineRunner:
    """流水线运行器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
    
    def run(self, image_path: str, pipeline_config: dict, output_dir: str,
            progress_callback: Optional[Callable] = None,
            cancel_flag: Optional[Callable] = None,
            task_id: str = None) -> dict:
        """
        运行流水线
        
        参数:
            image_path: 输入图片路径
            pipeline_config: 流水线配置
            output_dir: 输出目录
            progress_callback: 进度回调 (current, total, msg)
            cancel_flag: 取消标志
            task_id: 任务ID
        
        返回:
            运行结果
        """
        if task_id is None:
            task_id = f"pipeline_{datetime.now().strftime('%H%M%S')}"
        
        # 获取模型和 LoRA
        model_name = self.app.model_var.get()
        model_path = self.app._get_model_path(model_name)
        
        lora_path = None
        lora_weight = 1.0
        if hasattr(self.app, 'lora_var') and hasattr(self.app, 'lora_paths'):
            lora_display = self.app.lora_var.get()
            if lora_display:
                lora_path = self.app.lora_paths.get(lora_display)
                lora_weight = self.app.lora_weight_var.get() if hasattr(self.app, 'lora_weight_var') else 1.0
        
        # 获取 pipeline
        pipe, is_new = pipeline_pool.get_pipeline(
            model_path=model_path,
            model_name=os.path.basename(model_path),
            lora_path=lora_path,
            lora_weight=lora_weight,
            task_id=task_id
        )
        
        if pipe is None:
            return {"success": False, "error": "无法获取 Pipeline"}
        
        try:
            # 检查是否启用 ControlNet
            use_controlnet = False
            controlnet_pipe = None
            controlnet_type = "openpose"
            
            if hasattr(self.app, 'img2img_tab') and hasattr(self.app.img2img_tab, 'use_controlnet_var'):
                use_controlnet = self.app.img2img_tab.use_controlnet_var.get()
                if use_controlnet and hasattr(self.app.img2img_tab, 'controlnet_type_var'):
                    selected_type = self.app.img2img_tab.controlnet_type_var.get()
                    controlnet_type = selected_type.split(" ")[0] if " " in selected_type else "openpose"
            
            # 加载 ControlNet
            if use_controlnet:
                controlnet_pipe = self._setup_controlnet(pipe, controlnet_type)
                if controlnet_pipe:
                    logger.info(f"🧠 ControlNet 已加载: {controlnet_type}")
                    pipe = controlnet_pipe
            
            # 创建流水线
            pipeline = PipelineRegistry.create_pipeline_from_config(pipeline_config)
            
            def on_progress(current, total, msg):
                if progress_callback:
                    progress_callback(current, total, msg)
                if cancel_flag and cancel_flag():
                    raise Exception("用户取消")
            
            pipeline.set_progress_callback(on_progress)
            
            # 加载图片
            image = Image.open(image_path).convert('RGB')
            
            # 创建上下文 - ✅ 传递取消标志
            context = StepContext(
                input_image=image,
                input_path=image_path,
                output_dir=output_dir,
                global_config={
                    "model_path": model_path,
                    "pipe": pipe,
                    "lora_path": lora_path,
                    "lora_weight": lora_weight,
                    "use_controlnet": use_controlnet,
                    "controlnet_pipe": controlnet_pipe,
                    "controlnet_type": controlnet_type,
                    "cancel_flag": cancel_flag,  # ✅ 传递到 global_config
                },
                cancel_flag=cancel_flag  # ✅ 直接传递
            )
            
            # 运行流水线
            results = pipeline.run(context)
            
            # 检查是否被取消
            if context.is_cancelled():
                return {
                    "success": False,
                    "error": "用户取消",
                    "results": results,
                    "output_dir": output_dir,
                    "cancelled": True
                }
            
            # 后处理
            self._post_process_results(results)
            
            return {
                "success": True,
                "results": results,
                "output_dir": output_dir
            }
            
        except Exception as e:
            error_msg = str(e)
            if "用户取消" in error_msg or "cancelled" in error_msg.lower():
                return {
                    "success": False,
                    "error": "用户取消",
                    "output_dir": output_dir,
                    "cancelled": True
                }
            return {"success": False, "error": error_msg}
        finally:
            pipeline_pool.release_pipeline(model_path, lora_path, task_id)
    
    def _setup_controlnet(self, pipe, controlnet_type: str):
        """设置 ControlNet"""
        try:
            from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
            from utils.controlnet import get_controlnet_info
            
            info = get_controlnet_info(controlnet_type)
            logger.info(f"📦 加载 ControlNet: {info['name']}")
            
            controlnet = ControlNetModel.from_pretrained(
                info["model_id"],
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            
            controlnet_pipe = StableDiffusionControlNetPipeline(
                vae=pipe.vae,
                text_encoder=pipe.text_encoder,
                tokenizer=pipe.tokenizer,
                unet=pipe.unet,
                controlnet=controlnet,
                scheduler=pipe.scheduler,
                safety_checker=None,
                requires_safety_checker=False,
            )
            controlnet_pipe.to("cpu")
            controlnet_pipe.enable_vae_slicing()
            controlnet_pipe.enable_attention_slicing()
            
            return controlnet_pipe
            
        except Exception as e:
            logger.info(f"⚠️ ControlNet 加载失败: {e}")
            return None
    
    # core/pipeline/runner.py
    def _post_process_results(self, results: dict):
        """对结果进行后处理 - 支持水印去除 + 元数据清理 + EXIF注入 + 照片真实化"""
        from utils.image_post_processor import post_process_image
        from utils.watermark_remover import WatermarkRemover
        from PIL import Image
        import os
        
        for name, result in results.items():
            if result.success and result.output_path and os.path.exists(result.output_path):
                try:
                    # ===== 1. 水印去除（在后期处理之前） =====
                    if self.app.params_panel.remove_watermark_var.get():
                        try:
                            remover = WatermarkRemover()
                            img = Image.open(result.output_path)
                            
                            # 确定使用的方法
                            methods = ["opencv_inpaint", "opencv_blur"]
                            strength = self.app.params_panel.watermark_strength_var.get()
                            auto_detect = self.app.params_panel.watermark_auto_detect_var.get()
                            
                            cleaned = remover.remove_watermark(
                                img,
                                methods=methods,
                                strength=strength,
                                auto_detect=auto_detect
                            )
                            cleaned.save(result.output_path, quality=95)
                            logger.info(f"   🚫 [{name}] 水印已去除")
                        except Exception as e:
                            logger.info(f"   ⚠️ [{name}] 水印去除失败: {e}")
                    
                    # ===== 2. 图片后期处理（元数据清理 + EXIF注入 + 照片真实化） =====
                    final_path = post_process_image(
                        result.output_path,
                        self.app.params_panel,
                        log_prefix=f"[流水线-{name}]"
                    )
                    
                    if final_path != result.output_path:
                        try:
                            os.remove(result.output_path)
                        except:
                            pass
                        result.output_path = final_path
                        
                except Exception as e:
                    logger.info(f"⚠️ {name}: 后期处理失败 - {e}")