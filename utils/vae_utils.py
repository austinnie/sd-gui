# utils/vae_utils.py
"""
VAE 加载工具
"""

import os
import torch
from diffusers import AutoencoderKL


def load_vae(vae_path: str, device: str = "cpu") -> AutoencoderKL:
    """加载 VAE 模型"""
    if not vae_path or not os.path.exists(vae_path):
        raise FileNotFoundError(f"VAE 文件不存在: {vae_path}")
    
    print(f"🎨 加载 VAE: {os.path.basename(vae_path)}")
    
    vae = AutoencoderKL.from_single_file(
        vae_path,
        torch_dtype=torch.float32,
    )
    vae.to(device)
    print("✅ VAE 加载成功")
    
    return vae