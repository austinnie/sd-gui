# generate_model_previews.py
"""
模型批量评测工具 - 快速了解每个模型的能力
"""

import os
import sys
import torch
import json
import argparse
from datetime import datetime
from PIL import Image
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline
import gc

from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    StableDiffusionInpaintPipeline,
    EulerDiscreteScheduler  # ✅ 添加
)

# ==================== 配置区域 ====================
SD15_DIR = r"../models/sd-v1-5"
SDXL_DIR = r"../models/sdxl"
OUTPUT_DIR = r"./output/model_previews"

# 统一的评测提示词（不含 LoRA）
PROMPT = "masterpiece, best quality, photorealistic, 8k, a beautiful Asian woman, wearing elegant dress, full body shot, detailed face, natural lighting"
NEGATIVE_PROMPT = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text"

# 评测参数组合（快速了解模型在不同参数下的表现）
TEST_PARAMS = [
    {"name": "标准", "steps": 20, "cfg": 7.5, "width": 512, "height": 768},
    {"name": "高细节", "steps": 30, "cfg": 8.0, "width": 512, "height": 768},
    {"name": "大尺寸", "steps": 25, "cfg": 7.5, "width": 640, "height": 960},
    {"name": "横图", "steps": 25, "cfg": 7.5, "width": 896, "height": 512},
    {"name": "方图", "steps": 25, "cfg": 7.5, "width": 768, "height": 768},
]
# ==================================================

def parse_args():
    parser = argparse.ArgumentParser(description="模型批量评测工具")
    parser.add_argument("--model", type=str, default="all", 
                        help="指定要跑的模型: all, 或具体模型名（如 aiiiiii01_v10）")
    parser.add_argument("--type", type=str, choices=["sd15", "sdxl", "both"], default="both",
                        help="模型类型")
    parser.add_argument("--quick", action="store_true", 
                        help="快速模式：每个模型只跑标准参数")
    parser.add_argument("--re-run", action="store_true", 
                        help="强制重新跑，忽略已有结果")
    return parser.parse_args()

def ensure_dir(path):
    if not os.path.exists(path): os.makedirs(path)

def scan_models():
    """扫描所有模型"""
    models = []
    
    # SD 1.5 模型
    if os.path.exists(SD15_DIR):
        for f in os.listdir(SD15_DIR):
            if f.endswith('.safetensors') or f.endswith('.ckpt'):
                size_mb = os.path.getsize(os.path.join(SD15_DIR, f)) / (1024 * 1024)
                models.append({
                    "name": f,
                    "path": os.path.join(SD15_DIR, f),
                    "type": "sd15",
                    "size_mb": size_mb
                })
    
    # SDXL 模型
    if os.path.exists(SDXL_DIR):
        for f in os.listdir(SDXL_DIR):
            if f.endswith('.safetensors') or f.endswith('.ckpt'):
                size_mb = os.path.getsize(os.path.join(SDXL_DIR, f)) / (1024 * 1024)
                models.append({
                    "name": f,
                    "path": os.path.join(SDXL_DIR, f),
                    "type": "sdxl",
                    "size_mb": size_mb
                })
    
    # 按大小排序
    models.sort(key=lambda x: x["size_mb"])
    return models

def load_model(model_path, is_sdxl=False):
    """加载模型"""
    print(f"📦 加载: {os.path.basename(model_path)}")
    try:
        common_args = {
            "torch_dtype": torch.float32,
            "safety_checker": None,
            "requires_safety_checker": False,
            "use_safetensors": True,
            "low_cpu_mem_usage": True
        }
        if is_sdxl:
            pipe = StableDiffusionXLPipeline.from_single_file(model_path, **common_args)
        else:
            pipe = StableDiffusionPipeline.from_single_file(model_path, **common_args)
        
        pipe = pipe.to("cpu")
        pipe.enable_vae_slicing()
        pipe.enable_attention_slicing()
        
        # ✅ 使用 EulerDiscreteScheduler
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        print("✅ 使用 EulerDiscreteScheduler (稳定调度器)")
        
        print("✅ 加载完成")
        return pipe
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return None

