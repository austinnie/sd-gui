#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
謇ｹ驥丞崟逕溷崟逕滓仙勣 (菫ｮ螟咲沿)
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
    EulerDiscreteScheduler  # 笨 豺ｻ蜉 
)

# ==================== 扈滉ｸ郛灘ｭ倡岼蠖包ｼ亥ｿ鬘ｻ蝨ｨ蟇ｼ蜈･蠎謎ｹ句燕隶ｾ鄂ｮïｼ====================
CACHE_ROOT = r"E:\hf_cache\.cache"

# 笨 隶ｾ鄂ｮ謇譛臥ｼ灘ｭ倡岼蠖
os.environ['HF_HOME'] = CACHE_ROOT
os.environ['U2NET_HOME'] = os.path.join(CACHE_ROOT, "u2net")
os.environ['DEEPFACE_HOME'] = os.path.join(CACHE_ROOT, "deepface")

# 笨 蛻帛ｻｺ謇譛臥岼蠖
for env_var in ['HF_HOME', 'U2NET_HOME', 'DEEPFACE_HOME']:
    path = os.environ[env_var]
    os.makedirs(path, exist_ok=True)
    print(f"ð沒 {env_var} = {path}")

# 笨 邇ｰ蝨ｨ謇榊ｯｼ蜈･萓晁ｵ門ｺ
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
    """蜉 霓ｽ SD 讓｡蝙具ｼ亥黒霑帷ｨ倶ｸ鍋畑ïｼ"""
    # ===== 縲先眠蠅槭鮮SFW 讓｡蝙句謐｢ =====
    if nsfw_config.use_dedicated_models:
        if nsfw_config.level in [ContentLevel.EXPLICIT, ContentLevel.EXTREME]:
            explicit_path = nsfw_config.explicit_model_path
            if os.path.exists(explicit_path):
                print(f"ð沐 菴ｿ逕ｨ謌蝉ｺｺ讓｡蝙: {os.path.basename(explicit_path)}")
                model_path = explicit_path
                
    print(f"ð沒ｦ 蜉 霓ｽ蝗ｾ逕溷崟讓｡蝙: {os.path.basename(model_path)}...")
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
        print("笨 讓｡蝙句刈霓ｽ螳梧撰ｼ")
        

        # 笨 菴ｿ逕ｨ EulerDiscreteScheduler
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        print(f"笨 菴ｿ逕ｨ EulerDiscreteScheduler (遞ｳ螳夊ｰ蠎ｦ蝎ｨ)")
        
        return pipe, is_sdxl
    except Exception as e:
        print(f"笶 蜉 霓ｽ螟ｱ雍･: {e}")
        return None, None


def auto_shorten_prompt_for_clip(prompt, max_tokens=70):
    """
    邊ｾ邂謠千､ｺ隸堺ｻ･騾ょｺ CLIP 77 token 髯仙宛
    蜿よ焚:
        prompt: 蜴溷ｧ区署遉ｺ隸
        max_tokens: 譛螟ｧ token 謨ｰ (蟒ｺ隶ｮ 70ïｼ檎蕗菴咎㍼)
    
    霑泌屓:
        邊ｾ邂蜷守噪謠千､ｺ隸
    """
    if not prompt:
        return prompt
    
    # 謖蛾怜捷蛻蜑ｲ
    parts = [p.strip() for p in prompt.split(',') if p.strip()]
    
    # 蜴ｻ驥
    seen = set()
    unique_parts = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            unique_parts.append(p)
    
    # 謖蛾㍾隕∵ｧ謗貞ｺ擾ｼ磯柄蠎ｦ霎髟ｿ逧騾壼ｸｸ譖ｴ蜈ｷ菴難ｼ
    # 菫晉蕗譛驥崎ｦ∫噪隸搾ｼ磯柄蠎ｦ髟ｿ逧莨伜茨ｼ
    unique_parts.sort(key=lambda x: len(x), reverse=True)
    
    # 譫蟒ｺ扈捺棡ïｼ碁剞蛻ｶ髟ｿ蠎ｦ
    result = []
    current_len = 0
    for part in unique_parts:
        # 邊礼払莨ｰ隶｡ token 謨ｰïｼ域ｯ丈ｸｪ隸咲ｺｦ 1-2 tokenïｼ
        estimated_tokens = len(part.split()) + 2
        if current_len + estimated_tokens <= max_tokens:
            result.append(part)
            current_len += estimated_tokens
    
    return ', '.join(result) if result else prompt[:200]


