# generate_lora_previews_v2.py
"""
LoRA 批量测试工具 - v2
支持：多个基础模型 × 所有 LoRA
自动扫描所有模型，对比不同模型对同一 LoRA 的效果
"""

import os
import sys
import torch
import json
from PIL import Image, ImageDraw
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline
import gc
import argparse
from datetime import datetime

from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    StableDiffusionInpaintPipeline,
    EulerDiscreteScheduler  # ✅ 添加
)

# ==================== 配置区域 ====================
SD15_DIR = r"../models/sd-v1-5"
SDXL_DIR = r"../models/sdxl"
LORA_DIR = r"../models/test_lora" 
OUTPUT_DIR = r"./output/lora_previews_v2"

PROMPT_TEMPLATE_SD15 = "masterpiece, best quality, 1girl, solo, white background, sharp focus, <lora:NAME:1>"
PROMPT_TEMPLATE_SDXL = "masterpiece, best quality, 1girl, solo, white background, studio lighting, highly detailed, sharp focus, <lora:NAME:1>"

NEGATIVE_PROMPT_SD15 = "worst quality, low quality, deformed, blurry, bad anatomy"
NEGATIVE_PROMPT_SDXL = "worst quality, low quality, deformed, blurry, bad anatomy, extra limbs, missing limbs, text"

# 默认只跑 SD15 和 SDXL 各 5 个代表性模型（可以修改）
DEFAULT_MODELS = {
    "sd15": [
        "aiiiiiii01_v10.safetensors",
        "realisticmix_iiV12Version12.safetensors",
        "anycharactermixBaked_v20BakedVae.safetensors",
        "asianrealisticSdlife_v40.safetensors",
        "t3_sdVer3.safetensors",
    ],
    "sdxl": [
        "perfectionAsianILXL_v10.safetensors",
        "xlAsianRealisticMixNhiPNhChU_v10.safetensors",
    ]
}
# ==================================================

def parse_args():
    parser = argparse.ArgumentParser(description="LoRA 批量测试工具 - 多模型版")
    parser.add_argument("--list", type=str, default="all", 
                        help="LoRA 筛选: all, small, medium, large")
    parser.add_argument("--models", type=str, default="default",
                        help="模型选择: default, all, sd15, sdxl, 或逗号分隔的模型名")
    parser.add_argument("--re-run", action="store_true", 
                        help="强制执行重新跑一轮")
    return parser.parse_args()

def ensure_dir(path):
    if not os.path.exists(path): os.makedirs(path)

def scan_models():
    """扫描所有模型"""
    models = {}
    
    # SD 1.5 模型
    if os.path.exists(SD15_DIR):
        models["sd15"] = []
        for f in os.listdir(SD15_DIR):
            if f.endswith('.safetensors') or f.endswith('.ckpt'):
                models["sd15"].append({
                    "name": f,
                    "path": os.path.join(SD15_DIR, f),
                    "type": "sd15"
                })
    
    # SDXL 模型
    if os.path.exists(SDXL_DIR):
        models["sdxl"] = []
        for f in os.listdir(SDXL_DIR):
            if f.endswith('.safetensors') or f.endswith('.ckpt'):
                models["sdxl"].append({
                    "name": f,
                    "path": os.path.join(SDXL_DIR, f),
                    "type": "sdxl"
                })
    
    return models

def get_model_list(args):
    """根据参数获取要测试的模型列表"""
    all_models = scan_models()
    model_list = []
    
    if args.models == "default":
        # 使用默认的代表性模型
        for model_name in DEFAULT_MODELS.get("sd15", []):
            for m in all_models.get("sd15", []):
                if m["name"] == model_name:
                    model_list.append(m)
                    break
        for model_name in DEFAULT_MODELS.get("sdxl", []):
            for m in all_models.get("sdxl", []):
                if m["name"] == model_name:
                    model_list.append(m)
                    break
    
    elif args.models == "all":
        # 所有模型
        model_list = all_models.get("sd15", []) + all_models.get("sdxl", [])
    
    elif args.models == "sd15":
        model_list = all_models.get("sd15", [])
    
    elif args.models == "sdxl":
        model_list = all_models.get("sdxl", [])
    
    else:
        # 逗号分隔的模型名
        model_names = [m.strip() for m in args.models.split(",")]
        for model_name in model_names:
            for m in all_models.get("sd15", []) + all_models.get("sdxl", []):
                if model_name.lower() in m["name"].lower():
                    model_list.append(m)
                    break
    
    return model_list

