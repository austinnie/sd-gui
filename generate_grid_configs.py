# generate_grid_configs_v2.py
"""
多维度网格测试配置文件生成器 (优化版)
所有配置文件统一放在 grid_configs/ 目录下
支持: SD 1.5, SDXL, Lightning 极速模型
"""

import os
import json
from itertools import product

# ========== 动态获取项目配置路径 ==========
from config.app_config import app_config
model_base_paths = app_config.paths.get_resolved_model_paths()

# 如果没有读到配置，使用备用路径
sd15_folder = model_base_paths[0] if len(model_base_paths) > 0 else "../models/sd-v1-5"
sdxl_folder = model_base_paths[1] if len(model_base_paths) > 1 else "../models/sdxl"


# ========== 模型列表 ==========
SD15_MODELS = [
    "aiiiiiii01_v10.safetensors",
    "anycharactermixBaked_v20BakedVae.safetensors",
    "anytimeRealistic_v10.safetensors",
    "asianrealisticSdlife_v40.safetensors",
    "detailAsianRealistic_v60X21b.safetensors",
    "evalisenniaRealisticEastAsian_v40.safetensors",
    "evalisenniaSD15Ultra_v20.safetensors",
    "fantasticchixHR_v10Fp16NoEma.safetensors",
    "girlMix_V2.safetensors",
    "henmixrealV10_henmixrealV10.safetensors",
    "nexblendApex04Asian_v10.safetensors",
    "nexblendmixVividAsian_v10.safetensors",
    "nextphoto_v30.safetensors",
    "realisticmix_iiV12Version12.safetensors",
    "shmRealistic_v40.safetensors",
    "t3_sdVer3.safetensors",
    "ultimixFantastic_v11.safetensors",
    "zemihr_v2.safetensors",
]

SDXL_MODELS = [
    "perfectionAsianILXL_v10.safetensors",
    "xlAsianRealisticMixNhiPNhChU_v10.safetensors",
]

# Lightning 极速模型 (包含 1步, 2步, 4步)
LIGHTNING_MODELS = [
    "sdxl_lightning_1step_x0.safetensors",
    "sdxl_lightning_2step.safetensors",
    "sdxl_lightning_4step.safetensors",
]

JANUS_MODELS = ["1B", "7B"]

# ========== 预设尺寸（更多尺寸） ==========
PRESET_SIZES = {
    # SD 1.5 常用尺寸
    "标全(512x768)": {"width": 512, "height": 768},
    "标全_横(768x512)": {"width": 768, "height": 512},
    "细全(512x1024)": {"width": 512, "height": 1024},
    "高全(640x960)": {"width": 640, "height": 960},
    "极全(640x1024)": {"width": 640, "height": 1024},
    "超长(576x1024)": {"width": 576, "height": 1024},
    "方图(768x768)": {"width": 768, "height": 768},
    "横图(896x512)": {"width": 896, "height": 512},
    
    # SDXL 专用尺寸
    "SDXL方图(1024x1024)": {"width": 1024, "height": 1024},
    "SDXL竖图(896x1152)": {"width": 896, "height": 1152},
    "SDXL竖图(832x1216)": {"width": 832, "height": 1216},
    "SDXL竖图(768x1344)": {"width": 768, "height": 1344},
    "SDXL横图(1152x896)": {"width": 1152, "height": 896},
    "SDXL横图(1216x832)": {"width": 1216, "height": 832},
    "SDXL宽屏(1344x768)": {"width": 1344, "height": 768},
    "SDXL超宽(1536x640)": {"width": 1536, "height": 640},
    
    # 通用大尺寸（谨慎使用，CPU 可能内存不足）
    "大图(1024x768)": {"width": 1024, "height": 768},
    "大图(1280x720)": {"width": 1280, "height": 720},
    "大图(1920x1080)": {"width": 1920, "height": 1080},
}

# ========== 质量关键词 ==========
QUALITY_PROMPTS = {
    "sd15": "masterpiece, best quality, highly detailed, sharp focus",
    "sdxl": "masterpiece, best quality, highly detailed, sharp focus",
    "janus": "masterpiece, best quality, highly detailed",
}

NEGATIVE_PROMPT = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature"