# ===== 縲先眠蠅槭大惠 auto_shorten_prompt_for_clip 蜷朱擇豺ｻ蜉  count_tokens =====
def count_tokens(text):
    """邊礼払隶｡邂 token 謨ｰïｼCLIP 郤ｦ 1-2 token/隸搾ｼ"""
    if not text:
        return 0
    return len(text.split()) + 2
    
def generate_image(pipe, is_sdxl, prompt, negative, image_path, output_path,
                   strength, steps, cfg, width, height, 
                   max_strength=0.55,
                   use_inpaint=False):

    # ===== 縲先眠蠅槭鮮SFW 霑貊､ =====
    if nsfw_config.enabled:
        # 譽豬 NSFW 蜀螳ｹ
        has_nsfw, matched = nsfw_filter.detect_nsfw(prompt)
        if has_nsfw:
            print(f"   ð沐 譽豬句芦 NSFW 蜈ｳ髞ｮ隸: {matched}")
            print(f"   蠖灘燕遲臥ｺｧ: {nsfw_config.level.value}")
        
        # 譬ｹ謐ｮ遲臥ｺｧ霑貊､謠千､ｺ隸
        prompt, negative = nsfw_filter.filter_prompt(prompt, negative)
        print(f"   霑貊､蜷取署遉ｺ隸埼柄蠎ｦ: {len(prompt)} 蟄礼ｬｦ")
        
    # ===== 縲蝉ｿｮ螟阪大惠霑咎㈹隹逕ｨ邊ｾ邂蜃ｽ謨ｰ =====
    original_prompt_len = len(prompt)
    original_neg_len = len(negative)
    
    # ===== 縲先眠蠅槭醍ｲｾ邂謠千､ｺ隸 =====
    prompt = auto_shorten_prompt_for_clip(prompt, max_tokens=70)
    negative = auto_shorten_prompt_for_clip(negative, max_tokens=70)

    if len(prompt) < original_prompt_len:
        print(f"   笨ゑｸ 謠千､ｺ隸咲ｲｾ邂: {original_prompt_len} -> {len(prompt)} 蟄礼ｬｦ")
    
    # 譽譟･ token 謨ｰ
    token_count = count_tokens(prompt)
    if token_count > 75:
        print(f"   笞 ïｸ 謠千､ｺ隸 token 謨ｰ: {token_count}ïｼ悟庄閭ｽ陲ｫ謌ｪ譁ｭ")
        
    try:
        init_image = Image.open(image_path).convert('RGB')
        
        # --- 1. 閾ｪ蜉ｨ逕滓蝉ｺｺ迚ｩ驕ｮ鄂ｩ (rembg) ---
        if use_inpaint:
            try:
                foreground = remove(init_image)
                mask = foreground.convert('L')
                mask = mask.point(lambda p: 255 if p > 30 else 0, mode='L')
                print(f"   ð泱鯉ｸ 蟾ｲ逕滓蝉ｺｺ迚ｩ驕ｮ鄂ｩ (rembg)")
            except Exception as e:
                print(f"   笞 ïｸ rembg 螟ｱ雍･ïｼ御ｽｿ逕ｨ蜈ｨ蝗ｾ驕ｮ鄂ｩ: {e}")
                mask = Image.new('L', init_image.size, 255)
        else:
            mask = None
        
        # --- 2. 蟆ｺ蟇ｸ隹謨ｴ ---
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
        
        # --- 3. 莉朱咲ｽｮ隸ｻ蜿 max_strength ---
        actual_strength = min(strength, max_strength)
        if actual_strength != strength:
            print(f"   笞 ïｸ strength 莉 {strength} 髯崎ｳ {actual_strength} (max_strength={max_strength})")
        
        # --- 4. 譫騾  Inpaint 邂｡驕 ---
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
        print(f"   ð沁ｨ 蠑蟋矩㍾扈 (strength:{actual_strength:.2f}, steps:{steps})")

        # --- 5. 謇ｧ陦 ---
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
        
        # 笨 菫晏ｭ倅ｸｴ譌ｶ蝗ｾ蟷ｶ蜷主､逅
        temp_path = output_path.replace('.png', '_temp.png')
        result.images[0].save(temp_path)        
        print(f"   笨 蟾ｲ菫晏ｭ倅ｸｴ譌ｶ蝗ｾ: {os.path.basename(temp_path)}")
        
        # 笨 隹逕ｨ蜷主､逅ïｼ壼ｼｺ蛻ｶ霓ｬ荳ｺ郤ｯ逋ｽ螟ｧ逅遏ｳ
        post_process_to_marble(temp_path, output_path, brightness_enhance=1.05)
        print(f"   笨 蜷主､逅螳梧: {os.path.basename(output_path)}")
        
        # 蛻 髯､荳ｴ譌ｶ譁莉ｶ
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return True
    except Exception as e:
        print(f"   笶 逕滓仙､ｱ雍･: {e}")
        import traceback
        traceback.print_exc()
        return False
        

