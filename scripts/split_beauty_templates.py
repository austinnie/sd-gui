#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
拆分 beauty.json 为多个子分类
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def backup_file(filepath):
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        print(f"📦 已备份: {backup_path}")
        return backup_path
    return None


# 分类关键词映射
CATEGORY_MAP = {
    "beauty_pure": {
        "name": "清纯甜美",
        "icon": "🌸",
        "priority": 1,
        "keywords": ["清纯甜美", "纯欲", "校园", "初恋", "森系", "甜美", "仙女", "雪白肌肤", "睡衣居家", "晨光私密", "少女", "日系盐系", "韩系时尚", "复古港风", "不良少女"]
    },
    "beauty_sexy": {
        "name": "性感诱惑",
        "icon": "🔥",
        "priority": 2,
        "keywords": ["性感御姐", "色气满满", "诱惑", "兔女郎", "猫女郎", "湿身", "油光", "禁忌", "夜色", "捆绑", "束缚", "皮革", "半透明", "情趣", "内衣", "比基尼", "泳装", "真空", "丁字裤", "C字裤", "开裆", "蕾丝"]
    },
    "beauty_breast": {
        "name": "巨乳系列",
        "icon": "🍒",
        "priority": 3,
        "keywords": ["巨乳", "大臀", "蜜桃臀", "臀部", "真空巨乳", "胸部", "乳胶衣"]
    },
    "beauty_nude": {
        "name": "裸体艺术",
        "icon": "🎨",
        "priority": 4,
        "keywords": ["裸体", "私处", "人体", "光影", "剪影", "艺术裸体", "自然融合", "水镜", "布纹", "黑白", "轻纱", "岩石", "火与影", "超现实", "几何", "裸", "nude"]
    },
    "beauty_classic": {
        "name": "古典艺术",
        "icon": "🏛️",
        "priority": 5,
        "keywords": ["文艺复兴", "古典油画", "巴洛克", "洛可可", "新古典主义", "威尼斯", "古典", "女神", "希腊", "雅典娜", "阿佛洛狄忒", "阿尔忒弥斯", "赫拉", "珀耳塞福涅", "赫斯提亚", "尼刻", "缪斯", "厄俄斯", "大理石", "雕像"]
    },
    "beauty_anime": {
        "name": "动漫风格",
        "icon": "🎭",
        "priority": 6,
        "keywords": ["动漫", "二次元", "anime", "manga", "萝莉", "御姐", "女仆", "护士", "教师", "巫女", "女王", "精灵", "恶魔", "天使", "新娘", "百合", "触手", "捆绑艺术", "COS"]
    },
    "beauty_ethnic": {
        "name": "各国美女",
        "icon": "🌍",
        "priority": 7,
        "keywords": ["巴西", "哥伦比亚", "法国", "瑞典", "意大利", "日本", "韩国", "美国", "俄罗斯", "印度", "非洲", "亚洲", "中国", "英国", "德国", "西班牙", "北欧", "东欧"]
    },
    "beauty_style": {
        "name": "时尚风格",
        "icon": "👗",
        "priority": 8,
        "keywords": ["赛博朋克", "哥特", "暗黑", "欧美辣妹", "运动", "健身", "瑜伽", "运动力量", "极限", "太空"]
    }
}


def classify_template(name: str) -> str:
    """根据名称分类"""
    name_lower = name.lower()
    
    for cat_id, cat_info in CATEGORY_MAP.items():
        for keyword in cat_info["keywords"]:
            if keyword.lower() in name_lower:
                return cat_id
    
    # 默认放到 "其他"
    return "beauty_other"


