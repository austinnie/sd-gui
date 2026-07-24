# core/pipeline/presets.py
"""内置流水线配置 - 从 pipeline_tab.py 移出"""

BUILTIN_PIPELINES = {
    # ===== 风格转换类 =====
    "水彩风格": {
        "description": "转换为水彩画风格",
        "steps": [{"type": "watercolor", "config": {}}]
    },
    "国风水墨": {
        "description": "转换为国风水墨风格",
        "steps": [{"type": "ink_wash", "config": {}}]
    },
    "素描风格": {
        "description": "转换为素描风格",
        "steps": [{"type": "sketch", "config": {}}]
    },
    "赛博朋克": {
        "description": "转换为赛博朋克风格",
        "steps": [{"type": "cyberpunk", "config": {}}]
    },
    "蒸汽波": {
        "description": "转换为蒸汽波风格",
        "steps": [{"type": "vaporwave", "config": {}}]
    },
    "3D渲染": {
        "description": "转换为3D渲染风格",
        "steps": [{"type": "three_d_render", "config": {}}]
    },
    
    # ===== 场景/主题类 =====
    "海滩场景": {
        "description": "将人物放到海滩背景",
        "steps": [{"type": "beach", "config": {}}]
    },
    "森林场景": {
        "description": "将人物放到森林背景",
        "steps": [{"type": "forest", "config": {}}]
    },
    "太空场景": {
        "description": "将人物放到太空背景",
        "steps": [{"type": "space", "config": {}}]
    },
    "古堡场景": {
        "description": "将人物放到古堡背景",
        "steps": [{"type": "castle", "config": {}}]
    },
    "婚纱风格": {
        "description": "转换为婚纱/婚礼风格",
        "steps": [{"type": "wedding", "config": {}}]
    },
    
    # ===== 服装/造型类 =====
    "洛丽塔": {
        "description": "转换为洛丽塔风格",
        "steps": [{"type": "lolita", "config": {}}]
    },
    "和服风格": {
        "description": "转换为和服风格",
        "steps": [{"type": "kimono", "config": {}}]
    },
    "晚礼服": {
        "description": "转换为晚礼服风格",
        "steps": [{"type": "evening_gown", "config": {}}]
    },
    "复古照片": {
        "description": "转换为复古照片风格",
        "steps": [{"type": "vintage", "config": {}}]
    },
    "电影质感": {
        "description": "转换为电影质感风格",
        "steps": [{"type": "cinematic", "config": {}}]
    },
    
    # ===== 多人场景类 =====
    "情侣水彩": {
        "description": "情侣照片转换为水彩风格（双人优化）",
        "steps": [{"type": "couple_watercolor", "config": {}}]
    },
    "情侣油画": {
        "description": "情侣照片转换为油画风格（双人优化）",
        "steps": [{"type": "couple_oil_painting", "config": {}}]
    },
    "家庭素描": {
        "description": "家庭照片转换为素描风格（多人优化）",
        "steps": [{"type": "family_sketch", "config": {}}]
    },
    "朋友聚会": {
        "description": "朋友聚会照片风格化（多人优化）",
        "steps": [{"type": "friends_style", "config": {}}]
    },
    "团队照片": {
        "description": "团队照片风格化（多人优化）",
        "steps": [{"type": "group_photo", "config": {}}]
    },
    "婚纱照双人": {
        "description": "婚纱照风格（双人优化）",
        "steps": [{"type": "couple_wedding", "config": {}}]
    },
    
    # ===== 古风/汉服 =====
    "古风汉服": {
        "description": "将人物转换为古风汉服风格",
        "steps": [{"type": "hanfu", "config": {}}]
    },
    "赛博古风_霓虹": {
        "description": "汉服+赛博朋克融合 - 霓虹都市",
        "steps": [{"type": "cyber_hanfu", "config": {"strength": 0.40, "steps": 30, "cfg": 7.5}}]
    },
    "赛博古风_侠女": {
        "description": "汉服+赛博朋克融合 - 武侠风格",
        "steps": [{"type": "cyber_hanfu", "config": {"strength": 0.45, "steps": 35, "cfg": 8.0}}]
    },
    "赛博古风_仙女": {
        "description": "汉服+赛博朋克融合 - 仙女风格",
        "steps": [{"type": "cyber_hanfu", "config": {"strength": 0.35, "steps": 30, "cfg": 7.0}}]
    },
    "赛博古风_双人": {
        "description": "汉服+赛博朋克融合 - 双人场景",
        "steps": [{"type": "cyber_hanfu", "config": {"strength": 0.40, "steps": 35, "cfg": 7.5}}]
    },
    
    # ===== 雕像/材质 =====
    "大理石雕像": {
        "description": "将人物转换为大理石雕像风格（14种场景）",
        "steps": [{"type": "marble", "config": {}}]
    },
    "大理石雕像_快速": {
        "description": "快速版 - 只生成6种场景",
        "steps": [{"type": "marble", "config": {"scenes": 6}}]
    },
    "大理石瑜伽雕像": {
        "description": "将人物转换为大理石雕像瑜伽姿势 (16种经典体式)",
        "steps": [{"type": "marble_yoga", "config": {}}]
    },
    "大理石瑜伽雕像_快速": {
        "description": "快速版 - 只生成前6种瑜伽姿势",
        "steps": [{"type": "marble_yoga", "config": {"scenes": 6}}]
    },
    "青铜雕像": {
        "description": "将人物转换为青铜雕像风格（12种场景）",
        "steps": [{"type": "bronze_statue", "config": {}}]
    },
    "青铜雕像_快速": {
        "description": "快速版 - 只生成6种场景",
        "steps": [{"type": "bronze_statue", "config": {"scenes": 6}}]
    },
    
    # ===== 其他 =====
    "旗袍风格": {
        "description": "将人物转换为传统旗袍风格",
        "steps": [{"type": "qipao", "config": {}}]
    },
    "情侣拥抱": {
        "description": "生成情侣拥抱场景",
        "steps": [{"type": "couple", "config": {}}]
    },
    "浪漫接吻": {
        "description": "生成浪漫接吻场景",
        "steps": [{"type": "couple", "config": {}}]
    },
    "油画风格": {
        "description": "转换为油画风格",
        "steps": [{"type": "oil_painting", "config": {}}]
    },
    "动漫爱爱": {
        "description": "转换为动漫爱爱风格",
        "steps": [{"type": "anime_xxx", "config": {}}]
    },
    "瑜伽姿势": {
        "description": "转换为瑜伽姿势 (20种经典体式)",
        "steps": [{"type": "yoga", "config": {}}]
    },
    "瑜伽姿势_快速": {
        "description": "快速版 - 只生成前4种基础瑜伽姿势",
        "steps": [{"type": "yoga", "config": {"scenes": 4}}]
    },
    
    # ===== 去掉衣服 =====
    "去掉衣服_全部场景": {
        "description": "去掉衣服 - 所有场景",
        "steps": [{"type": "remove_clothes", "config": {}}]
    },
    "去掉衣服_比基尼": {
        "description": "比基尼/泳装 → 裸体",
        "steps": [{"type": "remove_clothes", "config": {"strength": 0.50, "steps": 30}}]
    },
    "去掉衣服_紧身衣": {
        "description": "紧身衣/瑜伽服 → 裸体",
        "steps": [{"type": "remove_clothes", "config": {"strength": 0.55, "steps": 30}}]
    },
    "去掉衣服_正装": {
        "description": "正装/外套 → 裸体",
        "steps": [{"type": "remove_clothes", "config": {"strength": 0.60, "steps": 35}}]
    },
    "去掉衣服_宽松": {
        "description": "宽松衣物 → 裸体",
        "steps": [{"type": "remove_clothes", "config": {"strength": 0.65, "steps": 40, "cfg": 6.5}}]
    },
    "去掉衣服_职业装": {
        "description": "职业装 → 裸体",
        "steps": [{"type": "remove_clothes", "config": {"strength": 0.60, "steps": 35}}]
    },
    "去掉衣服_校服": {
        "description": "校服/学生装 → 裸体",
        "steps": [{"type": "remove_clothes", "config": {"strength": 0.55, "steps": 30}}]
    },
    "去掉衣服_传统服装": {
        "description": "传统服装 → 裸体",
        "steps": [{"type": "remove_clothes", "config": {"strength": 0.60, "steps": 35}}]
    },
    "去掉衣服_内衣": {
        "description": "内衣/情趣内衣 → 裸体",
        "steps": [{"type": "remove_clothes", "config": {"strength": 0.45, "steps": 30}}]
    },
}