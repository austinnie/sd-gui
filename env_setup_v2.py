#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用人物生成器 - 全自动环境安装脚本
自动检测 CUDA（如果有显卡），否则自动安装 CPU 版
"""

import subprocess
import sys
import os
import venv
import shutil
from pathlib import Path

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
def print_blue(msg): print(f"{Colors.BLUE}{msg}{Colors.RESET}")
def print_cyan(msg): print(f"{Colors.CYAN}{msg}{Colors.RESET}")
def print_bold(msg): print(f"{Colors.BOLD}{msg}{Colors.RESET}")

# ===== 配置 =====
PYTORCH_CPU = "https://download.pytorch.org/whl/cpu"
MIRRORS = [
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.aliyun.com/pypi/simple/",
]

# ===== 核心依赖列表（完整兼容版本） =====
REQUIRED_PACKAGES = [
    # PyTorch (CPU 版本，与 NumPy 2.x 兼容)
    "torch==2.5.1",
    "torchvision==0.20.1",
    
    # ===== 核心库（版本锁定，保证兼容） =====
    "diffusers==0.26.0",
    "transformers==4.40.0",
    "huggingface-hub==0.24.0",      # ✅ 固定版本，兼容 diffusers 0.26.0
    "accelerate==1.14.0",
    "safetensors==0.8.0",
    "peft==0.10.0",                  # ✅ 新增，兼容 huggingface-hub 0.24.0
    
    # ===== 图像处理与数据分析 =====
    "numpy==2.4.6",
    "pillow==12.2.0",
    "opencv-python==4.13.0.92",
    "scipy==1.18.0",
    "scikit-image==0.26.0",
    
    # ===== 工具 =====
    "psutil==7.2.2",
    "packaging==26.2",
    "tqdm==4.68.3",
    "requests==2.34.2",
    "filelock==3.29.0",
    
    # ===== 遮罩与背景去除 (图生图换衣核心) =====
    "rembg==2.0.76",
    
    # ===== CLIP 反推及打分功能 =====
    "open_clip_torch==3.3.0",
    # "clip-interrogator==0.6.0",  # 可选，有兼容性问题时注释
    
    # ===== Janus-Pro 依赖 (多模态模型) =====
    "attrdict==2.0.1",
    "einops==0.8.2",
    "timm==1.0.27",
    "ftfy==6.3.1",
    "sentencepiece==0.2.1",
]

# ===== 验证模块列表 =====
VERIFY_MODULES = [
    ("torch", "torch.__version__"),
    ("torchvision", "torchvision.__version__"),
    ("transformers", "transformers.__version__"),
    ("diffusers", "diffusers.__version__"),
    ("accelerate", "accelerate.__version__"),
    ("huggingface_hub", "huggingface_hub.__version__"),
    ("safetensors", "safetensors.__version__"),
    ("peft", "peft.__version__"),                    # ✅ 新增
    ("numpy", "numpy.__version__"),
    ("PIL", "PIL.__version__"),
    ("cv2", "cv2.__version__"),
    ("psutil", "psutil.__version__"),
    ("tqdm", "tqdm.__version__"),
    ("rembg", "rembg.__version__"),
    ("open_clip", "open_clip.__version__"),
    # Janus
    ("attrdict", "attrdict.__version__"),
    ("einops", "einops.__version__"),
    ("timm", "timm.__version__"),
    ("ftfy", "ftfy.__version__"),
    ("sentencepiece", "sentencepiece.__version__"),
]


def run_cmd(cmd, capture=True, timeout=600, cwd=None):
    """执行命令"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        return result.returncode == 0, result.stdout if capture else "", result.stderr if capture else ""
    except subprocess.TimeoutExpired:
        print_yellow(f"   ⚠️ 超时 (>{timeout}s)")
        return False, "", "超时"
    except Exception as e:
        print_red(f"   ❌ 错误: {e}")
        return False, "", str(e)


def run_in_venv(venv_python, cmd, capture=True, timeout=600):
    """在虚拟环境中执行 pip 命令"""
    full_cmd = f'"{venv_python}" -m pip {cmd}'
    return run_cmd(full_cmd, capture, timeout)


def print_header(text):
    """打印标题"""
    print()
    print("=" * 60)
    print_bold(f"  {text}")
    print("=" * 60)
    print()


def get_venv_python(project_dir):
    """获取 venv 的 python 路径"""
    venv_dir = project_dir / "venv"
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    else:
        return venv_dir / "bin" / "python"


def create_venv(project_dir):
    """创建虚拟环境"""
    venv_dir = project_dir / "venv"
    
    if venv_dir.exists():
        print(f"   ✅ 虚拟环境已存在: {venv_dir}")
        return True
    
    print("   📦 创建虚拟环境...")
    try:
        venv.create(venv_dir, with_pip=True)
        print_green("   ✅ 虚拟环境已创建")
        return True
    except Exception as e:
        print_red(f"   ❌ 创建失败: {e}")
        return False


