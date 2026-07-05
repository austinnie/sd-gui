#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量图生图生成器
读取 output/configs/img2img_batch_config_*.json，批量生成图片
支持 多进程 并行加速
"""

import os
import sys
import json
import gc
import torch
import argparse
from datetime import datetime
import multiprocessing
import numpy as np

# ==================== 统一缓存目录（必须在导入库之前设置）====================
CACHE_ROOT = r"E:\hf_cache\.cache"

os.environ['HF_HOME'] = CACHE_ROOT
os.environ['U2NET_HOME'] = os.path.join(CACHE_ROOT, "u2net")
os.environ['DEEPFACE_HOME'] = os.path.join(CACHE_ROOT, "deepface")

for env_var in ['HF_HOME', 'U2NET_HOME', 'DEEPFACE_HOME']:
    path = os.environ[env_var]
    os.makedirs(path, exist_ok=True)
    print(f"📁 {env_var} = {path}")

# ✅ 现在导入依赖
from PIL import Image
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, StableDiffusionInpaintPipeline
from rembg import remove

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gui.tabs.img2img_tab import auto_shorten_prompt, safe_del


def ensure_dir(path):
    if not os.path.exists(path): os.makedirs(path)


def load_pipe(model_path):
    """加载 SD 模型（单进程专用）"""
    print(f"📦 加载图生图模型: {os.path.basename(model_path)}...")
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
        print("✅ 模型加载完成！")
        return pipe, is_sdxl
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return None, None


# ==================== 单线程核心生成函数 ====================
def generate_image(pipe, is_sdxl, prompt, negative, image_path, output_path,
                   strength, steps, cfg, width, height, 
                   use_inpaint=True):
    
    try:
        init_image = Image.open(image_path).convert('RGB')
        
        # --- 1. 自动生成衣服遮罩 ---
        if use_inpaint:
            from rembg import remove
            # 生成人物遮罩（白色=人物）
            person_only = remove(init_image, only_mask=True)
            
            # ✅ 【全新逻辑：用衣服遮罩去覆盖人物遮罩】
            # 1. 先把人物遮罩转换成“待重绘区域”遮罩（白色=目标区域）
            #    AI 必须能看清原图（背景+人物），才能知道“换衣服”不换脸
            # 2. 生成一个简单的“衣服区域”遮罩：直接提取全图，但必须手动限制范围
            #    SD 1.5 Inpaint 非常依赖遮罩精度，强行用 AI 遮罩反而会乱。
            
            # 我们不玩那些花里胡哨的遮罩运算了，直接做一个“精准衣服区域”遮罩
            # 下面是分步操作：
            
            # 第一步：生成黑白遮罩，白色=人物
            person_mask = person_only
            
            # 第二步：用 OpenCV 对人物遮罩做膨胀，把人物边缘扩大
            # 这样做的目的是：把人物边缘的那一点点空隙（比如手臂和身体之间的缝隙）填上
            import cv2
            import numpy as np
            # 先转成 numpy 数组
            mask_np = np.array(person_mask)
            # 把人物区域（白色）变成灰色，防止直接膨胀把背景也吞了
            mask_np = (mask_np > 128).astype(np.uint8) * 255
            # 膨胀（让白色区域向外扩张 5 个像素）
            kernel = np.ones((5,5), np.uint8)
            mask_np = cv2.dilate(mask_np, kernel, iterations=2)
            # 转回 PIL
            person_mask = Image.fromarray(mask_np)
            
            # 第三步：因为我们想要 AI “重绘衣服”，所以应该让 AI 尽可能把“人体自身”当成白色。
            # 只有当成白色，它才会去重绘。现在我们就用这个膨胀过的遮罩！
            mask = person_mask
            
            print(f"   🖌️ 已生成衣服遮罩 (精准人物轮廓)")
        else:
            mask = None
        
        # --- 2. 转化为 Inpaint 管道 ---
        if use_inpaint and mask is not None:
            inpainting_pipe = StableDiffusionInpaintPipeline(
                vae=pipe.vae,
                text_encoder=pipe.text_encoder,
                tokenizer=pipe.tokenizer,
                unet=pipe.unet,
                scheduler=pipe.scheduler,
                safety_checker=None,
                feature_extractor=None,
                requires_safety_checker=False
            )
            inpainting_pipe.to("cpu")
            inpainting_pipe.enable_attention_slicing()
            inpainting_pipe.vae.enable_slicing()
            if hasattr(inpainting_pipe.vae, 'enable_tiling'):
                inpainting_pipe.vae.enable_tiling()
            pipe = inpainting_pipe
        
        # --- 3. 尺寸调整 ---
        w, h = init_image.size
        if width > 0 and height > 0:
            if w != width or h != height:
                width = ((width + 31) // 64) * 64
                height = ((height + 31) // 64) * 64
                init_image = init_image.resize((width, height), Image.Resampling.LANCZOS)
        else:
            width = ((w + 31) // 64) * 64
            height = ((h + 31) // 64) * 64
            if w != width or h != height:
                init_image = init_image.resize((width, height), Image.Resampling.LANCZOS)
        
        if mask is not None:
            mask = mask.resize((width, height), Image.Resampling.LANCZOS)
        
        generator = torch.Generator("cpu").manual_seed(42)
        print(f"   🎨 局部重绘开始... (强度:{strength})")

        # ===== 【强制换衣提示词】 =====
        #forced_prompt = f"change clothes to, {prompt}"
        # ✅ 把“换衣服”指令提到最前面，防止被截断
        forced_prompt = f"{prompt}, change clothes to new outfit"
        
        forced_negative = f"{negative}, bra, panties, underwear, original outfit"
        # ==================================

        # --- 4. 调用 Inpaint ---
        if use_inpaint and mask is not None:
            result = pipe(
                prompt=forced_prompt,
                negative_prompt=forced_negative,
                image=init_image,
                mask_image=mask,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
            )
        else:
            result = pipe(
                prompt=forced_prompt,
                negative_prompt=forced_negative,
                image=init_image,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
            )
        
        result.images[0].save(output_path)
        return True
    except Exception as e:
        print(f"   ❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== 多进程专用函数 ====================
def worker_process(jobs_slice, config):
    """
    子进程的工作函数：加载模型、批量生成分配给它的图片
    """
    import torch
    from PIL import Image
    from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, StableDiffusionInpaintPipeline
    
    # 1. 每个进程单独加载一次模型
    model_path = config["model_path"]
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
    
    # 2. 执行切片任务
    for job in jobs_slice:
        # ===== 【关键修复】为缺失的参数添加全局默认值 =====
        # 防止 JSON 单行任务里没有 strength, steps, cfg 导致报错
        job_strength = job.get("strength", config.get("strength", 0.5))
        job_steps = job.get("steps", config.get("steps", 25))
        job_cfg = job.get("cfg", config.get("cfg", 7.5))
        # ====================================================
        
        # 生成文件名
        safe_name = "".join(c for c in job["name"] if c.isalnum() or c in " _-")[:50]
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}.png"
        output_path = os.path.join(config["output_dir"], filename)
        
        generate_image(
            pipe, is_sdxl,
            job["prompt"], job["negative"],
            config["target_image"], output_path,
            job_strength, job_steps, job_cfg,  # ✅ 这里用加了兜底的变量
            job["width"], job["height"]
        )

# ==================== 单线程主入口 ====================
def run_batch_single(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("=" * 60)
    print("🚀 批量图生图任务 (单线程模式)")
    print(f"配置文件: {config_file}")
    print(f"任务数: {len(config['jobs'])}")
    print("=" * 60)
    
    model_path = config.get("model_path")
    pipe, is_sdxl = load_pipe(model_path)
    if pipe is None:
        return
    
    output_dir = config.get("output_dir", "./output/batch_img2img")
    ensure_dir(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for idx, job in enumerate(config['jobs'], 1):
        name = job.get("name", f"job_{idx}")
        prompt = job["prompt"]
        negative = job.get("negative", "worst quality, low quality, deformed, blurry")
        width = job.get("width", 0)
        height = job.get("height", 0)
        strength = job.get("strength", config.get("strength", 0.5))
        steps = job.get("steps", config.get("steps", 25))
        cfg = job.get("cfg", config.get("cfg", 7.5))
        
        # 截断过长提示词
        if len(prompt) > 280:
            prompt = prompt[:280]
        if "couple scene" in prompt:
            prompt = "intimate couple, " + prompt
        
        print(f"\n[{idx}/{len(config['jobs'])}] 🚀 {name}")
        print(f"   强度: {strength}, CFG: {cfg}")
        print(f"   提示词长度: {len(prompt)} 字符")
        
        safe_name = "".join(c for c in name if c.isalnum() or c in " _-")[:50]
        filename = f"{timestamp}_{idx:03d}_{safe_name}.png"
        output_path = os.path.join(output_dir, filename)
        
        success = generate_image(
            pipe, is_sdxl, prompt, negative,
            config["target_image"], output_path,
            strength, steps, cfg, width, height
        )
        gc.collect()
    
    del pipe
    gc.collect()
    print("\n" + "=" * 60)
    print("✅ 所有任务完成！")
    print(f"📁 输出目录: {os.path.abspath(output_dir)}")
    print("=" * 60)


# ==================== 多线程主入口 ====================
def run_batch_parallel(config_file, processes=2):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    jobs = config["jobs"]
    total = len(jobs)
    
    # 确保输出目录存在
    output_dir = config.get("output_dir", "./output/batch_img2img")
    ensure_dir(output_dir)
    
    print("=" * 60)
    print(f"🚀 批量图生图任务 (多进程模式, {processes} 个进程)")
    print(f"配置文件: {config_file}")
    print(f"任务数: {total}")
    print("=" * 60)
    
    # 把任务平均分配给各个进程
    chunk_size = len(jobs) // processes
    chunks = []
    for i in range(processes):
        start = i * chunk_size
        end = start + chunk_size if i < processes - 1 else len(jobs)
        chunks.append(jobs[start:end])
    
    # 启动进程池
    with multiprocessing.Pool(processes=processes) as pool:
        pool.starmap(worker_process, [(chunks[i], config) for i in range(processes)])
    
    print("\n" + "=" * 60)
    print("✅ 所有任务完成！")
    print(f"📁 输出目录: {os.path.abspath(output_dir)}")
    print("=" * 60)


# ==================== 命令行入口 ====================
def main():
    parser = argparse.ArgumentParser(description="批量图生图工具")
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="配置文件路径 (例如: output/configs/img2img_batch_config_时间戳.json)")
    parser.add_argument("--parallel", action="store_true",
                        help="启用多进程模式 (默认不启用)")
    parser.add_argument("--processes", type=int, default=2,
                        help="多进程数量 (仅在 --parallel 时生效, 默认2, 内存压力大请设为1)")
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"❌ 配置文件不存在: {args.config}")
        print("💡 请先运行: python batch_img2img_config_generator.py --target-image 你的图片路径")
        return
    
    if args.parallel:
        run_batch_parallel(args.config, processes=args.processes)
    else:
        run_batch_single(args.config)


if __name__ == "__main__":
    # 注意：Windows 下使用 multiprocessing 必须在 if __name__ == "__main__": 下执行
    main()