# gui/model_loader.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型加载器 - 扫描和加载模型文件
"""

import os
from typing import List, Dict, Tuple

from config.app_config import app_config


def scan_checkpoints() -> Tuple[List[str], Dict[str, str]]:
    """
    扫描模型文件
    
    返回:
        (checkpoints, checkpoint_paths)
        - checkpoints: 显示名称列表
        - checkpoint_paths: {显示名称: 文件路径}
    """
    checkpoints = []
    checkpoint_paths = {}
    
    for search_dir in app_config.paths.model_base_paths:
        if not os.path.exists(search_dir):
            continue
        for item in os.listdir(search_dir):
            if item.endswith('.safetensors') or item.endswith('.ckpt'):
                file_path = os.path.join(search_dir, item)
                size_mb = os.path.getsize(file_path) // (1024 * 1024)
                if size_mb >= 2000:
                    display_name = f"{item} ({size_mb}MB)"
                    checkpoints.append(display_name)
                    checkpoint_paths[display_name] = file_path
    
    return checkpoints, checkpoint_paths


def scan_loras() -> Tuple[List[str], Dict[str, str], Dict[str, str]]:
    """
    扫描 LoRA 文件
    
    返回:
        (lora_files, lora_paths, lora_types)
        - lora_files: 显示名称列表
        - lora_paths: {显示名称: 文件路径}
        - lora_types: {显示名称: 'sd15' 或 'sdxl'}
    """
    from config.app_config import app_config
    
    lora_files = []
    lora_paths = {}
    lora_types = {}
    
    sd15_paths = app_config.paths.get_resolved_sd15_lora_paths()
    sdxl_paths = app_config.paths.get_resolved_sdxl_lora_paths()
    
    if not sd15_paths and not sdxl_paths:
        for search_dir in app_config.paths.get_resolved_lora_paths():
            if not os.path.exists(search_dir):
                continue
            dir_name = os.path.basename(search_dir).lower()
            if 'sdxl' in dir_name:
                sdxl_paths.append(search_dir)
            else:
                sd15_paths.append(search_dir)
    
    for search_dir in sd15_paths:
        if not os.path.exists(search_dir):
            continue
        for item in os.listdir(search_dir):
            if item.endswith('.safetensors'):
                file_path = os.path.join(search_dir, item)
                size_mb = os.path.getsize(file_path) // (1024 * 1024)
                display_name = f"🟢 [SD1.5] {item} ({size_mb}MB)"
                if display_name not in lora_paths:
                    lora_files.append(display_name)
                    lora_paths[display_name] = file_path
                    lora_types[display_name] = 'sd15'
    
    for search_dir in sdxl_paths:
        if not os.path.exists(search_dir):
            continue
        for item in os.listdir(search_dir):
            if item.endswith('.safetensors'):
                file_path = os.path.join(search_dir, item)
                size_mb = os.path.getsize(file_path) // (1024 * 1024)
                display_name = f"🔵 [SDXL] {item} ({size_mb}MB)"
                if display_name not in lora_paths:
                    lora_files.append(display_name)
                    lora_paths[display_name] = file_path
                    lora_types[display_name] = 'sdxl'
    
    lora_files.sort(key=lambda x: 0 if '[SD1.5]' in x else 1)
    
    return lora_files, lora_paths, lora_types


def scan_vaes() -> Tuple[List[str], Dict[str, str]]:
    """
    扫描 VAE 文件
    
    返回:
        (vae_files, vae_paths)
    """
    vae_files = []
    vae_paths = {}
    
    vae_dirs = ["./models/vae", "../models/vae"]
    
    for search_dir in vae_dirs:
        if not os.path.exists(search_dir):
            continue
        for item in os.listdir(search_dir):
            if item.endswith('.safetensors'):
                file_path = os.path.join(search_dir, item)
                size_mb = os.path.getsize(file_path) // (1024 * 1024)
                display_name = f"{item} ({size_mb}MB)"
                vae_files.append(display_name)
                vae_paths[display_name] = file_path
    
    seen = set()
    unique_files = []
    unique_paths = {}
    for f, p in zip(vae_files, vae_paths.values()):
        if f not in seen:
            seen.add(f)
            unique_files.append(f)
            unique_paths[f] = p
    
    return unique_files, unique_paths


def get_optimization_info() -> str:
    """获取内存优化信息"""
    mem = app_config.memory
    info = "⚡ 内存优化: "
    if mem.use_half_precision:
        info += "半精度 "
    if mem.enable_cpu_offload:
        info += "CPU Offload "
    if mem.vae_slicing:
        info += "VAE切片 "
    if mem.attention_slicing:
        info += "注意力切片 "
    return info.strip() or "⚡ 无特殊优化"