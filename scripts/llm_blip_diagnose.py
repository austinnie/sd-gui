# scripts/sys_diagnose.py
import os
import sys
import time
import subprocess

# 模拟生成 generate.py 的路径环境
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")

# 将 tools 目录加入路径，以便能读取 config.py
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ========== 颜色打印工具 ==========
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_RESET = "\033[0m"

def print_ok(msg):
    print(f"  {COLOR_GREEN}✅{COLOR_RESET} {msg}")

def print_fail(msg):
    print(f"  {COLOR_RED}❌{COLOR_RESET} {msg}")

def print_warn(msg):
    print(f"  {COLOR_YELLOW}⚠️{COLOR_RESET} {msg}")

# ========== 引入 config 配置 ==========
try:
    from tools.config import AI_APPRECIATION_ENGINE
    print_ok("成功读取 config.py 的 AI_APPRECIATION_ENGINE 配置。")
except ImportError:
    print_fail("无法从 tools.config 导入 AI_APPRECIATION_ENGINE，请检查 config.py。")
    AI_APPRECIATION_ENGINE = "unknown"

def check_ollama():
    """检查本地 Ollama 服务状态"""
    print(f"\n🔍 [1] 检查 Ollama 本地大模型服务...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            if models:
                print_ok("Ollama 服务正在运行。")
                print(f"   已安装的模型:")
                for m in models:
                    print(f"     - {m['name']}")
                return True
            else:
                print_warn("Ollama 正在运行，但未找到任何模型，请先使用 'ollama pull qwen2.5:1.5b' 下载。")
                return False
        else:
            print_fail(f"Ollama 服务响应异常 (状态码: {response.status_code})")
            return False
    except ImportError:
        print_fail("Python 环境缺少 requests 库，无法检测 Ollama。请运行: pip install requests")
        return False
    except Exception as e:
        print_fail(f"Ollama 连接失败 (请确认 'ollama serve' 已启动)。错误: {e}")
        return False

def check_blip_model():
    """检查 BLIP-large 本地缓存模型（兼容 Hugging Face 快照结构）"""
    print(f"\n🔍 [2] 检查 BLIP 看图模型本地缓存...")
    
    # 你截图中的基础缓存路径
    base_path = r"E:\hf_cache\.cache\hub\models--Salesforce--blip-image-captioning-large"
    
    if not os.path.exists(base_path):
        print_fail(f"BLIP 缓存主目录不存在: {base_path}")
        return False
    
    # 核心：寻找 Hugging Face 的 snapshots 目录
    snapshots_path = os.path.join(base_path, "snapshots")
    if not os.path.exists(snapshots_path):
        print_warn(f"未找到 snapshots 目录，缓存结构可能异常。")
        return False
    
    # 获取 snapshots 目录下的第一个文件夹（即那个哈希命名的文件夹）
    subfolders = [f for f in os.listdir(snapshots_path) if os.path.isdir(os.path.join(snapshots_path, f))]
    if not subfolders:
        print_warn("snapshots 目录为空，模型下载可能未完成。")
        return False
    
    # 进入第一个哈希文件夹
    target_folder = os.path.join(snapshots_path, subfolders[0])
    files = os.listdir(target_folder)
    
    if "pytorch_model.bin" in files or "model.safetensors" in files:
        print_ok(f"BLIP-large 模型核心权重已找到!")
        print(f"   实际路径: {target_folder}")
        return True
    else:
        print_warn(f"找到了快照目录，但文件夹内缺少 pytorch_model.bin 或 model.safetensors。")
        return False
def check_llm_engine_immediate():
    """直接测试 LLM 引擎 (BLIP + Ollama 联动)"""
    print(f"\n🔍 [3] 测试 LLM 鉴赏引擎 (BLIP + Ollama 联动)...")
    
    # 先检查 BLIP
    if not check_blip_model():
        print_fail("BLIP 缺失，无法完整测试 LLM 引擎。")
        return False
    
    # 检查 Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code != 200:
            print_fail("Ollama 服务未响应，无法进行联动测试。")
            return False
    except:
        print_fail("Ollama 连接失败，无法进行联动测试。")
        return False
    
    # 模拟一条简单的提示词
    test_prompt = "A white angel figure standing gracefully."
    try:
        llm_test_prompt = f"请将以下描述润色成一句优美的中文鉴赏（约50字）：{test_prompt}"
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5:1.5b", "prompt": llm_test_prompt, "stream": False},
            timeout=15
        )
        if response.status_code == 200:
            result = response.json().get("response", "")
            if result:
                print_ok("LLM 引擎联动成功！Ollama 返回润色结果。")
                print(f"   测试输出: {result[:50]}...")
                return True
            else:
                print_warn("Ollama 返回为空，请检查 qwen2.5:1.5b 是否下载完整。")
                return False
        else:
            print_fail(f"Ollama 执行生成失败 (状态码: {response.status_code})")
            return False
    except Exception as e:
        print_fail(f"LLM 联动测试抛出异常: {e}")
        return False

def check_combined_tag_blip():
    """快速检查 tag 和 blip 后端的基础依赖"""
    print(f"\n🔍 [4] 检查 Tag 和 BLIP 基础依赖...")
    try:
        from PIL import Image
        print_ok("PIL (图片处理库) 已安装。")
    except ImportError:
        print_fail("PIL 未安装，请运行: pip install pillow")
    
    try:
        from transformers import BlipProcessor
        print_ok("Transformers (BLIP 依赖库) 已安装。")
    except ImportError:
        print_fail("Transformers 未安装，请运行: pip install transformers")

def main():
    print("\n" + "="*60)
    print("  🤖 SD 系统反推模型全链路诊断工具")
    print("="*60)
    print(f"当前 config.py 配置的引擎: {AI_APPRECIATION_ENGINE}")
    
    # 1. 检查 Ollama
    check_ollama()
    
    # 2. 检查 BLIP
    check_blip_model()
    
    # 3. 做一次完整的测试
    check_llm_engine_immediate()
    
    # 4. 基础依赖
    check_combined_tag_blip()
    
    print("\n" + "="*60)
    print("  💡 诊断结束。如果显示 ❌，请根据提示修复后重新运行。")
    print("="*60)

if __name__ == "__main__":
    main()