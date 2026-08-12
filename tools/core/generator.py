# tools/core/generator.py
"""核心生成逻辑"""

import os
import sys
import time
import random
import torch
from datetime import datetime
from PIL import Image

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)


SAFE_MODE = True  
# 安全模式策略：
#   "simple" = 简单模式：在提示词后加 "wearing clothes"
#   "filter" = 过滤模式：移除露骨词汇 (nude, naked, explicit, pornographic, sex, hentai)
SAFE_MODE_STRATEGY = "filter"  # 可选: "simple" 或 "filter"
# 是否启用去水印
REMOVE_WATERMARK = True
# ==================== ⚙️ 内容文本开关 ====================
# 是否启用 content_texts 字段（将文本内容添加到提示词中）
USE_CONTENT_TEXTS = True  # 默认关闭，设为 True 开启
# ========================================================

from tools.config import (
    STEPS,
    MAX_LIMIT,
    #SAFE_MODE,
    #SAFE_MODE_STRATEGY,
    REMOVE_AI_TRACES,
    SKETCH_KEYWORDS,
    AUTO_DETECT_STYLE,
    #USE_CONTENT_TEXTS,
)
from tools.core.postprocessor import remove_ai_traces, is_sketch_style


def build_prompt(config):
    """
    分层构建提示词
    支持三种格式：
    1. 分层格式：subjects + styles + moods
    2. 扁平格式：只有 subjects（兼容旧配置）
    3. 内容文本扩展：subjects + styles + moods + content_texts
    """
    if "styles" in config and "moods" in config:
        subject = random.choice(config["subjects"])
        style = random.choice(config["styles"])
        mood = random.choice(config["moods"])
        
        if USE_CONTENT_TEXTS and "content_texts" in config and config["content_texts"]:
            text = random.choice(config["content_texts"])
            prompt = (
                f"{subject}, {style}, {mood}, "
                f"the scroll features the Chinese characters '{text}' written in flowing calligraphy"
            )
            print(f"   📜 已添加内容文本: {text[:20]}...")
        else:
            prompt = f"{subject}, {style}, {mood}"
        return prompt, "分层"
    else:
        prompt = random.choice(config["subjects"])
        return prompt, "扁平"


