# core/pipeline/steps/three_d_render_step.py
"""3D渲染风格转换步骤 - 使用 BaseStyleStep"""

from ..base_step import BaseStyleStep


class ThreeDRenderStep(BaseStyleStep):
    """3D渲染风格转换步骤"""
    
    def __init__(self):
        super().__init__("3d_render", "转换为3D渲染风格")
        self._config = {
            "strength": 0.50,
            "cfg": 8.5,
            "steps": 35,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "canny",
            "controlnet_strength": 0.6,
        }
    
    def get_default_config(self) -> dict:
        return self._config
    
    def get_config_schema(self) -> dict:
        return {
            "strength": {"type": "float", "default": 0.50, "min": 0.3, "max": 0.7},
            "cfg": {"type": "float", "default": 8.5, "min": 6, "max": 12},
            "steps": {"type": "int", "default": 35, "min": 25, "max": 60},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {
                "type": "choice",
                "default": "canny",
                "choices": ["canny", "hed", "lineart", "scribble", "depth"]
            },
            "controlnet_strength": {"type": "float", "default": 0.6, "min": 0.1, "max": 1.0},
        }
    
    def get_prompts(self) -> list:
        return [
            {
                "name": "3D人物",
                "prompt": "3d render, beautiful woman, realistic cgi, detailed, high quality, octane render, cinema 4d, blender, soft lighting, high detail, masterpiece, digital art",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, 2d, painting, sketch, photorealistic"
            },
            {
                "name": "3D场景",
                "prompt": "3d render, beautiful scene, realistic cgi, detailed, high quality, octane render, cinema 4d, blender, soft lighting, high detail, masterpiece, digital art",
                "negative": "worst quality, low quality, ugly, deformed, blurry, watermark, text, signature, 2d, painting, sketch"
            },
            {
                "name": "3D角色",
                "prompt": "3d render, fantasy character, beautiful woman, realistic cgi, detailed, high quality, octane render, cinema 4d, blender, soft lighting, high detail, masterpiece, digital art",
                "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature, 2d, painting, sketch"
            }
        ]