import os
import sys
import torch
import json
from PIL import Image, ImageDraw
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline
import gc
import argparse

from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    StableDiffusionInpaintPipeline,
    EulerDiscreteScheduler  # ✅ 添加
)

# ==================== 配置区域 ====================
SD15_MODEL_PATH = r"../models/sd-v1-5/aiiiiii01_v10.safetensors"
SDXL_MODEL_PATH = r"../models/sdxl/perfectionAsianILXL_v10.safetensors"
LORA_DIR = r"../models/test_lora" 
OUTPUT_DIR = r"./output/lora_previews"
PROMPT_TEMPLATE_SD15 = "masterpiece, best quality, 1girl, solo, white background, sharp focus, <lora:NAME:1>"
PROMPT_TEMPLATE_SDXL = "masterpiece, best quality, 1girl, solo, white background, studio lighting, highly detailed, sharp focus, <lora:NAME:1>"
NEGATIVE_PROMPT_SD15 = "worst quality, low quality, deformed, blurry, bad anatomy"
NEGATIVE_PROMPT_SDXL = "worst quality, low quality, deformed, blurry, bad anatomy, extra limbs, missing limbs, text"
# ✅ 新增：步数配置
SD15_STEPS = 12
SDXL_STEPS = 20
# ==================================================

def parse_args():
    parser = argparse.ArgumentParser(description="LoRA 批量测试工具")
    parser.add_argument("--list", type=str, default="all", 
                        help="指定要跑的列表: all, small, medium, large")
    parser.add_argument("--run", type=str, choices=["sd15", "sdxl", "both"], default="both",
                        help="指定要跑的模型阶段")
    parser.add_argument("--re-run", action="store_true", 
                        help="强制执行重新跑一轮")
    return parser.parse_args()

def ensure_dir(path):
    if not os.path.exists(path): os.makedirs(path)

def load_pipe(model_path, is_sdxl=False):
    print(f"📦 正在加载: {os.path.basename(model_path)}...")
    try:
        common_args = {
            "torch_dtype": torch.float32,
            "safety_checker": None,
            "requires_safety_checker": False,
            "use_safetensors": True,
            "low_cpu_mem_usage": True
        }
        if is_sdxl: pipe = StableDiffusionXLPipeline.from_single_file(model_path, **common_args)
        else: pipe = StableDiffusionPipeline.from_single_file(model_path, **common_args)
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

def scan_and_generate_list(lora_dir):
    files = []
    for f in os.listdir(lora_dir):
        if f.endswith('.safetensors'):
            path = os.path.join(lora_dir, f)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            files.append({"name": f, "path": path, "size_mb": size_mb})
    files.sort(key=lambda x: x["size_mb"])
    return files

def get_filtered_list(files, args):
    if args.list == "all": return files
    elif args.list == "small": return [f for f in files if f['size_mb'] < 50]
    elif args.list == "medium": return [f for f in files if 50 <= f['size_mb'] < 200]
    elif args.list == "large": return [f for f in files if f['size_mb'] >= 200]
    return files

def load_run_log():
    log_path = os.path.join(OUTPUT_DIR, "run_log.json")
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_run_log(log_data):
    log_path = os.path.join(OUTPUT_DIR, "run_log.json")
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

def generate_pipe_images(pipe, lora_name, prompt, output_path, size=(512, 768), is_sdxl=False):
    try:
        # ✅ 修改为调用配置变量
        steps = SDXL_STEPS if is_sdxl else SD15_STEPS
        
        result = pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT_SD15 if not is_sdxl else NEGATIVE_PROMPT_SDXL,
            num_inference_steps=steps,
            guidance_scale=7.5,
            height=size[1],
            width=size[0]
        )
        result.images[0].save(output_path)
        return True
    except Exception as e:
        print(f"   ⚠️ 生成异常: {e}")
        return False

def combine_images(sd15_path, sdxl_path, output_path):
    try:
        if not os.path.exists(sd15_path) or not os.path.exists(sdxl_path): return False
        img1 = Image.open(sd15_path)
        img2 = Image.open(sdxl_path)
        max_height = max(img1.height, img2.height)
        if img1.height < max_height: img1 = img1.resize((img1.width, max_height))
        if img2.height < max_height: img2 = img2.resize((img2.width, max_height))
        total_width = img1.width + img2.width
        new_img = Image.new('RGB', (total_width, max_height + 40))
        new_img.paste(img1, (0, 20))
        new_img.paste(img2, (img1.width, 20))
        draw = ImageDraw.Draw(new_img)
        draw.line([(img1.width, 0), (img1.width, max_height + 40)], fill="white", width=2)
        draw.text((20, 4), "⬅️ SD 1.5", fill="black")
        draw.text((img1.width + 20, 4), "SDXL ➡️", fill="black")
        new_img.save(output_path)
        return True
    except Exception as e:
        return False

