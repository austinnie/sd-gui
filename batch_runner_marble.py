#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
螟壼崟迚謇ｹ驥丞､逅隹蠎ｦ蝎ｨ (菫ｮ螟咲沿)
"""

import os
import subprocess
import sys
from pathlib import Path

# ==================== 驟咲ｽｮ ====================
IMAGE_DIR = r"output\good"
CONFIG_GEN_SCRIPT = r"gen_config_marble_v2.py"
IMG_GEN_SCRIPT = r"run_marble.py"

# 蝗ｾ逕溷崟蜈ｨ螻蜿よ焚
MODEL_PATH = r"../models/sd-v1-5/aiiiiii01_v10.safetensors"
STRENGTH = 0.25
MAX_STRENGTH = 0.55  # 笨 譁ｰ蠅橸ｼ壽怙螟ｧ蠑ｺ蠎ｦ髯仙宛
CFG = 7.0
STEPS = 15
# ===============================================

def get_image_files(directory):
    """闔ｷ蜿也岼蠖穂ｸ区園譛画髪謖∫噪蝗ｾ迚譁莉ｶ"""
    extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    files = []
    for f in os.listdir(directory):
        if Path(f).suffix.lower() in extensions:
            files.append(os.path.join(directory, f))
    return sorted(files)

def run_command(cmd):
    """謇ｧ陦悟多莉､蟷ｶ謇灘魂扈捺棡"""
    print(f"\nð泅 謇ｧ陦: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode

def process_images():
    """蟇ｹ豈丈ｸｪ蝗ｾ迚謇ｧ陦梧ｵ∵ｰｴ郤ｿ"""
    image_files = get_image_files(IMAGE_DIR)
    total = len(image_files)
    
    print("=" * 60)
    print(f"ð沒 謇ｾ蛻ｰ {total} 蠑 蝗ｾ迚")
    print(f"笞呻ｸ  STRENGTH={STRENGTH}, MAX_STRENGTH={MAX_STRENGTH}")
    print("=" * 60)
    
    for idx, img_path in enumerate(image_files, 1):
        print(f"\n{'='*60}")
        print(f"ð泱ｼïｸ 螟逅隨ｬ {idx}/{total} 蠑 蝗ｾ: {os.path.basename(img_path)}")
        print(f"{'='*60}")
        
        # --- 豁･鬪､ 1: 逕滓宣咲ｽｮ譁莉ｶ ---
        print(f"\n[1/2] 逕滓宣咲ｽｮ譁莉ｶ...")
        config_cmd = (
            f"python {CONFIG_GEN_SCRIPT} "
            f"--target-image \"{img_path}\" "
            f"--model \"{MODEL_PATH}\" "
            f"--strength {STRENGTH} "
            f"--max-strength {MAX_STRENGTH} "  # 笨 莨 騾 max_strength
            f"--cfg {CFG} "
            f"--steps {STEPS}"
        )
        if run_command(config_cmd) != 0:
            print(f"笶 逕滓宣咲ｽｮ螟ｱ雍･ïｼ瑚ｷｳ霑霑吝ｼ 蝗ｾ")
            continue
        
        # --- 蟇ｻ謇ｾ驟咲ｽｮ譁莉ｶ ---
        config_dir = Path("output/configs")
        if not config_dir.exists():
            print(f"笶 謇ｾ荳榊芦 configs 逶ｮ蠖")
            continue
        
        config_files = sorted(config_dir.glob("marble_batch_config_*.json"), key=os.path.getmtime, reverse=True)
        if not config_files:
            print(f"笶 豐｡譛画伽蛻ｰ marble_batch_config_*.json")
            continue
            
        latest_config = config_files[0]
        print(f"笨 謇ｾ蛻ｰ譛譁ｰ驟咲ｽｮ: {latest_config.name}")
        
        # --- 豁･鬪､ 2: 霍大崟 ---
        print(f"\n[2/2] 蠑蟋区音驥丞崟逕溷崟...")
        #run_cmd = f"python {IMG_GEN_SCRIPT} -c \"{latest_config}\""
        # 隨ｬ 67 陦鯉ｼ悟刈荳 --parallel 蜿よ焚
        run_cmd = f"python {IMG_GEN_SCRIPT} -c \"{latest_config}\" --parallel --processes 2"
        
        run_command(run_cmd)
        
        print(f"\n笨 蝗ｾ迚 {idx}/{total} 螟逅螳梧撰ｼ")
    
    print("\n" + "=" * 60)
    print("ð沁 謇譛牙崟迚螟逅螳梧撰ｼ")
    print("=" * 60)

if __name__ == "__main__":
    process_images()