def generate_style(pipe, init_image, prompt, output_filename, strength, 
                   mode="img2img", steps=STEPS, target_style="unknown"):
    """
    生成单张图片
    mode: "img2img" 或 "txt2img"
    steps: 当前生成使用的步数
    """
    # ========== 调试信息 ==========
    print(f"\n{'='*50}")
    print(f"📊 [调试] 参数详情:")
    print(f"  ├─ 图生图强度 (strength): {strength}")
    print(f"  └─ 迭代步数 (steps): {steps}")
    print(f"{'='*50}\n")
    
    max_limit = MAX_LIMIT
    
    if mode == "img2img":
        # 图生图：使用原图尺寸
        w, h = init_image.size
        if w > max_limit or h > max_limit:
            scale = max_limit / max(w, h)
            w, h = int(w * scale), int(h * scale)
        w, h = ((w + 31) // 64) * 64, ((h + 31) // 64) * 64
        
        try:
            image = init_image.resize((w, h), Image.Resampling.LANCZOS)
        except AttributeError:
            image = init_image.resize((w, h), Image.LANCZOS)
            
        print(f"[图生图] {os.path.basename(output_filename)} ({w}x{h})")
    else:
        # 文生图：随机选择尺寸
        aspect_ratios = [
            (512, 512), (512, 576), (576, 512), (512, 640), (640, 512),
            (512, 768), (768, 512), (576, 768), (768, 576), (448, 640), (640, 448),
            (768, 1360), (1080, 1920), (768, 1024),
            (1024, 576), (1280, 720), (1360, 768),
            (768, 768), (1024, 1024)
        ]
        w, h = random.choice(aspect_ratios)
        if w > max_limit:
            w = max_limit
        if h > max_limit:
            h = max_limit
        w, h = ((w + 31) // 64) * 64, ((h + 31) // 64) * 64
        image = None
        print(f"[文生图] {os.path.basename(output_filename)} ({w}x{h})")

    # ========== 安全模式处理 ==========
    full_prompt, neg_prompt = _apply_safety_mode(prompt)
    
    # ========== 自动添加解剖约束 ==========
    full_prompt = _add_anatomy_constraints(full_prompt)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 提示词: {full_prompt[:80]}...")
    print(f"  步数: {steps}")
    
    generator = torch.Generator("cpu").manual_seed(int(time.time_ns() % 1000000000))
    
    # ========== 生成 ==========
    gen_kwargs = {
        "prompt": full_prompt,
        "negative_prompt": neg_prompt,
        "num_inference_steps": steps,
        "guidance_scale": 7.5,
        "generator": generator,
        "width": w,
        "height": h,
    }
    
    if mode == "img2img":
        gen_kwargs["image"] = image
        gen_kwargs["strength"] = strength
    
    result = pipe(**gen_kwargs)
    
    # 保存图片
    result.images[0].save(output_filename, quality=95)
    
    # ========== 检测风格 ==========
    is_sketch = False
    if AUTO_DETECT_STYLE:
        prompt_lower = prompt.lower()
        is_sketch = any(kw in prompt_lower for kw in SKETCH_KEYWORDS)
        if not is_sketch:
            is_sketch = any(kw in target_style.lower() for kw in SKETCH_KEYWORDS)
    
    if is_sketch:
        print(f"\n🎨 检测到素描/线稿风格，仅清除元数据，跳过相机相关处理")
    
    # ========== 消除AI痕迹 ==========
    final_output = output_filename
    if REMOVE_AI_TRACES:
        final_output = remove_ai_traces(output_filename, is_sketch)
    
    # ========== 生成元数据文件 ==========
    _save_metadata(
        final_output, prompt, full_prompt, neg_prompt,
        target_style, mode, steps, strength, is_sketch
    )
    
    return final_output


def _apply_safety_mode(prompt):
    """应用安全模式"""
    if not SAFE_MODE:
        neg_prompt = _get_default_negative()
        return prompt, neg_prompt
    
    if SAFE_MODE_STRATEGY == "simple":
        full_prompt = f"{prompt}, wearing clothes"
        print(f"🛡️ [安全模式] 策略: 简单 (附加 wearing clothes)")
    elif SAFE_MODE_STRATEGY == "filter":
        safe_prompt = prompt
        for word in ["nude", "naked", "explicit", "pornographic"]:
            safe_prompt = safe_prompt.replace(word, "")
        for word in ["sex", "hentai", "penetration"]:
            safe_prompt = ", ".join([
                p for p in safe_prompt.split(",") 
                if word not in p.lower()
            ])
        safe_prompt = ", ".join([p.strip() for p in safe_prompt.split(",") if p.strip()])
        full_prompt = safe_prompt if safe_prompt.strip() else prompt
        print(f"🛡️ [安全模式] 策略: 过滤 (移除露骨词汇)")
    else:
        full_prompt = f"{prompt}, wearing clothes"
        print(f"🛡️ [安全模式] 策略: 默认 (附加 wearing clothes)")
    
    neg_prompt = _get_default_negative()
    return full_prompt, neg_prompt


def _get_default_negative():
    """获取默认负面提示词"""
    return (
        "worst quality, low quality, ugly, deformed, blurry, watermark, signature, logo, brand, "
        "bad hands, extra fingers, missing fingers, fused fingers, deformed hands, "
        "mutated hands, poorly drawn hands, six fingers, eleven fingers, "
        "bad anatomy, malformed limbs, extra limbs, missing limbs, "
        "bad proportions, disfigured, gross proportions, "
        "bad feet, extra toes, missing toes, fused toes, "
        "jumbled text, gibberish characters, messy ink, smudged writing, illegible scribbles"
    )


def _add_anatomy_constraints(prompt):
    """添加解剖约束"""
    prompt_lower = prompt.lower()
    constraints = []
    
    complex_pose_keywords = [
        "sex", "posing", "bending", "kneeling", "lying", 
        "standing", "spooning", "riding", "missionary", 
        "doggy", "cowgirl", "spread", "bent over", 
        "on top", "from behind", "oral", "blowjob", 
        "cunnilingus", "group", "threesome"
    ]
    multi_person_keywords = ["two", "multiple", "group", "couple", "pair", "man and woman"]
    wing_keywords = ["angel wings", "feathered wings", "bird wings", "butterfly wings", 
                     "dragon wings", "wings spread", "winged figure"]
    
    # 草稿阻断
    sketch_keywords = ["sketch", "pencil", "draft", "wireframe", "construction", 
                       "anatomy", "lineart", "structural"]
    if any(k in prompt_lower for k in sketch_keywords):
        wing_keywords = []
    
    if any(k in prompt_lower for k in complex_pose_keywords):
        constraints.extend(["natural body position", "correct anatomy", "realistic hands and feet"])
    
    if any(k in prompt_lower for k in multi_person_keywords):
        constraints.extend(["two hands per person", "two feet per person", "normal proportions"])
    
    if any(k in prompt_lower for k in wing_keywords):
        constraints.append("symmetrical wings")
        constraints.append("beautiful feathered wings")
    
    if constraints:
        constraint_text = ", ".join(constraints)
        prompt = f"{prompt}, {constraint_text}"
        print(f"   🧠 已添加解剖约束: {constraint_text}")
    
    return prompt


def _save_metadata(filepath, original_prompt, full_prompt, neg_prompt, 
                   target_style, mode, steps, strength, is_sketch):
    """保存元数据文件"""
    from tools.config import (
        AI_STRENGTH, AI_CHROMATIC_STRENGTH, REMOVE_AI_TRACES,
        AI_CLEAR_METADATA, AI_REALISTIC, AI_CAMERA, AI_INJECT_EXIF,
        AI_CHROMATIC_ABERRATION, AI_REALISTIC_NOISE, AI_NOISE_ISO_BASE,
        AI_MINOR_CROP, AI_CROP_PERCENT, AI_FINGERPRINT_OBFUSCATION,
        DEFAULT_STRENGTH
    )
    
    metadata_filename = filepath.replace('.png', '.txt').replace('.jpg', '.txt')
    
    try:
        with open(metadata_filename, "w", encoding="utf-8") as f:
            f.write(f"【生成时间】: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"【风格名称】: {target_style}\n")
            f.write(f"【生成模式】: {mode}\n")
            f.write(f"【迭代步数】: {steps}\n")
            f.write(f"\n【📊 Strength 参数详情】:\n")
            
            # 判断是否使用了默认强度
            if strength == DEFAULT_STRENGTH:
                f.write(f"  ├─ 图生图强度 (img2img strength): {DEFAULT_STRENGTH} (默认值)\n")
            else:
                f.write(f"  ├─ 图生图强度 (img2img strength): {strength}\n")
            f.write(f"  ├─ 照片真实化强度 (AI_STRENGTH): {AI_STRENGTH}\n")
            f.write(f"  ├─ 紫边模拟强度 (AI_CHROMATIC_STRENGTH): {AI_CHROMATIC_STRENGTH}\n")
            f.write(f"  └─ 消除AI痕迹总开关: {'✅ 已启用' if REMOVE_AI_TRACES else '❌ 已禁用'}\n")
            f.write(f"\n【📝 完整正向提示词】: \n{full_prompt}\n")
            f.write(f"\n【📝 完整负面提示词】: \n{neg_prompt}\n")
            
            if mode == "img2img":
                f.write(f"\n【🖼️ 参考图路径】: input.jpg\n")
            
            if REMOVE_AI_TRACES:
                f.write(f"\n【🔧 消除AI痕迹配置】:\n")
                f.write(f"   - 总开关: ✅ 已启用\n")
                f.write(f"   - 元数据清理: {'✅' if AI_CLEAR_METADATA else '❌'}\n")
                
                if is_sketch:
                    f.write(f"   - 风格检测: 素描/线稿 (⚠️ 跳过相机相关处理)\n")
                    f.write(f"   - 照片真实化: ⏭️ 已跳过 (素描风格)\n")
                    f.write(f"   - EXIF注入: ⏭️ 已跳过 (素描风格)\n")
                    f.write(f"   - 紫边模拟: ⏭️ 已跳过 (素描风格)\n")
                    f.write(f"   - 真实噪点: ⏭️ 已跳过 (素描风格)\n")
                    f.write(f"   - 轻微裁剪: {'✅' if AI_MINOR_CROP else '❌'} ({AI_CROP_PERCENT*100:.1f}%)\n")
                    f.write(f"   - 指纹混淆: {'✅' if AI_FINGERPRINT_OBFUSCATION else '❌'}\n")
                else:
                    f.write(f"   - 照片真实化: {'✅' if AI_REALISTIC else '❌'}\n")
                    f.write(f"   - 相机型号: {AI_CAMERA}\n")
                    f.write(f"   - 真实化强度: {AI_STRENGTH}\n")
                    f.write(f"   - EXIF注入: {'✅' if AI_INJECT_EXIF else '❌'}\n")
                    f.write(f"   - 紫边模拟: {'✅' if AI_CHROMATIC_ABERRATION else '❌'} (强度: {AI_CHROMATIC_STRENGTH})\n")
                    f.write(f"   - 真实噪点: {'✅' if AI_REALISTIC_NOISE else '❌'} (ISO: {AI_NOISE_ISO_BASE})\n")
                    f.write(f"   - 轻微裁剪: {'✅' if AI_MINOR_CROP else '❌'} ({AI_CROP_PERCENT*100:.1f}%)\n")
                    f.write(f"   - 指纹混淆: {'✅' if AI_FINGERPRINT_OBFUSCATION else '❌'}\n")
        
        print(f"   📝 已生成提示词记录: {os.path.basename(metadata_filename)}")
    except Exception as e:
        print(f"   ⚠️ 提示词记录文件写入失败: {e}")