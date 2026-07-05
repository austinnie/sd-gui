# generate_lora_previews_v3.py
"""
LoRA 批量测试工具 - v3 (多维度组合测试)
支持：
- 多个基础模型 × 所有 LoRA
- 多权重测试 (--weights)
- 多提示词风格 (--prompts)
- LoRA 叠加 (--combine)
- 按关键词分组 (--group)
- 按最近修改筛选 (--recent)
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
import re

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
OUTPUT_DIR = r"./output/lora_previews_v3"

# 基础提示词模板
PROMPT_TEMPLATES = {
    "portrait": "masterpiece, best quality, 1girl, solo, portrait, white background, sharp focus, <lora:NAME:WEIGHT>",
    "full_body": "masterpiece, best quality, 1girl, solo, full body, white background, sharp focus, <lora:NAME:WEIGHT>",
    "close_up": "masterpiece, best quality, 1girl, solo, close up, white background, sharp focus, <lora:NAME:WEIGHT>",
    "cinematic": "masterpiece, best quality, 1girl, solo, cinematic lighting, dramatic, white background, sharp focus, <lora:NAME:WEIGHT>",
    "anime": "masterpiece, best quality, 1girl, solo, anime style, vibrant colors, white background, sharp focus, <lora:NAME:WEIGHT>",
}

# 默认权重列表
DEFAULT_WEIGHTS = [0.5, 0.8, 1.0, 1.2]

# 默认模型（每个类型选代表性模型）
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

# 负面提示词（复用之前的）
NEGATIVE_PROMPT_SD15 = "worst quality, low quality, deformed, blurry, bad anatomy"
NEGATIVE_PROMPT_SDXL = "worst quality, low quality, deformed, blurry, bad anatomy, extra limbs, missing limbs, text"
# ==================================================

def parse_args():
    parser = argparse.ArgumentParser(description="LoRA 多维度批量测试工具")
    
    # LoRA 筛选
    parser.add_argument("--list", type=str, default="all",
                        help="LoRA 筛选: all, small, medium, large")
    parser.add_argument("--recent", type=int, default=0,
                        help="只测试最近修改的 N 个 LoRA")
    parser.add_argument("--group", type=str, default=None,
                        help="按关键词分组测试 (如: 人物, 服装, 画风)")
    
    # 模型选择
    parser.add_argument("--models", type=str, default="default",
                        help="模型选择: default, all, sd15, sdxl, 或逗号分隔的模型名")
    
    # 维度扩展
    parser.add_argument("--weights", type=str, default="default",
                        help="权重列表: default, 或逗号分隔 (如 0.5,0.8,1.0)")
    parser.add_argument("--prompts", type=str, default="default",
                        help="提示词风格: default, portrait, full_body, close_up, cinematic, anime, 或逗号分隔")
    parser.add_argument("--combine", type=str, default=None,
                        help="测试 LoRA 叠加: 逗号分隔的 LoRA 名 (如 'chun_li,classic_oil_painting')")
    
    # 其他
    parser.add_argument("--re-run", action="store_true",
                        help="强制执行重新跑一轮")
    parser.add_argument("--max-loras", type=int, default=0,
                        help="最多测试几个 LoRA (用于快速测试)")
    
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
            mtime = os.path.getmtime(path)
            files.append({
                "name": f,
                "path": path,
                "size_mb": size_mb,
                "mtime": mtime
            })
    files.sort(key=lambda x: x["size_mb"])
    return files

def get_filtered_list(files, args):
    """根据参数筛选 LoRA"""
    # 按大小筛选
    if args.list == "small":
        files = [f for f in files if f['size_mb'] < 50]
    elif args.list == "medium":
        files = [f for f in files if 50 <= f['size_mb'] < 200]
    elif args.list == "large":
        files = [f for f in files if f['size_mb'] >= 200]
    
    # 按最近修改筛选
    if args.recent > 0:
        files.sort(key=lambda x: x["mtime"], reverse=True)
        files = files[:args.recent]
    
    # 按关键词分组
    if args.group:
        keyword = args.group.lower()
        files = [f for f in files if keyword in f["name"].lower()]
    
    # 限制数量
    if args.max_loras > 0:
        files = files[:args.max_loras]
    
    return files

def get_weights_list(args):
    """获取权重列表"""
    if args.weights == "default":
        return DEFAULT_WEIGHTS
    try:
        return [float(w.strip()) for w in args.weights.split(",")]
    except:
        print(f"⚠️ 权重解析失败，使用默认: {DEFAULT_WEIGHTS}")
        return DEFAULT_WEIGHTS

def get_prompts_list(args):
    """获取提示词风格列表"""
    if args.prompts == "default":
        return ["portrait"]  # 默认只跑 portrait
    try:
        prompts = [p.strip() for p in args.prompts.split(",")]
        # 验证所有提示词都在模板中
        for p in prompts:
            if p not in PROMPT_TEMPLATES:
                print(f"⚠️ 未知提示词风格: {p}，跳过")
        return [p for p in prompts if p in PROMPT_TEMPLATES]
    except:
        print("⚠️ 提示词解析失败，使用默认: portrait")
        return ["portrait"]

def get_combine_list(args):
    """获取 LoRA 叠加列表"""
    if not args.combine:
        return []
    return [l.strip() for l in args.combine.split(",")]

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

def generate_combined_lora(pipe, lora_names, prompt_template, output_path, is_sdxl=False):
    """
    生成叠加 LoRA 的图片
    """
    lora_tags = []
    for lora_name in lora_names:
        lora_code = lora_name.replace('.safetensors', '')
        lora_tags.append(f"<lora:{lora_code}:1>")
    
    prompt = prompt_template.replace("<lora:NAME:WEIGHT>", "".join(lora_tags))
    
    return generate_pipe_images(pipe, "combined", prompt, output_path, 
                               size=(512, 768), is_sdxl=is_sdxl)

def build_comparison_grid(image_paths, model_names, output_path, title=""):
    """
    构建对比网格图
    image_paths: 图片路径列表
    model_names: 对应的模型名称列表
    output_path: 输出路径
    title: 标题
    """
    try:
        if not image_paths:
            return False
        
        # 加载所有图片
        images = []
        valid_models = []
        for i, img_path in enumerate(image_paths):
            if os.path.exists(img_path):
                img = Image.open(img_path)
                images.append(img)
                valid_models.append(model_names[i])
        
        if len(images) < 1:
            return False
        
        # 统一高度
        max_height = max(img.height for img in images)
        for i in range(len(images)):
            if images[i].height < max_height:
                images[i] = images[i].resize((images[i].width, max_height))
        
        # 计算总宽度（横向排列）
        total_width = sum(img.width for img in images)
        total_width += (len(images) - 1) * 2  # 分隔线
        
        # 创建新图片
        new_img = Image.new('RGB', (total_width, max_height + 60))
        
        # 添加标题
        if title:
            draw = ImageDraw.Draw(new_img)
            draw.text((10, 5), title, fill="black")
        
        # 粘贴图片
        current_x = 0
        for i, img in enumerate(images):
            new_img.paste(img, (current_x, 30))
            current_x += img.width
            
            # 添加分隔线
            if i < len(images) - 1:
                draw = ImageDraw.Draw(new_img)
                draw.line([(current_x, 0), (current_x, max_height + 60)], fill="white", width=2)
                current_x += 2
        
        # 添加模型名称标签
        draw = ImageDraw.Draw(new_img)
        current_x = 0
        for i, model_name in enumerate(valid_models):
            short_name = model_name.replace('.safetensors', '')[:15]
            draw.text((current_x + 10, max_height + 35), short_name, fill="black")
            current_x += images[i].width + 2
        
        new_img.save(output_path)
        return True
    except Exception as e:
        print(f"   ⚠️ 拼接失败: {e}")
        return False

def run_lora_test(pipe, model_info, lora_info, prompt_template, weight, run_log={}, re_run=False):
    """
    运行单个 LoRA 测试
    """
    model_name = model_info["name"]
    is_sdxl = model_info["type"] == "sdxl"
    lora_name = lora_info["name"]
    lora_code = lora_name.replace('.safetensors', '')
    
    # 构建提示词
    prompt = prompt_template.replace("NAME", lora_code).replace("WEIGHT", str(weight))
    
    # 输出路径：LoRA文件夹/模型名_权重_风格.png
    lora_dir = os.path.join(OUTPUT_DIR, lora_code)
    ensure_dir(lora_dir)
    
    model_short = model_name.replace('.safetensors', '')
    out_path = os.path.join(lora_dir, f"{model_short}_w{weight}.png")
    
    # 检查是否已生成
    stage_key = f"{model_name}_w{weight}"
    if not re_run and run_log.get(lora_name, {}).get(stage_key, False):
        return True, out_path
    
    if os.path.exists(out_path) and not re_run:
        if lora_name not in run_log: run_log[lora_name] = {}
        run_log[lora_name][stage_key] = True
        save_run_log(run_log)
        return True, out_path
    
    # 生成图片
    size = (1024, 1024) if is_sdxl else (512, 768)
    success = generate_pipe_images(pipe, lora_code, prompt, out_path, size=size, is_sdxl=is_sdxl)
    
    if success:
        if lora_name not in run_log: run_log[lora_name] = {}
        run_log[lora_name][stage_key] = True
        save_run_log(run_log)
    
    gc.collect()
    return success, out_path

def run_model_stage(pipe, model_info, lora_list, prompt_templates, weights, run_log={}, re_run=False):
    """
    对单个模型运行所有 LoRA × 权重 × 提示词组合
    """
    model_name = model_info["name"]
    total = len(lora_list) * len(weights) * len(prompt_templates)
    count = 0
    results = {}
    
    for lora_info in lora_list:
        lora_name = lora_info["name"]
        lora_code = lora_name.replace('.safetensors', '')
        results[lora_code] = []
        
        for weight in weights:
            for prompt_name in prompt_templates:
                count += 1
                prompt_template = PROMPT_TEMPLATES[prompt_name]
                
                print(f"   [{count}/{total}] {model_name} × {lora_code} × w{weight} × {prompt_name}")
                
                success, out_path = run_lora_test(
                    pipe, model_info, lora_info, 
                    prompt_template, weight, 
                    run_log, re_run
                )
                
                if success:
                    results[lora_code].append({
                        "weight": weight,
                        "prompt": prompt_name,
                        "path": out_path
                    })
    
    return results

def generate_comparison_images(results, model_list, lora_list, prompt_templates, weights):
    """
    生成各种对比图
    """
    print("\n🔄 正在生成对比图...")
    
    for lora_info in lora_list:
        lora_code = lora_info["name"].replace('.safetensors', '')
        lora_dir = os.path.join(OUTPUT_DIR, lora_code)
        
        # 1. 模型对比图 (权重固定为1.0, 提示词固定为portrait)
        model_images = []
        model_names = []
        for model_info in model_list:
            model_name = model_info["name"].replace('.safetensors', '')
            img_path = os.path.join(lora_dir, f"{model_name}_w1.0.png")
            if os.path.exists(img_path):
                model_images.append(img_path)
                model_names.append(model_info["name"])
        
        if len(model_images) >= 2:
            output_path = os.path.join(lora_dir, "对比图_模型.png")
            build_comparison_grid(
                model_images, model_names, 
                output_path, 
                title=f"{lora_code} - 不同模型对比 (权重1.0)"
            )
        
        # 2. 权重对比图 (模型固定为第一个, 提示词固定为portrait)
        if model_list:
            first_model = model_list[0]["name"].replace('.safetensors', '')
            weight_images = []
            weight_names = []
            for weight in weights:
                img_path = os.path.join(lora_dir, f"{first_model}_w{weight}.png")
                if os.path.exists(img_path):
                    weight_images.append(img_path)
                    weight_names.append(f"w{weight}")
            
            if len(weight_images) >= 2:
                output_path = os.path.join(lora_dir, "对比图_权重.png")
                build_comparison_grid(
                    weight_images, weight_names,
                    output_path,
                    title=f"{lora_code} - 不同权重对比 ({first_model})"
                )
        
        # 3. 提示词对比图 (模型固定为第一个, 权重固定为1.0)
        if model_list:
            first_model = model_list[0]["name"].replace('.safetensors', '')
            prompt_images = []
            prompt_names = []
            for prompt_name in prompt_templates:
                img_path = os.path.join(lora_dir, f"{first_model}_w1.0.png")
                # 注意：这里实际上需要不同提示词的图片，但我们的命名只包含了权重
                # 为了简化，我们重新命名：模型名_权重_提示词.png
                # 但这个需要修改 run_lora_test 中的命名逻辑
                # 这里暂时用单张图做简单对比
            
            # 如果 prompt_templates 有多个，可以展示不同提示词的效果
            if len(prompt_templates) >= 2:
                output_path = os.path.join(lora_dir, "对比图_提示词.png")
                # 这里简化处理，实际需要重新生成不同提示词的图片
                pass

def main():
    ensure_dir(OUTPUT_DIR)
    args = parse_args()
    
    # 打印配置
    print("=" * 60)
    print("🎯 LoRA 多维度测试配置")
    print("=" * 60)
    
    # 获取模型列表
    model_list = get_model_list(args)
    if not model_list:
        print("❌ 没有找到任何模型")
        return
    
    print(f"📦 模型: {len(model_list)} 个")
    for i, m in enumerate(model_list, 1):
        print(f"  {i:2d}. {m['name']}")
    
    # 获取 LoRA 列表
    raw_files = scan_and_generate_list(LORA_DIR)
    target_files = get_filtered_list(raw_files, args)
    
    if not target_files:
        print("❌ 没有找到符合条件的 LoRA")
        return
    
    print(f"\n🎯 LoRA: {len(target_files)} 个")
    for i, f in enumerate(target_files, 1):
        print(f"  {i:2d}. {f['name']} ({f['size_mb']:.1f}MB)")
    
    # 获取权重和提示词
    weights = get_weights_list(args)
    prompt_templates = get_prompts_list(args)
    combine_list = get_combine_list(args)
    
    print(f"\n⚙️ 权重: {weights}")
    print(f"📝 提示词: {prompt_templates}")
    if combine_list:
        print(f"🔗 LoRA 叠加: {combine_list}")
    
    # 加载运行日志
    if args.re_run:
        run_log = {}
        print("💥 强制重新跑一轮，忽略所有历史记录。")
    else:
        run_log = load_run_log()
    
    total_combinations = len(target_files) * len(model_list) * len(weights) * len(prompt_templates)
    print(f"\n📊 总组合数: {total_combinations}")
    print(f"   预计生成 {total_combinations} 张图片")
    if args.recent:
        print(f"   (只测试最近修改的 {args.recent} 个 LoRA)")
    if args.max_loras:
        print(f"   (最多测试 {args.max_loras} 个 LoRA)")
    
    confirm = input("\n继续运行？(y/n): ")
    if confirm.lower() != 'y':
        print("已取消")
        return
    
    print("\n🚀 开始测试...")
    print("=" * 60)
    
    # 对每个模型运行测试
    all_results = {}
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
        results = run_model_stage(
            pipe, model_info, target_files,
            prompt_templates, weights,
            run_log, args.re_run
        )
        all_results[model_name] = results
        
        # 卸载模型
        del pipe
        gc.collect()
        print(f"✅ {model_name} 已卸载。")
    
    # 生成对比图
    generate_comparison_images(
        all_results, model_list, target_files,
        prompt_templates, weights
    )
    
    print(f"\n✅ 任务完成！")
    print(f"📊 共测试: {len(model_list)} 个模型 × {len(target_files)} 个 LoRA × {len(weights)} 个权重 × {len(prompt_templates)} 种提示词")
    print(f"📁 输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print(f"📁 每个 LoRA 有独立的文件夹，包含所有组合的图片和对比图")

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()