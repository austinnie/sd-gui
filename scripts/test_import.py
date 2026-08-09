# scripts/test_import.py
# 放在 scripts/ 目录内

import sys
import os

# 添加当前目录到 Python 路径（用于找 model_index.py）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

# 添加 tools 目录到 Python 路径（用于找 config.py）
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)  # v8_universal_generator/
TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")
sys.path.insert(0, TOOLS_DIR)

print(f"📁 当前目录: {CURRENT_DIR}")
print(f"📁 tools 目录: {TOOLS_DIR}")
print("=" * 60)

try:
    from config import SD_MODEL_PATH, AVAILABLE_MODELS, MODEL_SELECTION_MODE
    
    print("✅ 成功导入 config.py")
    print("=" * 60)
    print(f"选择模式: {MODEL_SELECTION_MODE}")
    print(f"模型路径: {SD_MODEL_PATH}")
    print(f"模型名称: {os.path.basename(SD_MODEL_PATH)}")
    print(f"可用模型总数: {len(AVAILABLE_MODELS)} 个")
    
    # 显示当前模型信息
    current_model = None
    for m in AVAILABLE_MODELS:
        # 比较路径（支持相对路径和绝对路径）
        if m.get("path") == SD_MODEL_PATH or m.get("absolute_path") == SD_MODEL_PATH:
            current_model = m
            break
    
    if current_model:
        print(f"\n📊 当前模型详情:")
        print(f"  名称: {current_model['name']}")
        print(f"  大小: {current_model['size_gb']} GB")
        print(f"  标签: {', '.join(current_model['tags'])}")
        print(f"  评分: {current_model['score']}")
        print(f"  OpenVINO可用: {current_model['is_ov']}")
        print(f"  相对路径: {current_model.get('path', 'N/A')}")
    else:
        print(f"\n⚠️ 当前模型未在索引中找到（可能是 legacy 模式）")
        print(f"   使用路径: {SD_MODEL_PATH}")
        print(f"   尝试在索引中查找...")
        
        # 尝试通过文件名查找
        filename = os.path.basename(SD_MODEL_PATH)
        for m in AVAILABLE_MODELS:
            if m.get("filename") == filename:
                print(f"   找到匹配: {m['name']}")
                current_model = m
                break
    
    # 显示 Top 5 推荐模型
    print(f"\n⭐ Top 5 推荐模型:")
    for i, m in enumerate(AVAILABLE_MODELS[:5]):
        stars = "⭐" * (m["score"] // 20)
        print(f"   {i+1}. {m['name'][:40]:40s} {m['size_gb']:.1f}GB {stars}")
    
    print("=" * 60)
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print(f"\n💡 请检查:")
    print(f"   1. tools/config.py 是否存在")
    print(f"   2. scripts/models_index.json 是否存在")
    print(f"   3. 当前工作目录: {os.getcwd()}")
    print(f"   4. sys.path: {sys.path}")
    
except Exception as e:
    print(f"❌ 运行时错误: {e}")
    import traceback
    traceback.print_exc()