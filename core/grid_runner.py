# core/grid_runner.py
"""
网格测试运行器 - 支持 SD 和 Janus-Pro
"""

import os
import json
import time
import torch
from datetime import datetime
from diffusers import StableDiffusionPipeline
import gc
from PIL import Image
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    StableDiffusionInpaintPipeline,
    EulerDiscreteScheduler,
)

from utils.logger import get_logger

logger = get_logger(__name__)

class GridRunner:
    """网格测试运行器 - 支持 SD 和 Janus-Pro"""
    
    def __init__(self, app=None):
        self.app = app
        self.pipe = None
        self.model_type = None  # "sd" 或 "janus"
        self.is_running = False
        self.cancel = False
        self._loaded = False  # ✅ 标记是否已加载
        
    def load_config(self, config_path):
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    

    def load_model(self, model_path, model_type="sd"):
        """加载模型（如果 pipe 已注入则跳过）"""
        if self._loaded and self.pipe is not None:
            logger.info(f"✅ 使用已注入的 Pipeline")
            return self.pipe
        
        self.model_type = model_type
        
        if model_type == "janus":
            return self._load_janus_model()
        else:
            return self._load_sd_model(model_path)
    
    def _load_sd_model(self, model_path):
        """加载 SD 模型"""
        """加载 SD 模型（仅在没有注入时使用）"""
        if self.pipe is not None:
            return self.pipe
            
        if self.pipe is None:
            logger.info(f"📦 加载 SD 模型: {model_path}")
            self.pipe = StableDiffusionPipeline.from_single_file(
                model_path,
                torch_dtype=torch.float32,
            )
            self.pipe = self.pipe.to("cpu")
            self.pipe.enable_vae_slicing()
            self.pipe.enable_attention_slicing()
            
            # ✅ 使用 EulerDiscreteScheduler
            self.pipe.scheduler = EulerDiscreteScheduler.from_config(self.pipe.scheduler.config)
            logger.info(f"✅ 使用 EulerDiscreteScheduler (稳定调度器)")
        
            logger.info(f"✅ SD 模型加载完成")
        return self.pipe
    
    def _load_janus_model(self):
        """加载 Janus-Pro 模型"""
        from core.janus import janus_loader
        
        if not janus_loader.is_loaded():
            logger.info(f"📦 加载 Janus-Pro-1B 模型...")
            success = janus_loader.load(model_name="1B")
            if success:
                logger.info(f"✅ Janus-Pro 模型加载完成")
                self.pipe = janus_loader.get_model()  # 统一接口
                return self.pipe
            else:
                logger.info(f"❌ Janus-Pro 模型加载失败")
                return None
        else:
            logger.info(f"✅ Janus-Pro 模型已加载")
            self.pipe = janus_loader.get_model()
            return self.pipe
    
    def run_grid(self, config_path, progress_callback=None):
        """
        运行网格测试
        
        Args:
            config_path: 配置文件路径
            progress_callback: 进度回调函数 (current, total, name)
        """
        # 加载配置
        config = self.load_config(config_path)
        grid = config.get('grid', [])
        total = len(grid)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 网格测试: {config.get('name', '未命名')}")
        logger.info(f"   共 {total} 个组合")
        logger.info(f"   模型类型: {self.model_type}")
        logger.info(f"{'='*60}\n")
        
        # 加载模型
        model_path = config.get('model', None)
        model_type = config.get('model_type', 'sd')  # ✅ 从配置读取模型类型
        
        if model_type == "janus":
            self.load_model(None, "janus")
        else:
            self.load_model(model_path, "sd")
        
        # 创建输出目录
        output_dir = config.get('output_dir', './output/grid_tests')
        os.makedirs(output_dir, exist_ok=True)
        
        # 记录结果
        results = []
        self.is_running = True
        self.cancel = False
        
        for idx, item in enumerate(grid):
            if self.cancel:
                logger.info(f"⏹️ 已取消")
                break
            
            name = item.get('name', f'组合_{idx+1}')
            params = item.get('params', {})
            
            # 合并全局 prompt（如果没在 params 中单独指定）
            if 'prompt' not in params and 'prompt' in config:
                params['prompt'] = config['prompt']
            if 'negative' not in params and 'negative' in config:
                params['negative'] = config['negative']
            
            # 更新进度
            if progress_callback:
                progress_callback(idx + 1, total, name)
            
            logger.info(f"\n[{idx+1}/{total}] {name}")
            logger.info(f"  参数: {params}")
            
            try:
                # 生成图片
                result = self._generate_one(params, idx)
                
                if result:
                    # 保存图片
                    filename = f"{idx+1:03d}_{name.replace(' ', '_')}.png"
                    filepath = os.path.join(output_dir, filename)
                    result.save(filepath)
                    
                    results.append({
                        "name": name,
                        "params": params,
                        "file": filename,
                        "success": True,
                    })
                    logger.info(f"  ✅ 已保存: {filename}")
                else:
                    results.append({
                        "name": name,
                        "params": params,
                        "file": None,
                        "success": False,
                        "error": "生成失败",
                    })
                    logger.info(f"  ❌ 生成失败")
                    
            except Exception as e:
                logger.info(f"  ❌ 错误: {e}")
                results.append({
                    "name": name,
                    "params": params,
                    "file": None,
                    "success": False,
                    "error": str(e),
                })
            
            # 清理内存
            gc.collect()
        
        # 保存报告
        report_path = os.path.join(output_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "config": config,
                "model_type": self.model_type,
                "results": results,
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 报告已保存: {report_path}")
        logger.info(f"📁 图片目录: {output_dir}")
        
        self.is_running = False
        return results
    
    def _generate_one(self, params, seed_offset=0):
        """生成单张图片 - 自动判断模型类型"""
        if self.model_type == "janus":
            return self._generate_janus_one(params, seed_offset)
        else:
            return self._generate_sd_one(params, seed_offset)
    
    def _generate_sd_one(self, params, seed_offset=0):
        """SD 生成"""
        steps = params.get('steps', 25)
        cfg = params.get('cfg', 7.5)
        width = params.get('width', 512)
        height = params.get('height', 768)
        seed = params.get('seed', 42) + seed_offset
        hires = params.get('hires', False)
        
        prompt = params.get('prompt', 'masterpiece, best quality, photorealistic, 8k, a beautiful woman')
        negative = params.get('negative', 'worst quality, low quality, ugly, deformed, blurry')
        
        generator = torch.Generator("cpu").manual_seed(seed)
        
        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative,
            num_inference_steps=steps,
            guidance_scale=cfg,
            height=height,
            width=width,
            generator=generator,
        )
        
        image = result.images[0]
        
        # ===== 【新增】图片后期处理 =====
        from utils.image_post_processor import post_process_image
        
        # 需要获取 params_panel 的引用
        if hasattr(self, 'app') and self.app:
            params_panel = self.app.params_panel
            # 临时保存
            temp_path = f"temp_{seed_offset}.png"
            image.save(temp_path)
            
            final_path = post_process_image(
                temp_path,
                params_panel,
                prompt=prompt,
                log_prefix="[网格测试]"
            )
            
            # 加载处理后的图片
            if final_path != temp_path:
                os.remove(temp_path)
                image = Image.open(final_path)
                os.remove(final_path)
        
        return image
    
    def _generate_janus_one(self, params, seed_offset=0):
        """Janus-Pro 生成"""
        from core.janus import janus_generate
        
        prompt = params.get('prompt', 'masterpiece, best quality, a beautiful woman')
        negative = params.get('negative', '')
        temperature = params.get('temperature', 0.8)
        max_tokens = params.get('max_tokens', 2048)
        seed = params.get('seed', 42) + seed_offset
        
        image, metadata = janus_generate.generate(
            prompt=prompt,
            negative_prompt=negative,
            temperature=temperature,
            max_new_tokens=max_tokens,
            seed=seed
        )
        
        return image
    
    def cancel_run(self):
        """取消运行"""
        self.cancel = True


# 兼容旧代码的别名
GridRunner = GridRunner