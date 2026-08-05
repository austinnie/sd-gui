# tools/ai_clean_config.py
"""
消除AI痕迹配置
"""

# ==================== 消除AI痕迹开关 ====================
REMOVE_AI_TRACES = True  # 总开关

# 各功能开关
AI_CLEAR_METADATA = True   # 清除元数据（转换为JPG）
AI_INJECT_EXIF = True      # 注入EXIF信息
AI_REALISTIC = True        # 照片真实化

# 参数配置
AI_CAMERA = "sony_a7iv"    # 相机预设: sony_a7iv, canon_r5, nikon_z8, iphone_15
AI_STRENGTH = "medium"     # 强度: light / medium / strong
AI_STYLE = "portrait"      # 风格: portrait, landscape, street, night

# 是否随机化参数（让每张照片的EXIF略有不同）
AI_RANDOMIZE = True

# ==================== 🆕 图像指纹混淆 ====================
AI_FINGERPRINT_OBFUSCATION = True   # 图像指纹混淆
AI_DISTORTION_STRENGTH = 0.002      # 扭曲强度 (0.001-0.005)

# ==================== 🆕 紫边模拟 ====================
AI_CHROMATIC_ABERRATION = True      # 紫边/色散模拟（真实镜头特征）
AI_CHROMATIC_STRENGTH = 0.3         # 紫边强度 (0.1-0.8)