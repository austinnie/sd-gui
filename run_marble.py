#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量图生图生成器 (修复版)
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

from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    StableDiffusionInpaintPipeline,
    EulerDiscreteScheduler  # ✅ 添加
)

# ==================== 统一缓存目录（必须在导入库之前设置）====================
CACHE_ROOT = r"E:\hf_cache\.cache"

# ✅ 设置所有缓存目录
os.environ['HF_HOME'] = CACHE_ROOT
os.environ['U2NET_HOME'] = os.path.join(CACHE_ROOT, "u2net")
os.environ['DEEPFACE_HOME'] = os.path.join(CACHE_ROOT, "deepface")

# ✅ 创建所有目录
for env_var in ['HF_HOME', 'U2NET_HOME', 'DEEPFACE_HOME']:
    path = os.environ[env_var]
    os.makedirs(path, exist_ok=True)
    print(f"📁 {env_var} = {path}")

# ✅ 现在才导入依赖库
from PIL import Image, ImageEnhance
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, StableDiffusionInpaintPipeline
from rembg import remove

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gui.tabs.img2img_tab import auto_shorten_prompt, safe_del

from core.nsfw_filter import nsfw_filter
from config.nsfw_config import nsfw_config, ContentLevel


def ensure_dir(path):
    if not os.path.exists(path): os.makedirs(path)


def load_pipe(model_path):
    """加载 SD 模型（单进程专用）"""
    # ===== 【新增】NSFW 模型切换 =====
    if nsfw_config.use_dedicated_models:
        if nsfw_config.level in [ContentLevel.EXPLICIT, ContentLevel.EXTREME]:
            explicit_path = nsfw_config.explicit_model_path
            if os.path.exists(explicit_path):
                print(f"🔞 使用成人模型: {os.path.basename(explicit_path)}")
                model_path = explicit_path
                
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
        

        # ✅ 使用 EulerDiscreteScheduler
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        print(f"✅ 使用 EulerDiscreteScheduler (稳定调度器)")
        
        return pipe, is_sdxl
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return None, None


def auto_shorten_prompt_for_clip(prompt, max_tokens=70):
    """
    精简提示词以适应 CLIP 77 token 限制
    参数:
        prompt: 原始提示词
        max_tokens: 最大 token 数 (建议 70，留余量)
    
    返回:
        精简后的提示词
    """
    if not prompt:
        return prompt
    
    # 按逗号分割
    parts = [p.strip() for p in prompt.split(',') if p.strip()]
    
    # 去重
    seen = set()
    unique_parts = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            unique_parts.append(p)
    
    # 按重要性排序（长度较长的通常更具体）
    # 保留最重要的词（长度长的优先）
    unique_parts.sort(key=lambda x: len(x), reverse=True)
    
    # 构建结果，限制长度
    result = []
    current_len = 0
    for part in unique_parts:
        # 粗略估计 token 数（每个词约 1-2 token）
        estimated_tokens = len(part.split()) + 2
        if current_len + estimated_tokens <= max_tokens:
            result.append(part)
            current_len += estimated_tokens
    
    return ', '.join(result) if result else prompt[:200]


# ===== 【新增】在 auto_shorten_prompt_for_clip 后面添加 count_tokens =====
def count_tokens(text):
    """粗略计算 token 数（CLIP 约 1-2 token/词）"""
    if not text:
        return 0
    return len(text.split()) + 2
    
