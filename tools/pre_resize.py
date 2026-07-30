#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
前置工具：多档位图片缩小器
自动识别 tools 目录下的 input.xxx，直接覆盖原文件。
在顶部修改 SCALE_MODE 即可切换不同尺寸。

使用方法：
  1. 将图片放到 tools 目录下，命名为 input.jpg / input.png / input.webp
  2. 修改 SCALE_MODE 选择档位
  3. 运行 python pre_resize.py
  4. 原图会被缩放并覆盖
"""
import os
from PIL import Image
from config import INPUT_IMAGE_NAME, MAX_LIMIT

# ==================== ⚙️ 尺寸档位配置 ====================
# 档位说明：
# 0 = 极速测试 (256)   - 最快，仅适合测试流程，脸部会崩
# 1 = 迷你 (320)       - 快速测试，适合纯头像
# 2 = 极速 (384)       - 适合纯头像、特写、极速测试
# 3 = 标准 (512)       - 适合半身照、日常发公众号壁纸（最快最清晰）⭐ 默认
# 4 = 中档 (576)       - 比标准稍好，速度略慢
# 5 = 高清 (640)       - 适合全身照、大场景，不会崩脸
# 6 = 细节 (768)       - 适合极其复杂的全身照和细节要求高的风景/雕像
# 7 = 超清 (896)       - 细节丰富，适合精细场景
# 8 = 准高清 (1024)    - 大图，细节很好，速度较慢
# 9 = 高清 (1280)      - 大图，细节丰富，速度慢
# 10 = 超高清 (1536)   - 超大图，细节极致，速度很慢，需要大显存

SCALE_MODE = 6  # 👈 改这个数字就行（0-10）

# 档位映射
SCALE_MAP = {
    0: 256,      # 极速测试
    1: 320,      # 迷你
    2: 384,      # 极速
    3: 512,      # 标准 ⭐
    4: 576,      # 中档
    5: 640,      # 高清
    6: 768,      # 细节
    7: 896,      # 超清
    8: 1024,     # 准高清
    9: 1280,     # 高清
    10: 1536,    # 超高清
}

# 档位名称映射（用于显示）
SCALE_NAMES = {
    0: "极速测试",
    1: "迷你",
    2: "极速",
    3: "标准 ⭐",
    4: "中档",
    5: "高清",
    6: "细节",
    7: "超清",
    8: "准高清",
    9: "高清大图",
    10: "超高清",
}

# ==================== 核心逻辑 ====================

def find_and_replace_image(base_name):
    """
    在 tools 目录下查找 input.xxx，缩小，直接覆盖原文件
    """
    # 获取当前目录（tools 目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查档位是否有效
    if SCALE_MODE not in SCALE_MAP:
        print(f"❌ 错误：SCALE_MODE={SCALE_MODE} 无效！有效范围: 0-10")
        print(f"📋 可用档位：")
        for key, value in SCALE_MAP.items():
            print(f"   {key} = {value} ({SCALE_NAMES.get(key, '')})")
        return False
    
    target_max_limit = SCALE_MAP[SCALE_MODE]
    mode_name = SCALE_NAMES.get(SCALE_MODE, f"模式{SCALE_MODE}")
    
    print("="*50)
    print("🔄 图片缩小器 (tools 目录)")
    print("="*50)
    print(f"📂 工作目录: {current_dir}")
    print(f"📏 目标档位: {SCALE_MODE} -> {mode_name}")
    print(f"📏 最大边长: {target_max_limit}px")
    print("="*50)

    for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        path = os.path.join(current_dir, base_name + ext)
        if os.path.exists(path):
            print(f"📸 找到原图: {path}")
            
            # 1. 读取图片
            img = Image.open(path).convert('RGB')
            w, h = img.size
            print(f"📐 原图尺寸: {w}x{h}")

            # 2. 如果已经比目标小，直接跳过
            if w <= target_max_limit and h <= target_max_limit:
                print(f"✅ 原图已经小于或等于 {target_max_limit}，无需缩小")
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

            print(f"📐 目标尺寸: {target_w}x{target_h}")

            # 5. 执行缩小并直接覆盖原文件
            small_img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            small_img.save(path, quality=95)
            
            print(f"✅ 已完成！已覆盖原文件")
            print(f"💡 提示：如需换档，修改 SCALE_MODE 后重新运行")
            return True

    print(f"❌ 找不到 {base_name} 图片！")
    print(f"💡 请确保图片放在 tools 目录下，命名为:")
    print(f"   {base_name}.jpg / {base_name}.png / {base_name}.webp")
    return False

if __name__ == "__main__":
    find_and_replace_image(INPUT_IMAGE_NAME)