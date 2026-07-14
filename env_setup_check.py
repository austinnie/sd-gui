# env_setup_check.py
"""测试 env_setup.py 的验证功能"""  # ✅ 更新注释

import sys
import subprocess
from pathlib import Path

# 获取虚拟环境的 python 路径
project_dir = Path(__file__).parent.absolute()
venv_python = project_dir / "venv" / "Scripts" / "python.exe"

if not venv_python.exists():
    print(f"❌ 虚拟环境不存在: {venv_python}")
    print("请先运行: python -m venv venv")
    sys.exit(1)

print("=" * 60)
print("🧪 测试 env_setup.py 验证功能")  # ✅ 更新显示文字
print("=" * 60)
print(f"虚拟环境: {venv_python}")
print()

# 1. 测试模块导入（忽略 stderr）
print("📦 测试模块导入...")
modules = [
    "torch",
    "diffusers",
    "transformers",
    "accelerate",
    "numpy",
    "cv2",
    "PIL",
    "controlnet_aux",
]

all_ok = True
for mod in modules:
    cmd = f'"{venv_python}" -c "import {mod}; print({mod}.__version__)"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"   ✅ {mod}: {version}")
        else:
            print(f"   ❌ {mod}: {result.stderr.strip()[:80]}...")
            all_ok = False
    except Exception as e:
        print(f"   ❌ {mod}: {e}")
        all_ok = False

print()

# 2. 测试 ControlNet 检测器
print("🔧 测试 ControlNet 检测器...")
detectors = [
    "CannyDetector",
    "HEDdetector", 
    "MLSDdetector",
    "MidasDetector",
    "DWposeDetector",
    "OpenposeDetector",
]

for det in detectors:
    cmd = f'"{venv_python}" -c "from controlnet_aux import {det}; print(\'OK\')"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"   ✅ {det}")
        else:
            print(f"   ❌ {det}: {result.stderr.strip()[:80]}...")
            all_ok = False
    except Exception as e:
        print(f"   ❌ {det}: {e}")
        all_ok = False

print()

# 3. 测试 protobuf（检查版本）
print("📦 测试 protobuf...")
cmd = f'"{venv_python}" -c "import google.protobuf; print(google.protobuf.__version__)"'
try:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        version = result.stdout.strip()
        print(f"   protobuf 版本: {version}")
        
        # 检查 DWposeDetector 是否可用（不依赖 protobuf 版本）
        cmd2 = f'"{venv_python}" -c "from controlnet_aux import DWposeDetector; print(\'OK\')"'
        result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True, timeout=10)
        if result2.returncode == 0:
            print(f"   ✅ DWposeDetector 可用")
            print(f"   💡 推荐使用 DWposeDetector（不依赖 mediapipe/protobuf）")
        else:
            print(f"   ⚠️ DWposeDetector 不可用")
            all_ok = False
    else:
        print(f"   ❌ protobuf 未安装")
        all_ok = False
except Exception as e:
    print(f"   ❌ protobuf: {e}")
    all_ok = False

print()

# 4. 检查可用的检测器列表
print("📊 可用检测器汇总:")
cmd = f'"{venv_python}" -c "import controlnet_aux; print([x for x in dir(controlnet_aux) if not x.startswith(\'_\') and x.endswith(\'Detector\')])"'
try:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        detectors_list = result.stdout.strip()
        print(f"   {detectors_list}")
except:
    pass

print()

# 5. 总结
print("=" * 60)
if all_ok:
    print("🎉 所有测试通过！env_setup.py 的验证功能可用")  # ✅ 更新
    print("💡 推荐使用 DWposeDetector（比 OpenPose 更精准）")
else:
    print("⚠️ 部分测试失败，请检查环境")
    print()
    print("💡 建议修复:")
    print("   1. 重新运行检测:")
    print("      python check_controlnet_simple.py")
print("=" * 60)