def generate_one(pipe, params, seed=42):
    """生成单张图片"""
    try:
        generator = torch.Generator("cpu").manual_seed(seed)
        result = pipe(
            prompt=PROMPT,
            negative_prompt=NEGATIVE_PROMPT,
            num_inference_steps=params["steps"],
            guidance_scale=params["cfg"],
            height=params["height"],
            width=params["width"],
            generator=generator
        )
        return result.images[0]
    except Exception as e:
        print(f"   ⚠️ 生成失败: {e}")
        return None

def run_model_test(model_info, quick_mode=False, re_run=False):
    """评测单个模型"""
    model_name = model_info["name"]
    model_path = model_info["path"]
    is_sdxl = model_info["type"] == "sdxl"
    
    # 创建输出目录
    model_output_dir = os.path.join(OUTPUT_DIR, model_name.replace('.safetensors', ''))
    ensure_dir(model_output_dir)
    
    # 检查是否已评测
    done_file = os.path.join(model_output_dir, ".done")
    if os.path.exists(done_file) and not re_run:
        print(f"⏭️ 跳过 {model_name} (已评测)")
        return
    
    print(f"\n{'='*60}")
    print(f"🔍 评测模型: {model_name}")
    print(f"   类型: {'SDXL' if is_sdxl else 'SD 1.5'}")
    print(f"   大小: {model_info['size_mb']:.1f} MB")
    print(f"{'='*60}")
    
    # 加载模型
    pipe = load_model(model_path, is_sdxl)
    if pipe is None:
        return
    
    # 确定要跑的参数
    params_list = TEST_PARAMS[:1] if quick_mode else TEST_PARAMS
    
    # 生成图片
    success_count = 0
    for params in params_list:
        print(f"\n   [{params['name']}] 步数:{params['steps']} CFG:{params['cfg']} {params['width']}x{params['height']}")
        
        # 用3个不同的种子，看看稳定性
        for seed in [42, 100, 200]:
            image = generate_one(pipe, params, seed)
            if image:
                filename = f"{params['name']}_seed{seed}.png"
                filepath = os.path.join(model_output_dir, filename)
                image.save(filepath)
                success_count += 1
                print(f"   ✅ {filename}")
            else:
                print(f"   ❌ 种子{seed} 失败")
    
    # 生成评测报告
    report = {
        "model_name": model_name,
        "model_type": "sdxl" if is_sdxl else "sd15",
        "model_path": model_path,
        "size_mb": model_info["size_mb"],
        "tested_at": datetime.now().isoformat(),
        "success_count": success_count,
        "total_count": len(params_list) * 3,
        "params": params_list
    }
    
    report_path = os.path.join(model_output_dir, "report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 标记完成
    with open(done_file, 'w') as f:
        f.write("done")
    
    # 清理内存
    del pipe
    gc.collect()
    print(f"\n✅ {model_name} 评测完成，共生成 {success_count} 张图片")
    print(f"   报告: {report_path}")

def main():
    ensure_dir(OUTPUT_DIR)
    args = parse_args()
    
    # 扫描所有模型
    all_models = scan_models()
    print(f"📁 找到 {len(all_models)} 个模型")
    
    # 过滤模型
    if args.model != "all":
        all_models = [m for m in all_models if args.model.lower() in m["name"].lower()]
        print(f"🎯 过滤后: {len(all_models)} 个模型")
    
    if args.type == "sd15":
        all_models = [m for m in all_models if m["type"] == "sd15"]
    elif args.type == "sdxl":
        all_models = [m for m in all_models if m["type"] == "sdxl"]
    
    if not all_models:
        print("❌ 没有符合条件的模型")
        return
    
    print(f"\n📋 本次评测 {len(all_models)} 个模型:")
    for i, m in enumerate(all_models, 1):
        print(f"  {i:2d}. {m['name']} ({m['type']})")
    
    print(f"\n🚀 开始评测...")
    print(f"   模式: {'快速' if args.quick else '完整'}")
    print(f"   重跑: {'是' if args.re_run else '否'}")
    print("-" * 60)
    
    for i, model in enumerate(all_models, 1):
        print(f"\n[{i}/{len(all_models)}]")
        run_model_test(model, args.quick, args.re_run)
    
    print(f"\n✅ 全部完成！")
    print(f"📁 结果目录: {os.path.abspath(OUTPUT_DIR)}")
    print(f"📊 共评测 {len(all_models)} 个模型")

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()