# ========== 测试参数范围 ==========
STEPS_SD15 = [20, 25, 30]
STEPS_SDXL = [30, 35, 40]
STEPS_LIGHTNING = [1, 4, 8, 10]  # 加入 1步，对应 lightning_1step_x0
CFG_VALUES = [7.0, 7.5, 8.0]

# 尺寸列表
SIZES_SD15 = [
    "标全(512x768)", 
    "标全_横(768x512)",
    "高全(640x960)", 
    "方图(768x768)", 
    "横图(896x512)",
]

SIZES_SDXL = [
    "SDXL方图(1024x1024)",
    "SDXL竖图(896x1152)",
    "SDXL竖图(832x1216)",
    "SDXL横图(1152x896)",
    "SDXL宽屏(1344x768)",
]

# Lightning 极速专用尺寸 (只跑最常用的一两个尺寸，防止CPU崩)
SIZES_LIGHTNING = [
    "SDXL方图(1024x1024)",
    "SDXL竖图(896x1152)",
]

# 是否启用高清修复
HIRES_VALUES = [False, True]

# Janus 参数
JANUS_TEMPS = [0.4, 0.6, 0.8, 1.0, 1.2]
JANUS_TOKENS = [1024, 2048, 4096]


# ==================== 核心生成逻辑 ====================

