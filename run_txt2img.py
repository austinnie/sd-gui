#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文生图批量 - 执行生成器
读取 output/configs/txt2img_batch_config_*.json，批量生成图片
"""

import os
import sys
import json
import gc
import torch
import argparse
from PIL import Image
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline
from datetime import datetime

from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    StableDiffusionInpaintPipeline,
    EulerDiscreteScheduler  # ✅ 添加
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gui.tabs.txt2img_tab import auto_shorten_prompt


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def load_pipe(model_path):
    """加载 SD 模型"""
    print(f"📦 加载文生图模型: {os.path.basename(model_path)}...")
    try:
        common_args = {
            "torch_dtype": torch.float32,
            "safety_checker": None,
            "requires_safety_checker": False,
            "use_safetensors": True,
            "low_cpu_mem_usage": False
        }
        is_sdxl = "sdxl" in model_path.lower() or "xl" in model_path.lower()
        
        if is_sdxl:
            pipe = StableDiffusionXLPipeline.from_single_file(model_path, **common_args)
        else:
            pipe = StableDiffusionPipeline.from_single_file(model_path, **common_args)
        
        pipe = pipe.to("cpu")
        pipe.enable_vae_slicing()
        pipe.enable_attention_slicing()
        if hasattr(pipe.vae, 'enable_tiling'):
            pipe.vae.enable_tiling()
            

        # ✅ 使用 EulerDiscreteScheduler
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        print("✅ 使用 EulerDiscreteScheduler (稳定调度器)")
        
        print("✅ 模型加载完成！")
        return pipe, is_sdxl
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return None, None


def generate_image(pipe, is_sdxl, prompt, negative, output_path, steps, cfg, width, height):
    """生成单张文生图"""
    try:
        width = ((width + 31) // 64) * 64
        height = ((height + 31) // 64) * 64
        
        generator = torch.Generator("cpu").manual_seed(42)
        print(f"   🎨 文生图开始... ({width}x{height}, CFG:{cfg}, 步数:{steps})")
        
        result = pipe(
            prompt=prompt,
            negative_prompt=negative,
            num_inference_steps=steps,
            guidance_scale=cfg,
            height=height,
            width=width,
            generator=generator,
        )
        
        result.images[0].save(output_path)
        return True
    except Exception as e:
        print(f"   ❌ 生成失败: {e}")
        return False


def run_batch(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("=" * 60)
    print("🚀 批量文生图任务")
    print(f"配置文件: {config_file}")
    print(f"任务数: {len(config['jobs'])}")
    print("=" * 60)
    
    model_path = config.get("model_path")
    pipe, is_sdxl = load_pipe(model_path)
    if pipe is None:
        return
    
    output_dir = config.get("output_dir", "./output/batch_txt2img")
    ensure_dir(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for idx, job in enumerate(config['jobs'], 1):
        name = job.get("name", f"任务_{idx}")
        prompt = job["prompt"]
        negative = job.get("negative", "worst quality, low quality, deformed")
        width = job.get("width", 512)
        height = job.get("height", 768)
        cfg = job.get("cfg", config.get("cfg", 7.5))
        steps = job.get("steps", config.get("steps", 25))
        
        print(f"\n[{idx}/{len(config['jobs'])}] 🚀 {name}")
        print(f"   尺寸: {width}x{height}, CFG: {cfg}, 步数: {steps}")
        
        safe_name = "".join(c for c in name if c.isalnum() or c in " _-")[:50]
        filename = f"{timestamp}_{idx:03d}_{safe_name}.png"
        output_path = os.path.join(output_dir, filename)
        
        success = generate_image(
            pipe, is_sdxl, prompt, negative,
            output_path, steps, cfg, width, height
        )
        gc.collect()
    
    del pipe
    gc.collect()
    print("\n" + "=" * 60)
    print("✅ 所有文生图任务完成！")
    print(f"📁 输出目录: {os.path.abspath(output_dir)}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="批量文生图工具")
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="配置文件路径 (例如: output/configs/txt2img_batch_config_时间戳.json)")
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"❌ 配置文件不存在: {args.config}")
        print("💡 请先运行: python batch_txt2img_config_generator.py")
        return
    
    run_batch(args.config)


if __name__ == "__main__":
    main()