# gui/chat/utils/param_estimator.py
"""参数估算工具"""

import tkinter as tk


class ParamEstimator:
    """参数估算器"""
    
    @staticmethod
    def estimate_params(prompt: str, quality_mode: str = "快速") -> dict:
        """估算参数"""
        prompt_lower = prompt.lower()

        is_portrait = any(k in prompt_lower for k in ['portrait', 'headshot', 'close up', 'face', '头像', '特写'])
        is_full_body = any(k in prompt_lower for k in ['full body', 'standing', '全身', '站立'])
        is_landscape = any(k in prompt_lower for k in ['landscape', 'scenery', '风景', '山水'])
        is_couple = any(k in prompt_lower for k in ['couple', 'two people', '双人', '情侣'])

        # 根据模式调整尺寸
        if quality_mode == "超高质量":
            size_config = {
                "portrait": (768, 1024),
                "full_body": (768, 1152),
                "landscape": (1344, 768),
                "couple": (896, 1344),
                "default": (768, 1024),
            }
            steps_override = 30
        elif quality_mode == "快速":
            size_config = {
                "portrait": (256, 384),
                "full_body": (256, 384),
                "landscape": (448, 256),
                "couple": (320, 448),
                "default": (256, 384),
            }
            steps_override = 8
        elif quality_mode == "平衡":
            size_config = {
                "portrait": (384, 512),
                "full_body": (384, 576),
                "landscape": (640, 384),
                "couple": (448, 640),
                "default": (384, 576),
            }
            steps_override = 12
        else:  # 高质量
            size_config = {
                "portrait": (512, 640),
                "full_body": (512, 768),
                "landscape": (896, 512),
                "couple": (640, 896),
                "default": (512, 768),
            }
            steps_override = 20

        if is_portrait:
            width, height = size_config["portrait"]
        elif is_full_body:
            width, height = size_config["full_body"]
        elif is_landscape:
            width, height = size_config["landscape"]
        elif is_couple:
            width, height = size_config["couple"]
        else:
            width, height = size_config["default"]

        return {"width": width, "height": height, "steps": steps_override}
    
    @staticmethod
    def optimize_parameters(prompt: str, image_features: dict = None) -> dict:
        """优化参数（图生图用）"""
        prompt_lower = prompt.lower()
        params = {}

        if any(k in prompt_lower for k in ['快速', '快', 'quick', 'fast']):
            params["steps"] = 8
        elif any(k in prompt_lower for k in ['高质量', 'high quality', 'masterpiece']):
            params["steps"] = 30
        else:
            params["steps"] = 12

        if any(k in prompt_lower for k in ['写实', 'realistic']):
            params["cfg"] = 8.0
        elif any(k in prompt_lower for k in ['动漫', 'anime']):
            params["cfg"] = 6.5
        else:
            params["cfg"] = 7.5

        if any(k in prompt_lower for k in ['微调', 'slight']):
            params["strength"] = 0.25
        elif any(k in prompt_lower for k in ['大幅', 'major']):
            params["strength"] = 0.55
        else:
            params["strength"] = 0.40

        if image_features and image_features.get("has_face"):
            params["strength"] = min(params["strength"], 0.35)

        return params