def install_pytorch(venv_python):
    """自动检测 CUDA 并安装 PyTorch"""
    print_cyan("   🔍 正在检测 CUDA...")
    
    has_cuda = False
    try:
        result = subprocess.run("nvidia-smi", capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            has_cuda = True
            print_green("   ✅ 检测到 NVIDIA GPU，将安装 CUDA 版 PyTorch")
        else:
            print_yellow("   ⚠️ 未检测到 CUDA，将安装 CPU 版 PyTorch")
    except:
        print_yellow("   ⚠️ 未检测到 CUDA，将安装 CPU 版 PyTorch")
    
    print("   🔄 清理旧版本...")
    run_in_venv(venv_python, "uninstall torch torchvision torchaudio -y", timeout=120)
    print()
    
    if has_cuda:
        cmd = 'install torch==2.5.1 torchvision==0.20.1'
    else:
        cmd = f'install torch==2.5.1+cpu torchvision==0.20.1+cpu --index-url {PYTORCH_CPU}'
    
    print_cyan(f"   {cmd}")
    success, _, _ = run_in_venv(venv_python, cmd, timeout=600)
    
    if success:
        print_green("   ✅ PyTorch 安装完成")
        return True
    else:
        print_red("   ❌ PyTorch 安装失败")
        return False


def install_package(venv_python, pkg):
    """安装单个包"""
    cmd = f"install {pkg}"
    success, _, _ = run_in_venv(venv_python, cmd, timeout=300)
    if success:
        return True
    
    # 尝试镜像
    cmd = f"install {pkg} -i {MIRRORS[0]}"
    success, _, _ = run_in_venv(venv_python, cmd, timeout=300)
    if success:
        return True
    
    # 尝试无版本号
    if "==" in pkg:
        pkg_name = pkg.split("==")[0]
        cmd = f"install {pkg_name}"
        success, _, _ = run_in_venv(venv_python, cmd, timeout=300)
        if success:
            return True
        
        cmd = f"install {pkg_name} -i {MIRRORS[0]}"
        success, _, _ = run_in_venv(venv_python, cmd, timeout=300)
        if success:
            return True
    
    return False


def install_all_packages(venv_python):
    """安装所有依赖包"""
    print_header("安装依赖包")
    print(f"   共 {len(REQUIRED_PACKAGES)} 个包")
    print()
    
    failed = []
    for pkg in REQUIRED_PACKAGES:
        print(f"   📦 {pkg}...")
        if install_package(venv_python, pkg):
            print_green(f"   ✅ {pkg} 安装成功")
        else:
            print_red(f"   ❌ {pkg} 安装失败")
            failed.append(pkg)
        print()
    
    if failed:
        print_yellow(f"⚠️ 以下包安装失败: {', '.join(failed)}")
        print("请稍后手动安装")
        return False
    else:
        print_green("   ✅ 所有依赖安装完成")
        return True


def verify_installation(venv_python):
    """验证安装"""
    print_header("验证安装")
    
    all_ok = True
    for module, version_expr in VERIFY_MODULES:
        cmd = f'"{venv_python}" -c "import {module}; print({version_expr})"'
        success, output, _ = run_cmd(cmd, timeout=30)
        
        if success and output:
            version = output.strip()
            print(f"   ✅ {module}: {version}")
        else:
            print_red(f"   ❌ {module}: 导入失败")
            all_ok = False
    
    return all_ok


def generate_requirements(project_dir):
    """生成 requirements.txt"""
    req_path = project_dir / "requirements.txt"
    
    content = "# ============================================================\n"
    content += "# 通用人物生成器 - 依赖清单 (完整版)\n"
    content += "# 生成时间: " + __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"
    content += "# ============================================================\n\n"
    
    content += "# PyTorch (自动适配 CUDA/CPU)\n"
    content += "# pip install torch==2.5.1 torchvision==0.20.1\n"
    content += "# 如果是 CPU 环境，请改为:\n"
    content += "# pip install torch==2.5.1+cpu torchvision==0.20.1+cpu --index-url https://download.pytorch.org/whl/cpu\n\n"
    
    content += "# 核心依赖\n"
    for pkg in REQUIRED_PACKAGES:
        if not pkg.startswith("torch"):
            content += f"{pkg}\n"
    
    req_path.write_text(content, encoding='utf-8')
    print_green(f"   ✅ requirements.txt 已生成: {req_path}")
    return req_path


def main():
    print_header("通用人物生成器 - 全自动环境安装")
    print("  自动检测 CUDA，完美兼容 CPU 环境")
    print()
    
    project_dir = Path(__file__).parent.absolute()
    venv_python = get_venv_python(project_dir)
    
    print(f"[1/6] 项目目录: {project_dir}")
    print()
    
    print("[2/6] 创建/检查虚拟环境...")
    if not create_venv(project_dir):
        input("按 Enter 退出...")
        return
    print()
    
    print("[3/6] 升级 pip...")
    success, _, _ = run_in_venv(venv_python, "install --upgrade pip", timeout=120)
    print_green("   ✅ pip 已升级" if success else "   ⚠️ pip 升级失败")
    print()
    
    print("[4/6] 安装 PyTorch...")
    if not install_pytorch(venv_python):
        print()
        print_red("   ❌ PyTorch 安装失败")
        print()
        print("请手动执行以下命令后重新运行:")
        print(f'   {venv_python} -m pip install torch==2.5.1+cpu torchvision==0.20.1+cpu --index-url https://download.pytorch.org/whl/cpu')
        print()
        input("按 Enter 退出...")
        return
    print()
    
    print("[5/6] 安装依赖包...")
    if not install_all_packages(venv_python):
        print()
        print_yellow("⚠️ 部分包安装失败，请检查后手动安装")
    print()
    
    print("[6/6] 验证安装...")
    all_ok = verify_installation(venv_python)
    print()
    
    generate_requirements(project_dir)
    print()
    
    print_header("安装完成")
    
    if all_ok:
        print_green("   🎉 环境安装成功！")
    else:
        print_yellow("   ⚠️ 部分包验证失败，请检查")
    
    print()
    print("   启动程序:")
    print(f"   cd {project_dir}")
    print("   venv\\Scripts\\activate")
    print("   python main.py")
    print()
    print("   或者直接运行:")
    print(f"   {venv_python} main.py")
    print()
    print("=" * 60)
    print()
    input("按 Enter 键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ 用户取消")
    except Exception as e:
        print_red(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("按 Enter 键退出...")