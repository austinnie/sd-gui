# scripts/switch_model.py
# ==================== 🔄 模型切换工具（支持 SD1.5 + SDXL） ====================
"""
用法:
    python switch_model.py --list                    # 列出所有模型
    python switch_model.py --list --type sdxl       # 只列出 SDXL 模型
    python switch_model.py --type sd15|sdxl         # 切换模型类型（自动降级）
    python switch_model.py --force sd15|sdxl        # 强制切换（不降级）
    python switch_model.py --suggest                # 智能推荐
    python switch_model.py --status                 # 显示状态
    python switch_model.py --set <名称>             # 设置默认模型
    python switch_model.py --refresh                # 重新生成索引
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

CONFIG_FILE = os.path.join(PROJECT_ROOT, "tools", "config.py")
INDEX_FILE = os.path.join(CURRENT_DIR, "models_index.json")

# ==================== 模型类型定义 ====================
MODEL_TYPES = {
    "sd15": {
        "name": "SD1.5",
        "icon": "🟢",
        "fallback_type": None,
    },
    "sdxl": {
        "name": "SDXL",
        "icon": "🔵",
        "fallback_type": "sd15",
    },
}


def get_index():
    """获取索引数据，如果不存在则自动生成"""
    if not os.path.exists(INDEX_FILE):
        print("⚠️ 索引不存在，正在生成...")
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "model_index.py")])
    
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"⚠️ 索引文件损坏 ({e})，正在重建...")
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "model_index.py"), "--refresh"])
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)


def get_models_by_type(data, model_type):
    """获取指定类型的所有模型"""
    return [m for m in data.get("models", []) if m.get("model_type") == model_type]


def resolve_model_path(data, model_entry):
    """解析模型路径（多层 fallback）"""
    if not model_entry:
        return None
    
    # 1. 相对路径
    if "path" in model_entry and model_entry["path"]:
        abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, model_entry["path"]))
        if os.path.exists(abs_path):
            return abs_path
    
    # 2. 绝对路径
    if "absolute_path" in model_entry and model_entry["absolute_path"]:
        if os.path.exists(model_entry["absolute_path"]):
            return model_entry["absolute_path"]
    
    # 3. 直接路径
    if "path" in model_entry and model_entry["path"]:
        if os.path.exists(model_entry["path"]):
            return model_entry["path"]
    
    # 4. 根据文件名查找
    if "filename" in model_entry:
        model_type = model_entry.get("model_type", "sd15")
        
        # 在索引记录的目录中查找
        model_dirs = data.get("model_dirs", {})
        if model_type in model_dirs:
            fallback_path = os.path.join(model_dirs[model_type], model_entry["filename"])
            if os.path.exists(fallback_path):
                return fallback_path
        
        # 在标准位置查找
        standard_dirs = [
            os.path.join(PROJECT_ROOT, "models", model_type),
            os.path.join(os.path.dirname(PROJECT_ROOT), "models", model_type),
        ]
        for dir_path in standard_dirs:
            fallback_path = os.path.join(dir_path, model_entry["filename"])
            if os.path.exists(fallback_path):
                return fallback_path
    
    return None


def set_config_value(key, value):
    """修改 config.py 中的配置值"""
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 找不到 config.py 文件: {CONFIG_FILE}")
        return False
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否已存在该配置
        pattern = rf'{key} = .*?\n'
        if re.search(pattern, content):
            content = re.sub(pattern, f'{key} = "{value}"\n', content)
        else:
            # 在文件开头的导入部分之后添加
            import_match = re.search(r'(import.*?\n)+', content)
            if import_match:
                insert_pos = import_match.end()
                content = content[:insert_pos] + f'\n{key} = "{value}"\n' + content[insert_pos:]
            else:
                content = f'{key} = "{value}"\n\n' + content
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"❌ 写入 config.py 失败: {e}")
        return False


def get_active_model_type():
    """从 config.py 读取当前激活的模型类型"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.search(r'MODEL_TYPE = "(.*?)"', content)
            if match:
                return match.group(1)
    except Exception:
        pass
    return "sd15"


