# gui/tabs/lora_manager/test_runner.py
"""LoRA 批量测试运行器"""

import os
import gc
import json
import random
import time
import torch
from datetime import datetime
from PIL import Image, ImageDraw
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, EulerDiscreteScheduler

from .utils import load_run_log, save_run_log


class LoraTestRunner:
    """LoRA 批量测试运行器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.cancel_operation = False
    
    def run_tests(self, lora_files: list, config: dict, progress_callback=None) -> dict:
        """运行批量测试"""
        from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, EulerDiscreteScheduler
        
        output_dir = config.get('output_dir', './output/lora_previews')
        os.makedirs(output_dir, exist_ok=True)
        
        run_log_path = os.path.join(output_dir, "run_log.json")
        if config.get('re_run', False):
            run_log = {}
            self.tab._append_test_log("💥 强制重跑模式")
        else:
            run_log = load_run_log(run_log_path)
        
        # ✅ 从 config 获取模型类型
        model_type = config.get('model_type', 'both')
        total = len(lora_files)
        if model_type == 'both':
            total *= 2
        
        pipe_sd15 = None
        pipe_sdxl = None
        processed = 0
        results = []
        
        try:
            # SD 1.5 阶段
            if model_type in ['sd15', 'both']:
                sd15_model = config.get('sd15_model_path')
                if sd15_model and os.path.exists(sd15_model):
                    self.tab._append_test_log(f"📦 加载 SD 1.5: {os.path.basename(sd15_model)}")
                    pipe_sd15 = StableDiffusionPipeline.from_single_file(
                        sd15_model,
                        torch_dtype=torch.float32,
                        safety_checker=None,
                        requires_safety_checker=False,
                        use_safetensors=True,
                        low_cpu_mem_usage=True
                    )
                    pipe_sd15.to("cpu")
                    pipe_sd15.enable_vae_slicing()
                    pipe_sd15.enable_attention_slicing()
                    pipe_sd15.scheduler = EulerDiscreteScheduler.from_config(pipe_sd15.scheduler.config)
                    self.tab._append_test_log("✅ SD 1.5 加载完成")
                    
                    for idx, lora_info in enumerate(lora_files):
                        if self.cancel_operation:
                            break
                        result = self._test_single_lora(
                            pipe_sd15, lora_info, output_dir,
                            is_sdxl=False, run_log=run_log,
                            idx=idx, total=len(lora_files),
                            config=config
                        )
                        results.append(result)
                        processed += 1
                        if progress_callback:
                            progress_callback(processed / total, f"SD1.5 {idx+1}/{len(lora_files)}")
                    
                    del pipe_sd15
                    gc.collect()
                    self.tab._append_test_log("🗑️ SD 1.5 已卸载")
            
            # SDXL 阶段
            if model_type in ['sdxl', 'both'] and not self.cancel_operation:
                sdxl_model = config.get('sdxl_model_path')
                if sdxl_model and os.path.exists(sdxl_model):
                    self.tab._append_test_log(f"📦 加载 SDXL: {os.path.basename(sdxl_model)}")
                    pipe_sdxl = StableDiffusionXLPipeline.from_single_file(
                        sdxl_model,
                        torch_dtype=torch.float32,
                        safety_checker=None,
                        requires_safety_checker=False,
                        use_safetensors=True,
                        low_cpu_mem_usage=True
                    )
                    pipe_sdxl.to("cpu")
                    pipe_sdxl.enable_vae_slicing()
                    pipe_sdxl.enable_attention_slicing()
                    pipe_sdxl.scheduler = EulerDiscreteScheduler.from_config(pipe_sdxl.scheduler.config)
                    self.tab._append_test_log("✅ SDXL 加载完成")
                    
                    for idx, lora_info in enumerate(lora_files):
                        if self.cancel_operation:
                            break
                        result = self._test_single_lora(
                            pipe_sdxl, lora_info, output_dir,
                            is_sdxl=True, run_log=run_log,
                            idx=idx, total=len(lora_files),
                            config=config
                        )
                        results.append(result)
                        processed += 1
                        if progress_callback:
                            progress_callback(processed / total, f"SDXL {idx+1}/{len(lora_files)}")
                    
                    del pipe_sdxl
                    gc.collect()
                    self.tab._append_test_log("🗑️ SDXL 已卸载")
            
            # 生成对比图
            if not self.cancel_operation and model_type == 'both':
                self.tab._append_test_log("🔄 生成对比图...")
                self._generate_comparison_images(lora_files, output_dir)
            
            save_run_log(run_log_path, run_log)
            
            if self.cancel_operation:
                self.tab._append_test_log("⏹️ 测试已取消")
            else:
                self.tab._append_test_log(f"✅ 测试完成！共处理 {processed} 个任务")
            
            return {'total': processed, 'results': results}
            
        except Exception as e:
            self.tab._append_test_log(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return {'total': 0, 'results': [], 'error': str(e)}
    
    def _test_single_lora(self, pipe, lora_info: dict, output_dir: str, is_sdxl: bool,
                          run_log: dict, idx: int, total: int, config: dict) -> dict:
        """测试单个 LoRA"""
        lora_name = lora_info["name"]
        lora_code = lora_name.replace('.safetensors', '')
        
        # 构建提示词
        if is_sdxl:
            base_prompt = config.get('sdxl_prompt', '').replace("NAME", lora_code)
            base_negative = config.get('sdxl_negative', '')
            steps = config.get('sdxl_steps', 20)
            size_str = config.get('sdxl_size', '1024x1024')
        else:
            base_prompt = config.get('sd15_prompt', '').replace("NAME", lora_code)
            base_negative = config.get('sd15_negative', '')
            steps = config.get('sd15_steps', 12)
            size_str = config.get('sd15_size', '512x768')
        
        # 解析尺寸
        try:
            w, h = map(int, size_str.split('x'))
        except:
            w, h = 512, 768
        
        lora_dir = os.path.join(output_dir, lora_code)
        os.makedirs(lora_dir, exist_ok=True)
        
        stage_key_base = "sdxl" if is_sdxl else "sd15"
        out_path = os.path.join(lora_dir, f"{stage_key_base.upper()}.png")
        
        # 检查是否跳过
        if not config.get('re_run', False):
            if run_log.get(lora_name, {}).get(stage_key_base, False):
                return {'name': lora_name, 'skipped': True}
            if os.path.exists(out_path):
                if lora_name not in run_log:
                    run_log[lora_name] = {}
                run_log[lora_name][stage_key_base] = True
                return {'name': lora_name, 'skipped': True}
        
        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            generator = torch.Generator("cpu").manual_seed(42)
            result = pipe(
                prompt=base_prompt,
                negative_prompt=base_negative,
                num_inference_steps=steps,
                guidance_scale=7.5,
                height=h,
                width=w,
                generator=generator,
                num_images_per_prompt=1
            )
            result.images[0].save(out_path)
            
            if lora_name not in run_log:
                run_log[lora_name] = {}
            run_log[lora_name][stage_key_base] = True
            
            self.tab._append_test_log(f"   ✅ [{idx+1}/{total}] 已保存: {os.path.basename(out_path)}")
            
            return {'name': lora_name, 'success': True, 'path': out_path}
            
        except Exception as e:
            self.tab._append_test_log(f"   ❌ [{idx+1}/{total}] 生成失败: {e}")
            return {'name': lora_name, 'success': False, 'error': str(e)}
    
    def _generate_comparison_images(self, lora_files: list, output_dir: str):
        """生成对比图"""
        for lora_info in lora_files:
            lora_code = lora_info["name"].replace('.safetensors', '')
            lora_dir = os.path.join(output_dir, lora_code)
            
            sd15_path = os.path.join(lora_dir, "SD15.png")
            sdxl_path = os.path.join(lora_dir, "SDXL.png")
            combined_out = os.path.join(lora_dir, "对比图.png")
            
            if os.path.exists(sd15_path) and os.path.exists(sdxl_path):
                if not os.path.exists(combined_out):
                    try:
                        img1 = Image.open(sd15_path)
                        img2 = Image.open(sdxl_path)
                        max_height = max(img1.height, img2.height)
                        if img1.height < max_height:
                            img1 = img1.resize((img1.width, max_height))
                        if img2.height < max_height:
                            img2 = img2.resize((img2.width, max_height))
                        total_width = img1.width + img2.width
                        new_img = Image.new('RGB', (total_width, max_height + 40))
                        new_img.paste(img1, (0, 20))
                        new_img.paste(img2, (img1.width, 20))
                        draw = ImageDraw.Draw(new_img)
                        draw.line([(img1.width, 0), (img1.width, max_height + 40)], fill="white", width=2)
                        draw.text((20, 4), "⬅️ SD 1.5", fill="black")
                        draw.text((img1.width + 20, 4), "SDXL ➡️", fill="black")
                        new_img.save(combined_out)
                        self.tab._append_test_log(f"   ✅ {lora_code} 对比图已生成")
                    except Exception as e:
                        self.tab._append_test_log(f"   ⚠️ {lora_code} 对比图生成失败: {e}")