def scan_and_generate_list(lora_dir):
    """扫描 LoRA 列表"""
    files = []
    for f in os.listdir(lora_dir):
        if f.endswith('.safetensors'):
            path = os.path.join(lora_dir, f)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            files.append({"name": f, "path": path, "size_mb": size_mb})
    files.sort(key=lambda x: x["size_mb"])
    return files

def get_filtered_list(files, args):
    """根据参数筛选 LoRA"""
    if args.list == "all": return files
    elif args.list == "small": return [f for f in files if f['size_mb'] < 50]
    elif args.list == "medium": return [f for f in files if 50 <= f['size_mb'] < 200]
    elif args.list == "large": return [f for f in files if f['size_mb'] >= 200]
    return files

def load_run_log():
    """加载运行日志"""
    log_path = os.path.join(OUTPUT_DIR, "run_log.json")
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_run_log(log_data):
    """保存运行日志"""
    log_path = os.path.join(OUTPUT_DIR, "run_log.json")
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

def load_pipe(model_path, is_sdxl=False):
    """加载模型"""
    print(f"📦 正在加载: {os.path.basename(model_path)}...")
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
        
        print("✅ 加载完成！")
        return pipe
    except Exception as e:
        print(f"❌ 模型加载失败 {model_path}: {e}")
        return None

def generate_pipe_images(pipe, lora_name, prompt, output_path, size=(512, 768), is_sdxl=False):
    """生成单张图片"""
    try:
        result = pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT_SD15 if not is_sdxl else NEGATIVE_PROMPT_SDXL,
            num_inference_steps=8 if not is_sdxl else 12,
            guidance_scale=7.5,
            height=size[1],
            width=size[0]
        )
        result.images[0].save(output_path)
        return True
    except Exception as e:
        print(f"   ⚠️ 生成异常: {e}")
        return False

def combine_images(model_outputs, output_path):
    """
    将多个模型的输出拼接成一张对比图
    model_outputs: [(model_name, image_path), ...]
    """
    try:
        # 加载所有图片
        images = []
        model_names = []
        for model_name, img_path in model_outputs:
            if not os.path.exists(img_path):
                return False
            img = Image.open(img_path)
            images.append(img)
            model_names.append(model_name)
        
        # 统一高度
        max_height = max(img.height for img in images)
        for i in range(len(images)):
            if images[i].height < max_height:
                images[i] = images[i].resize((images[i].width, max_height))
        
        # 计算总宽度（每个模型占一列）
        total_width = sum(img.width for img in images)
        # 加上分隔线宽度
        total_width += (len(images) - 1) * 2
        
        # 创建新图片
        new_img = Image.new('RGB', (total_width, max_height + 40))
        
        # 粘贴图片
        current_x = 0
        for i, img in enumerate(images):
            new_img.paste(img, (current_x, 20))
            current_x += img.width
            
            # 添加分隔线（除了最后一个）
            if i < len(images) - 1:
                draw = ImageDraw.Draw(new_img)
                draw.line([(current_x, 0), (current_x, max_height + 40)], fill="white", width=2)
                current_x += 2
        
        # 添加模型名称标签
        draw = ImageDraw.Draw(new_img)
        current_x = 0
        for i, model_name in enumerate(model_names):
            # 模型名简称
            short_name = model_name.replace('.safetensors', '')[:20]
            draw.text((current_x + 10, 4), short_name, fill="black")
            current_x += images[i].width + 2
        
        new_img.save(output_path)
        return True
    except Exception as e:
        print(f"   ⚠️ 拼接失败: {e}")
        return False

