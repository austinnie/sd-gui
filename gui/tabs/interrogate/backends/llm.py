# gui/tabs/interrogate/backends/llm.py
"""LLM 反推后端 - 使用 BLIP + LLM 增强"""

from PIL import Image
from .base import InterrogateBackend
from services.llm_service import llm_service
from .blip import BlipBackend


from utils.logger import get_logger, info, warning, error, debug

logger = get_logger(__name__)
class LLMBackend(InterrogateBackend):
    """LLM 增强后端 - BLIP 描述 + LLM 优化"""
    
    def interrogate(self, image_path: str, **kwargs) -> str:
        if self.tab.cancel_interrogate:
            return "已取消"
        
        # 1. 先用 BLIP 生成描述
        blip = BlipBackend(self.tab)
        caption = blip.interrogate(image_path, model_name="BLIP-large (详细)")
        
        if self.tab.cancel_interrogate:
            return "已取消"
        
        # 2. 检查 LLM 是否可用
        if not llm_service.is_available():
            # 如果 LLM 不可用，尝试启动检查
            llm_service.check_status()
            if not llm_service.is_available():
                return f"{caption}\n\n⚠️ LLM 未就绪，使用 BLIP 原始描述\n请确保 Ollama 已启动并下载模型"
        
        # 3. 使用 LLM 增强
        logger.info(f"🧠 使用 LLM 增强描述...")
        
        prompt = f"""请将以下图片描述转换为 Stable Diffusion 提示词格式（英文，用逗号分隔）：

原始描述：{caption}

要求：
1. 添加高质量修饰词：masterpiece, best quality, photorealistic, 8k
2. 如果是人物，描述性别、服装、表情、背景
3. 如果是风景，描述光线、氛围、色彩
4. 用英文，逗号分隔

正面提示词："""

        try:
            llm_result = llm_service.generate(prompt, timeout=30, max_tokens=300)
            
            if not llm_result:
                return f"{caption}\n\n⚠️ LLM 生成失败，使用 BLIP 原始描述"
            
            # 提取提示词
            import re
            match = re.search(r'正面提示词[：:]\s*(.+?)(?=\n|$)', llm_result, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            # 如果格式不对，清理后返回
            clean = llm_result.strip()
            # 移除可能的"正面提示词："前缀
            clean = re.sub(r'^正面提示词[：:]\s*', '', clean)
            return clean
            
        except Exception as e:
            logger.info(f"⚠️ LLM 增强失败: {e}")
            return f"{caption}\n\n⚠️ LLM 增强失败，使用 BLIP 原始描述"