def post_process_to_marble(image_path, output_path, brightness_enhance=1.0):
    """
    蜷主､逅ïｼ壼ｼｺ蛻ｶ霓ｬ荳ｺ郤ｯ逋ｽ螟ｧ逅遏ｳ謨域棡
    
    蜿よ焚:
        image_path: 霎灘･蝗ｾ迚霍ｯ蠕
        output_path: 霎灘ｺ蝗ｾ迚霍ｯ蠕
        brightness_enhance: 莠ｮ蠎ｦ蠅槫ｼｺ邉ｻ謨ｰ (1.0=荳榊序, 1.05=謠蝉ｺｮ5%, 0.95=蜿俶囓5%)
                           隶ｾ鄂ｮ荳ｺ 1.0 蜊ｳ荳崎ｰ謨ｴ莠ｮ蠎ｦ
    """
    try:
        img = Image.open(image_path).convert('RGB')
        
        # 1. 霓ｬ荳ｺ轣ｰ蠎ｦïｼ亥悉濶ｲïｼ
        gray = img.convert('L')
        
        # 2. 蠅槫ｼｺ蟇ｹ豈泌ｺｦïｼ郁ｮｩ髦ｴ蠖ｱ譖ｴ貂譎ｰïｼ
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(1.3)
        
        # 3. 莠ｮ蠎ｦ蠅槫ｼｺïｼ亥庄騾会ｼ
        if brightness_enhance != 1.0:
            brightness = ImageEnhance.Brightness(enhanced)
            result = brightness.enhance(brightness_enhance)
        else:
            result = enhanced
        
        result.save(output_path)
        return output_path
        
    except Exception as e:
        print(f"   笞 ïｸ 蜷主､逅螟ｱ雍･: {e}ïｼ檎峩謗･菫晏ｭ伜次蝗ｾ")
        Image.open(image_path).save(output_path)
        return output_path
    
# ==================== 螟夊ｿ帷ｨ倶ｸ鍋畑蜃ｽ謨ｰ (菫ｮ螟咲沿) ====================
def worker_process(jobs_slice, config):
    """
    蟄占ｿ帷ｨ狗噪蟾･菴懷ｽ謨ｰïｼ壼刈霓ｽ讓｡蝙九∵音驥冗函謌仙驟咲ｻ吝ｮ逧蝗ｾ迚
    """
    import torch
    from PIL import Image, ImageEnhance
    from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, StableDiffusionInpaintPipeline
    from rembg import remove
    
    # 1. 豈丈ｸｪ霑帷ｨ句黒迢ｬ蜉 霓ｽ荳谺｡讓｡蝙
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
    
    # 笨 莉朱咲ｽｮ隸ｻ蜿 max_strength
    max_strength = config.get("max_strength", 0.55)
    
    # 2. 謇ｧ陦悟迚莉ｻ蜉｡
    for job in jobs_slice:
        job_strength = job.get("strength", config.get("strength", 0.5))
        job_steps = job.get("steps", config.get("steps", 25))
        job_cfg = job.get("cfg", config.get("cfg", 7.5))
        
        # 逕滓先枚莉ｶ蜷
        safe_name = "".join(c for c in job["name"] if c.isalnum() or c in " _-")[:50]
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}.png"
        output_path = os.path.join(config["output_dir"], filename)
        
        # 笨 莨 騾 max_strength
        generate_image(
            pipe, is_sdxl,
            job["prompt"], job["negative"],
            config["target_image"], output_path,
            job_strength, job_steps, job_cfg,
            job.get("width", 0), job.get("height", 0),
            max_strength=max_strength,  # 笨 莉朱咲ｽｮ隸ｻ蜿
            use_inpaint=False
        )


