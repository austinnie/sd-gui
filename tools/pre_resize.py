#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
前置工具：多档位图片缩小器
自动识别 input.xxx，直接覆盖原文件。
在顶部修改 SCALE_MODE 即可切换不同尺寸。
"""
import os
from PIL import Image
from config import INPUT_IMAGE_NAME, MAX_LIMIT

# ==================== ⚙️ 尺寸档位配置 ====================
# 1 = 极速 (384) 适合纯头像、特写、极速测试
# 2 = 标准 (512) 适合半身照、日常发公众号壁纸（最快最清晰）
# 3 = 高清 (640) 适合全身照、大场景，不会崩脸
# 4 = 细节 (768) 适合极其复杂的全身照和细节要求极高的风景/雕像
SCALE_MODE = 2  # 👈 改这个数字就行（1, 2, 3, 4）

# 档位映射
SCALE_MAP = {
    1: 384,
    2: 512,
    3: 640,
    4: 768
}

# ==================== 核心逻辑 ====================

def find_and_replace_image(base_name):
    """找到原图，缩小，直接覆盖原文件"""
    target_max_limit = SCALE_MAP.get(SCALE_MODE, 512)
    print(f"📏 目标尺寸模式: {SCALE_MODE} -> 最大限制边长: {target_max_limit}")

    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = base_name + ext
        if os.path.exists(path):
            print(f"📸 找到原图: {path}")
            
            # 1. 读取图片
            img = Image.open(path).convert('RGB')
            w, h = img.size
            print(f"📐 原图尺寸: {w}x{h}")

            # 2. 如果已经比目标小，直接跳过
            if w <= target_max_limit and h <= target_max_limit:
                print(f"✅ 原图已经小于 {target_max_limit}，无需缩小，原路返回。")
                return True

            # 3. 等比例缩小到目标以内
            target_w, target_h = w, h
            if target_w > target_max_limit or target_h > target_max_limit:
                if target_w > target_h:
                    scale = target_max_limit / target_w
                else:
                    scale = target_max_limit / target_h
                target_w = int(target_w * scale)
                target_h = int(target_h * scale)

            # 4. 对齐到 64 的倍数 (SD 硬要求)
            target_w = ((target_w + 31) // 64) * 64
            target_h = ((target_h + 31) // 64) * 64

            # 5. 执行缩小并直接覆盖原文件
            small_img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            small_img.save(path, quality=95)
            
            print(f"✅ 已完成！缩小至 {target_w}x{target_h}，已直接覆盖原文件！")
            return True

    print(f"❌ 找不到 {base_name} 图片！")
    return False

if __name__ == "__main__":
    find_and_replace_image(INPUT_IMAGE_NAME)