def generate_image(pipe, is_sdxl, prompt, negative, image_path, output_path,
                   strength, steps, cfg, width, height, 
                   max_strength=0.55,
                   use_inpaint=False):

    # ===== 【新增】NSFW 过滤 =====
    if nsfw_config.enabled:
        # 检测 NSFW 内容
        has_nsfw, matched = nsfw_filter.detect_nsfw(prompt)
        if has_nsfw:
            print(f"   🔞 检测到 NSFW 关键词: {matched}")
            print(f"   当前等级: {nsfw_config.level.value}")
        
        # 根据等级过滤提示词
        prompt, negative = nsfw_filter.filter_prompt(prompt, negative)
        print(f"   过滤后提示词长度: {len(prompt)} 字符")
        
    # ===== 【修复】在这里调用精简函数 =====
    original_prompt_len = len(prompt)
    original_neg_len = len(negative)
    
    # ===== 【新增】精简提示词 =====
    prompt = auto_shorten_prompt_for_clip(prompt, max_tokens=70)
    negative = auto_shorten_prompt_for_clip(negative, max_tokens=70)

    if len(prompt) < original_prompt_len:
        print(f"   ✂️ 提示词精简: {original_prompt_len} -> {len(prompt)} 字符")
    
    # 检查 token 数
    token_count = count_tokens(prompt)
    if token_count > 75:
        print(f"   ⚠️ 提示词 token 数: {token_count}，可能被截断")
        
    try:
        init_image = Image.open(image_path).convert('RGB')
        
        # --- 1. 自动生成人物遮罩 (rembg) ---
        if use_inpaint:
            try:
                foreground = remove(init_image)
                mask = foreground.convert('L')
                mask = mask.point(lambda p: 255 if p > 30 else 0, mode='L')
                print(f"   🖌️ 已生成人物遮罩 (rembg)")
            except Exception as e:
                print(f"   ⚠️ rembg 失败，使用全图遮罩: {e}")
                mask = Image.new('L', init_image.size, 255)
        else:
            mask = None
        
        # --- 2. 尺寸调整 ---
        w, h = init_image.size
        if width > 0 and height > 0:
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
        
        # --- 3. 从配置读取 max_strength ---
        actual_strength = min(strength, max_strength)
        if actual_strength != strength:
            print(f"   ⚠️ strength 从 {strength} 降至 {actual_strength} (max_strength={max_strength})")
        
        # --- 4. 构造 Inpaint 管道 ---
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
        
        generator = torch.Generator("cpu").manual_seed(42)
        print(f"   🎨 开始重绘 (strength:{actual_strength:.2f}, steps:{steps})")

        # --- 5. 执行 ---
        if use_inpaint and mask is not None:
            result = pipe(
                prompt=prompt,
                negative_prompt=negative,
                image=init_image,
                mask_image=mask,
                strength=actual_strength,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
            )
        else:
            result = pipe(
                prompt=prompt,
                negative_prompt=negative,
                image=init_image,
                strength=actual_strength,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
            )
        
        # ✅ 保存临时图并后处理
        temp_path = output_path.replace('.png', '_temp.png')
        result.images[0].save(temp_path)        
        print(f"   ✅ 已保存临时图: {os.path.basename(temp_path)}")
        
        # ✅ 调用后处理：强制转为纯白大理石
        post_process_to_marble(temp_path, output_path, brightness_enhance=1.05)
        print(f"   ✅ 后处理完成: {os.path.basename(output_path)}")
        
        # 删除临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return True
    except Exception as e:
        print(f"   ❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        

def post_process_to_marble(image_path, output_path, brightness_enhance=1.0):
    """
    后处理：强制转为纯白大理石效果
    
    参数:
        image_path: 输入图片路径
        output_path: 输出图片路径
        brightness_enhance: 亮度增强系数 (1.0=不变, 1.05=提亮5%, 0.95=变暗5%)
                           设置为 1.0 即不调整亮度
    """
    try:
        img = Image.open(image_path).convert('RGB')
        
        # 1. 转为灰度（去色）
        gray = img.convert('L')
        
        # 2. 增强对比度（让阴影更清晰）
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(1.3)
        
        # 3. 亮度增强（可选）
        if brightness_enhance != 1.0:
            brightness = ImageEnhance.Brightness(enhanced)
            result = brightness.enhance(brightness_enhance)
        else:
            result = enhanced
        
        result.save(output_path)
        return output_path
        
    except Exception as e:
        print(f"   ⚠️ 后处理失败: {e}，直接保存原图")
        Image.open(image_path).save(output_path)
        return output_path
    
# ==================== 多进程专用函数 (修复版) ====================
def worker_process(jobs_slice, config):
    """
    子进程的工作函数：加载模型、批量生成分配给它的图片
    """
    import torch
    from PIL import Image, ImageEnhance
    from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, StableDiffusionInpaintPipeline
    from rembg import remove
    
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
    
    # ✅ 从配置读取 max_strength
    max_strength = config.get("max_strength", 0.55)
    
    # 2. 执行切片任务
    for job in jobs_slice:
        job_strength = job.get("strength", config.get("strength", 0.5))
        job_steps = job.get("steps", config.get("steps", 25))
        job_cfg = job.get("cfg", config.get("cfg", 7.5))
        
        # 生成文件名
        safe_name = "".join(c for c in job["name"] if c.isalnum() or c in " _-")[:50]
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}.png"
        output_path = os.path.join(config["output_dir"], filename)
        
        # ✅ 传递 max_strength
        generate_image(
            pipe, is_sdxl,
            job["prompt"], job["negative"],
            config["target_image"], output_path,
            job_strength, job_steps, job_cfg,
            job.get("width", 0), job.get("height", 0),
            max_strength=max_strength,  # ✅ 从配置读取
            use_inpaint=False
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
    
    # ✅ 从配置读取 max_strength
    max_strength = config.get("max_strength", 0.55)
    
    for idx, job in enumerate(config['jobs'], 1):
        name = job.get("name", f"job_{idx}")
        prompt = job["prompt"]
        negative = job.get("negative", "worst quality, low quality, deformed, blurry")
        width = job.get("width", 0)
        height = job.get("height", 0)
        strength = job.get("strength", config.get("strength", 0.5))
        steps = job.get("steps", config.get("steps", 25))
        cfg = job.get("cfg", config.get("cfg", 7.5))
        
        # ===== 【新增】在生成前精简提示词 =====
        #prompt = auto_shorten_prompt_for_clip(prompt, max_tokens=70)
        #negative = auto_shorten_prompt_for_clip(negative, max_tokens=60)        
        
        if len(prompt) > 280:
            prompt = prompt[:280]
        
        print(f"\n[{idx}/{len(config['jobs'])}] 🚀 {name}")
        print(f"   强度: {strength}, max_strength: {max_strength}, CFG: {cfg}")
        print(f"   提示词长度: {len(prompt)} 字符")
        #print(f"   预估 token 数: {count_tokens(prompt)}")
        
        safe_name = "".join(c for c in name if c.isalnum() or c in " _-")[:50]
        filename = f"{timestamp}_{idx:03d}_{safe_name}.png"
        output_path = os.path.join(output_dir, filename)
        
        # ✅ 传递 max_strength
        success = generate_image(
            pipe, is_sdxl, prompt, negative,
            config["target_image"], output_path,
            strength, steps, cfg, width, height,
            max_strength=max_strength
        )
        gc.collect()
    
    del pipe
    gc.collect()
    print("\n" + "=" * 60)
    print("✅ 所有任务完成！")
    print(f"📁 输出目录: {os.path.abspath(output_dir)}")
    print("=" * 60)


# ==================== 多进程主入口 ====================
def run_batch_parallel(config_file, processes=2):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    jobs = config["jobs"]
    total = len(jobs)
    
    output_dir = config.get("output_dir", "./output/batch_img2img")
    ensure_dir(output_dir)
    
    print("=" * 60)
    print(f"🚀 批量图生图任务 (多进程模式, {processes} 个进程)")
    print(f"配置文件: {config_file}")
    print(f"任务数: {total}")
    print(f"max_strength: {config.get('max_strength', 0.55)}")
    print("=" * 60)
    
    chunk_size = len(jobs) // processes
    chunks = []
    for i in range(processes):
        start = i * chunk_size
        end = start + chunk_size if i < processes - 1 else len(jobs)
        chunks.append(jobs[start:end])
    
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
                        help="配置文件路径")
    parser.add_argument("--parallel", action="store_true",
                        help="启用多进程模式")
    parser.add_argument("--processes", type=int, default=2,
                        help="多进程数量 (默认2)")
    parser.add_argument("--max-strength", type=float, default=None,  # ✅ 可选覆盖
                        help="覆盖配置文件中的 max_strength")
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"❌ 配置文件不存在: {args.config}")
        return
    
    # ✅ 如果命令行指定了 max_strength，临时覆盖配置文件
    if args.max_strength is not None:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config["max_strength"] = args.max_strength
        with open(args.config, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ 已覆盖 max_strength = {args.max_strength}")
    
    if args.parallel:
        run_batch_parallel(args.config, processes=args.processes)
    else:
        run_batch_single(args.config)


if __name__ == "__main__":
    main()