def run_stage(pipe, files, stage_name, is_sdxl=False, run_log={}, re_run=False):
    total = len(files)
    for i, lora_info in enumerate(files):
        lora_name = lora_info["name"]
        lora_code = lora_name.replace('.safetensors', '')
        
        if not is_sdxl:
            prompt = PROMPT_TEMPLATE_SD15.replace("NAME", lora_code)
        else:
            prompt = PROMPT_TEMPLATE_SDXL.replace("NAME", lora_code)
            
        # ✅ 每个 LoRA 单独建一个子文件夹
        lora_dir = os.path.join(OUTPUT_DIR, lora_code)
        ensure_dir(lora_dir)
        
        if not is_sdxl:
            out_path = os.path.join(lora_dir, "SD15.png")
        else:
            out_path = os.path.join(lora_dir, "SDXL.png")

        # 检查是否需要跳过
        stage_key = "sd15" if not is_sdxl else "sdxl"
        if not re_run and run_log.get(lora_name, {}).get(stage_key, False):
            print(f"   [{i+1}/{total}] ⏭️ 跳过 {lora_name} (已标记完成)")
            continue
            
        if os.path.exists(out_path) and not re_run:
            if lora_name not in run_log: run_log[lora_name] = {}
            run_log[lora_name][stage_key] = True
            save_run_log(run_log)
            print(f"   [{i+1}/{total}] ⏭️ 跳过 {lora_name} (文件已存在)")
            continue

        print(f"   [{i+1}/{total}] 🚀 {stage_name} 测试 {lora_name} ({lora_info['size_mb']:.1f}MB)")
        success = generate_pipe_images(pipe, lora_code, prompt, out_path, 
                             size=(1024, 1024) if is_sdxl else (512, 768), 
                             is_sdxl=is_sdxl)
        
        if success:
            if lora_name not in run_log: run_log[lora_name] = {}
            run_log[lora_name][stage_key] = True
            save_run_log(run_log)
        
        gc.collect()
    return True

def run_test():
    ensure_dir(OUTPUT_DIR)
    args = parse_args()
    
    if args.re_run:
        run_log = {}
        print("💥 强制重新跑一轮，忽略所有历史记录。")
    else:
        run_log = load_run_log()
    
    raw_files = scan_and_generate_list(LORA_DIR)
    target_files = get_filtered_list(raw_files, args)
    total = len(target_files)
    print(f"🎯 本次任务目标: {total} 个 LoRA (来自筛选: {args.list})")

    if args.run in ["sd15", "both"]:
        print(f"\n{'='*40}\n【第一阶段：SD 1.5】\n{'='*40}")
        pipe_sd15 = load_pipe(SD15_MODEL_PATH, is_sdxl=False)
        if pipe_sd15:
            run_stage(pipe_sd15, target_files, "SD1.5", is_sdxl=False, run_log=run_log, re_run=args.re_run)
            del pipe_sd15; gc.collect(); print("✅ SD 1.5 已卸载。")
        else: print("❌ SD 1.5 无法加载。")

    if args.run in ["sdxl", "both"]:
        print(f"\n{'='*40}\n【第二阶段：SDXL】\n{'='*40}")
        pipe_sdxl = load_pipe(SDXL_MODEL_PATH, is_sdxl=True)
        if pipe_sdxl:
            run_stage(pipe_sdxl, target_files, "SDXL", is_sdxl=True, run_log=run_log, re_run=args.re_run)
            
            print("🔄 正在拼接 SD1.5 和 SDXL 的对比图...")
            for lora_info in target_files:
                lora_name = lora_info["name"]
                lora_code = lora_name.replace('.safetensors', '')
                lora_dir = os.path.join(OUTPUT_DIR, lora_code)
                
                sd15_path = os.path.join(lora_dir, "SD15.png")
                sdxl_path = os.path.join(lora_dir, "SDXL.png")
                combined_out = os.path.join(lora_dir, "对比图.png")
                
                if not os.path.exists(combined_out) or args.re_run:
                    combine_images(sd15_path, sdxl_path, combined_out)
                    
            del pipe_sdxl; gc.collect(); print("✅ SDXL 已卸载。")
        else: print("❌ SDXL 无法加载。")

    print(f"\n✅ 任务完成！共处理 {total} 个 LoRA。")
    print(f"📁 请查看: {os.path.abspath(OUTPUT_DIR)} (每个 LoRA 都有独立的文件夹)")

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    run_test()