def split_beauty():
    """拆分 beauty.json"""
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_file = os.path.join(project_root, "templates", "prompts", "beauty.json")
    output_dir = os.path.join(project_root, "templates", "prompts")
    
    if not os.path.exists(source_file):
        print(f"❌ 源文件不存在: {source_file}")
        return False
    
    # 备份
    backup_file(source_file)
    
    # 读取
    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    templates = data.get("templates", [])
    print(f"📖 读取 {len(templates)} 个模板")
    
    # 分类
    classified = {cat_id: [] for cat_id in CATEGORY_MAP.keys()}
    classified["beauty_other"] = []
    unmatched = []
    
    for template in templates:
        name = template.get("name", "")
        cat_id = classify_template(name)
        classified[cat_id].append(template)
        if cat_id == "beauty_other":
            unmatched.append(name)
    
    # 统计
    print("\n📊 分类统计:")
    total = 0
    for cat_id, items in classified.items():
        if items:
            cat_name = CATEGORY_MAP.get(cat_id, {}).get("name", cat_id)
            print(f"   {cat_name}: {len(items)} 个")
            total += len(items)
    print(f"   📝 总计: {total} 个")
    
    if unmatched:
        print(f"\n⚠️ 未匹配的模板 ({len(unmatched)} 个):")
        for name in unmatched[:10]:
            print(f"      - {name}")
        if len(unmatched) > 10:
            print(f"      ... 共 {len(unmatched)} 个")
    
    # 写入拆分后的文件
    print("\n📁 写入拆分文件...")
    
    for cat_id, items in classified.items():
        if not items:
            continue
        
        cat_info = CATEGORY_MAP.get(cat_id, {})
        cat_name = cat_info.get("name", cat_id)
        icon = cat_info.get("icon", "📁")
        priority = cat_info.get("priority", 99)
        
        output_data = {
            "name": cat_name,
            "icon": icon,
            "priority": priority,
            "templates": items
        }
        
        output_file = os.path.join(output_dir, f"{cat_id}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ {cat_id}.json: {len(items)} 个模板")
    
    # 更新 categories.json
    categories_file = os.path.join(output_dir, "categories.json")
    with open(categories_file, 'r', encoding='utf-8') as f:
        categories_data = json.load(f)
    
    # 获取现有的分类列表
    existing_categories = {c["id"]: c for c in categories_data.get("categories", [])}
    
    # 添加新分类
    for cat_id, items in classified.items():
        if not items:
            continue
        if cat_id not in existing_categories:
            cat_info = CATEGORY_MAP.get(cat_id, {})
            existing_categories[cat_id] = {
                "id": cat_id,
                "name": cat_info.get("name", cat_id),
                "icon": cat_info.get("icon", "📁"),
                "priority": cat_info.get("priority", 99),
                "file": f"{cat_id}.json"
            }
    
    # 更新 categories.json
    categories_data["categories"] = list(existing_categories.values())
    categories_data["categories"].sort(key=lambda x: x.get("priority", 99))
    
    with open(categories_file, 'w', encoding='utf-8') as f:
        json.dump(categories_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ categories.json 已更新")
    
    # 可选择删除或保留原文件
    print(f"\n💡 原文件: {source_file}")
    print("   确认无误后可删除原 beauty.json")


if __name__ == "__main__":
    print("=" * 50)
    print("🔧 beauty.json 自动拆分工具")
    print("=" * 50)
    
    split_beauty()
    
    print("\n✅ 拆分完成！")
    print("\n📁 生成的文件:")
    print("   templates/prompts/")
    print("   ├── beauty_pure.json     # 清纯甜美")
    print("   ├── beauty_sexy.json     # 性感诱惑")
    print("   ├── beauty_breast.json   # 巨乳系列")
    print("   ├── beauty_nude.json     # 裸体艺术")
    print("   ├── beauty_classic.json  # 古典艺术")
    print("   ├── beauty_anime.json    # 动漫风格")
    print("   ├── beauty_ethnic.json   # 各国美女")
    print("   ├── beauty_style.json    # 时尚风格")
    print("   ├── beauty_other.json    # 其他")
    print("   └── categories.json      # 已更新")