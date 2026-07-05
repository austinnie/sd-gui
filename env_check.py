#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境信息收集脚本
用于诊断 SD_OpenVINO 项目的依赖问题
"""

import subprocess
import sys
import os
import platform
import json
from datetime import datetime

def run_cmd(cmd):
    """执行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except Exception as e:
        return f"错误: {e}"

def get_pip_list():
    """获取已安装的包列表"""
    output = run_cmd("pip list")
    packages = {}
    for line in output.split('\n')[2:]:  # 跳过表头
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                packages[parts[0]] = parts[1]
    return packages

def check_import(module_name):
    """检查模块是否能导入"""
    try:
        exec(f"import {module_name}")
        return "✅ 成功"
    except ImportError as e:
        return f"❌ 失败: {e}"
    except Exception as e:
        return f"⚠️ 警告: {e}"

def get_version_info():
    """获取关键库的版本信息"""
    info = {}
    tests = [
        "torch",
        "diffusers",
        "transformers",
        "accelerate",
        "huggingface_hub",
        "gradio",
        "PIL",
        "cv2",
        "numpy",
        "psutil",
        "safetensors",
        "packaging"
    ]
    
    for mod in tests:
        try:
            if mod == "PIL":
                import PIL
                info[mod] = PIL.__version__
            elif mod == "cv2":
                import cv2
                info[mod] = cv2.__version__
            else:
                module = __import__(mod)
                info[mod] = module.__version__
        except ImportError:
            info[mod] = "未安装"
        except Exception as e:
            info[mod] = f"错误: {e}"
    return info

def get_pipeline_import_status():
    """检查 diffusers pipeline 导入状态"""
    results = {}
    pipelines = [
        "StableDiffusionPipeline",
        "StableDiffusionXLPipeline",
        "StableDiffusionImg2ImgPipeline",
        "StableDiffusionXLImg2ImgPipeline",
        "DPMSolverMultistepScheduler"
    ]
    
    for pipe in pipelines:
        try:
            exec(f"from diffusers import {pipe}")
            results[pipe] = "✅ 成功"
        except ImportError as e:
            results[pipe] = f"❌ 失败: {e}"
        except Exception as e:
            results[pipe] = f"⚠️ 错误: {e}"
    return results

def main():
    print("=" * 70)
    print("SD_OpenVINO 环境信息收集")
    print(f"收集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 系统信息
    print("\n📁 系统信息:")
    print(f"   操作系统: {platform.system()} {platform.release()}")
    print(f"   架构: {platform.machine()}")
    print(f"   Python 版本: {sys.version}")
    print(f"   当前路径: {os.getcwd()}")
    print(f"   虚拟环境: {sys.prefix}")
    
    # 判断是否在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"   虚拟环境激活: {'✅ 是' if in_venv else '❌ 否'}")
    
    # PyTorch 信息
    print("\n🔥 PyTorch 信息:")
    try:
        import torch
        print(f"   版本: {torch.__version__}")
        print(f"   CUDA 可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA 版本: {torch.version.cuda}")
            print(f"   GPU 数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            print("   ⚠️ CUDA 不可用，将使用 CPU 运行")
    except ImportError:
        print("   ❌ PyTorch 未安装")
    
    # 已安装的包列表
    print("\n📦 已安装的核心包 (pip list):")
    packages = get_pip_list()
    core_packages = ["torch", "diffusers", "transformers", "accelerate", 
                     "huggingface-hub", "gradio", "opencv-python", 
                     "numpy", "pillow", "psutil", "safetensors"]
    for pkg in core_packages:
        version = packages.get(pkg, "未安装")
        pkg_display = pkg.replace("-", " ")
        print(f"   {pkg_display}: {version}")
    
    # 详细版本信息
    print("\n🔍 详细版本信息:")
    versions = get_version_info()
    for pkg, ver in versions.items():
        print(f"   {pkg}: {ver}")
    
    # Pipeline 导入测试
    print("\n🚀 Diffusers Pipeline 导入测试:")
    pipe_status = get_pipeline_import_status()
    for pipe, status in pipe_status.items():
        print(f"   {pipe}: {status}")
    
    # 关键功能测试
    print("\n🧪 关键功能测试:")
    
    # 测试 CUDA 内存（如果可用）
    try:
        import torch
        if torch.cuda.is_available():
            print(f"   GPU 显存: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
            print(f"   当前 GPU 内存使用: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
    except:
        pass
    
    # 测试内存使用
    try:
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        print(f"   当前进程内存: {mem_mb:.1f} MB")
    except:
        pass
    
    # 配置文件检查
    print("\n📄 配置文件检查:")
    config_files = ["gui_config.json", "scene_patterns.json"]
    for cfg in config_files:
        if os.path.exists(cfg):
            try:
                with open(cfg, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"   ✅ {cfg} 存在 (大小: {os.path.getsize(cfg)} bytes)")
            except Exception as e:
                print(f"   ⚠️ {cfg} 存在但读取失败: {e}")
        else:
            print(f"   ❌ {cfg} 不存在")
    
    # 模型目录检查
    print("\n📁 模型目录检查:")
    try:
        with open("gui_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        model_paths = config.get("paths", {}).get("model_base_paths", [])
        for path in model_paths:
            if os.path.exists(path):
                models = [f for f in os.listdir(path) if f.endswith(('.safetensors', '.ckpt'))]
                print(f"   ✅ {path}: {len(models)} 个模型文件")
            else:
                print(f"   ❌ {path}: 不存在")
    except:
        print("   ⚠️ 无法读取 gui_config.json")
    
    # 输出目录
    try:
        output_dir = config.get("paths", {}).get("output_dir", "./output")
        if os.path.exists(output_dir):
            print(f"   ✅ 输出目录: {output_dir}")
        else:
            print(f"   ⚠️ 输出目录不存在: {output_dir}")
    except:
        pass
    
    # 网络配置
    print("\n🌐 网络配置:")
    hf_endpoint = os.environ.get('HF_ENDPOINT', '未设置')
    hf_home = os.environ.get('HF_HOME', '未设置')
    print(f"   HF_ENDPOINT: {hf_endpoint}")
    print(f"   HF_HOME: {hf_home}")
    
    print("\n" + "=" * 70)
    print("环境信息收集完成")
    print("=" * 70)
    
    # 保存到文件
    output_file = f"environment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("SD_OpenVINO 环境信息报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        
        # 重新获取完整输出并写入文件
        original_stdout = sys.stdout
        sys.stdout = f
        
        try:
            # 重新执行一次主要输出
            print(f"Python 版本: {sys.version}")
            print(f"虚拟环境路径: {sys.prefix}")
            print(f"\n已安装包列表:")
            for pkg, ver in packages.items():
                print(f"  {pkg}=={ver}")
        finally:
            sys.stdout = original_stdout
    
    print(f"\n💾 详细报告已保存到: {output_file}")

if __name__ == "__main__":
    main()