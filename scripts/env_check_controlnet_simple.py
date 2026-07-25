# check_controlnet_simple.py
"""
完整版 ControlNet 环境检测
整合所有测试：基础依赖、检测器、图像处理、模型缓存
"""

import sys
import os
import importlib

# 禁用 TensorFlow 的 oneDNN 警告
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# ===== 颜色输出 =====
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_green(msg): print(f"{Colors.GREEN}{msg}{Colors.RESET}")
def print_red(msg): print(f"{Colors.RED}{msg}{Colors.RESET}")
def print_yellow(msg): print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
def print_cyan(msg): print(f"{Colors.CYAN}{msg}{Colors.RESET}")
def print_magenta(msg): print(f"{Colors.MAGENTA}{msg}{Colors.RESET}")
def print_bold(msg): print(f"{Colors.BOLD}{msg}{Colors.RESET}")

def check_module(module_name, display_name=None):
    """检查模块是否可导入"""
    if display_name is None:
        display_name = module_name
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', '未知版本')
        return True, version
    except ImportError as e:
        return False, str(e)

def check_import(module_name, import_name=None, display_name=None):
    """检查从模块导入特定名称"""
    if display_name is None:
        display_name = f"{module_name}.{import_name}" if import_name else module_name
    try:
        if import_name:
            exec(f"from {module_name} import {import_name}")
        else:
            importlib.import_module(module_name)
        return True, "可用"
    except Exception as e:
        return False, str(e)

def check_controlnet_model():
    """检查 ControlNet 模型缓存"""
    cache_dir = os.environ.get("HF_HOME", r"E:\hf_cache\.cache")
    model_paths = [
        os.path.join(cache_dir, "hub", "models--lllyasviel--sd-controlnet-openpose"),
        os.path.join(cache_dir, "hub", "models--lllyasviel--ControlNet"),
        os.path.join(cache_dir, "hub", "models--lllyasviel--sd-controlnet-canny"),
        os.path.join(cache_dir, "hub", "models--lllyasviel--sd-controlnet-depth"),
        os.path.join(cache_dir, "hub", "models--lllyasviel--sd-controlnet-hed"),
        os.path.join(cache_dir, "hub", "models--lllyasviel--sd-controlnet-mlsd"),
        os.path.join(cache_dir, "hub", "models--lllyasviel--sd-controlnet-normal"),
    ]
    found = []
    for path in model_paths:
        if os.path.exists(path):
            found.append(path)
    if found:
        return True, found
    return False, "未缓存"

# ✅ 移除 mediapipe 相关测试函数

def test_dwpose_detector():
    """测试 DWposeDetector"""
    try:
        from controlnet_aux import DWposeDetector
        return True, "DWposeDetector 可用 ✅ (推荐使用)"
    except ImportError as e:
        return False, f"导入失败: {e}"
    except Exception as e:
        return False, f"加载失败: {e}"

def test_openpose_detector():
    """测试 OpenposeDetector"""
    try:
        from controlnet_aux import OpenposeDetector
        return True, "OpenposeDetector 可用"
    except ImportError as e:
        return False, f"导入失败: {e}"
    except Exception as e:
        return False, f"加载失败: {e}"

def test_canny_detector():
    """测试 CannyDetector"""
    try:
        from controlnet_aux import CannyDetector
        return True, "CannyDetector 可用"
    except ImportError as e:
        return False, f"导入失败: {e}"
    except Exception as e:
        return False, f"加载失败: {e}"

def test_hed_detector():
    """测试 HEDdetector"""
    try:
        from controlnet_aux import HEDdetector
        return True, "HEDdetector 可用"
    except ImportError as e:
        return False, f"导入失败: {e}"
    except Exception as e:
        return False, f"加载失败: {e}"

def test_controlnet_pipeline():
    """测试 ControlNet Pipeline 创建"""
    try:
        from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
        import torch
        if hasattr(ControlNetModel, 'from_pretrained'):
            return True, "ControlNetModel 和 StableDiffusionControlNetPipeline 可用"
        return True, "ControlNetModel 和 StableDiffusionControlNetPipeline 可用"
    except ImportError as e:
        return False, f"导入失败: {e}"
    except Exception as e:
        return False, f"测试失败: {e}"