def switch_model_type(model_type, auto_fallback=True):
    """切换模型类型"""
    data = get_index()
    
    # 检查该类型是否有模型
    models = get_models_by_type(data, model_type)
    
    if not models:
        config = MODEL_TYPES.get(model_type, {})
        fallback_type = config.get("fallback_type")
        
        if auto_fallback and fallback_type:
            fallback_models = get_models_by_type(data, fallback_type)
            if fallback_models:
                fallback_name = MODEL_TYPES.get(fallback_type, {}).get("name", fallback_type)
                print(f"⚠️ {config.get('name', model_type)} 无可用模型，自动降级到 {fallback_name}")
                return switch_model_type(fallback_type, auto_fallback=False)
            else:
                print(f"❌ {config.get('name', model_type)} 和 {fallback_type} 都无可用模型")
                return False, None
        else:
            print(f"❌ {config.get('name', model_type)} 无可用模型")
            return False, None
    
    # 选择最佳模型
    default_name = data.get("default")
    selected_model = None
    
    if default_name:
        for m in models:
            if m["name"] == default_name:
                selected_model = m
                break
    
    if not selected_model:
        selected_model = models[0]
    
    # 验证路径
    path = resolve_model_path(data, selected_model)
    if not path:
        for m in models:
            path = resolve_model_path(data, m)
            if path:
                selected_model = m
                break
    
    if not path:
        print(f"❌ 模型路径无效: {selected_model.get('name', '未知')}")
        return False, None
    
    # 更新 config.py
    if set_config_value("MODEL_TYPE", model_type):
        type_name = MODEL_TYPES.get(model_type, {}).get("name", model_type)
        print(f"✅ 已切换到 {type_name}")
        print(f"   📁 模型: {selected_model['name']}")
        print(f"   📂 路径: {path}")
        return True, selected_model
    else:
        return False, None


