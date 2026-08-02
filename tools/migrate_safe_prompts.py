# migrate_safe_prompts.py
import os
import shutil

# ==================== 配置 ====================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(CURRENT_DIR, "prompts")
TARGET_DIR = os.path.join(CURRENT_DIR, "prompts_new")

# 安全、适合微信公众号迁移的"白名单"文件名（不包含 .py）
# 这些是你发过来的纯安全、国风、机甲、动植物线稿、奢侈品设计文件
SAFE_FILENAMES = [
    # --- 书画与传统文化 ---
    "calligraphy_art",
    "cn_painting_art",
    
    # --- 动植物线稿 ---
    "dragon_sketch",
    "horse_sketch",
    "tiger_sketch",
    "crane_sketch",
    "koi_sketch",
    "pig_sketch",
    "rooster_sketch",
    "monkey_sketch",
    "goat_sketch",
    "snake_sketch",
    "rabbit_sketch",
    "ox_sketch",
    "rat_sketch",
    "dog_sketch",
    "cat_sketch",
    "flower_sketch",
    "bird_sketch",
    
    # --- 纯机械、机甲与特摄设定 ---
    "mecha_blueprint",
    "mecha_sketch",
    "mecha_glow",
    "gundam_sketch",
    "transformers_sketch",
    "rider_sketch",
    "eva_sketch",
    "gits_sketch",
    
    # --- 奢侈品、设计、建筑 ---
    "jewelry_showcase",
    "jewelry_blueprint",
    "bag_blueprint",
    "watch_blueprint",
    "city_sketch",
]

# ==================== 执行迁移 ====================
def migrate_files():
    print("="*50)
    print("🚀 开始将安全提示词复制到 prompts_new 目录...")
    print("="*50)
    
    # 1. 确保目标目录存在
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        print(f"✅ 已创建目标目录: {TARGET_DIR}")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    # 2. 遍历白名单，进行复制
    for filename in SAFE_FILENAMES:
        source_path = os.path.join(SOURCE_DIR, f"{filename}.py")
        target_path = os.path.join(TARGET_DIR, f"{filename}.py")
        
        # 检查源文件是否存在
        if not os.path.exists(source_path):
            print(f"⚠️ 警告：源文件不存在，跳过: {filename}.py")
            skip_count += 1
            continue
            
        try:
            # 如果目标文件已存在，先删掉旧的（执行覆盖更新）
            if os.path.exists(target_path):
                os.remove(target_path)
                
            # 复制文件
            shutil.copy2(source_path, target_path)
            print(f"✅ 成功迁移: {filename}.py")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 迁移失败 {filename}.py: {e}")
            error_count += 1

    print("="*50)
    print(f"🏁 迁移完成！")
    print(f"   ✅ 成功复制: {success_count} 个文件")
    print(f"   ⚠️  源文件缺失: {skip_count} 个文件")
    print(f"   ❌ 复制出错: {error_count} 个文件")
    print("="*50)
    print("💡 提醒：原 prompts 目录的文件完好无损，若无需旧文件可自行清理。")
    print("💡 生成时默认使用 prompts_new 目录。")

if __name__ == "__main__":
    migrate_files()