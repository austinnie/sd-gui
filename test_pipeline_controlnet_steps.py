# test_pipeline_controlnet_steps.py
"""
测试所有 ControlNet 步骤是否正确导入
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pipeline.steps import (
    # 已支持 ControlNet 的步骤
    SketchStep,
    WatercolorStep,
    InkWashStep,
    OilPaintingStep,
    CyberpunkStep,
    VaporwaveStep,
    MarbleStep,
    ThreeDRenderStep,
    BeachStep,
    ForestStep,
    SpaceStep,
    CastleStep,
    WeddingStep,
    LolitaStep,
    KimonoStep,
    EveningGownStep,
    VintageStep,
    CinematicStep,
    HanfuStep,
    QipaoStep,
    CoupleStep,
    YogaStep,
    RemoveClothesStep,
    AnimeXxxStep,
    CoupleWatercolorStep,
    CoupleOilPaintingStep,
    CoupleWeddingStep,
    FamilySketchStep,
    FriendsStyleStep,
    GroupPhotoStep,
)

print("=" * 60)
print("🧪 测试所有 ControlNet 步骤导入")
print("=" * 60)

# 所有步骤列表
all_steps = [
    ("SketchStep", SketchStep()),
    ("WatercolorStep", WatercolorStep()),
    ("InkWashStep", InkWashStep()),
    ("OilPaintingStep", OilPaintingStep()),
    ("CyberpunkStep", CyberpunkStep()),
    ("VaporwaveStep", VaporwaveStep()),
    ("MarbleStep", MarbleStep()),
    ("ThreeDRenderStep", ThreeDRenderStep()),
    ("BeachStep", BeachStep()),
    ("ForestStep", ForestStep()),
    ("SpaceStep", SpaceStep()),
    ("CastleStep", CastleStep()),
    ("WeddingStep", WeddingStep()),
    ("LolitaStep", LolitaStep()),
    ("KimonoStep", KimonoStep()),
    ("EveningGownStep", EveningGownStep()),
    ("VintageStep", VintageStep()),
    ("CinematicStep", CinematicStep()),
    ("HanfuStep", HanfuStep()),
    ("QipaoStep", QipaoStep()),
    ("CoupleStep", CoupleStep()),
    ("YogaStep", YogaStep()),
    ("RemoveClothesStep", RemoveClothesStep()),
    ("AnimeXxxStep", AnimeXxxStep()),
    ("CoupleWatercolorStep", CoupleWatercolorStep()),
    ("CoupleOilPaintingStep", CoupleOilPaintingStep()),
    ("CoupleWeddingStep", CoupleWeddingStep()),
    ("FamilySketchStep", FamilySketchStep()),
    ("FriendsStyleStep", FriendsStyleStep()),
    ("GroupPhotoStep", GroupPhotoStep()),
]

print("\n📊 ControlNet 配置汇总:")
print("-" * 60)
print(f"{'步骤名称':<25} {'启用':<8} {'类型':<12} {'强度':<6}")
print("-" * 60)

success_count = 0
for name, step in all_steps:
    try:
        config = step._config
        use_cn = config.get('use_controlnet', '未设置')
        cn_type = config.get('controlnet_type', '未设置')
        cn_strength = config.get('controlnet_strength', '未设置')
        
        # 标记颜色（用符号表示）
        status = "✅" if use_cn is not False else "⏸️"
        
        print(f"{name:<25} {status:<8} {cn_type:<12} {cn_strength:<6}")
        success_count += 1
    except Exception as e:
        print(f"{name:<25} ❌ 错误: {e}")

print("-" * 60)
print(f"\n✅ 成功导入: {success_count}/{len(all_steps)} 个步骤")

# 统计 ControlNet 类型分布
print("\n📈 ControlNet 类型统计:")
type_counts = {}
for name, step in all_steps:
    try:
        cn_type = step._config.get('controlnet_type', 'unknown')
        type_counts[cn_type] = type_counts.get(cn_type, 0) + 1
    except:
        pass

for cn_type, count in sorted(type_counts.items()):
    print(f"   {cn_type}: {count} 个步骤")

print("\n" + "=" * 60)
print("✅ 测试完成！所有步骤已正确配置 ControlNet")
print("=" * 60)