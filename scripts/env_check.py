#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境信息收集脚本
用于诊断 SD_OpenVINO 项目的依赖问题
包含 ControlNet 环境检测
"""

import subprocess
import sys
import os
import platform
import json
from datetime import datetime

# ===== 颜色输出 =====
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_green(msg): print(f"{Colors.GREEN}{msg}{Colors.RESET}")
def print_red(msg): print(f"{Colors.RED}{msg}{Colors.RESET}")
def print_yellow(msg): print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
def print_cyan(msg): print(f"{Colors.CYAN}{msg}{Colors.RESET}")
def print_bold(msg): print(f"{Colors.BOLD}{msg}{Colors.RESET}")

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
    for line in output.split('\n')[2:]:
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
        "packaging",
        "controlnet_aux",
        # ✅ 移除 mediapipe
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
        "DPMSolverMultistepScheduler",
        "ControlNetModel",
        "StableDiffusionControlNetPipeline",
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

def check_controlnet_detectors():
    """检查 controlnet_aux 检测器"""
    detectors = {
        "CannyDetector": "边缘检测",
        "HEDdetector": "边缘/轮廓检测",
        "MLSDdetector": "直线检测",
        "MidasDetector": "深度检测",
        "NormalBaeDetector": "法线检测",
        "LineartDetector": "线稿检测",
        "PidiNetDetector": "边缘检测",
        "ZoeDetector": "深度检测",
        "DWposeDetector": "姿态检测 (DWPose) ⭐推荐",
        "OpenposeDetector": "姿态检测 (OpenPose)",
        "MediapipeFaceDetector": "人脸检测",
    }
    
    results = {}
    for det, name in detectors.items():
        try:
            exec(f"from controlnet_aux import {det}")
            results[det] = f"✅ {name}"
        except ImportError:
            results[det] = f"❌ {name} - 不可用"
        except Exception as e:
            results[det] = f"⚠️ {name} - {e}"
    return results

def check_controlnet_cache():
    """检查 ControlNet 模型缓存"""
    cache_dir = os.environ.get("HF_HOME", r"E:\hf_cache\.cache")
    model_paths = [
        os.path.join(cache_dir, "hub", "models--lllyasviel--sd-controlnet-openpose"),
        os.path.join(cache_dir, "hub", "models--lllyasviel--ControlNet"),
    ]
    for path in model_paths:
        if os.path.exists(path):
            return True, path
    return False, "未缓存"

def main():
    print("=" * 70)
    print_bold("🔍 SD_OpenVINO 环境信息收集")
    print(f"收集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # ===== 系统信息 =====
    print_cyan("\n📁 系统信息")
    print("-" * 50)
    print(f"   操作系统: {platform.system()} {platform.release()}")
    print(f"   架构: {platform.machine()}")
    print(f"   Python 版本: {sys.version}")
    print(f"   当前路径: {os.getcwd()}")
    print(f"   虚拟环境: {sys.prefix}")
    
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"   虚拟环境激活: {'✅ 是' if in_venv else '❌ 否'}")
    
    # ===== PyTorch 信息 =====
    print_cyan("\n🔥 PyTorch 信息")
    print("-" * 50)
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
            print_yellow("   ⚠️ CUDA 不可用，将使用 CPU 运行")
    except ImportError:
        print_red("   ❌ PyTorch 未安装")
    
    # ===== 已安装的核心包 =====
    print_cyan("\n📦 已安装的核心包")
    print("-" * 50)
    packages = get_pip_list()
    core_packages = [
        "torch", "diffusers", "transformers", "accelerate", 
        "huggingface-hub", "gradio", "opencv-python", 
        "numpy", "pillow", "psutil", "safetensors",
        "controlnet-aux",
    ]
    for pkg in core_packages:
        version = packages.get(pkg, "未安装")
        pkg_display = pkg.replace("-", " ")
        status = "✅" if version != "未安装" else "❌"
        print(f"   {status} {pkg_display}: {version}")
    
    # ===== 详细版本信息 =====
    print_cyan("\n🔍 详细版本信息")
    print("-" * 50)
    versions = get_version_info()
    for pkg, ver in versions.items():
        status = "✅" if ver != "未安装" else "❌"
        print(f"   {status} {pkg}: {ver}")
    
    # ===== Pipeline 导入测试 =====
    print_cyan("\n🚀 Diffusers Pipeline 导入测试")
    print("-" * 50)
    pipe_status = get_pipeline_import_status()
    for pipe, status in pipe_status.items():
        print(f"   {pipe}: {status}")
    
    # ===== ControlNet 检测器 =====
    print_cyan("\n🔧 ControlNet 检测器")
    print("-" * 50)
    try:
        detectors = check_controlnet_detectors()
        for det, status in detectors.items():
            print(f"   {status}")
    except ImportError:
        print_yellow("   ⚠️ controlnet_aux 未安装")
    except Exception as e:
        print_red(f"   ❌ 检测失败: {e}")
    
    # ===== ControlNet 模型缓存 =====
    print_cyan("\n💾 ControlNet 模型缓存")
    print("-" * 50)
    ok, path = check_controlnet_cache()
    if ok:
        print_green(f"   ✅ 已缓存: {path}")
    else:
        print_yellow("   ℹ️ 未缓存 (首次使用会自动下载, 约 1.5GB)")
    
    # ===== 关键功能测试 =====
    print_cyan("\n🧪 关键功能测试")
    print("-" * 50)
    
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
    
    # ✅ 移除 mediapipe 测试
    
    # ===== 配置文件检查 =====
    print_cyan("\n📄 配置文件检查")
    print("-" * 50)
    config_files = ["data/configs/gui_config.json", "data/configs/scene_patterns.json", "data/configs/pipelines_config.json"]
    for cfg in config_files:
        if os.path.exists(cfg):
            try:
                with open(cfg, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                size = os.path.getsize(cfg)
                print(f"   ✅ {cfg} (大小: {size} bytes)")
            except Exception as e:
                print_yellow(f"   ⚠️ {cfg} 存在但读取失败: {e}")
        else:
            print_yellow(f"   ⚠️ {cfg} 不存在")
    
    # ===== 模型目录检查 =====
    print_cyan("\n📁 模型目录检查")
    print("-" * 50)
    try:
        with open("data/configs/gui_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        model_paths = config.get("paths", {}).get("model_base_paths", [])
        for path in model_paths:
            if os.path.exists(path):
                models = [f for f in os.listdir(path) if f.endswith(('.safetensors', '.ckpt'))]
                print(f"   ✅ {path}: {len(models)} 个模型文件")
            else:
                print_yellow(f"   ⚠️ {path}: 不存在")
    except:
        print_yellow("   ⚠️ 无法读取 gui_config.json")
    
    # ===== 网络配置 =====
    print_cyan("\n🌐 网络配置")
    print("-" * 50)
    hf_endpoint = os.environ.get('HF_ENDPOINT', '未设置')
    hf_home = os.environ.get('HF_HOME', '未设置')
    hf_cache = os.environ.get('HF_HUB_CACHE', '未设置')
    print(f"   HF_ENDPOINT: {hf_endpoint}")
    print(f"   HF_HOME: {hf_home}")
    print(f"   HF_HUB_CACHE: {hf_cache}")
    
    # ===== 总结 =====
    print("\n" + "=" * 70)
    print_bold("📊 总结")
    print("=" * 70)
    
    critical = [
        ("torch", "PyTorch"),
        ("diffusers", "Diffusers"),
        ("transformers", "Transformers"),
        ("numpy", "NumPy"),
        ("cv2", "OpenCV"),
        ("controlnet_aux", "controlnet_aux"),
    ]
    
    all_ok = True
    for mod, name in critical:
        ver = versions.get(mod, "未安装")
        if ver != "未安装" and not str(ver).startswith("错误"):
            print_green(f"   ✅ {name}: {ver}")
        else:
            print_red(f"   ❌ {name}: {ver}")
            all_ok = False
    
    if all_ok:
        print_green("\n   🎉 环境完整，可以正常运行！")
        print_cyan("   💡 推荐使用 DWposeDetector（比 OpenPose 更精准）")
    else:
        print_yellow("\n   ⚠️ 部分组件缺失，请检查安装")
    
    print("\n" + "=" * 70)
    
    output_file = f"environment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("SD_OpenVINO 环境信息报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("已安装包列表:\n")
        for pkg, ver in packages.items():
            f.write(f"  {pkg}=={ver}\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("详细版本信息:\n")
        for pkg, ver in versions.items():
            f.write(f"  {pkg}: {ver}\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("ControlNet 检测器状态:\n")
        try:
            detectors = check_controlnet_detectors()
            for det, status in detectors.items():
                f.write(f"  {status}\n")
        except:
            f.write("  controlnet_aux 未安装\n")
    
    print(f"\n💾 详细报告已保存到: {output_file}")

if __name__ == "__main__":
    main()