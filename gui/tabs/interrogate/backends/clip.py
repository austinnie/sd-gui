# gui/tabs/interrogate/backends/clip.py
"""CLIP 反推后端 - 带 LLM 降级"""

import re
from PIL import Image
from .base import InterrogateBackend

_cli_interrogator = None

# ✅ 添加导入
from services.llm_service import llm_service

# ✅ 在文件顶部添加
import os
from services.cache_config import CACHE_ROOT

_cli_interrogator = None

class ClipBackend(InterrogateBackend):
    """CLIP 详细模式（支持 LLM 降级）"""
    
    def interrogate(self, image_path: str, **kwargs) -> str:
        global _cli_interrogator
        
        mode = kwargs.get('mode', 'fast')
        model = kwargs.get('model', 'ViT-L-14/openai')
        
        # 尝试加载 CLIP Interrogator
        if _cli_interrogator is None:
            # ✅ 在 try 外面定义
            cache_path = os.path.join(CACHE_ROOT, "clip_interrogator")
            os.makedirs(cache_path, exist_ok=True)
            
            try:
                from clip_interrogator import Config, Interrogator
                config = Config()
                config.clip_model_name = "ViT-L-14/openai"
                config.device = "cpu"
                # ✅ 指定缓存目录
                config.cache_dir = cache_path
                _cli_interrogator = Interrogator(config)
                print("✅ CLIP Interrogator 加载成功")
                print(f"   📁 缓存: {cache_path}")
            except ImportError:
                print("⚠️ CLIP Interrogator 未安装，使用 LLM 降级方案")
                return self._fallback_with_llm(image_path, mode)
            except Exception as e:
                print(f"⚠️ CLIP 加载失败: {e}")
                return self._fallback_with_llm(image_path, mode)
        
        if _cli_interrogator is None:
            return self._fallback_with_llm(image_path, mode)
        
        try:
            image = Image.open(image_path).convert('RGB')
            if max(image.size) > 512:
                image.thumbnail((512, 512))
            
            if mode == "best":
                result = _cli_interrogator.interrogate(image)
            elif mode == "fast":
                result = _cli_interrogator.interrogate_fast(image)
            else:
                result = _cli_interrogator.interrogate_classic(image)
            
            result = result.replace('"', '').replace('"', '')
            result = re.sub(r'\s+', ' ', result).strip()
            return result
            
        except Exception as e:
            print(f"⚠️ CLIP 推理失败: {e}")
            return self._fallback_with_llm(image_path, mode)
    
    def _fallback_with_llm(self, image_path: str, mode: str) -> str:
        """使用 BLIP + LLM 作为降级方案"""
        print("🔄 使用 BLIP + LLM 降级方案...")
        
        # 1. 先用 BLIP 生成描述
        from .blip import BlipBackend
        blip = BlipBackend(self.tab)
        caption = blip.interrogate(image_path, model_name="BLIP-large (详细)")
        
        if self.tab.cancel_interrogate:
            return "已取消"
        
        # 2. ✅ 直接使用 llm_service
        if llm_service.is_available():
            print("🧠 使用 LLM 增强描述...")
            prompt = f"""请将以下图片描述转换为 Stable Diffusion 提示词格式（英文，用逗号分隔）：

原始描述：{caption}

要求：
1. 添加高质量修饰词：masterpiece, best quality, photorealistic, 8k
2. 如果是人物，描述性别、服装、表情、背景
3. 用英文，逗号分隔

正面提示词："""
            
            llm_result = llm_service.generate(prompt, timeout=30, max_tokens=200)
            if llm_result:
                import re
                match = re.search(r'正面提示词[：:]\s*(.+?)(?=\n|$)', llm_result, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
                return llm_result.strip()
        
        # 3. 没有 LLM，直接使用 BLIP 结果
        return caption