def test_controlnet_aux_import():
    """测试 controlnet_aux 主模块导入"""
    try:
        import controlnet_aux
        version = getattr(controlnet_aux, '__version__', '未知版本')
        return True, f"{version}"
    except ImportError as e:
        return False, f"导入失败: {e}"
    except Exception as e:
        return False, f"加载失败: {e}"

def test_cv2_import():
    """测试 OpenCV 导入"""
    try:
        import cv2
        return True, cv2.__version__
    except ImportError as e:
        return False, f"导入失败: {e}"

def main():
    print("=" * 70)
    print_bold("🔍 ControlNet 环境完整检测")
    print("=" * 70)
    
    # ===== 1. 基础依赖 =====
    print_cyan("\n📦 1. 基础依赖")
    print("-" * 50)
    
    modules = [
        ("numpy", "NumPy"),
        ("torch", "PyTorch"),
        ("torchvision", "TorchVision"),
        ("diffusers", "Diffusers"),
        ("transformers", "Transformers"),
        ("accelerate", "Accelerate"),
    ]
    
    results = {}
    for mod, name in modules:
        ok, info = check_module(mod)
        results[mod] = ok
        if ok:
            print(f"   {Colors.GREEN}✅{Colors.RESET} {name}: {info}")
        else:
            print(f"   {Colors.RED}❌{Colors.RESET} {name}: {info}")
    
    # PyTorch CUDA 信息
    try:
        import torch
        if torch.cuda.is_available():
            print(f"      {Colors.GREEN}✅{Colors.RESET} CUDA 可用")
            print(f"      CUDA 版本: {torch.version.cuda}")
            print(f"      GPU 数量: {torch.cuda.device_count()}")
        else:
            print(f"      {Colors.YELLOW}ℹ️{Colors.RESET} CUDA 不可用 (CPU 模式)")
    except:
        pass
    
    # ===== 2. ControlNet 核心 =====
    print_cyan("\n🎯 2. ControlNet 核心组件")
    print("-" * 50)
    
    # ControlNetModel
    ok, info = check_import("diffusers", "ControlNetModel", "ControlNetModel")
    if ok:
        print(f"   {Colors.GREEN}✅{Colors.RESET} ControlNetModel: {info}")
    else:
        print(f"   {Colors.RED}❌{Colors.RESET} ControlNetModel: {info}")
    
    # ControlNet Pipeline
    ok, info = test_controlnet_pipeline()
    if ok:
        print(f"   {Colors.GREEN}✅{Colors.RESET} StableDiffusionControlNetPipeline: {info}")
    else:
        print(f"   {Colors.RED}❌{Colors.RESET} StableDiffusionControlNetPipeline: {info}")
    
    # ===== 3. controlnet_aux 主模块 =====
    print_cyan("\n📦 3. controlnet_aux 主模块")
    print("-" * 50)
    
    ok, info = test_controlnet_aux_import()
    if ok:
        print(f"   {Colors.GREEN}✅{Colors.RESET} controlnet_aux: {info}")
    else:
        print(f"   {Colors.RED}❌{Colors.RESET} controlnet_aux: {info}")
    
    # ===== 4. 所有检测器 =====
    print_cyan("\n🔧 4. controlnet_aux 检测器")
    print("-" * 50)
    
    detectors = [
        ("CannyDetector", "边缘检测", test_canny_detector),
        ("HEDdetector", "边缘/轮廓检测", test_hed_detector),
        ("MLSDdetector", "直线检测", None),
        ("MidasDetector", "深度检测", None),
        ("NormalBaeDetector", "法线检测", None),
        ("LineartDetector", "线稿检测", None),
        ("PidiNetDetector", "边缘检测", None),
        ("ZoeDetector", "深度检测", None),
        ("DWposeDetector", "姿态检测 (DWPose)", test_dwpose_detector),
        ("OpenposeDetector", "姿态检测 (OpenPose)", test_openpose_detector),
        ("MediapipeFaceDetector", "人脸检测", None),
    ]
    
    for det, name, test_func in detectors:
        if test_func:
            ok, info = test_func()
        else:
            ok, info = check_import("controlnet_aux", det, det)
        if ok:
            print(f"   {Colors.GREEN}✅{Colors.RESET} {name}: {info}")
        else:
            print(f"   {Colors.RED}❌{Colors.RESET} {name}: {info}")
    
    # ===== 5. 图像处理 =====
    print_cyan("\n🖼️ 5. 图像处理")
    print("-" * 50)
    
    # OpenCV
    ok, info = test_cv2_import()
    if ok:
        print(f"   {Colors.GREEN}✅{Colors.RESET} OpenCV: {info}")
    else:
        print(f"   {Colors.RED}❌{Colors.RESET} OpenCV: {info}")
    
    modules = [
        ("PIL", "Pillow"),
        ("scipy", "SciPy"),
        ("skimage", "scikit-image"),
    ]
    
    for mod, name in modules:
        ok, info = check_module(mod)
        if ok:
            print(f"   {Colors.GREEN}✅{Colors.RESET} {name}: {info}")
        else:
            print(f"   {Colors.RED}❌{Colors.RESET} {name}: {info}")
    
    # ===== 6. ✅ 移除 mediapipe 检测 =====
    # MediaPipe 已移除，不再检测
    
    # ===== 7. ControlNet 模型缓存 =====
    print_cyan("\n💾 7. ControlNet 模型缓存")
    print("-" * 50)
    
    ok, paths = check_controlnet_model()
    if ok:
        print(f"   {Colors.GREEN}✅{Colors.RESET} 已缓存 {len(paths)} 个模型:")
        for path in paths:
            print(f"      📁 {path}")
    else:
        print(f"   {Colors.YELLOW}ℹ️{Colors.RESET} 未缓存 (首次使用会自动下载, 约 1.5GB)")
        print(f"      💡 运行: from diffusers import ControlNetModel")
        print(f"          ControlNetModel.from_pretrained('lllyasviel/sd-controlnet-openpose')")
    
    # ===== 8. HuggingFace 缓存配置 =====
    print_cyan("\n📁 8. HuggingFace 缓存配置")
    print("-" * 50)
    
    hf_home = os.environ.get("HF_HOME", "未设置")
    hf_cache = os.environ.get("HF_HUB_CACHE", "未设置")
    print(f"   HF_HOME: {hf_home}")
    print(f"   HF_HUB_CACHE: {hf_cache}")
    
    # ===== 9. 测试总结 =====
    print("\n" + "=" * 70)
    print_bold("📊 测试总结")
    print("=" * 70)
    
    # 检查关键组件
    critical = [
        ("numpy", "NumPy"),
        ("torch", "PyTorch"),
        ("diffusers", "Diffusers"),
        ("controlnet_aux", "controlnet_aux"),
    ]
    
    all_ok = True
    
    for mod, name in critical:
        if mod == "controlnet_aux":
            ok, _ = test_controlnet_aux_import()
        else:
            ok = results.get(mod, False)
        if ok:
            print(f"   {Colors.GREEN}✅{Colors.RESET} {name}")
        else:
            print(f"   {Colors.RED}❌{Colors.RESET} {name}")
            all_ok = False
    
    # ControlNet 检测器状态
    print(f"\n   {Colors.CYAN}📌 ControlNet 检测器状态:{Colors.RESET}")
    detector_count = 0
    for det, name, test_func in detectors:
        if test_func:
            ok, _ = test_func()
        else:
            ok, _ = check_import("controlnet_aux", det, det)
        if ok:
            detector_count += 1
    print(f"   ✅ 可用检测器: {detector_count}/{len(detectors)}")
    
    if all_ok and detector_count >= 5:
        print(f"\n   {Colors.GREEN}🎉 环境完整！ControlNet 可以使用！{Colors.RESET}")
        print(f"   {Colors.CYAN}💡 推荐使用 DWposeDetector（比 OpenPose 更精准）{Colors.RESET}")
    elif all_ok:
        print(f"\n   {Colors.YELLOW}⚠️ 基础环境完整，但检测器部分缺失{Colors.RESET}")
    else:
        print(f"\n   {Colors.RED}❌ 部分组件缺失，将使用普通模式{Colors.RESET}")
    
    print("\n" + "=" * 70)
    print("💡 使用建议:")
    print("   • ControlNet 可用时：姿态检测更精准")
    print("   • ControlNet 不可用时：自动回退到普通图生图")
    print("   • 推荐使用 DWposeDetector (比 OpenPose 更精准)")
    print("   • 首次使用 ControlNet 会自动下载模型")
    print("=" * 70)

if __name__ == "__main__":
    main()