def list_models(filter_type=None):
    """列出所有模型"""
    data = get_index()
    models = data.get("models", [])
    
    if filter_type:
        models = [m for m in models if m.get("model_type") == filter_type]
        if not models:
            print(f"❌ 没有找到 {filter_type} 类型的模型")
            return
    
    if not models:
        print("❌ 没有找到任何模型")
        return
    
    print(f"\n📚 可用模型列表 (共 {len(models)} 个):")
    if filter_type:
        type_name = MODEL_TYPES.get(filter_type, {}).get("name", filter_type)
        print(f"   🔍 过滤类型: {type_name}")
    print("=" * 80)
    
    for i, m in enumerate(models):
        default = " 👑" if m["name"] == data.get("default") else ""
        ov = " [OV]" if m.get("is_ov") else ""
        stars = "⭐" * (m.get("score", 0) // 20)
        icon = m.get("model_type_icon", "📁")
        type_name = m.get("model_type_name", "")
        size = m.get("size_gb", 0)
        
        print(f"  [{i:2d}] {icon} {m['name'][:45]:45s} {size:4.1f}GB  {stars}{ov}{default}")
        print(f"        类型: {type_name} | 标签: {', '.join(m.get('tags', []))}")
    
    # 显示类型统计
    print("\n📊 模型类型统计:")
    type_groups = data.get("type_groups", {})
    for model_type, group in type_groups.items():
        print(f"   {group['icon']} {group['name']}: {group['count']} 个")
        if group.get('default'):
            print(f"      默认: {group['default']}")
    
    print(f"\n🏆 全局默认: {data.get('default', '无')}")
    print(f"📅 索引更新: {data.get('generated', '未知')}")


def show_suggestion():
    """智能推荐"""
    data = get_index()
    models = data.get("models", [])
    
    if not models:
        print("❌ 没有找到任何模型")
        return
    
    # 统计各类型
    type_counts = {}
    for model_type in MODEL_TYPES.keys():
        type_models = [m for m in models if m.get("model_type") == model_type]
        type_counts[model_type] = len(type_models)
    
    # 优先级：SDXL > SD1.5
    if type_counts.get("sdxl", 0) > 0:
        suggestion = "sdxl"
        reason = "SDXL 提供更高质量和分辨率"
        best = None
        for m in models:
            if m.get("model_type") == "sdxl":
                best = m["name"]
                break
    elif type_counts.get("sd15", 0) > 0:
        suggestion = "sd15"
        reason = "SD1.5 兼容性更好，速度更快"
        best = None
        for m in models:
            if m.get("model_type") == "sd15":
                best = m["name"]
                break
    else:
        print("❌ 没有可推荐的模型类型")
        return
    
    config = MODEL_TYPES.get(suggestion, {})
    print(f"\n💡 智能推荐: {config['icon']} {config['name']}")
    print(f"   原因: {reason}")
    print(f"   可用数量: {type_counts.get(suggestion, 0)} 个")
    if best:
        print(f"   最佳模型: {best}")
    
    # 检查当前激活类型
    active = get_active_model_type()
    if active != suggestion and type_counts.get(active, 0) > 0:
        print(f"\n   ⚠️ 当前激活的是 {MODEL_TYPES.get(active, {}).get('name', active)}")
        print(f"   💡 建议切换: python switch_model.py --type {suggestion}")


def show_status():
    """显示当前状态"""
    data = get_index() if os.path.exists(INDEX_FILE) else None
    
    print("\n📊 当前配置状态:")
    print("=" * 60)
    
    if data:
        models = data.get("models", [])
        print(f"  索引文件: {INDEX_FILE}")
        print(f"  模型总数: {len(models)}")
        print(f"  全局默认: {data.get('default', '无')}")
        print(f"  默认类型: {data.get('default_type', '无')}")
        
        # 类型统计
        type_groups = data.get("type_groups", {})
        if type_groups:
            print(f"\n  📁 模型类型:")
            for model_type, group in type_groups.items():
                print(f"     {group['icon']} {group['name']}: {group['count']} 个")
                if group.get('default'):
                    print(f"        默认: {group['default']}")
    else:
        print(f"  ⚠️ 找不到索引文件: {INDEX_FILE}")
    
    # 读取 config.py
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        model_type_match = re.search(r'MODEL_TYPE = "(.*?)"', content)
        mode_match = re.search(r'MODEL_SELECTION_MODE = "(.*?)"', content)
        ov_match = re.search(r'USE_OPENVINO_MODEL = (True|False)', content)
        active_match = re.search(r'ACTIVE_MODEL = (\d+)', content)
        
        print(f"\n  📄 配置文件: {CONFIG_FILE}")
        print(f"  模型类型: {model_type_match.group(1) if model_type_match else '未设置 (默认 sd15)'}")
        if mode_match:
            print(f"  选择模式: {mode_match.group(1)}")
        if ov_match:
            print(f"  OpenVINO: {ov_match.group(1)}")
        if active_match:
            print(f"  Legacy 编号: {active_match.group(1)}")
    
    # 智能建议
    print("\n" + "-" * 60)
    show_suggestion()
    
    print(f"\n💡 可用命令:")
    print(f"  --list                   列出所有模型")
    print(f"  --list --type sdxl       只列出 SDXL 模型")
    print(f"  --type sd15|sdxl         切换模型类型（自动降级）")
    print(f"  --force sd15|sdxl        强制切换（不降级）")
    print(f"  --suggest                智能推荐")
    print(f"  --set <名称>             设置默认模型")
    print(f"  --refresh               重新生成索引")


def main():
    parser = argparse.ArgumentParser(description="SD 模型切换工具（支持 SD1.5 + SDXL）")
    parser.add_argument("--list", action="store_true", help="列出所有模型")
    parser.add_argument("--type", choices=["sd15", "sdxl"], help="切换模型类型（自动降级）")
    parser.add_argument("--force", choices=["sd15", "sdxl"], help="强制切换模型类型（不降级）")
    parser.add_argument("--suggest", action="store_true", help="智能推荐")
    parser.add_argument("--status", action="store_true", help="显示状态")
    parser.add_argument("--set", type=str, help="设置默认模型")
    parser.add_argument("--refresh", action="store_true", help="重新生成索引")
    
    args = parser.parse_args()
    
    if args.status or (not any(vars(args).values())):
        show_status()
    
    elif args.list:
        list_models()
    
    elif args.type:
        switch_model_type(args.type, auto_fallback=True)
    
    elif args.force:
        switch_model_type(args.force, auto_fallback=False)
    
    elif args.suggest:
        show_suggestion()
    
    elif args.set:
        data = get_index()
        models = data.get("models", [])
        found = None
        for m in models:
            if args.set.lower() in m["name"].lower():
                found = m
                break
        
        if found:
            data["default"] = found["name"]
            data["default_type"] = found.get("model_type", "sd15")
            with open(INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已设置默认模型: {found['name']}")
            # 自动切换到对应类型
            model_type = found.get("model_type", "sd15")
            set_config_value("MODEL_TYPE", model_type)
            type_name = MODEL_TYPES.get(model_type, {}).get("name", model_type)
            print(f"   📊 自动切换到: {type_name}")
        else:
            print(f"❌ 未找到包含 '{args.set}' 的模型")
            list_models()
    
    elif args.refresh:
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "model_index.py"), "--refresh"])


if __name__ == "__main__":
    main()