# ==================== 蜊慕ｺｿ遞倶ｸｻ蜈･蜿｣ ====================
def run_batch_single(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("=" * 60)
    print("ð泅 謇ｹ驥丞崟逕溷崟莉ｻ蜉｡ (蜊慕ｺｿ遞区ｨ｡蠑)")
    print(f"驟咲ｽｮ譁莉ｶ: {config_file}")
    print(f"莉ｻ蜉｡謨ｰ: {len(config['jobs'])}")
    print("=" * 60)
    
    model_path = config.get("model_path")
    pipe, is_sdxl = load_pipe(model_path)
    if pipe is None:
        return
    
    output_dir = config.get("output_dir", "./output/batch_img2img")
    ensure_dir(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 笨 莉朱咲ｽｮ隸ｻ蜿 max_strength
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
        
        # ===== 縲先眠蠅槭大惠逕滓仙燕邊ｾ邂謠千､ｺ隸 =====
        #prompt = auto_shorten_prompt_for_clip(prompt, max_tokens=70)
        #negative = auto_shorten_prompt_for_clip(negative, max_tokens=60)        
        
        if len(prompt) > 280:
            prompt = prompt[:280]
        
        print(f"\n[{idx}/{len(config['jobs'])}] ð泅 {name}")
        print(f"   蠑ｺ蠎ｦ: {strength}, max_strength: {max_strength}, CFG: {cfg}")
        print(f"   謠千､ｺ隸埼柄蠎ｦ: {len(prompt)} 蟄礼ｬｦ")
        #print(f"   鬚莨ｰ token 謨ｰ: {count_tokens(prompt)}")
        
        safe_name = "".join(c for c in name if c.isalnum() or c in " _-")[:50]
        filename = f"{timestamp}_{idx:03d}_{safe_name}.png"
        output_path = os.path.join(output_dir, filename)
        
        # 笨 莨 騾 max_strength
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
    print("笨 謇譛我ｻｻ蜉｡螳梧撰ｼ")
    print(f"ð沒 霎灘ｺ逶ｮ蠖: {os.path.abspath(output_dir)}")
    print("=" * 60)


# ==================== 螟夊ｿ帷ｨ倶ｸｻ蜈･蜿｣ ====================
def run_batch_parallel(config_file, processes=2):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    jobs = config["jobs"]
    total = len(jobs)
    
    output_dir = config.get("output_dir", "./output/batch_img2img")
    ensure_dir(output_dir)
    
    print("=" * 60)
    print(f"ð泅 謇ｹ驥丞崟逕溷崟莉ｻ蜉｡ (螟夊ｿ帷ｨ区ｨ｡蠑, {processes} 荳ｪ霑帷ｨ)")
    print(f"驟咲ｽｮ譁莉ｶ: {config_file}")
    print(f"莉ｻ蜉｡謨ｰ: {total}")
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
    print("笨 謇譛我ｻｻ蜉｡螳梧撰ｼ")
    print(f"ð沒 霎灘ｺ逶ｮ蠖: {os.path.abspath(output_dir)}")
    print("=" * 60)


# ==================== 蜻ｽ莉､陦悟･蜿｣ ====================
def main():
    parser = argparse.ArgumentParser(description="謇ｹ驥丞崟逕溷崟蟾･蜈ｷ")
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="驟咲ｽｮ譁莉ｶ霍ｯ蠕")
    parser.add_argument("--parallel", action="store_true",
                        help="蜷ｯ逕ｨ螟夊ｿ帷ｨ区ｨ｡蠑")
    parser.add_argument("--processes", type=int, default=2,
                        help="螟夊ｿ帷ｨ区焚驥 (鮟倩ｮ､2)")
    parser.add_argument("--max-strength", type=float, default=None,  # 笨 蜿ｯ騾芽ｦ逶
                        help="隕逶夜咲ｽｮ譁莉ｶ荳ｭ逧 max_strength")
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"笶 驟咲ｽｮ譁莉ｶ荳榊ｭ伜惠: {args.config}")
        return
    
    # 笨 螯よ棡蜻ｽ莉､陦梧欠螳壻ｺ max_strengthïｼ御ｸｴ譌ｶ隕逶夜咲ｽｮ譁莉ｶ
    if args.max_strength is not None:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config["max_strength"] = args.max_strength
        with open(args.config, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"笨 蟾ｲ隕逶 max_strength = {args.max_strength}")
    
    if args.parallel:
        run_batch_parallel(args.config, processes=args.processes)
    else:
        run_batch_single(args.config)


if __name__ == "__main__":
    main()