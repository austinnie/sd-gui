# core/pipeline/steps/ink_wash_step.py
"""国风水墨风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class InkWashStep(BaseStyleStep):
    """国风水墨风格转换步骤"""
    
    def __init__(self):
        super().__init__("ink_wash", "转换为国风水墨风格")
        self._config = {
            "strength": 0.45,
            "cfg": 7.5,
            "steps": 30,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "lineart",
            "controlnet_strength": 0.6,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.45, "min": 0.25, "max": 0.65},
            "cfg": {"type": "float", "default": 7.5, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 30, "min": 20, "max": 50},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "lineart",
                "choices": ["canny", "hed", "lineart", "scribble"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        """生成国风水墨风格的 12 种场景提示词"""
        # 统一的高强度负面防御词（适配 SD 1.5 特点，专门防御断手和假印章）
        base_negative = (
            "worst quality, low quality, ugly, deformed, blurry, bad anatomy, "
            "(mutated hands and fingers:1.5), (fused fingers:1.5), (fused hand:1.5), "
            "(missing fingers:1.5), (extra digits:1.5), (red stamp:1.4), watermark, text, signature, "
            "photorealistic, 3d render, oil painting, color, neon, modern, over-saturated"
        )

        return [
            # ===== 原版 4 个场景的笔触增强版 =====
            {
                "name": "水墨人物_增强",
                "prompt": "ink wash painting style, traditional Chinese painting, a beautiful woman, splashed ink and dry brush technique, delicate ink wash shading, black ink on rice paper, elegant minimalist style, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "水墨山水_增强",
                "prompt": "ink wash painting style, traditional Chinese landscape, mountains and rivers, flying white brush strokes, wet wash technique, rich tonal contrast, black ink on rice paper, elegant minimalist style, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "水墨花鸟_增强",
                "prompt": "ink wash painting style, traditional Chinese flower and bird painting, elegant brush strokes, soft ink diffusion, black ink on rice paper, minimalist style, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "水墨古风_增强",
                "prompt": "ink wash painting style, ancient Chinese style, elegant lady in traditional clothing, flowing brush strokes, ink wash texture, black ink on rice paper, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },

            # ===== 新增 4 个：针对手部结构优化（执扇/执笔/坐船/剪影） =====
            {
                "name": "水墨仕女执扇",
                "prompt": "ink wash painting style, traditional Chinese painting, a beautiful woman holding a traditional folding fan, ribs clearly separated by fingers, elegant graceful pose, flowing ink brush strokes, black ink on rice paper, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "水墨仕女执笔",
                "prompt": "ink wash painting style, traditional Chinese painting, a beautiful woman holding a writing brush, fingers clearly defined around the brush, elegant pose, flowing ink brush strokes, black ink on rice paper, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "水墨轻舟小憩",
                "prompt": "ink wash painting style, traditional Chinese painting, a beautiful woman sitting in a small wooden boat on a misty river, holding a bamboo pole, elegant brush strokes, black ink on rice paper, minimalist composition, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "水墨圆月剪影",
                "prompt": "ink wash painting style, traditional Chinese painting, a beautiful woman, elegant silhouette standing against a full moon, dramatic ink contrast, flying ink, minimalist black ink on rice paper, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },

            # ===== 新增 4 个：纯风景/植物（避开人体结构陷阱） =====
            {
                "name": "水墨山水_飞白",
                "prompt": "ink wash painting style, traditional Chinese landscape, majestic mountains, dry brush technique, flying white (feibai) effect on flowing river, black ink on rice paper, misty atmosphere, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "水墨花鸟_剪影",
                "prompt": "ink wash painting style, traditional Chinese flower and bird painting, two birds silhouettes perched on a branch, wet ink wash, soft ink diffusion, minimalist composition, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "水墨寒梅绽放",
                "prompt": "ink wash painting style, traditional Chinese painting, a blooming plum blossom branch, splashed ink, dry brush texture, delicate flowers, black ink on rice paper, elegant minimalist style, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            },
            {
                "name": "水墨太极武者",
                "prompt": "ink wash painting style, traditional Chinese painting, a beautiful woman doing Tai Chi, dynamic posture, flowing wide-sleeved robes, distinct folds, black ink on rice paper, elegant minimalist style, oriental art, high quality, masterpiece, fine art, monochrome",
                "negative": base_negative
            }
        ]