def run_stage(pipe, model_info, files, run_log={}, re_run=False):
    """
    对单个模型运行所有 LoRA 测试
    """
    model_name = model_info["name"]
    is_sdxl = model_info["type"] == "sdxl"
    
    total = len(files)
    for i, lora_info in enumerate(files):
        lora_name = lora_info["name"]
        lora_code = lora_name.replace('.safetensors', '')
        
        # 选择提示词模板
        if is_sdxl:
            prompt = PROMPT_TEMPLATE_SDXL.replace("NAME", lora_code)
        else:
            prompt = PROMPT_TEMPLATE_SD15.replace("NAME", lora_code)
        
        # 每个 LoRA 单独建一个子文件夹
        lora_dir = os.path.join(OUTPUT_DIR, lora_code)
        ensure_dir(lora_dir)
        
        # 输出路径：模型名.png
        out_path = os.path.join(lora_dir, f"{model_name.replace('.safetensors', '')}.png")
        
        # 检查是否需要跳过
        stage_key = model_name
        if not re_run and run_log.get(lora_name, {}).get(stage_key, False):
            print(f"   [{i+1}/{total}] ⏭️ 跳过 {lora_name} ({model_name})")
            continue
            
        if os.path.exists(out_path) and not re_run:
            if lora_name not in run_log: run_log[lora_name] = {}
            run_log[lora_name][stage_key] = True
            save_run_log(run_log)
            print(f"   [{i+1}/{total}] ⏭️ 跳过 {lora_name} ({model_name})")
            continue

        print(f"   [{i+1}/{total}] 🚀 {model_name} 测试 {lora_name} ({lora_info['size_mb']:.1f}MB)")
        
        # 生成图片
        size = (1024, 1024) if is_sdxl else (512, 768)
        success = generate_pipe_images(pipe, lora_code, prompt, out_path, size=size, is_sdxl=is_sdxl)
        
        if success:
            if lora_name not in run_log: run_log[lora_name] = {}
            run_log[lora_name][stage_key] = True
            save_run_log(run_log)
        
        gc.collect()
    
    return True

def generate_comparison_images(files, model_list):
    """
    为每个 LoRA 生成所有模型的对比图
    """
    print("🔄 正在生成对比图...")
    for lora_info in files:
        lora_name = lora_info["name"]
        lora_code = lora_name.replace('.safetensors', '')
        lora_dir = os.path.join(OUTPUT_DIR, lora_code)
        
        # 收集所有模型的输出
        model_outputs = []
        for model_info in model_list:
            model_name = model_info["name"]
            img_path = os.path.join(lora_dir, f"{model_name.replace('.safetensors', '')}.png")
            if os.path.exists(img_path):
                model_outputs.append((model_name, img_path))
        
        # 生成对比图
        if len(model_outputs) >= 2:
            combined_out = os.path.join(lora_dir, "对比图.png")
            combine_images(model_outputs, combined_out)
            print(f"   ✅ {lora_code} 对比图已生成 ({len(model_outputs)} 个模型)")
        else:
            print(f"   ⚠️ {lora_code} 只有 {len(model_outputs)} 个模型，跳过对比图")

def main():
    ensure_dir(OUTPUT_DIR)
    args = parse_args()
    
    # 获取模型列表
    model_list = get_model_list(args)
    if not model_list:
        print("❌ 没有找到任何模型")
        return
    
    print(f"🎯 本次测试 {len(model_list)} 个模型:")
    for i, m in enumerate(model_list, 1):
        print(f"  {i:2d}. {m['name']} ({m['type']})")
    
    # 获取 LoRA 列表
    raw_files = scan_and_generate_list(LORA_DIR)
    target_files = get_filtered_list(raw_files, args)
    total = len(target_files)
    print(f"🎯 本次任务目标: {total} 个 LoRA (来自筛选: {args.list})")
    
    # 加载运行日志
    if args.re_run:
        run_log = {}
        print("💥 强制重新跑一轮，忽略所有历史记录。")
    else:
        run_log = load_run_log()
    
    # 对每个模型运行测试
    for model_idx, model_info in enumerate(model_list, 1):
        model_name = model_info["name"]
        is_sdxl = model_info["type"] == "sdxl"
        
        print(f"\n{'='*40}")
        print(f"【模型 {model_idx}/{len(model_list)}】{model_name}")
        print(f"{'='*40}")
        
        # 加载模型
        pipe = load_pipe(model_info["path"], is_sdxl)
        if not pipe:
            print(f"❌ 无法加载 {model_name}，跳过")
            continue
        
        # 运行测试
        run_stage(pipe, model_info, target_files, run_log=run_log, re_run=args.re_run)
        
        # 卸载模型
        del pipe
        gc.collect()
        print(f"✅ {model_name} 已卸载。")
    
    # 生成对比图
    generate_comparison_images(target_files, model_list)
    
    print(f"\n✅ 任务完成！共测试 {len(model_list)} 个模型 × {total} 个 LoRA")
    print(f"📁 请查看: {os.path.abspath(OUTPUT_DIR)}")
    print(f"📊 每个 LoRA 有独立的文件夹，包含所有模型的输出和对比图")

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()