# scripts/switch_model.py
# ==================== 🔄 模型切换工具 ====================
"""
用法:
    python switch_model.py --list              # 列出所有模型
    python switch_model.py --set <名称>        # 切换智能推荐模型
    python switch_model.py --mode <模式>       # 切换选择模式 (legacy/smart/manual)
    python switch_model.py --legacy <编号>     # 切换到旧版编号模式
    python switch_model.py --ov                # 启用 OpenVINO
    python switch_model.py --no-ov             # 禁用 OpenVINO
    python switch_model.py --refresh           # 重新生成索引
"""

import os
import sys
import json
import argparse
import subprocess
import re

# ==================== 路径配置 ====================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # scripts/
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)               # v8_universal_generator/

# config.py 在 tools/ 目录（和 scripts/ 同级）
CONFIG_FILE = os.path.join(PROJECT_ROOT, "tools", "config.py")
INDEX_FILE = os.path.join(CURRENT_DIR, "models_index.json")


def get_index():
    """获取索引数据"""
    if not os.path.exists(INDEX_FILE):
        print("⚠️ 索引不存在，正在生成...")
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "model_index.py")])
    
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def list_models():
    """列出所有模型"""
    data = get_index()
    print(f"\n📚 可用模型列表 (共 {data['total_models']} 个):")
    print("=" * 80)
    for i, m in enumerate(data["models"]):
        default = " 👑" if m["name"] == data["default"] else ""
        ov = " [OV]" if m["is_ov"] else ""
        stars = "⭐" * (m["score"] // 20)
        print(f"  [{i:2d}] {m['name'][:45]:45s} {m['size_gb']:4.1f}GB  {stars}{ov}{default}")
        if m["tags"]:
            print(f"        标签: {', '.join(m['tags'])}")
    
    print(f"\n🏆 当前默认: {data['default']}")
    print(f"📅 索引更新: {data['generated']}")


def set_smart_default(model_name):
    """设置智能模式的默认模型"""
    data = get_index()
    
    found = None
    for m in data["models"]:
        if model_name.lower() in m["name"].lower():
            found = m
            break
    
    if not found:
        print(f"❌ 未找到包含 '{model_name}' 的模型")
        print("提示: 使用 --list 查看所有模型")
        return
    
    data["default"] = found["name"]
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 智能模式默认模型已切换: {found['name']}")
    print(f"   📁 {found['path']}")
    print(f"   🏷️  标签: {', '.join(found['tags'])}")
    
    # 同时切换 config.py 到 smart 模式
    set_mode("smart")


def set_mode(mode):
    """切换选择模式"""
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 找不到 config.py 文件: {CONFIG_FILE}")
        return
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    if mode in ["legacy", "smart", "manual"]:
        # 检查是否已有 MODEL_SELECTION_MODE
        if 'MODEL_SELECTION_MODE' not in content:
            # 在文件开头添加配置（在 import 之后）
            import_section = re.search(r'(import.*?\n)+', content)
            if import_section:
                insert_pos = import_section.end()
                content = content[:insert_pos] + \
                         f'\n# ==================== 🔵 模型选择配置 ====================\n' + \
                         f'MODEL_SELECTION_MODE = "{mode}"\n\n' + \
                         content[insert_pos:]
            else:
                content = '# ==================== 🔵 模型选择配置 ====================\n' + \
                         f'MODEL_SELECTION_MODE = "{mode}"\n\n' + content
        else:
            content = re.sub(
                r'MODEL_SELECTION_MODE = ".*?"',
                f'MODEL_SELECTION_MODE = "{mode}"',
                content
            )
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✅ 已切换到 {mode} 模式")
    else:
        print(f"❌ 无效模式: {mode}，可选: legacy, smart, manual")


def set_legacy_model(index):
    """切换到旧版编号模式"""
    data = get_index()
    legacy_mapping = data.get("legacy_mapping", {})
    
    if str(index) not in legacy_mapping:
        print(f"❌ 无效编号: {index}，可用: {list(legacy_mapping.keys())}")
        return
    
    filename = legacy_mapping[str(index)]
    
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 找不到 config.py 文件: {CONFIG_FILE}")
        return
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 修改 ACTIVE_MODEL
    if 'ACTIVE_MODEL' in content:
        content = re.sub(r'ACTIVE_MODEL = \d+', f'ACTIVE_MODEL = {index}', content)
    else:
        # 在文件中添加 ACTIVE_MODEL
        import_section = re.search(r'(import.*?\n)+', content)
        if import_section:
            insert_pos = import_section.end()
            content = content[:insert_pos] + \
                     f'\n# ==================== 🔵 模型选择配置 ====================\n' + \
                     f'ACTIVE_MODEL = {index}\n' + \
                     content[insert_pos:]
        else:
            content = '# ==================== 🔵 模型选择配置 ====================\n' + \
                     f'ACTIVE_MODEL = {index}\n\n' + content
    
    # 切换到 legacy 模式
    if 'MODEL_SELECTION_MODE' in content:
        content = re.sub(r'MODEL_SELECTION_MODE = ".*?"', 'MODEL_SELECTION_MODE = "legacy"', content)
    else:
        # 添加 MODEL_SELECTION_MODE
        if '# ==================== 🔵 模型选择配置 ====================' in content:
            content = content.replace(
                '# ==================== 🔵 模型选择配置 ====================',
                '# ==================== 🔵 模型选择配置 ====================\nMODEL_SELECTION_MODE = "legacy"'
            )
        else:
            content = content.replace(
                'ACTIVE_MODEL',
                'MODEL_SELECTION_MODE = "legacy"\nACTIVE_MODEL'
            )
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ 已切换到 legacy 模式，使用编号 {index}: {filename}")


def toggle_ov(enable=True):
    """切换 OpenVINO 模式"""
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 找不到 config.py 文件: {CONFIG_FILE}")
        return
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    if 'USE_OPENVINO_MODEL' not in content:
        # 在文件中添加 USE_OPENVINO_MODEL
        import_section = re.search(r'(import.*?\n)+', content)
        if import_section:
            insert_pos = import_section.end()
            content = content[:insert_pos] + \
                     f'\n# ==================== 🔵 模型选择配置 ====================\n' + \
                     f'USE_OPENVINO_MODEL = {enable}\n' + \
                     content[insert_pos:]
        else:
            content = '# ==================== 🔵 模型选择配置 ====================\n' + \
                     f'USE_OPENVINO_MODEL = {enable}\n\n' + content
    else:
        if enable:
            content = content.replace("USE_OPENVINO_MODEL = False", "USE_OPENVINO_MODEL = True")
            print("✅ 已启用 OpenVINO 模式")
        else:
            content = content.replace("USE_OPENVINO_MODEL = True", "USE_OPENVINO_MODEL = False")
            print("✅ 已关闭 OpenVINO 模式")
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def show_status():
    """显示当前状态"""
    data = get_index() if os.path.exists(INDEX_FILE) else None
    
    print("\n📊 当前配置状态:")
    
    # 检查 config.py 是否存在
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        mode_match = re.search(r'MODEL_SELECTION_MODE = "(.*?)"', content)
        ov_match = re.search(r'USE_OPENVINO_MODEL = (True|False)', content)
        active_match = re.search(r'ACTIVE_MODEL = (\d+)', content)
        
        print(f"  配置文件: {CONFIG_FILE}")
        print(f"  选择模式: {mode_match.group(1) if mode_match else '未设置 (默认 legacy)'}")
        print(f"  OpenVINO: {ov_match.group(1) if ov_match else 'False'}")
        if active_match:
            print(f"  Legacy 编号: {active_match.group(1)}")
    else:
        print(f"  ⚠️ 找不到 config.py: {CONFIG_FILE}")
    
    if data:
        print(f"  智能推荐: {data.get('default', '无')}")
        print(f"  模型总数: {data.get('total_models', 0)}")
        print(f"  索引文件: {INDEX_FILE}")
    else:
        print(f"  ⚠️ 找不到索引文件: {INDEX_FILE}")
    
    print(f"\n💡 可用命令:")
    print(f"  --list          列出所有模型")
    print(f"  --set <名称>    切换智能推荐模型")
    print(f"  --mode <模式>   切换模式 (legacy/smart/manual)")
    print(f"  --legacy <编号> 切换到旧版编号 (0-3)")
    print(f"  --ov            启用 OpenVINO")
    print(f"  --no-ov         禁用 OpenVINO")
    print(f"  --refresh       重新生成索引")


def main():
    parser = argparse.ArgumentParser(description="SD 模型切换工具")
    parser.add_argument("--list", action="store_true", help="列出所有模型")
    parser.add_argument("--set", type=str, help="设置智能模式默认模型")
    parser.add_argument("--mode", choices=["legacy", "smart", "manual"], help="切换选择模式")
    parser.add_argument("--legacy", type=int, help="切换到旧版编号模式 (0-3)")
    parser.add_argument("--ov", action="store_true", help="启用 OpenVINO")
    parser.add_argument("--no-ov", action="store_true", help="禁用 OpenVINO")
    parser.add_argument("--refresh", action="store_true", help="重新生成索引")
    parser.add_argument("--status", action="store_true", help="显示当前状态")
    
    args = parser.parse_args()
    
    if args.status or (not any(vars(args).values())):
        show_status()
    elif args.list:
        list_models()
    elif args.set:
        set_smart_default(args.set)
    elif args.mode:
        set_mode(args.mode)
    elif args.legacy is not None:
        set_legacy_model(args.legacy)
    elif args.ov:
        toggle_ov(True)
    elif args.no_ov:
        toggle_ov(False)
    elif args.refresh:
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "model_index.py"), "--refresh"])


if __name__ == "__main__":
    main()