def generate_sd_grid_configs(output_dir="grid_configs"):
    """生成 SD/SDXL/Lightning 网格测试配置 (一模型一文件)"""
    os.makedirs(output_dir, exist_ok=True)
    
    # ===== 1. 统一模型列表 =====
    all_models = []
    for m in SD15_MODELS: all_models.append({"name": m, "type": "sd15", "folder": sd15_folder})
    for m in SDXL_MODELS: all_models.append({"name": m, "type": "sdxl", "folder": sdxl_folder})
    for m in LIGHTNING_MODELS: all_models.append({"name": m, "type": "lightning", "folder": sdxl_folder})

    configs = []
    
    # ===== 2. 循环遍历模型 =====
    for model_info in all_models:
        model_name = model_info["name"]
        model_type = model_info["type"]
        model_folder = model_info["folder"]
        
        # 根据类型分配参数
        if model_type == "lightning":
            steps_list = STEPS_LIGHTNING
            size_list = SIZES_LIGHTNING
            quality_tag = QUALITY_PROMPTS["sdxl"]
        elif model_type == "sdxl":
            steps_list = STEPS_SDXL
            size_list = SIZES_SDXL
            quality_tag = QUALITY_PROMPTS["sdxl"]
        else: # sd15
            steps_list = STEPS_SD15
            size_list = SIZES_SD15
            quality_tag = QUALITY_PROMPTS["sd15"]

        # 基础提示词
        prompt = f"{quality_tag}, a beautiful Asian woman, wearing elegant dress, full body shot, detailed face, natural lighting"
        
        # 打包当前模型的所有参数组合
        grid_combos = []
        for steps, cfg, size_name, hires in product(steps_list, CFG_VALUES, size_list, HIRES_VALUES):
            size = PRESET_SIZES[size_name]
            combo = {
                "name": f"s{steps}_c{cfg}_{size_name}_h{str(hires)[0]}",
                "params": {
                    "steps": steps, "cfg": cfg,
                    "width": size["width"], "height": size["height"],
                    "seed": 42, "hires": hires
                }
            }
            grid_combos.append(combo)

        model_short = model_name.replace('.safetensors', '')[:30]
        
        # 生成总配置
        full_config = {
            "name": f"{model_type.upper()}_{model_short}_全参数测试",
            "description": f"{model_type.upper()}: {model_name} | 共 {len(grid_combos)} 种组合",
            "model_type": "sd",
            "model": f"{model_folder}/{model_name}",
            "prompt": prompt,
            "negative": NEGATIVE_PROMPT,
            "output_dir": f"./output/grid_tests/{model_type}_{model_short}",
            "grid": grid_combos
        }
        configs.append(full_config)
    
    # ===== 3. 保存文件 =====
    for config in configs:
        filename = f"{config['name']}.json"
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        filepath = os.path.join(output_dir, safe_filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ SD/SDXL/Lightning: 共生成 {len(configs)} 个配置文件 (每个文件包含多个参数组合)")
    return configs


def generate_janus_grid_configs(output_dir="grid_configs"):
    """生成 Janus-Pro 网格测试配置"""
    os.makedirs(output_dir, exist_ok=True)
    configs = []
    
    for model_name in JANUS_MODELS:
        for temp, max_tokens in product(JANUS_TEMPS, JANUS_TOKENS):
            config = {
                "name": f"Janus_{model_name}_t{temp}_tk{max_tokens}",
                "description": f"Janus-Pro-{model_name} | 温度{temp} Token{max_tokens}",
                "model_type": "janus",
                "prompt": f"{QUALITY_PROMPTS['janus']}, a beautiful Asian woman, wearing elegant dress, full body shot, detailed face",
                "negative": NEGATIVE_PROMPT,
                "output_dir": f"./output/janus_grid_tests/{model_name}",
                "grid": [{
                    "name": f"t{temp}_tk{max_tokens}",
                    "params": {
                        "temperature": temp,
                        "max_tokens": max_tokens,
                        "seed": 42
                    }
                }]
            }
            configs.append(config)
    
    for config in configs:
        filename = f"{config['name']}.json"
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        filepath = os.path.join(output_dir, safe_filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Janus: {len(configs)} 个配置文件")
    return configs


def generate_combined_grid_config(output_dir="grid_configs"):
    """生成组合网格测试配置（一个文件包含所有组合）"""
    os.makedirs(output_dir, exist_ok=True)
    grid = []
    
    # SD 1.5 参数组合（用全部尺寸）
    for steps, cfg, size_name, hires in product(STEPS_SD15, CFG_VALUES, list(PRESET_SIZES.keys()), HIRES_VALUES):
        size = PRESET_SIZES[size_name]
        if size["width"] > 1024 or size["height"] > 1024: continue
        grid.append({
            "name": f"SD15_s{steps}_c{cfg}_{size_name}_h{str(hires)[0]}",
            "params": {"steps": steps, "cfg": cfg, "width": size["width"], "height": size["height"], "seed": 42, "hires": hires}
        })
    
    # SDXL 参数组合
    for steps, cfg, size_name, hires in product(STEPS_SDXL, CFG_VALUES, SIZES_SDXL, HIRES_VALUES):
        size = PRESET_SIZES[size_name]
        grid.append({
            "name": f"SDXL_s{steps}_c{cfg}_{size_name}_h{str(hires)[0]}",
            "params": {"steps": steps, "cfg": cfg, "width": size["width"], "height": size["height"], "seed": 42, "hires": hires}
        })

    config = {
        "name": "综合参数网格测试_全部组合",
        "description": f"包含 SD1.5 和 SDXL 的所有参数组合，共 {len(grid)} 种",
        "model_type": "sd",
        "model": f"{sd15_folder}/aiiiiiii01_v10.safetensors",
        "prompt": f"{QUALITY_PROMPTS['sd15']}, a beautiful Asian woman, wearing elegant dress, full body shot, detailed face, natural lighting",
        "negative": NEGATIVE_PROMPT,
        "output_dir": "./output/grid_tests/combined_all",
        "grid": grid
    }
    
    filepath = os.path.join(output_dir, "combined_grid_config.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 组合配置: 1 个文件 ({len(grid)} 个组合)")
    return config


def generate_quick_test_config(output_dir="grid_configs"):
    """生成快速测试配置（少量组合，适合快速验证）"""
    os.makedirs(output_dir, exist_ok=True)
    
    quick_params = [
        # SD 1.5
        {"model": "sd15", "steps": 20, "cfg": 7.5, "size": "标全(512x768)", "hires": False},
        {"model": "sd15", "steps": 25, "cfg": 7.5, "size": "高全(640x960)", "hires": False},
        {"model": "sd15", "steps": 30, "cfg": 8.0, "size": "方图(768x768)", "hires": False},
        {"model": "sd15", "steps": 25, "cfg": 7.5, "size": "横图(896x512)", "hires": False},
        {"model": "sd15", "steps": 25, "cfg": 7.5, "size": "标全(512x768)", "hires": True},
        # SDXL / Lightning
        {"model": "sdxl", "steps": 30, "cfg": 7.5, "size": "SDXL方图(1024x1024)", "hires": False},
        {"model": "sdxl", "steps": 35, "cfg": 8.0, "size": "SDXL竖图(896x1152)", "hires": False},
        {"model": "sdxl", "steps": 30, "cfg": 7.5, "size": "SDXL横图(1152x896)", "hires": False},
        {"model": "sdxl", "steps": 35, "cfg": 7.5, "size": "SDXL方图(1024x1024)", "hires": True},
    ]
    
    grid = []
    for params in quick_params:
        size = PRESET_SIZES[params["size"]]
        grid.append({
            "name": f"{params['model']}_s{params['steps']}_c{params['cfg']}_{params['size']}_h{str(params['hires'])[0]}",
            "params": {
                "steps": params["steps"], "cfg": params["cfg"],
                "width": size["width"], "height": size["height"],
                "seed": 42, "hires": params["hires"]
            }
        })

    config = {
        "name": "快速测试_9组合",
        "description": "快速验证 SD1.5 和 SDXL 的关键参数组合",
        "model_type": "sd",
        "model": f"{sd15_folder}/aiiiiiii01_v10.safetensors",
        "prompt": f"{QUALITY_PROMPTS['sd15']}, a beautiful Asian woman, wearing elegant dress, full body shot, detailed face, natural lighting",
        "negative": NEGATIVE_PROMPT,
        "output_dir": "./output/grid_tests/quick_test",
        "grid": grid
    }
    
    filepath = os.path.join(output_dir, "quick_test_config.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 快速测试: 1 个文件 ({len(grid)} 个组合)")
    return config


def generate_multi_prompt_config(output_dir="grid_configs"):
    """生成多提示词测试配置（同一参数测试不同提示词）"""
    os.makedirs(output_dir, exist_ok=True)
    
    prompts = [
        "a beautiful Asian woman, wearing elegant dress, full body shot, detailed face, natural lighting",
        "a beautiful Japanese woman in kimono, traditional garden, full body, soft sunlight",
        "a beautiful Korean woman in hanbok, palace background, full body, elegant pose",
        "a beautiful Chinese woman in qipao, modern city background, full body, fashion photography",
        "a beautiful woman in casual clothes, street photography, full body, urban setting",
    ]
    
    grid = []
    for i, prompt in enumerate(prompts):
        grid.append({
            "name": f"prompt_{i+1}",
            "params": {
                "steps": 25, "cfg": 7.5,
                "width": 512, "height": 768,
                "seed": 42 + i, "hires": False,
                "prompt": f"{QUALITY_PROMPTS['sd15']}, {prompt}"
            }
        })

    config = {
        "name": "多提示词对比测试",
        "description": "同一参数下测试5种不同提示词",
        "model_type": "sd",
        "model": f"{sd15_folder}/aiiiiiii01_v10.safetensors",
        "negative": NEGATIVE_PROMPT,
        "output_dir": "./output/grid_tests/prompt_comparison",
        "grid": grid
    }
    
    filepath = os.path.join(output_dir, "multi_prompt_config.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 多提示词配置: 1 个文件 ({len(grid)} 个组合)")
    return config


# ==================== 主入口 ====================

def main():
    print("=" * 60)
    print("🚀 多维度网格测试配置生成器 (优化版)")
    print("=" * 60)
    
    output_dir = "grid_configs"
    print(f"\n📁 输出目录: {output_dir}/")
    print("-" * 40)
    
    print("\n📦 生成 SD/SDXL 配置...")
    sd_configs = generate_sd_grid_configs(output_dir)
    
    print("\n📦 生成 Janus 配置...")
    janus_configs = generate_janus_grid_configs(output_dir)
    
    print("\n📦 生成组合配置...")
    generate_combined_grid_config(output_dir)
    
    print("\n📦 生成快速测试配置...")
    generate_quick_test_config(output_dir)
    
    print("\n📦 生成多提示词配置...")
    generate_multi_prompt_config(output_dir)
    
    total = len(sd_configs) + len(janus_configs) + 3
    
    print("\n" + "=" * 60)
    print("✅ 生成完成！")
    print(f"   📊 SD/SDXL/Lightning: {len(sd_configs)} 个总文件")
    print(f"   📊 Janus 配置: {len(janus_configs)} 个文件")
    print(f"   📊 组合/快速/多提示词: 3 个文件")
    print(f"   📊 总计: {total} 个配置文件")
    print(f"   📁 保存位置: {os.path.abspath(output_dir)}/")
    print("=" * 60)


if __name__ == "__main__":
    main()